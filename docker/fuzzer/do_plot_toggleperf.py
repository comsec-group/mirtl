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

simulator_names = {
    SimulatorType.SIM_VERILATOR: "Verilator",
    SimulatorType.SIM_ICARUS: "Icarus Verilog",
    SimulatorType.SIM_CXXRTL: "CXXRTL"
}

axtops = {
    SimulatorType.SIM_VERILATOR: 300,
    SimulatorType.SIM_ICARUS: 5000,
    SimulatorType.SIM_CXXRTL: 130
}

nums_cells   = [10, 100, 250]# Might add the value , 500]
simulators = list(map(int, [SimulatorType.SIM_VERILATOR, SimulatorType.SIM_ICARUS, SimulatorType.SIM_CXXRTL]))

max_simlen = 300
# max_simlen = 300

def format_with_commas(value, _):
    return "{:,.0f}".format(value)

num_processes = 128
gross_perf_exp_simlen = 1000 # Might eventually read this from the JSON


def performance_heuristic(preparation_time, execution_time_per_simlen, cumulated_toggle_for_this_simlen, simlen):
    num_compexec_cycles = 1/(preparation_time + execution_time_per_simlen*simlen)
    avg_toggle_per_compexec_cycle = cumulated_toggle_for_this_simlen
    return num_compexec_cycles*avg_toggle_per_compexec_cycle

def plot_data(toggleval_dict, elapsed_times_dict):

    elapsed_times_per_pair_gen = elapsed_times_dict["gen"]
    elapsed_times_per_pair_build = elapsed_times_dict["build"]
    elapsed_times_per_pair_exec = elapsed_times_dict["exec"]

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
            assert f"{curr_num_cells}_{simulator_id}_{gross_perf_exp_simlen}" in elapsed_times_per_pair_gen, f"{curr_num_cells}_{simulator_id}_{gross_perf_exp_simlen} not in elapsed_times_per_pair_gen"
            assert f"{curr_num_cells}_{simulator_id}_{gross_perf_exp_simlen}" in elapsed_times_per_pair_build, f"{curr_num_cells}_{simulator_id}_{gross_perf_exp_simlen} not in elapsed_times_per_pair_build"
            fixed_preparation_time_per_simulator_per_numcellid[simulator_id].append(elapsed_times_per_pair_gen[f"{curr_num_cells}_{simulator_id}_{gross_perf_exp_simlen}"] + elapsed_times_per_pair_build[f"{curr_num_cells}_{simulator_id}_{gross_perf_exp_simlen}"])

    # For each simulator, get the execution time per input
    fixed_execution_time_per_simulator_per_numcellid = []
    for simulator_id in simulators:
        fixed_execution_time_per_simulator_per_numcellid.append([])
        for curr_num_cells in nums_cells:
            assert f"{curr_num_cells}_{simulator_id}_{gross_perf_exp_simlen}" in elapsed_times_per_pair_exec, f"{curr_num_cells}_{simulator_id}_{gross_perf_exp_simlen} not in elapsed_times_per_pair_exec"
            fixed_execution_time_per_simulator_per_numcellid[simulator_id].append(elapsed_times_per_pair_exec[f"{curr_num_cells}_{simulator_id}_{gross_perf_exp_simlen}"]/gross_perf_exp_simlen)

    # For each simulator, get the value change per numcells and per simlen
    toggleval_all_ret_vals = toggleval_dict["all_ret_vals"]
    toggleval_max_simlen = toggleval_dict["max_simlen"]
    toggleval_max_nums_cells = toggleval_dict["max_nums_cells"]

    # Check that all the cell numbers have been evaluated for toggle
    for curr_num_cells in nums_cells:
        assert curr_num_cells in toggleval_max_nums_cells, f"curr_num_cells={curr_num_cells} not in toggleval_max_nums_cells={toggleval_max_nums_cells}"
    # Check that we evaluated enough simlens
    assert toggleval_max_simlen >= max_simlen, f"toggleval_max_simlen={toggleval_max_simlen} < max_simlen={max_simlen}"

    # Cumulate the togglevals
    #  toggleval_all_ret_vals_cumulated[num_cells][simlen] = cumulated_toggle_for_this_simlen
    toggleval_all_ret_vals_cumulated = []
    for max_num_cells_id in range(len(toggleval_max_nums_cells)):
        toggleval_all_ret_vals_cumulated.append([])
        for curr_simlen in range(max_simlen):
            toggleval_all_ret_vals_cumulated[max_num_cells_id].append(sum(toggleval_all_ret_vals[max_num_cells_id][:curr_simlen+1]))

    # For each numcells and simlen, compute the performance heuristic
    performance_heuristic_per_simulator_per_numcellid = []
    for simulator_id in simulators:
        performance_heuristic_per_simulator_per_numcellid.append([])
        for curr_num_cells_id, curr_num_cells in enumerate(nums_cells):
            performance_heuristic_per_simulator_per_numcellid[simulator_id].append([])
            for curr_simlen in range(max_simlen):
                print(f"curr_num_cells={curr_num_cells}, curr_simlen={curr_simlen}")
                performance_heuristic_per_simulator_per_numcellid[simulator_id][curr_num_cells_id].append(performance_heuristic(fixed_preparation_time_per_simulator_per_numcellid[simulator_id][curr_num_cells_id], fixed_execution_time_per_simulator_per_numcellid[simulator_id][curr_num_cells_id], toggleval_all_ret_vals_cumulated[curr_num_cells_id][curr_simlen], curr_simlen))

    # # Find the peaks (argmax and max)
    # for simulator_id in simulators:
    #     for curr_num_cells_id, curr_num_cells in enumerate(nums_cells):
    #         max_perf = max(performance_heuristic_per_simulator_per_numcellid[simulator_id][curr_num_cells_id])
    #         max_perf_id = performance_heuristic_per_simulator_per_numcellid[simulator_id][curr_num_cells_id].index(max_perf)
    #         print(f"simulator_id={simulator_id}, curr_num_cells={curr_num_cells}, max_perf={max_perf}, max_perf_id={max_perf_id}")

    fig, ax = plt.subplots(figsize=(6, 1.6*3), nrows=3, ncols=1)

    for simulator_id in simulators:
        ax[simulator_id].xaxis.set_major_formatter(FuncFormatter(format_with_commas))
        ax[simulator_id].grid(True)

        for curr_num_cells_id, curr_num_cells in enumerate(nums_cells):
            x = range(1, max_simlen+1)
            y = performance_heuristic_per_simulator_per_numcellid[simulator_id][curr_num_cells_id][:max_simlen]

            ax[simulator_id].plot(x, y, label=f"{format_with_commas(curr_num_cells, None)} cells", marker='o', linestyle='solid', linewidth=1, markersize=3)
            ax[simulator_id].legend(loc='center', ncol=2)
            ax[simulator_id].set_title(f"{simulator_names[simulator_id]}")
            ax[simulator_id].set_ylim(bottom=0, top=axtops[simulator_id])

    ax[1].set_ylabel('Cell output bit toggles per second')
    ax[-1].set_xlabel('Number of stimuli per circuit')
    plt.tight_layout()
    plt.savefig("netperf.png", dpi=300)
    plt.savefig("netperf.pdf")

# Retreive the toggle data
with open("testtoggle_results.json", "r") as f:
    toggleval_dict = json.load(f)

# Retreive the perf data
with open("eval_execperf.json", "r") as f:
    elapsed_times_dict = json.load(f)

plot_data(toggleval_dict, elapsed_times_dict)
