# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from collections import defaultdict
import json
import matplotlib.pyplot as plt
import sys

SENSITIVITY_THRESHOLD = 0.015
CELLSIZE_HISTOGRAM_BIN_WIDTH = 5

name_replacement_substrings = (
    ("reduce_", "r-"),
    ("logic_", "l-"),
)

colors = {
    "Transfuzz": "darkred",
    "Verismith": "darkgray",
}

summary_path_transfuzz  = sys.argv[1]
summary_path_verismith  = sys.argv[2]

with open(summary_path_transfuzz, "r") as f:
    summary_transfuzz = json.load(f)
del summary_path_transfuzz
with open(summary_path_verismith, "r") as f:
    summary_verismith = json.load(f)
del summary_path_verismith

summary_transfuzz_by_type = summary_transfuzz["nums_cells_by_type"]
summary_verismith_by_type = summary_verismith["nums_cells_by_type"]
summary_transfuzz_by_size = summary_transfuzz["nums_cells_by_size"]
summary_verismith_by_size = summary_verismith["nums_cells_by_size"]
del summary_transfuzz
del summary_verismith

# May reintegrate the $_ cells
cell_types_to_remove = []
for key in list(summary_transfuzz_by_type.keys()):
    if key.startswith("$_"):
        cell_types_to_remove.append(key)
for key in cell_types_to_remove:
    del summary_transfuzz_by_type[key]

summary_transfuzz_by_size_prepared = defaultdict(int)
summary_verismith_by_size_prepared = defaultdict(int)

# Prepare the data for the data by size
for elem in summary_transfuzz_by_size:
    if elem == "":
        summary_transfuzz_by_size_prepared[0] += int(summary_transfuzz_by_size[elem])
    else:
        summary_transfuzz_by_size_prepared[int(elem)] = int(summary_transfuzz_by_size[elem])
del summary_transfuzz_by_size
for elem in summary_verismith_by_size:
    if elem == "":
        summary_verismith_by_size_prepared[0] += int(summary_verismith_by_size[elem])
    else:
        summary_verismith_by_size_prepared[int(elem)] = int(summary_verismith_by_size[elem])
del summary_verismith_by_size

# Compute the proportions per type
curr_sum = sum(summary_transfuzz_by_type.values())
for elem in summary_transfuzz_by_type:
    summary_transfuzz_by_type[elem] /= curr_sum
curr_sum = sum(summary_verismith_by_type.values())
for elem in summary_verismith_by_type:
    summary_verismith_by_type[elem] /= curr_sum

# Compute the proportions per size
curr_sum = sum(summary_transfuzz_by_size_prepared.values())
for elem in summary_transfuzz_by_size_prepared:
    summary_transfuzz_by_size_prepared[elem] /= curr_sum
curr_sum = sum(summary_verismith_by_size_prepared.values())
for elem in summary_verismith_by_size_prepared:
    summary_verismith_by_size_prepared[elem] /= curr_sum

##########################
# Plot the distribution by cell type
##########################

# Collect all X ticks
all_xticks = list(set(summary_transfuzz_by_type.keys()).union(set(summary_verismith_by_type.keys())))

# Fill in the missing values
for elem in all_xticks:
    if elem not in summary_transfuzz_by_type:
        summary_transfuzz_by_type[elem] = 0
    if elem not in summary_verismith_by_type:
        summary_verismith_by_type[elem] = 0

# Remove the xticks where boths are 0
xticks_to_remove = []
for elem in all_xticks:
    if summary_transfuzz_by_type[elem] < SENSITIVITY_THRESHOLD and summary_verismith_by_type[elem] < SENSITIVITY_THRESHOLD:
        xticks_to_remove.append(elem)
        print(f"Removing {elem} from the xticks: transfuzz={summary_transfuzz_by_type[elem]}, verismith={summary_verismith_by_type[elem]}")
for elem in xticks_to_remove:
    all_xticks.remove(elem)
    # Remove them from the summaries as well
    del summary_transfuzz_by_type[elem]
    del summary_verismith_by_type[elem]

all_xticks = list(sorted(all_xticks))

# all_xticks = [elem for elem in all_xticks if summary_transfuzz_by_type[elem] + summary_verismith_by_type[elem] > 0.05]

# Plot the distributions
fig, ax = plt.subplots(figsize=(6, 2))

summary_transfuzz_by_type_ys = [summary_transfuzz_by_type[elem] for elem in all_xticks]
summary_verismith_by_type_ys = [summary_verismith_by_type[elem] for elem in all_xticks]

# Multiply by 100 to get percentages
summary_transfuzz_by_type_ys = [elem*100 for elem in summary_transfuzz_by_type_ys]
summary_verismith_by_type_ys = [elem*100 for elem in summary_verismith_by_type_ys]

ax.grid(axis='y', linestyle='--', linewidth=0.5)

# Do grouped bar plot
bar_width = 0.30
bar_positions = [i for i in range(len(all_xticks))]
ax.bar([i - 0.5*bar_width for i in bar_positions], summary_transfuzz_by_type_ys, bar_width, label="Transfuzz", zorder=3, color=colors["Transfuzz"], edgecolor='black')
ax.bar([i + 0.5*bar_width for i in bar_positions], summary_verismith_by_type_ys, bar_width, label="Verismith", zorder=3, color=colors["Verismith"], edgecolor='black')

