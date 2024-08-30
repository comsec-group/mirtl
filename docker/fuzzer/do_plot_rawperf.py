# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import json

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

from enum import IntEnum

class SimulatorType(IntEnum):
    SIM_VERILATOR = 0
    SIM_ICARUS = 1
    SIM_CXXRTL = 2
    YOSYS = 3

simulator_colors = {
    SimulatorType.SIM_VERILATOR: 'r',
    SimulatorType.SIM_ICARUS: 'g',
    SimulatorType.SIM_CXXRTL: 'b',
    SimulatorType.YOSYS: 'orange'
}

simulator_names = ['Verilator', 'Icarus', 'CXXRTL']

PATH_TO_WORKDIR_ROOT = '/scratch/simufuzz-workdir'

if __name__ != '__main__':
    raise ImportError('This module cannot be imported')

################
# Collect the arguments
################

num_workloads_per_pool = 1000000

num_reps_per_point = 600 # approx 10 hours

simulator_names = ['Verilator', 'Icarus Verilog', 'CXXRTL']
num_cells_list  = [10, 100, 200, 300] # Might add the elements , 400, 500, 600, 700, 800, 900, 1000]
simulators      = list(map(int, [SimulatorType.SIM_VERILATOR, SimulatorType.SIM_ICARUS, SimulatorType.SIM_CXXRTL]))

exp_simlen = 1000

DO_TRACE = False
if DO_TRACE:
    print(f"Warning: DO_TRACE is set to True")

################
# Create and run the workloads
################

def format_with_commas(value, _):
    return "{:,.0f}".format(value)


def plot_data_singleplot(elapsed_times_per_pair_gen, elapsed_times_per_pair_build, elapsed_times_per_pair_exec, elapsed_times_per_pair_build_yosys):

    NUM_PLOTS = 3

    ################
    # Gen perf
    ################

    all_averages_gen = dict()
    for num_cells in num_cells_list:
        for simulator_id, _ in enumerate(simulators):
            all_averages_gen[f"{num_cells}_{simulator_id}_{exp_simlen}"] = np.median(elapsed_times_per_pair_gen[f"{num_cells}_{simulator_id}_{exp_simlen}"])
    all_averages_build = dict()
    for num_cells in num_cells_list:
        for simulator_id, _ in enumerate(simulators):
            all_averages_build[f"{num_cells}_{simulator_id}_{exp_simlen}"] = np.median(elapsed_times_per_pair_build[f"{num_cells}_{simulator_id}_{exp_simlen}"])
    all_averages_exec = dict()
    for num_cells in num_cells_list:
        for simulator_id, _ in enumerate(simulators):
            all_averages_exec[f"{num_cells}_{simulator_id}_{exp_simlen}"] = np.median(elapsed_times_per_pair_exec[f"{num_cells}_{simulator_id}_{exp_simlen}"])

    all_averages_build_yosys = dict()
    for num_cells in num_cells_list:
        all_averages_build_yosys[f"{num_cells}_{simulator_id}_{exp_simlen}"] = np.median(elapsed_times_per_pair_build_yosys[f"{num_cells}_{simulator_id}_{exp_simlen}"])

    all_averages_together = [all_averages_gen, all_averages_build, all_averages_exec]

    # Plot the responses for different events and regions
    # Do one subplot per simulator
    fig, axs = plt.subplots(figsize=(6, NUM_PLOTS*1.6), nrows=NUM_PLOTS, sharex=True)

    # For generation, the plot is the same for all simulators
    series_id = 0
    x = num_cells_list
    y = [all_averages_together[series_id][f"{num_cells}_{simulator_id}_{exp_simlen}"] for num_cells in num_cells_list]
    axs[series_id].plot(x, y, label=f"TransFuzz circuit generator", marker='o', linestyle='solid', linewidth=1, markersize=3, color='k')
    axs[series_id].legend()
    axs[series_id].grid(True)
    axs[series_id].set_ylim(bottom=0)

    for series_id in range(1, 3):
        x = num_cells_list
        for simulator_id, _ in enumerate(simulators):
            y = [all_averages_together[series_id][f"{num_cells}_{simulator_id}_{exp_simlen}"] for num_cells in num_cells_list]

            if series_id == 2:
                # Just give a single simlen
                y = [y[i] / exp_simlen for i in range(len(y))]

            axs[series_id].plot(x, y, label=f"{simulator_names[simulator_id]}", marker='o', markeredgecolor='k', linestyle='solid', linewidth=1, markersize=3, color=simulator_colors[simulator_id])
            # Make the Y axis logarithmic

        # Add Yosys to the build plot
        if series_id == 1:
            x = num_cells_list
            y = [all_averages_build_yosys[f"{num_cells}_{simulator_id}_{exp_simlen}"] for num_cells in num_cells_list]
            axs[series_id].plot(x, y, label=f"Yosys", marker='o', markeredgecolor='k', linestyle='solid', linewidth=1, markersize=3, color=simulator_colors[SimulatorType.YOSYS])

        if series_id == 2:
            axs[series_id].set_yscale('log')

        axs[series_id].legend(loc='center', ncol=2)
        axs[series_id].grid(True)
        axs[series_id].set_ylim(bottom=0)

    axs[0].set_title('Generation performance')
    axs[1].set_title('Build performance')
    axs[2].set_title('Execution performance')

    axs[2].set_yticks([0.0001, 2*0.00001])
    axs[2].set_yticklabels(['$10^{-4}$', '$2\cdot10^{-5}$'])

    plt.subplots_adjust(wspace=-1.3, hspace=-1)

    axs[-1].xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    # axs[-1][1].set_xlabel('Number of cells')
    axs[1].set_ylabel('Duration (s)')
    # axs[1].set_ylabel('Duration (s)')

    axs[2].set_xlabel('Number of cells')
    # ax.set_ylabel('Time (s)')
    plt.tight_layout()

    plt.savefig('eval_perf_singleplot.png', dpi=300)
    plt.savefig('eval_perf_singleplot.pdf', dpi=300)

# Reload it
with open('eval_execperf.json', 'r') as f:
    elapsed_times_per_pair = json.load(f)
elapsed_times_per_pair_gen = elapsed_times_per_pair["gen"]
elapsed_times_per_pair_build = elapsed_times_per_pair["build"]
elapsed_times_per_pair_exec = elapsed_times_per_pair["exec"]

elapsed_times_per_pair_build_yosys = None
with open('eval_execperf_yosys.json', 'r') as f:
    elapsed_times_per_pair_build_yosys = json.load(f)["build"]

plot_data_singleplot(elapsed_times_per_pair_gen, elapsed_times_per_pair_build, elapsed_times_per_pair_exec, elapsed_times_per_pair_build_yosys)
