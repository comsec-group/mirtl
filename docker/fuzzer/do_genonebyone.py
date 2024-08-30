# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import json
import os
import subprocess
import multiprocessing as mp
import sys
import random
import numpy as np

# sys.argv[1]: number of processes
# sys.argv[2]: max num cells main
# sys.argv[3]: simlen

PATH_TO_WORKDIR_ROOT = '/scratch/simufuzz-workdir'

from pydefs.netwire import NetWire
from pybackend.backend import build_executable_worker, run_executable_worker
from pybackend.cleanupnetlist import cleanup_netlist
from pytriage.triage import triage_err_msg
from pycommon.fuzzparams import FuzzerParams, FuzzerState
from pycommon.runparams import SimulatorType
from pynetgenerator.genonebyone import gen_random_onebyone_netlist, gen_total_num_cells, gen_netlist_from_cells_and_netwires, find_requesters_per_clkin_type
from pynetgenerator.splitsubnetids import split_subnet_ids, ClkInType
from pycellgenerator.allcells import randomize_authorized_combinational_cell_types, randomize_authorized_stateful_cell_types, ALL_CELL_PORTS_STATEFUL

# Select the EDA tools to be compared here
FirstSimulator = SimulatorType.SIM_ICARUS
# Verilator should always be second, not first (just because of a fix for file system issues)
SecondSimulator = SimulatorType.SIM_VERILATOR

if __name__ != '__main__':
    raise ImportError('This module cannot be imported')

################
# Collect the arguments
################

num_processes = int(sys.argv[1])
num_workloads_per_pool = 1000000

min_num_cells = 2
max_num_cells = int(sys.argv[2])

simlen = int(sys.argv[3])

DO_TRACE = False
if DO_TRACE:
    print(f"Warning: DO_TRACE is set to True")

################
# Create and run the workloads
################

