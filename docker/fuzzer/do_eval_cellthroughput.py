# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Throughput of cells when testing Yosys against

import json
import os
import multiprocessing as mp
import sys
import random
import time

# sys.argv[1]: number of processes

PATH_TO_WORKDIR_ROOT = '/scratch/simufuzz-workdir'

from pybackend.backend import build_executable_worker, run_executable_worker, get_cell_stats
from pybackend.cleanupnetlist import cleanup_netlist
from pycommon.fuzzparams import FuzzerParams, FuzzerState
from pycommon.runparams import SimulatorType
from pynetgenerator.genonebyone import gen_random_onebyone_netlist, gen_total_num_cells, gen_netlist_from_cells_and_netwires, find_requesters_per_clkin_type
from pynetgenerator.splitsubnetids import split_subnet_ids, ClkInType
from pycellgenerator.allcells import randomize_authorized_combinational_cell_types, randomize_authorized_stateful_cell_types, ALL_CELL_PORTS_STATEFUL

if __name__ != '__main__':
    raise ImportError('This module cannot be imported')

################
# Collect the arguments
################

num_processes = int(sys.argv[1])
num_workloads_per_pool = 1000000

num_reps_per_point = 200

simulator_names = ['Verilator', 'Icarus', 'cxxrtl']

num_cells       = 1000
simulators      = list(map(int, [SimulatorType.SIM_VERILATOR, SimulatorType.SIM_ICARUS, SimulatorType.SIM_CXXRTL])) #[SimulatorType.SIM_VERILATOR, SimulatorType.SIM_ICARUS, SimulatorType.SIM_CXXRTL]))
simlen = 70

min_num_cells_clockdrivers = 0
max_num_cells_clockdrivers = 0

DO_TRACE = False
if DO_TRACE:
    print(f"Warning: DO_TRACE is set to True")

################
# Create and run the workloads
################

def format_with_commas(value, _):
    return "{:,.0f}".format(value)