# Change the X axis limits
ax.set_xlim(-0.35, len(all_xticks)-0.72)

# Tilt the x-axis labels

all_xticks_fixednames = []
for elem in all_xticks:
    curr_name = elem
    for replacement in name_replacement_substrings:
        curr_name = curr_name.replace(replacement[0], replacement[1])
    all_xticks_fixednames.append(curr_name)

plt.xticks(bar_positions, all_xticks_fixednames, rotation=90, ha='center')
# plt.tick_params(axis='x', which='major', pad=15)  # Increase padding to move labels to the right

# ax.set_xlabel("Cell type")
ax.set_ylabel("Proportion (%)")

# Move Y label to the right
ax.yaxis.set_label_coords(-0.06, 0.5)

# ax.set_title("Distribution of cell types in the dataset")
ax.legend(framealpha=1)
plt.tight_layout()
plt.savefig("celldistribs.png", dpi=300, bbox_inches='tight')
# plt.savefig("../../figures/celldistribs.pdf", bbox_inches='tight')

# Compute the standard deviation and variance for each fuzzer
import numpy as np
transfuzz_std = np.std(summary_transfuzz_by_type_ys)
verismith_std = np.std(summary_verismith_by_type_ys)

print(f"Transfuzz std:  {transfuzz_std*100:.2f}%")
print(f"Verismith std:  {verismith_std*100:.2f}%")


##########################
# Plot the distribution by cell size
##########################
plt.clf()

# Make a grouped histogram
fig, ax = plt.subplots(figsize=(6, 1.8))

# Generate the bins
transfuzz_bins = []
verismith_bins = []
max_key_in_transfuzz = max(summary_transfuzz_by_size_prepared.keys())
max_key_in_verismith = max(summary_verismith_by_size_prepared.keys())
for curr_bin_id in range((max_key_in_transfuzz+CELLSIZE_HISTOGRAM_BIN_WIDTH-1)//CELLSIZE_HISTOGRAM_BIN_WIDTH):
    curr_bin_sum = 0
    for elem_id_in_bin in range(CELLSIZE_HISTOGRAM_BIN_WIDTH):
        curr_bin_sum += summary_transfuzz_by_size_prepared[curr_bin_id*CELLSIZE_HISTOGRAM_BIN_WIDTH + elem_id_in_bin]
    transfuzz_bins.append(curr_bin_sum)
for curr_bin_id in range((max_key_in_verismith+CELLSIZE_HISTOGRAM_BIN_WIDTH-1)//CELLSIZE_HISTOGRAM_BIN_WIDTH):
    curr_bin_sum = 0
    for elem_id_in_bin in range(CELLSIZE_HISTOGRAM_BIN_WIDTH):
        curr_bin_sum += summary_verismith_by_size_prepared[curr_bin_id*CELLSIZE_HISTOGRAM_BIN_WIDTH + elem_id_in_bin]
    verismith_bins.append(curr_bin_sum)

print(f"transfuzz_bins: {transfuzz_bins}"
      f"\nverismith_bins: {verismith_bins}")

# Make a grouped bar plot
num_ticks = max(len(transfuzz_bins), len(verismith_bins))
transfuzz_bins += [0] * (num_ticks - len(transfuzz_bins))
verismith_bins += [0] * (num_ticks - len(verismith_bins))

# Multiply by 100 to get percentages
transfuzz_bins = [elem*100 for elem in transfuzz_bins]
verismith_bins = [elem*100 for elem in verismith_bins]

# Only have 7 bins, and let be the last one the sum of the rest
num_ticks = 9
transfuzz_bins = transfuzz_bins[:num_ticks-1] + [sum(transfuzz_bins[num_ticks-1:])]
verismith_bins = verismith_bins[:num_ticks-1] + [sum(verismith_bins[num_ticks-1:])]

ax.grid(axis='y', linestyle='--', linewidth=0.5)

bar_width = 0.30
bar_positions = [i for i in range(num_ticks)]
ax.bar([i - 0.5*bar_width for i in bar_positions], transfuzz_bins, bar_width, label="Transfuzz", zorder=3, color=colors["Transfuzz"], edgecolor='black')
ax.bar([i + 0.5*bar_width for i in bar_positions], verismith_bins, bar_width, label="Verismith", zorder=3, color=colors["Verismith"], edgecolor='black')

# Tilt the x-axis labels
xtick_labels = [f"{i*CELLSIZE_HISTOGRAM_BIN_WIDTH}-{(i+1)*CELLSIZE_HISTOGRAM_BIN_WIDTH}" for i in range(num_ticks)]
# Fix the label name
xtick_labels[0] = "1"+xtick_labels[0][1:]
xtick_labels[-1] = xtick_labels[-1].split("-")[0] + "-" + "∞"

plt.xticks(bar_positions, xtick_labels, rotation=90, ha='center')

ax.set_ylabel("Proportion (%)")

# Move Y label to the right
ax.yaxis.set_label_coords(-0.06, 0.5)

ax.legend(framealpha=1)
plt.tight_layout()
plt.savefig("celldistribs_size.png", dpi=300, bbox_inches='tight')
