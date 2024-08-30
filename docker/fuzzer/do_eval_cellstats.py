# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from collections import defaultdict
import json
import os
import multiprocessing as mp
import sys
import random
import time

# sys.argv[1]: number of processes
# sys.argv[2]: number of designs

PATH_TO_WORKDIR_ROOT = '/scratch/simufuzz-workdir'

from pybackend.backend import get_cell_stats
from pybackend.cleanupnetlist import cleanup_netlist
from pycommon.fuzzparams import FuzzerParams, FuzzerState
from pycommon.runparams import SimulatorType
from pynetgenerator.genonebyone import gen_random_onebyone_netlist, gen_netlist_from_cells_and_netwires, find_requesters_per_clkin_type
from pynetgenerator.splitsubnetids import split_subnet_ids, ClkInType
from pycellgenerator.allcells import randomize_authorized_combinational_cell_types, randomize_authorized_stateful_cell_types, ALL_CELL_PORTS_STATEFUL

if __name__ != '__main__':
    raise ImportError('This module cannot be imported')

################
# Collect the arguments
################

num_processes = int(sys.argv[1])
num_workloads_per_pool = 1000000

num_workloads = int(sys.argv[2])

num_reps_per_point = 1000

simulator_names = ['Verilator', 'Icarus', 'cxxrtl']
num_cells       = 700

DO_TRACE = False
if DO_TRACE:
    print(f"Warning: DO_TRACE is set to True")

simlen = 1

################
# Create and run the workloads
################

def format_with_commas(value, _):
    return "{:,.0f}".format(value)

# Return elapsed time in seconds
def run_workload(workload):
    start_time = time.time()
    # try:
    num_cells, simulator_id, simlen, randseed = workload
    workload_str = '_'.join(map(str, workload))
    random.seed(randseed)
    workdir = os.path.join(PATH_TO_WORKDIR_ROOT, f"tmp/obj_dir_example_cellstats_{workload_str}")

    authorized_combinational_cell_types = randomize_authorized_combinational_cell_types([])
    authorized_stateful_cell_types      = randomize_authorized_stateful_cell_types(True, [])
    proportion_final_cells_connected_to_output = random.uniform(FuzzerParams.ProportionFinalCellsConnectedToOutputMin, FuzzerParams.ProportionFinalCellsConnectedToOutputMax)
    fuzzerstate = FuzzerState(workdir, FuzzerParams.CellMinDimension, FuzzerParams.CellMaxDimension, True, num_cells, num_cells, FuzzerParams.MinInputWidthWords, max(FuzzerParams.MinOutputWidthWords, proportion_final_cells_connected_to_output), simlen, DO_TRACE, authorized_combinational_cell_types, authorized_stateful_cell_types)

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
    # Check that the inputs.txt file has the right number of lines
    with open(os.path.join(workdir, 'inputs.txt'), 'r') as f:
        inputs_str_lines = f.readlines()
        assert len(inputs_str_lines) >= fuzzerstate.simlen and len(inputs_str_lines) <= fuzzerstate.simlen + 200, f"inputs.txt has {len(inputs_str_lines)} lines, but should have at least {fuzzerstate.simlen} lines." # The +200 is to account for the clkin signals

    start_time_build = time.time()
    opt = False
    num_cells_by_type, num_cells_by_size = get_cell_stats(fuzzerstate, netlist_dict, simulator_id, False, opt, template_input_port_tuples)
    start_time_exec = time.time()
    end_time = time.time()

    # except Exception as e:
    #     print(f"Exception info (workload {workload_str}): {e}")
    #     return None

    try:
        os.system(f"rm -rf {workdir}")
    except Exception as e:
        pass

    return num_cells_by_type, num_cells_by_size

def gen_data(simlen: int):
    workloads = []
    randseed = 0
    # Put the num_reps_per_point loop as external to delocalize the workloads
    for workload_id in range(num_workloads):
        workloads.append((num_cells, SimulatorType.SIM_ICARUS, simlen, randseed))
        randseed += 1

    with mp.Pool(num_processes) as pool:
        nums_cells_by_type__nums_cells_by_size = pool.map(run_workload, workloads)

    nums_cells_by_type = defaultdict(int)
    nums_cells_by_size = defaultdict(int)

    for num_cells_by_type, num_cells_by_size in nums_cells_by_type__nums_cells_by_size:
        for cell_type, curr_num_occurrences in num_cells_by_type.items():
            nums_cells_by_type[cell_type] += curr_num_occurrences
        for cell_size, curr_num_occurrences in num_cells_by_size.items():
            nums_cells_by_size[cell_size] += curr_num_occurrences

    with open('eval_cellstats_simufuzz.json', 'w') as f:
        json.dump({"nums_cells_by_type": nums_cells_by_type, "nums_cells_by_size": nums_cells_by_size}, f, indent=4)

gen_data(simlen)
