# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Helper script to understand which fno- flags would potentially erase a found issue.

import itertools
import json
import os
import multiprocessing as mp
import sys
import random

# sys.argv[1]: number of processes
# sys.argv[2]: max num cells
# sys.argv[3]: simlen

IS_VERILATOR = True
PATH_TO_WORKDIR_ROOT = '/scratch/simufuzz-workdir'

from pybackend.backend import build_executable_worker, run_executable_worker
from pybackend.cleanupnetlist import cleanup_netlist
from pycommon.fuzzparams import FuzzerParams, FuzzerState
from pycommon.runparams import SimulatorType
from pynetgenerator.genonebyone import gen_random_onebyone_netlist, gen_total_num_cells, gen_netlist_from_cells_and_netwires, find_requesters_per_clkin_type
from pynetgenerator.splitsubnetids import split_subnet_ids, ClkInType
from pycellgenerator.allcells import randomize_authorized_combinational_cell_types, randomize_authorized_stateful_cell_types

if __name__ != '__main__':
    raise ImportError('This module cannot be imported')

DO_TRACE = False
if DO_TRACE:
    print(f"Warning: DO_TRACE is set to True")

################
# Collect the arguments
################

all_fno_flags = [
    '',
    '-fno-acyc-simp',
    '-fno-assemble',
    '-fno-case',
    '-fno-combine',
    '-fno-const',
    '-fno-const-bit-op-tree',
    '-fno-dedup',
    '-fno-dfg',
    '-fno-dfg-peephole',
    '-fno-dfg-pre-inline',
    '-fno-dfg-post-inline',
    '-fno-expand',
    '-fno-gate',
    '-fno-inline',
    '-fno-life',
    '-fno-life-post',
    '-fno-localize',
    '-fno-merge-cond',
    '-fno-merge-cond-motion',
    '-fno-merge-const-pool',
    '-fno-reloop',
    '-fno-reorder',
    '-fno-split',
    '-fno-subst',
    '-fno-subst-const',
    '-fno-table',
    '-fno-acyc-simp -fno-assemble -fno-case -fno-combine -fno-const -fno-const-bit-op-tree -fno-dedup -fno-dfg -fno-dfg-peephole -fno-dfg-pre-inline -fno-dfg-post-inline -fno-expand -fno-gate -fno-inline -fno-life -fno-life-post -fno-localize -fno-merge-cond -fno-merge-cond-motion -fno-merge-const-pool -fno-reloop -fno-reorder -fno-split -fno-subst -fno-subst-const -fno-table'
]

workloads = [
    1078810
]

expected_signatures = [
    0x4
]
assert len(workloads) == len(expected_signatures), f"len(workloads) = {len(workloads)}, len(expected_signatures) = {len(expected_signatures)}"

num_reps = 1

num_processes = int(sys.argv[1])

simlen = int(sys.argv[4])

min_num_cells = 1
max_num_cells = int(sys.argv[2])

min_num_cells_clockdrivers = 0
max_num_cells_clockdrivers = 0

all_workload_triples = list(itertools.product(range(len(workloads)), range(len(all_fno_flags)), range(num_reps)))

################
# Create and run the workloads
################

def characterize_fno_worker(workload_id: int, fno_flags_id: int, rep_id: int = 0):
    expected_signature = expected_signatures[workload_id]
    workload = workloads[workload_id]

    random.seed(workload)

    workdir = os.path.join(PATH_TO_WORKDIR_ROOT, f"tmp/obj_dir_example_fno_worker_wl{workload}_fno{fno_flags_id}_rep{rep_id}")

    num_cells = gen_total_num_cells(min_num_cells, max_num_cells)
    num_cells_clockdrivers = gen_total_num_cells(min_num_cells_clockdrivers, max_num_cells_clockdrivers)
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
            for input_word_id in range(fuzzerstate.num_input_words):
                random_inputs_list.append((curr_subnet_or_clkin_id, random.randint(0, 2 ** 32 - 1))) 
        else:
            random_inputs_list.append((curr_subnet_or_clkin_id, random.randint(0, 2 ** 32 - 1))) 

    os.makedirs(workdir, exist_ok=True)
    # Write netlist
    netlist_dict = cleanup_netlist(netlist_dict)

    with open(os.path.join(workdir, 'netlist.json'), 'w') as f:
        json.dump(netlist_dict, f)
    # Write random inputs
    with open(os.path.join(workdir, 'inputs.txt'), 'w') as f:
        f.write(f"{len(random_inputs_list)}\n" + '\n'.join(map(lambda x: f"{x[0]} {x[1]:x}", random_inputs_list)))

    # Generate the tuples for the clkin-type inputs
    template_input_port_tuples = []
    for clkin_type in splitted_requesters_per_clkin_type:
        for clkin_subnet_id, clkin_subnet in enumerate(splitted_requesters_per_clkin_type[clkin_type]):
            template_input_port_tuples.append((f"{ClkInType.to_char(clkin_type)}{clkin_subnet_id}", max(map(lambda c: c[3], clkin_subnet))))

    # Verilator
    build_executable_worker(fuzzerstate, netlist_dict, SimulatorType.SIM_CXXRTL, False, True, template_input_port_tuples, verilator_fno_flags=all_fno_flags[fno_flags_id])
    elapsed_time_first, output_signature_first, _, stderr_first = run_executable_worker(fuzzerstate, SimulatorType.SIM_CXXRTL)
    if elapsed_time_first is None:
        print(f"Skipping workload {workload} as Verilator did not finish")
        return
    
    if output_signature_first == expected_signature:
        print(f"Match in workload {workload} for fnoid {fno_flags_id}. Num cells: {num_cells}.")
    else:
        print(f"Mismatch in workload {workload} for fnoid {fno_flags_id}: Expected signature {expected_signature}, got {output_signature_first}. Workdir: {workdir} Num cells: {num_cells}.")

with mp.Pool(num_processes) as pool:
    pool.starmap(characterize_fno_worker, all_workload_triples)
