# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

import json

################
# Collect the arguments
################
from enum import IntEnum
class SimulatorType(IntEnum):
    SIM_VERILATOR = 0
    SIM_ICARUS = 1
    SIM_CXXRTL = 2
    YOSYS = 3

simulator_names = {
    SimulatorType.SIM_VERILATOR: "Verilator",
    SimulatorType.SIM_ICARUS: "Icarus Verilog",
    SimulatorType.SIM_CXXRTL: "CXXRTL",
    SimulatorType.YOSYS: "Yosys"
}

nums_cells = [10] + [50*i for i in range(1, 8)] # Might increase to range(1, 41) 
simulators = list(map(int, [SimulatorType.SIM_VERILATOR, SimulatorType.SIM_ICARUS, SimulatorType.SIM_CXXRTL, SimulatorType.YOSYS])) #[SimulatorType.SIM_VERILATOR, SimulatorType.SIM_ICARUS, SimulatorType.SIM_CXXRTL]))

max_simlen = 70

def format_with_commas(value, _):
    return "{:,.0f}".format(value)

num_processes = 128

def performance_heuristic(preparation_time, execution_time_per_simlen, cumulated_toggle_for_this_simlen, max_simlen):
    num_compexec_cycles = 1/(preparation_time + execution_time_per_simlen*max_simlen)
    avg_toggle_per_compexec_cycle = cumulated_toggle_for_this_simlen
    return num_compexec_cycles*avg_toggle_per_compexec_cycle

