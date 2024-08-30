# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import matplotlib.pyplot as plt
import json
import sys

TIMEOUT_VAL = 900

path_to_transfuzz_summary = sys.argv[1]
path_to_verismith_summary = sys.argv[2]

with open(path_to_transfuzz_summary, "r") as f:
    pairs_transfuzz = json.load(f)
with open(path_to_verismith_summary, "r") as f:
    pairs_verismith = json.load(f)

# Make a dot plot
x_values_transfuzz = list(map(lambda a: int(a[0]), pairs_transfuzz))
x_values_verismith = list(map(lambda a: int(a[0]), pairs_verismith))

# For the Y values, we change TIMEOUT to the timeout value
y_values_transfuzz = list(map(lambda a: TIMEOUT_VAL if a[1] == "TIMEOUT" else float(a[1]), pairs_transfuzz))
y_values_verismith = list(map(lambda a: TIMEOUT_VAL if a[1] == "TIMEOUT" else float(a[1]), pairs_verismith))


# Average number of cells for each fuzzer
avg_num_cells_transfuzz = sum(x_values_transfuzz) / len(x_values_transfuzz)
avg_num_cells_verismith = sum(x_values_verismith) / len(x_values_verismith)

print(f"Average number of cells for TransFuzz: {avg_num_cells_transfuzz}")
print(f"Average number of cells for Verismith: {avg_num_cells_verismith}")

# Average time per cell
avg_time_per_cell_transfuzz = sum(y_values_transfuzz) / sum(x_values_transfuzz)
avg_time_per_cell_verismith = sum(y_values_verismith) / sum(x_values_verismith)

print(f"Average time (seconds) per cell for TransFuzz: {avg_time_per_cell_transfuzz:.4f}")
print(f"Average time (seconds) per cell for Verismith: {avg_time_per_cell_verismith:.4f}")
print(f"Speedup per cell: {avg_time_per_cell_verismith / avg_time_per_cell_transfuzz:.2f}")

# Plot the data

fig, ax = plt.subplots(figsize=(6, 2.5))
ax.scatter(x_values_transfuzz, y_values_transfuzz, label="TransFuzz", color="blue", s=10)
ax.scatter(x_values_verismith, y_values_verismith, label="Verismith", color="red", s=10)

# ax.set_ylim(0, 5)

# Add labels and title
plt.xlabel("Num cells")
plt.ylabel("Time (s)")
plt.legend()

# plt.savefig("celldistribs_size.png", dpi=300)
# plt.savefig("../../figures/celldistribs_size.pdf")

# plt.savefig("perfpercell_verismith.png", dpi=300)
# plt.savefig("../../figures/perfpercell_verismith.pdf")