# Return elapsed time in seconds
def run_workload(workload):
    try:
        num_cells, simulator_id, simlen, workload_id = workload
        random.seed(workload_id)
        workdir_opt = os.path.join(PATH_TO_WORKDIR_ROOT, f"tmp/obj_dir_example_yosys_opt_{workload_id}")
        workdir_noopt = os.path.join(PATH_TO_WORKDIR_ROOT, f"tmp/obj_dir_example_yosys_noopt_{workload_id}")

        num_cells = gen_total_num_cells(num_cells, num_cells)
        num_cells_clockdrivers = gen_total_num_cells(min_num_cells_clockdrivers, max_num_cells_clockdrivers)
        authorized_combinational_cell_types = randomize_authorized_combinational_cell_types([])
        authorized_stateful_cell_types      = randomize_authorized_stateful_cell_types(True, [])
        proportion_final_cells_connected_to_output = random.uniform(FuzzerParams.ProportionFinalCellsConnectedToOutputMin, FuzzerParams.ProportionFinalCellsConnectedToOutputMax)
        fuzzerstate_opt = FuzzerState(workdir_opt, FuzzerParams.CellMinDimension, FuzzerParams.CellMaxDimension, True, num_cells, num_cells, FuzzerParams.MinInputWidthWords, max(FuzzerParams.MinOutputWidthWords, proportion_final_cells_connected_to_output), simlen, DO_TRACE, authorized_combinational_cell_types, authorized_stateful_cell_types)

        BASE_SUBNET_ID = 0 # Be careful if you modify this because stuff does not get mixed up in netlist.json (which cells belong to which subnet)
        all_cells_base, all_netwires_base = gen_random_onebyone_netlist(fuzzerstate_opt, BASE_SUBNET_ID, num_cells)

        # Create the subnets
        all_requesters_per_clkin_type = find_requesters_per_clkin_type([all_cells_base], [BASE_SUBNET_ID])

        # Split the clocks
        splitted_requesters_per_clkin_type = split_subnet_ids(all_requesters_per_clkin_type)
        del all_requesters_per_clkin_type

        all_cells_list = [all_cells_base]
        all_netwires_list = [all_netwires_base]
        netlist_dict = gen_netlist_from_cells_and_netwires(fuzzerstate_opt, all_cells_list, all_netwires_list, splitted_requesters_per_clkin_type)
        num_subnets = len(netlist_dict['cell_types'])
        num_subnets_or_clkins = num_subnets + len(netlist_dict['clkin_ports_names'])


        # all_cells_first, all_netwires_first = gen_random_onebyone_netlist(fuzzerstate_opt, num_cells_clockdrivers, None)
        # all_cells_list, all_netwires_list = [all_cells_first, all_cells_base], [all_netwires_first, all_netwires_base]

        # Generate the random inputs. This is a list of pairs (subnet_or_clkin_id, input id)
        random_inputs_list = []
        # Actually, we start by setting all the clocks to 0 so all the posedge events are understood equally by all simulators.
        curr_clkin_id = num_subnets
        for clkin_type in splitted_requesters_per_clkin_type:
            for clkin_subnet_id, clkin_subnet in enumerate(splitted_requesters_per_clkin_type[clkin_type]):
                random_inputs_list.append((curr_clkin_id, 0))
                curr_clkin_id += 1

        for _ in range(fuzzerstate_opt.simlen):
            curr_rand = random.random()
            curr_is_subnet = num_subnets_or_clkins == num_subnets or curr_rand < FuzzerParams.ProbaToggleSubnet
            if curr_is_subnet:
                curr_subnet_or_clkin_id = random.randint(0, num_subnets - 1)
            else:
                curr_subnet_or_clkin_id = random.randint(num_subnets, num_subnets_or_clkins - 1)

            curr_is_subnet = curr_subnet_or_clkin_id < num_subnets
            if curr_is_subnet and fuzzerstate_opt.is_input_full_random:
                new_line = tuple([curr_subnet_or_clkin_id] + [random.randint(0, 2 ** 32 - 1) for _ in range(fuzzerstate_opt.num_input_words)])
                random_inputs_list.append(new_line)
            else:
                random_inputs_list.append((curr_subnet_or_clkin_id, random.randint(0, 2 ** 32 - 1))) 
        inputs_str_lines = [str(len(random_inputs_list))]
        for curr_tuple in random_inputs_list:
            inputs_str_lines.append(' '.join(map(lambda val: hex(val)[2:], curr_tuple)))

        os.makedirs(workdir_noopt, exist_ok=True)
        os.makedirs(workdir_opt, exist_ok=True)
        # Write netlist
        netlist_dict = cleanup_netlist(netlist_dict)

        # Generate the tuples for the clkin-type inputs
        template_input_port_tuples = []
        for clkin_type in splitted_requesters_per_clkin_type:
            for clkin_subnet_id, clkin_subnet in enumerate(splitted_requesters_per_clkin_type[clkin_type]):
                template_input_port_tuples.append((f"{ClkInType.to_char(clkin_type)}{clkin_subnet_id}", max(map(lambda c: c[3], clkin_subnet))))

        with open(os.path.join(workdir_noopt, 'netlist.json'), 'w') as f:
            json.dump(netlist_dict, f)
        # Write random inputs
        with open(os.path.join(workdir_noopt, 'inputs.txt'), 'w') as f:
            f.write('\n'.join(inputs_str_lines))

        with open(os.path.join(workdir_opt, 'netlist.json'), 'w') as f:
            json.dump(netlist_dict, f)
        # Write random inputs
        with open(os.path.join(workdir_opt, 'inputs.txt'), 'w') as f:
            f.write('\n'.join(inputs_str_lines))

        # simulator_opt = random.choice([SimulatorType.SIM_ICARUS, SimulatorType.SIM_ICARUS])
        simulator_opt = SimulatorType.SIM_ICARUS
        # simulator_noopt = random.choice([SimulatorType.SIM_ICARUS, SimulatorType.SIM_ICARUS])
        simulator_noopt = SimulatorType.SIM_ICARUS

        simulator_id_icarus = simulators.index(SimulatorType.SIM_ICARUS)

        start_time = time.time()
        # Opt
        build_executable_worker(fuzzerstate_opt, netlist_dict, simulator_opt, False, True, template_input_port_tuples)
        elapsed_time_opt, output_signature_opt, _, stderr_opt = run_executable_worker(fuzzerstate_opt, simulator_opt)
        if elapsed_time_opt is None:
            print(f"Skipping workload_id {workload_id} (opt) as the simulator did not finish")
            return

        # Noopt
        fuzzerstate_noopt = FuzzerState(workdir_noopt, FuzzerParams.CellMinDimension, FuzzerParams.CellMaxDimension, True, num_cells, num_cells, FuzzerParams.MinInputWidthWords, max(FuzzerParams.MinOutputWidthWords, proportion_final_cells_connected_to_output), simlen, DO_TRACE, authorized_combinational_cell_types, authorized_stateful_cell_types)
        fuzzerstate_noopt.workdir = workdir_noopt
        build_executable_worker(fuzzerstate_noopt, netlist_dict, simulator_noopt, False, False, template_input_port_tuples)
        elapsed_time_noopt, output_signature_noopt, _, stderr_noopt = run_executable_worker(fuzzerstate_noopt, simulator_noopt)
        if elapsed_time_noopt is None:
            print(f"Skipping workload_id {workload_id} (noopt) as the simulator did not finish")
            return

        end_time = time.time()

        # Count the cells
        opt = False
        num_cells_by_type, num_cells_by_size = get_cell_stats(fuzzerstate_noopt, netlist_dict, simulator_id_icarus, False, opt, template_input_port_tuples)
        num_cells = sum(num_cells_by_type.values())

    except Exception as e:
        print(f"Exception info: {e}")
        return None

    try:
        os.system(f"rm -rf {workdir_noopt}")
        os.system(f"rm -rf {workdir_opt}")
    except Exception as e:
        return None

    # return (start_time_build-start_time, start_time_exec-start_time_build, end_time-start_time_exec)
    return end_time-start_time, num_cells

