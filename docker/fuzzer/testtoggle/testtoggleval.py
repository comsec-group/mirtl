# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import json
import os
import subprocess
import random
import concurrent.futures

from pybackend.backend import build_executable_worker, run_executable_worker
from pybackend.cleanupnetlist import cleanup_netlist
from pycommon.fuzzparams import FuzzerParams, FuzzerState
from pycommon.runparams import RunParams, SimulatorType
from pynetgenerator.genonebyone import gen_random_onebyone_netlist, gen_total_num_cells, gen_netlist_from_cells_and_netwires, find_requesters_per_clkin_type
from pynetgenerator.splitsubnetids import split_subnet_ids, ClkInType
from pycellgenerator.allcells import randomize_authorized_combinational_cell_types, randomize_authorized_stateful_cell_types, ALL_CELL_PORTS_STATEFUL
from pyentropy.togglevalanalysis import toggleval_coverage

import multiprocessing as mp
from copy import deepcopy

PATH_TO_WORKDIR_ROOT = '/scratch/simufuzz-workdir'

DO_TRACE = True # Traces are required in the toggle experiment

def testtoggleval_wrapper(workload, min_num_cells, max_num_cells, simlen: int):
    timeout = 20

    while True:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit the function to the executor
            future = executor.submit(__testtoggleval, workload, min_num_cells, max_num_cells, simlen)

            # Wait for the function to complete or timeout
            try:
                ret = future.result(timeout=timeout)
                if ret is not None:
                    return ret
                else:
                    workload += 1000000
            except concurrent.futures.TimeoutError:
                workload += 1000000

# For a single workload, flip a single bit and see whether the output has changed
def __testtoggleval(workload, min_num_cells, max_num_cells, simlen: int):
    try:
        random.seed(workload)
        workdir = os.path.join(PATH_TO_WORKDIR_ROOT, f"tmp/obj_dir_example_testtoggleval_{workload}")

        num_cells = gen_total_num_cells(min_num_cells, max_num_cells)
        authorized_combinational_cell_types = randomize_authorized_combinational_cell_types([])
        authorized_stateful_cell_types      = randomize_authorized_stateful_cell_types(True, [])
        proportion_final_cells_connected_to_output = random.uniform(FuzzerParams.ProportionFinalCellsConnectedToOutputMin, FuzzerParams.ProportionFinalCellsConnectedToOutputMax)
        fuzzerstate = FuzzerState(workdir, FuzzerParams.CellMinDimension, FuzzerParams.CellMaxDimension, True, min_num_cells, max_num_cells, FuzzerParams.MinInputWidthWords, max(FuzzerParams.MinOutputWidthWords, proportion_final_cells_connected_to_output), simlen, DO_TRACE, authorized_combinational_cell_types, authorized_stateful_cell_types)

        BASE_SUBNET_ID = 0 # Be careful if you modify this because stuff does not get mixed up in netlist.json (which cells belong to which subnet)
        all_cells_base, all_netwires_base = gen_random_onebyone_netlist(fuzzerstate, BASE_SUBNET_ID, num_cells)

        # Create the subnets
        all_requesters_per_clkin_type = find_requesters_per_clkin_type([all_cells_base], [BASE_SUBNET_ID])

        # Split the clocks
        splitted_requesters_per_clkin_type = split_subnet_ids(all_requesters_per_clkin_type)
        del all_requesters_per_clkin_type

        all_cells_list = [all_cells_base]
        all_netwires_list = [all_netwires_base]
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
        build_executable_worker(fuzzerstate, netlist_dict, SimulatorType.SIM_VERILATOR, False, True, template_input_port_tuples)
        elapsed_time_noflip, output_signature_noflip, _, stderr_noflip = run_executable_worker(fuzzerstate, SimulatorType.SIM_VERILATOR)

        incremental_coverage = toggleval_coverage(fuzzerstate.get_tracefile(), simlen)
        return incremental_coverage

    except subprocess.TimeoutExpired:
        print(f"Timeout exception in workload {workload}")
        return None
