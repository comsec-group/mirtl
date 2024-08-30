# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import json

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

PATH_TO_WORKDIR_ROOT = '/scratch/simufuzz-workdir'

from pycommon.runparams import SimulatorType

if __name__ != '__main__':
    raise ImportError('This module cannot be imported')

################
# Collect the arguments
################

num_workloads_per_pool = 1000000

num_reps_per_point = 600 # approx 10 hours

simulator_names = ['Verilator', 'Icarus Verilog', 'CXXRTL']
num_cells_list  = [10, 100]# Might add the elements , 250, 500]
simulators      = list(map(int, [SimulatorType.SIM_VERILATOR, SimulatorType.SIM_ICARUS, SimulatorType.SIM_CXXRTL]))
simlen = 1000

DO_TRACE = False
if DO_TRACE:
    print(f"Warning: DO_TRACE is set to True")

################
# Create and run the workloads
################

def format_with_commas(value, _):
    return "{:,.0f}".format(value)


def plot_data_separate(elapsed_times_per_pair_gen, elapsed_times_per_pair_build, elapsed_times_per_pair_exec):

    ################
    # Gen perf
    ################

    all_averages = dict()
    for num_cells in num_cells_list:
        for simulator_id, _ in enumerate(simulators):
            all_averages[f"{num_cells}_{simulator_id}_{simlen}"] = np.mean(elapsed_times_per_pair_gen[f"{num_cells}_{simulator_id}_{simlen}"])

    # Plot the responses for different events and regions
    # Do one subplot per simulator
    fig, axs = plt.subplots(figsize=(6, len(simulators)*1.5), nrows=len(simulators), sharex=True)
    # ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    # Set major formatter
    if type(axs) not in (list, np.ndarray):
        axs = [axs]

    for ax in axs:
        print("type(ax):", type(ax))
        ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    axs[-1].set_xlabel('Number of cells')
    axs[1].set_ylabel('Duration (s)')

    # Plot one line per simulator
    for simulator_id, _ in enumerate(simulators):
        x = num_cells_list
        y = [all_averages[f"{num_cells}_{simulator_id}_{simlen}"] for num_cells in num_cells_list]
        axs[simulator_id].plot(x, y, label=f"simlen={format_with_commas(simlen, None)}", marker='o', linestyle='solid', linewidth=1, markersize=3)
        # axs[simulator_id].legend()
        axs[simulator_id].grid(True)
        axs[simulator_id].set_title(f"{simulator_names[simulator_id]}")
    # ax.set_xlabel('Number of cells')
    # ax.set_ylabel('Time (s)')
    plt.tight_layout()

    plt.savefig('eval_perf_gen.png', dpi=300)
    plt.savefig('eval_perf_gen.pdf', dpi=300)

    ################
    # Build perf
    ################

    all_averages = dict()
    for num_cells in num_cells_list:
        for simulator_id, _ in enumerate(simulators):
            all_averages[f"{num_cells}_{simulator_id}_{simlen}"] = np.mean(elapsed_times_per_pair_build[f"{num_cells}_{simulator_id}_{simlen}"])

    # Plot the responses for different events and regions
    # Do one subplot per simulator
    plt.clf()
    fig, axs = plt.subplots(figsize=(6, len(simulators)*1.5), nrows=len(simulators), sharex=True)
    # ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    # Set major formatter
    if type(axs) not in (list, np.ndarray):
        axs = [axs]
    for ax in axs:
        ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    axs[-1].set_xlabel('Number of cells')
    axs[1].set_ylabel('Duration (s)')

    # Plot one line per simulator
    for simulator_id, _ in enumerate(simulators):
        x = num_cells_list
        y = [all_averages[f"{num_cells}_{simulator_id}_{simlen}"] for num_cells in num_cells_list]
        axs[simulator_id].plot(x, y, label=f"simlen={format_with_commas(simlen, None)}", marker='o', linestyle='solid', linewidth=1, markersize=3)
        # axs[simulator_id].legend()
        axs[simulator_id].grid(True)
        axs[simulator_id].set_title(f"{simulator_names[simulator_id]}")
    # ax.set_xlabel('Number of cells')
    # ax.set_ylabel('Time (s)')
    plt.tight_layout()

    plt.savefig('eval_perf_build.png', dpi=300)
    plt.savefig('eval_perf_build.pdf', dpi=300)

    ################
    # Exec perf
    ################

    all_averages = dict()
    for num_cells in num_cells_list:
        for simulator_id, _ in enumerate(simulators):
            all_averages[f"{num_cells}_{simulator_id}_{simlen}"] = np.mean(elapsed_times_per_pair_exec[f"{num_cells}_{simulator_id}_{simlen}"])

    # Plot the responses for different events and regions
    # Do one subplot per simulator
    plt.clf()
    fig, axs = plt.subplots(figsize=(6, len(simulators)*1.3), nrows=len(simulators), sharex=True)
    # ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    # Set major formatter
    if type(axs) not in (list, np.ndarray):
        axs = [axs]
    for ax in axs:
        ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    axs[-1].set_xlabel('Number of cells')
    axs[1].set_ylabel('Duration (s)')

    # Plot one line per simulator
    for simulator_id, _ in enumerate(simulators):
        x = num_cells_list
        y = [all_averages[f"{num_cells}_{simulator_id}_{simlen}"] for num_cells in num_cells_list]
        axs[simulator_id].plot(x, y, label=f"simlen={format_with_commas(simlen, None)}", marker='o', linestyle='solid', linewidth=1, markersize=3)
        # axs[simulator_id].legend()
        axs[simulator_id].grid(True)
        axs[simulator_id].set_title(f"{simulator_names[simulator_id]}")
    # ax.set_xlabel('Number of cells')
    # ax.set_ylabel('Time (s)')
    plt.tight_layout()

    plt.savefig('eval_perf_exec.png', dpi=300)
    plt.savefig('eval_perf_exec.pdf', dpi=300)



