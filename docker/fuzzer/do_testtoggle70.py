# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from testtoggle.testtoggle import testtoggle_wrapper
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import json
import multiprocessing as mp
import sys

################
# Collect the arguments
################

def format_with_commas(value, _):
    return "{:,.0f}".format(value)

num_processes = int(sys.argv[1])

# forbidden_cell_ids = []
# for cell_id, cell_name in enumerate(ALL_CELL_PORTS.keys()):
#     if cell_name not in ALL_CELL_NAMES_TRANSMITTERS:
#         forbidden_cell_ids.append(cell_id)

num_reps_per_point = 10

max_nums_cells   = [10] + [50*i for i in range(1, 8)] # Might increase to range(1, 41) 

max_simlen = 70



def gen_data():
    workloads = []
    curr_workload_id = 0

    for max_num_cells in max_nums_cells:
        min_num_cells = max_num_cells
        for rep_id in range(num_reps_per_point):
            workloads.append((curr_workload_id, min_num_cells, max_num_cells, max_simlen))
            curr_workload_id += 1

    with mp.Pool(num_processes) as pool:
        curr_flat_ret_vals = pool.starmap(testtoggle_wrapper, workloads)

    # curr_flat_ret_vals[num_cells][rep_id][simlen] = ret_val

    # curr_averaged_hierarch_ret_vals[num_cells][simlen] = avg_val
    curr_averaged_hierarch_ret_vals = [[0 for _ in range(max_simlen)] for _ in range(len(max_nums_cells))]
    for curr_max_num_cells_id in range(len(max_nums_cells)):
        for rep_id in range(num_reps_per_point):
            for curr_simlen in range(max_simlen):
                curr_averaged_hierarch_ret_vals[curr_max_num_cells_id][curr_simlen] += curr_flat_ret_vals[curr_max_num_cells_id*num_reps_per_point+rep_id][curr_simlen]
        for curr_simlen in range(max_simlen):
            curr_averaged_hierarch_ret_vals[curr_max_num_cells_id][curr_simlen] /= num_reps_per_point

    # index_in_flat_ret_vals = 0
    # for curr_max_num_cells_id in range(len(max_nums_cells)):
    #     curr_averaged_hierarch_ret_vals.append([])
    #         for rep_id in range(num_reps_per_point):
    #             curr_averaged_hierarch_ret_vals[curr_max_num_cells_id][curr_simlen] += curr_flat_ret_vals[index_in_flat_ret_vals][curr_simlen]
    #     for curr_simlen in range(max_simlen):
    #         curr_averaged_hierarch_ret_vals[curr_max_num_cells_id].append(0)
    #         index_in_flat_ret_vals += 1
    #         curr_averaged_hierarch_ret_vals[curr_max_num_cells_id][curr_simlen] /= num_reps_per_point

    print(f"curr_averaged_hierarch_ret_vals[0]: {curr_averaged_hierarch_ret_vals[0]}")

    return curr_averaged_hierarch_ret_vals


def plot_data(all_ret_vals):

    # Plot the responses for different events and regions
    # Do one subplot per cell size
    fig, ax = plt.subplots(figsize=(6, 3))

    ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    print(f"len(all_ret_vals): {len(all_ret_vals)}")
    print(f"len(all_ret_vals[0]): {len(all_ret_vals[0])}")

    # Plot one line per max_num_cells
    for max_num_cells_id in range(len(max_nums_cells)):
        x = range(1, max_simlen+1)
        y = all_ret_vals[max_num_cells_id][:max_simlen]

        ax.plot(x, y, label=f"Num_cells={format_with_commas(max_nums_cells[max_num_cells_id], None)}", marker='o', linestyle='solid', linewidth=1, markersize=3)
        ax.legend()
        ax.grid(True)
    ax.set_xlabel('Simlen')
    ax.set_ylabel('New toggles')
    plt.tight_layout()

    plt.savefig('eval_toggle_incr70.png', dpi=300)
    plt.savefig('eval_toggle_incr70.pdf', dpi=300)


def plot_data_cumulated(all_ret_vals):
    all_ret_vals_cumulated = []
    for max_num_cells_id in range(len(max_nums_cells)):
        all_ret_vals_cumulated.append([])
        for curr_simlen in range(max_simlen):
            all_ret_vals_cumulated[max_num_cells_id].append(sum(all_ret_vals[max_num_cells_id][:curr_simlen+1]))

    # Plot the responses for different events and regions
    # Do one subplot per cell size
    fig, ax = plt.subplots(figsize=(6, 3))

    ax.xaxis.set_major_formatter(FuncFormatter(format_with_commas))
    print(f"len(all_ret_vals_cumulated): {len(all_ret_vals_cumulated)}")
    print(f"len(all_ret_vals_cumulated[0]): {len(all_ret_vals_cumulated[0])}")

    # Plot one line per max_num_cells
    for max_num_cells_id in range(len(max_nums_cells)):
        x = range(1, max_simlen+1)
        y = all_ret_vals_cumulated[max_num_cells_id][:max_simlen]

        ax.plot(x, y, label=f"Num_cells={format_with_commas(max_nums_cells[max_num_cells_id], None)}", marker='o', linestyle='solid', linewidth=1, markersize=3)
        ax.legend()
        ax.grid(True)
    ax.set_xlabel('Simlen')
    ax.set_ylabel('New toggles')
    plt.tight_layout()

    plt.savefig('eval_toggle70.png', dpi=300)
    plt.savefig('eval_toggle70.pdf', dpi=300)

# Gen the data
all_ret_vals = gen_data()
dump_dict = {
    "max_simlen": max_simlen,
    "max_nums_cells": max_nums_cells,
    "all_ret_vals": all_ret_vals
}
with open("testtoggle_results70.json", "w") as f:
    json.dump(dump_dict, f)

# Retreive the data
with open("testtoggle_results70.json", "r") as f:
    all_ret_vals = json.load(f)["all_ret_vals"]
plot_data(all_ret_vals)
plot_data_cumulated(all_ret_vals)