def plot_data(toggleval_dict, elapsed_times_dict, elapsed_times_dict_yosys):

    elapsed_times_per_pair_gen = elapsed_times_dict["gen"]
    elapsed_times_per_pair_build = elapsed_times_dict["build"]
    elapsed_times_per_pair_exec = elapsed_times_dict["exec"]

    new_gen_pairs = []
    new_build_pairs = []
    new_exec_pairs = []

    # Add the data for Yosys
    for curr_key in elapsed_times_per_pair_gen:
        if f"_{SimulatorType.SIM_ICARUS}_" in curr_key:
            new_gen_pairs.append((curr_key.replace(f"_{SimulatorType.SIM_ICARUS}_", f"_{SimulatorType.YOSYS}_"), elapsed_times_per_pair_gen[curr_key]))
            # elapsed_times_per_pair_gen[curr_key.replace(f"_{SimulatorType.SIM_ICARUS}_", f"_{SimulatorType.YOSYS}_")] = elapsed_times_per_pair_gen[curr_key]

    for curr_key in elapsed_times_per_pair_build:
        if f"_{SimulatorType.SIM_ICARUS}_" in curr_key:
            curr_num_cells = int(curr_key.split("_")[0])
            new_build_pairs.append((curr_key.replace(f"_{SimulatorType.SIM_ICARUS}_", f"_{SimulatorType.YOSYS}_"), elapsed_times_per_pair_build[curr_key] + elapsed_times_dict_yosys["build"][f"{curr_num_cells}_{0}_{70}"]))
            # elapsed_times_per_pair_build[curr_key.replace(f"_{SimulatorType.SIM_ICARUS}_", f"_{SimulatorType.YOSYS}_")] = elapsed_times_per_pair_build[curr_key] + elapsed_times_dict_yosys["build"][f"{curr_num_cells}_{SimulatorType.SIM_ICARUS}_{70}"]

    for curr_key in elapsed_times_per_pair_build:
        if f"_{SimulatorType.SIM_ICARUS}_" in curr_key:
            curr_num_cells = int(curr_key.split("_")[0])
            new_exec_pairs.append((curr_key.replace(f"_{SimulatorType.SIM_ICARUS}_", f"_{SimulatorType.YOSYS}_"), elapsed_times_per_pair_exec[curr_key]))

    for curr_pair in new_gen_pairs:
        elapsed_times_per_pair_gen[curr_pair[0]] = curr_pair[1]
    for curr_pair in new_build_pairs:
        elapsed_times_per_pair_build[curr_pair[0]] = curr_pair[1]
    for curr_pair in new_exec_pairs:
        elapsed_times_per_pair_exec[curr_pair[0]] = curr_pair[1]
    # Done adding data for Yosys

    # Compute the means
    for curr_key in elapsed_times_per_pair_gen:
        elapsed_times_per_pair_gen[curr_key] = np.mean(elapsed_times_per_pair_gen[curr_key])
    for curr_key in elapsed_times_per_pair_build:
        elapsed_times_per_pair_build[curr_key] = np.mean(elapsed_times_per_pair_build[curr_key])
    for curr_key in elapsed_times_per_pair_exec:
        elapsed_times_per_pair_exec[curr_key] = np.mean(elapsed_times_per_pair_exec[curr_key])

    # For each simulator, get the preparation time
    fixed_preparation_time_per_simulator_per_numcellid = []
    for simulator_id in simulators:
        fixed_preparation_time_per_simulator_per_numcellid.append([])
        for curr_num_cells in nums_cells:
            fixed_preparation_time_per_simulator_per_numcellid[simulator_id].append(elapsed_times_per_pair_gen[f"{curr_num_cells}_{simulator_id}_{max_simlen}"] + elapsed_times_per_pair_build[f"{curr_num_cells}_{simulator_id}_{max_simlen}"])

    # For each simulator, get the execution time per input
    fixed_execution_time_per_simulator_per_numcellid = []
    for simulator_id in simulators:
        fixed_execution_time_per_simulator_per_numcellid.append([])
        for curr_num_cells in nums_cells:
            fixed_execution_time_per_simulator_per_numcellid[simulator_id].append(elapsed_times_per_pair_exec[f"{curr_num_cells}_{simulator_id}_{max_simlen}"]/max_simlen)

    # For each simulator, get the value change per numcells and per max_simlen
    toggleval_all_ret_vals = toggleval_dict["all_ret_vals"]
    toggleval_max_simlen = toggleval_dict["max_simlen"]
    toggleval_max_nums_cells = toggleval_dict["max_nums_cells"]

    # Check that all the cell numbers have been evaluated for toggle
    for curr_num_cells in nums_cells:
        assert curr_num_cells in toggleval_max_nums_cells, f"curr_num_cells={curr_num_cells} not in toggleval_max_nums_cells={toggleval_max_nums_cells}"
    # Check that we evaluated enough simlens
    assert toggleval_max_simlen >= max_simlen, f"toggleval_max_simlen={toggleval_max_simlen} < max_simlen={max_simlen}"

    # Cumulate the togglevals
    #  toggleval_all_ret_vals_cumulated[num_cells][max_simlen] = cumulated_toggle_for_this_simlen
    toggleval_all_ret_vals_cumulated = []
    for max_num_cells_id in range(len(toggleval_max_nums_cells)):
        toggleval_all_ret_vals_cumulated.append([])
        for curr_simlen in range(max_simlen):
            toggleval_all_ret_vals_cumulated[max_num_cells_id].append(sum(toggleval_all_ret_vals[max_num_cells_id][:curr_simlen+1]))

    # For each numcells and max_simlen, compute the performance heuristic
    performance_heuristic_per_simulator_per_numcellid = []
    for simulator_id in simulators:
        performance_heuristic_per_simulator_per_numcellid.append([])
        for curr_num_cells_id, curr_num_cells in enumerate(nums_cells):
            performance_heuristic_per_simulator_per_numcellid[simulator_id].append([])
            for curr_simlen in range(max_simlen):
                performance_heuristic_per_simulator_per_numcellid[simulator_id][curr_num_cells_id].append(performance_heuristic(fixed_preparation_time_per_simulator_per_numcellid[simulator_id][curr_num_cells_id], fixed_execution_time_per_simulator_per_numcellid[simulator_id][curr_num_cells_id], toggleval_all_ret_vals_cumulated[curr_num_cells_id][curr_simlen], curr_simlen))
            performance_heuristic_per_simulator_per_numcellid[simulator_id][curr_num_cells_id] = performance_heuristic_per_simulator_per_numcellid[simulator_id][curr_num_cells_id][max_simlen-1]

    opti_icarus_vs_verilator = []
    for curr_num_cells_id, curr_num_cells in enumerate(nums_cells):
        new_val = 1/performance_heuristic_per_simulator_per_numcellid[SimulatorType.SIM_ICARUS][curr_num_cells_id] + 1/performance_heuristic_per_simulator_per_numcellid[SimulatorType.SIM_VERILATOR][curr_num_cells_id]
        new_val = 1/new_val
        opti_icarus_vs_verilator.append(new_val)
    opti_icarus_vs_cxxrtl = []
    for curr_num_cells_id, curr_num_cells in enumerate(nums_cells):
        new_val = 1/performance_heuristic_per_simulator_per_numcellid[SimulatorType.SIM_ICARUS][curr_num_cells_id] + 1/performance_heuristic_per_simulator_per_numcellid[SimulatorType.SIM_CXXRTL][curr_num_cells_id]
        new_val = 1/new_val
        opti_icarus_vs_cxxrtl.append(new_val)
    opti_verilator_vs_cxxrtl = []
    for curr_num_cells_id, curr_num_cells in enumerate(nums_cells):
        new_val = 1/performance_heuristic_per_simulator_per_numcellid[SimulatorType.SIM_VERILATOR][curr_num_cells_id] + 1/performance_heuristic_per_simulator_per_numcellid[SimulatorType.SIM_CXXRTL][curr_num_cells_id]
        new_val = 1/new_val
        opti_verilator_vs_cxxrtl.append(new_val)
    opti_icarus_vs_yosys = []
    for curr_num_cells_id, curr_num_cells in enumerate(nums_cells):
        new_val = 1/performance_heuristic_per_simulator_per_numcellid[SimulatorType.SIM_ICARUS][curr_num_cells_id] + 1/performance_heuristic_per_simulator_per_numcellid[SimulatorType.YOSYS][curr_num_cells_id]
        new_val = 1/new_val
        opti_icarus_vs_yosys.append(new_val)

    fig, ax = plt.subplots(figsize=(6, 1.8))

    ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    ax.grid(True)

    x = nums_cells
    y = opti_icarus_vs_verilator
    ax.plot(x, y, label="Icarus & Verilator", marker='o', markersize=3, linestyle='-', linewidth=0.5)

    x = nums_cells
    y = opti_icarus_vs_cxxrtl
    ax.plot(x, y, label="Icarus & CXXRTL", marker='o', markersize=3, linestyle='-', linewidth=0.5)

    x = nums_cells
    y = opti_verilator_vs_cxxrtl
    ax.plot(x, y, label="Verilator & CXXRTL", marker='o', markersize=3, linestyle='-', linewidth=0.5)

    x = nums_cells
    y = opti_icarus_vs_yosys
    ax.plot(x, y, label="Icarus & Yosys", marker='o', markersize=3, linestyle='-', linewidth=0.5)

    ax.set_yticks([0, 25, 50, 75, 100, 125, 150])

    # ax.legend(ncol=1, loc='center', bbox_to_anchor=(0.5, 0.65))
    ax.legend(ncol=1, loc='center')
    ax.set_ylabel('Differential\nperformance')
    ax.set_xlabel('Circuit size (number of cells)')
    # Set a log y axis
    ax.set_yscale('log')
    # ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig("netperf70.png", dpi=300)
    plt.savefig("netperf70.pdf")

# Retreive the toggle data
with open("testtoggle_results70.json", "r") as f:
    toggleval_dict = json.load(f)

# Retreive the perf data
with open('eval_execperf70.json', 'r') as f:
    elapsed_times_dict = json.load(f)

# Retreive the Yosys perf data
with open('eval_execperf_yosys70.json', 'r') as f:
    elapsed_times_dict_yosys = json.load(f)

plot_data(toggleval_dict, elapsed_times_dict, elapsed_times_dict_yosys)