def plot_data_singleplot(elapsed_times_per_pair_gen, elapsed_times_per_pair_build, elapsed_times_per_pair_exec):

    ################
    # Gen perf
    ################

    all_averages_gen = dict()
    for num_cells in num_cells_list:
        for simulator_id, _ in enumerate(simulators):
            all_averages_gen[f"{num_cells}_{simulator_id}_{simlen}"] = np.mean(elapsed_times_per_pair_gen[f"{num_cells}_{simulator_id}_{simlen}"])
    all_averages_build = dict()
    for num_cells in num_cells_list:
        for simulator_id, _ in enumerate(simulators):
            all_averages_build[f"{num_cells}_{simulator_id}_{simlen}"] = np.mean(elapsed_times_per_pair_build[f"{num_cells}_{simulator_id}_{simlen}"])
    all_averages_exec = dict()
    for num_cells in num_cells_list:
        for simulator_id, _ in enumerate(simulators):
            all_averages_exec[f"{num_cells}_{simulator_id}_{simlen}"] = np.mean(elapsed_times_per_pair_exec[f"{num_cells}_{simulator_id}_{simlen}"])

    all_averages_together = [all_averages_gen, all_averages_build, all_averages_exec]

    # Plot the responses for different events and regions
    # Do one subplot per simulator
    fig, axs = plt.subplots(figsize=(6, len(simulators)*1.2), nrows=len(simulators), ncols=3, sharex=True)

    # Plot one line per simulator

    series_colors = ['k', 'r', 'blue']

    for series_id in range(3):
        for simulator_id, _ in enumerate(simulators):
            x = num_cells_list
            y = [all_averages_together[series_id][f"{num_cells}_{simulator_id}_{simlen}"] for num_cells in num_cells_list]
            axs[series_id][simulator_id].plot(x, y, label=f"simlen={format_with_commas(simlen, None)}", marker='o', linestyle='solid', linewidth=1, markersize=3, color=series_colors[series_id])
            # axs[series_id][simulator_id].legend()
            axs[series_id][simulator_id].grid(True)
            axs[series_id][simulator_id].set_ylim(bottom=0)
            if series_id == 0:
                axs[series_id][simulator_id].set_title(f"{simulator_names[simulator_id]}")

    plt.subplots_adjust(wspace=-1.3, hspace=-1)

    for ax in axs[0]:
        ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    axs[-1][1].set_xlabel('Number of cells')
    axs[1][0].set_ylabel('Duration (s)')
    # axs[1].set_ylabel('Duration (s)')


    # ax.set_xlabel('Number of cells')
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

plot_data_singleplot(elapsed_times_per_pair_gen, elapsed_times_per_pair_build, elapsed_times_per_pair_exec)