def gen_data(num_cells: int, simlen: int):

    print(f"Generating workloads...")
    workloads = []
    workload_id = 0
    # Put the num_reps_per_point loop as external to delocalize the workloads
    for _ in range(num_reps_per_point):
        for simulator_id, simulator in enumerate(simulators):
            if simulator != SimulatorType.SIM_ICARUS:
                continue
            workloads.append((num_cells, simulator_id, simlen, workload_id))
            workload_id += 1

    print(f"Running workloads...")
    with mp.Pool(num_processes) as pool:
        all_workload_results = pool.map(run_workload, workloads)

    all_elapsed_times = []
    all_num_cells = []

    for workload_id, workload_result in enumerate(all_workload_results):
        if workload_result is not None:
            elapsed_time, num_cells = workload_result
            all_elapsed_times.append(elapsed_time)
            all_num_cells.append(num_cells)

    return all_elapsed_times, all_num_cells

all_elapsed_times, all_num_cells = gen_data(num_cells, simlen)

print("all_elapsed_times:", all_elapsed_times)
print("all_num_cells:", all_num_cells)

all_pairs = list(zip(all_num_cells, all_elapsed_times))

with open('perfpercell_transfuzz.json', 'w') as f:
    json.dump(all_pairs, f, indent=4)

# # Save the data
# elapsed_times_per_pair = {"gen": elapsed_times_per_pair_gen, "build": elapsed_times_per_pair_build, "exec": elapsed_times_per_pair_exec, "simlen": simlen}
# with open('eval_cellthroughput.json', 'w') as f:
#     json.dump(elapsed_times_per_pair, f)

# # Reload it
# with open('eval_cellthroughput.json', 'r') as f:
#     elapsed_times_per_pair = json.load(f)
# elapsed_times_per_pair_gen = elapsed_times_per_pair["gen"]
# elapsed_times_per_pair_build = elapsed_times_per_pair["build"]
# elapsed_times_per_pair_exec = elapsed_times_per_pair["exec"]