def run_workload(workload, match_verbose: bool = True):
    try:
        random.seed(workload)
        np.random.seed(workload)
        workdir = os.path.join(PATH_TO_WORKDIR_ROOT, f"tmp/obj_dir_example_sim_{workload}")

        num_cells = gen_total_num_cells(min_num_cells, max_num_cells)
        authorized_combinational_cell_types = randomize_authorized_combinational_cell_types([])
        authorized_stateful_cell_types      = randomize_authorized_stateful_cell_types(True, [])
        proportion_final_cells_connected_to_output = random.uniform(FuzzerParams.ProportionFinalCellsConnectedToOutputMin, FuzzerParams.ProportionFinalCellsConnectedToOutputMax)
        fuzzerstate = FuzzerState(workdir, FuzzerParams.CellMinDimension, FuzzerParams.CellMaxDimension, True, min_num_cells, max_num_cells, FuzzerParams.MinInputWidthWords, max(FuzzerParams.MinOutputWidthWords, proportion_final_cells_connected_to_output), simlen, DO_TRACE, authorized_combinational_cell_types, authorized_stateful_cell_types)

        BASE_SUBNET_ID = 0 # Be careful if you modify this because stuff does not get mixed up in netlist.json (which cells belong to which subnet)
        all_cells_base, all_netwires_base = gen_random_onebyone_netlist(fuzzerstate, BASE_SUBNET_ID, num_cells)

        # Find the requested clock signals
        all_requesters_per_clkin_type = find_requesters_per_clkin_type([all_cells_base], [BASE_SUBNET_ID])

        # Split the clocks
        splitted_requesters_per_clkin_type = split_subnet_ids(all_requesters_per_clkin_type)
        del all_requesters_per_clkin_type

        all_cells_list = [all_cells_base]
        all_netwires_list = [all_netwires_base]


        # Potentially create a second subnet to provide one of the clkin signals
        if splitted_requesters_per_clkin_type and random.random() < FuzzerParams.ProbaSecondSubnet:
            # Pick a random clkin type
            clkin_type = random.choice(list(splitted_requesters_per_clkin_type.keys()))
            clkin_type_wire = random.randrange(len(splitted_requesters_per_clkin_type[clkin_type]))
            clkin_cell_port_list = splitted_requesters_per_clkin_type[clkin_type][clkin_type_wire]
            del splitted_requesters_per_clkin_type[clkin_type][clkin_type_wire]

            # Create a new subnet
            all_cells_second, all_netwires_second = gen_random_onebyone_netlist(fuzzerstate, BASE_SUBNET_ID + 1, FuzzerParams.MaxNumCellsNonPrimarySubnet)

            # Add the offset to the input and output ports, as they are scaled by the number of subnets
            for netwire in all_netwires_second:
                if netwire.dst_port_name == "O":
                    netwire.dst_port_offset += 32*FuzzerParams.MinOutputWidthWords*(BASE_SUBNET_ID + 1)
                if netwire.src_port_name == "I":
                    netwire.src_port_offset += 32*FuzzerParams.MinInputWidthWords*(BASE_SUBNET_ID + 1)

            all_requesters_per_clkin_type_second = find_requesters_per_clkin_type([all_cells_second], [BASE_SUBNET_ID+1])
            splitted_requesters_per_clkin_type_second = split_subnet_ids(all_requesters_per_clkin_type_second)
            del all_requesters_per_clkin_type_second
            # Merge the splitted requesters: they should not tick at the same time
            for clkin_type in splitted_requesters_per_clkin_type_second:
                splitted_requesters_per_clkin_type[clkin_type] = splitted_requesters_per_clkin_type.get(clkin_type, []) + splitted_requesters_per_clkin_type_second[clkin_type]

            all_cells_list.append(all_cells_second)
            all_netwires_list.append(all_netwires_second)

            # Add the connections from one output to the other inputs
            # Find some output bit
            out_netwire_list_second = list(filter(lambda netwire: netwire.dst_port_name == "O", all_netwires_second))
            out_netwire_selected_second = random.choice(out_netwire_list_second)

            for clkin_cell_port in clkin_cell_port_list:
                dst_subnet_id, dst_cell_id, dst_port_name, dst_port_width = clkin_cell_port
                src_cell_id = out_netwire_selected_second.src_cell_id
                src_port_name = out_netwire_selected_second.src_port_name
                src_port_offset = out_netwire_selected_second.src_port_offset
                src_port_width = out_netwire_selected_second.width
                assert dst_port_width == 1, f"dst_port_width: {dst_port_width}"
                # assert dst_port_width == src_port_width, f"dst_port_width: {dst_port_width}, src_port_width: {src_port_width}"
                new_netwire = NetWire(dst_subnet_id, dst_cell_id, dst_port_name, 0, BASE_SUBNET_ID + 1, src_cell_id, src_port_name, src_port_offset, 1)
                all_netwires_list[-1].append(new_netwire)

        netlist_dict = gen_netlist_from_cells_and_netwires(fuzzerstate, all_cells_list, all_netwires_list, splitted_requesters_per_clkin_type)
        num_subnets = len(netlist_dict['cell_types'])
        num_subnets_or_clkins = num_subnets + len(netlist_dict['clkin_ports_names'])

        # Generate the random inputs. This is a list of pairs (subnet_or_clkin_id, input id)
        random_inputs_list = []
        # Actually, we start by setting all the clocks to 0 so all the posedge events are understood equally by all simulators.
        curr_clkin_id = num_subnets
        for clkin_type in splitted_requesters_per_clkin_type:
            for clkin_subnet_id, clkin_subnet in enumerate(splitted_requesters_per_clkin_type[clkin_type]):
                random_inputs_list.append((curr_clkin_id, 0))
                curr_clkin_id += 1

        for _ in range(fuzzerstate.simlen):
            curr_rand = random.random()
            curr_is_subnet = num_subnets_or_clkins == num_subnets or curr_rand < FuzzerParams.ProbaToggleSubnet
            if curr_is_subnet:
                curr_subnet_or_clkin_id = random.randint(0, num_subnets - 1)
            else:
                curr_subnet_or_clkin_id = random.randint(num_subnets, num_subnets_or_clkins - 1)

            curr_is_subnet = curr_subnet_or_clkin_id < num_subnets
            if curr_is_subnet and fuzzerstate.is_input_full_random:
                new_line = tuple([curr_subnet_or_clkin_id] + [random.randint(0, 2 ** 32 - 1) for _ in range(fuzzerstate.num_input_words)])
                random_inputs_list.append(new_line)
            else:
                random_inputs_list.append((curr_subnet_or_clkin_id, random.randint(0, 2 ** 32 - 1)))
        inputs_str_lines = [str(len(random_inputs_list))]
        for curr_tuple in random_inputs_list:
            inputs_str_lines.append(' '.join(map(lambda val: hex(val)[2:], curr_tuple)))

        os.makedirs(workdir, exist_ok=True)
        # Write netlist
        netlist_dict = cleanup_netlist(netlist_dict)

        # Generate the tuples for the clkin-type inputs
        template_input_port_tuples = []
        for clkin_type in splitted_requesters_per_clkin_type:
            for clkin_subnet_id, clkin_subnet in enumerate(splitted_requesters_per_clkin_type[clkin_type]):
                template_input_port_tuples.append((f"{ClkInType.to_char(clkin_type)}{clkin_subnet_id}", max(map(lambda c: c[3], clkin_subnet))))

        with open(os.path.join(workdir, 'netlist.json'), 'w') as f:
            json.dump(netlist_dict, f)
        # Write random inputs
        with open(os.path.join(workdir, 'inputs.txt'), 'w') as f:
            f.write('\n'.join(inputs_str_lines))

        # The first simulator
        build_executable_worker(fuzzerstate, netlist_dict, FirstSimulator, False, True, template_input_port_tuples)
        elapsed_time_first, output_signature_first, _, stderr_first = run_executable_worker(fuzzerstate, FirstSimulator)
        if elapsed_time_first is None:
            print(f"Skipping workload {workload} as Verilator did not finish")
            return
        # if elapsed_time_first is not None:
        #     # Remove the work directory using os
        #     print(f"Elapsed time for wl {workload:>6}: {elapsed_time_first:>4}, output signature: {hex(int(output_signature_first, 10)).rjust(14) if output_signature_first else 'X'}")
        # else:
        #     print(f"Elapsed time is None in workload {workload}")

        # The second simulator
        build_executable_worker(fuzzerstate, netlist_dict, SecondSimulator, False, True, template_input_port_tuples)
        elapsed_time_second, output_signature_second, _, stderr_second = run_executable_worker(fuzzerstate, SecondSimulator)
        # if elapsed_time_second is not None:
        #     # Remove the work directory using os
        #     print(f"Elapsed time for wl {workload:>6}: {elapsed_time_second:>4}, output signature: {hex(int(output_signature_second, 10)).rjust(14) if output_signature_second else 'X'}")
        # else:
        #     print(f"Elapsed time is None in workload {workload}")

        if elapsed_time_first is not None and elapsed_time_second is not None:
            if output_signature_first != output_signature_second:
                # Try a second time to build Verilator
                subprocess.run(f"rm -rf {workdir}/obj_dir", shell=True)
                build_executable_worker(fuzzerstate, netlist_dict, SecondSimulator, False, True, template_input_port_tuples)
                elapsed_time_second, output_signature_second, _, stderr_second = run_executable_worker(fuzzerstate, SecondSimulator)

                if output_signature_first != output_signature_second:
                    print(f"Output signatures are different for wl {workload}: {hex(int(output_signature_first))} and {hex(int(output_signature_second))}, num cells: {num_cells}")
                else:
                    print(f"Match {hex(int(output_signature_first)):>16} wl {int(workload):>16} (second attempt)")
                    subprocess.run(f"rm -rf {workdir}", shell=True)
            else:
                if match_verbose:
                    print(f"Match {hex(int(output_signature_first)):>16} wl {int(workload):>16}")
                subprocess.run(f"rm -rf {workdir}", shell=True)
        else:
            print(f"Warning: Could not compare signatures as some did not finish (Verilator finished: {elapsed_time_first is not None}, Icarus finished: {elapsed_time_second is not None})")

    except Exception as e:
        print(f"Exception info (workload {workload}): {e}")
        print(f"Error in workload {workload}: {triage_err_msg(stderr_first) if stderr_first is not None else 'No stderr.'}")

print(f"Running one-by-one cell insertion on {num_processes} processes with params min_cells: {min_num_cells}, max_cells: {max_num_cells}, simlen: {simlen}")
# Arbitrary initial seed
while_id = 0

while True:
    while_id += 1
    workloads = [while_id*num_workloads_per_pool + i for i in range(num_workloads_per_pool)]
    with mp.Pool(num_processes) as pool:
        pool.map(run_workload, workloads)
