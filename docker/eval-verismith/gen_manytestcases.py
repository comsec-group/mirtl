# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from collections import defaultdict
import multiprocessing as mp
import json
import os
import subprocess
import sys

# sys.argv[1]: target directory
# sys.argv[2]: num test cases

target_dirpath = sys.argv[1]
num_testcases  = int(sys.argv[2])
root_path_to_verismith = sys.argv[3]

# Find the path to verismith
from pathlib import Path
def find_file_in_subdirectories(root_dir, filename):
    root_path = Path(root_dir)
    matches = []
    for path in root_path.rglob(filename):
        matches.append(path)
    assert len(matches) == 1, f"Expected to find exactly one file with name {filename} in the subdirectories of {root_dir}, but found {len(matches)} files."
    return matches[0]
path_to_verismith = find_file_in_subdirectories(root_path_to_verismith, "verismith")

# Create the directory if it does not already exist
os.makedirs(target_dirpath, exist_ok=True)

# Make sure that the path to Verismith is correct
assert os.path.exists(path_to_verismith), f"Path to Verismith does not exist: {path_to_verismith}"

# Generates a list of modules
def __gen_design():
    # Generate a design using the command `cabal run verismith generate`
    design = subprocess.run([f"{path_to_verismith} generate"], shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
    return design

def __get_cell_distribution(design_filepath):
    # We use Yosys for this.
    curr_env = os.environ.copy()
    curr_env["VERILOG_INPUT"] = design_filepath
    curr_env["TOP_MODULE"] = "top"

    stdout = subprocess.run(f"yosys -c stats.ys.tcl", shell=True, env=curr_env, stdout=subprocess.PIPE).stdout.decode('utf-8')

    # Find the last occurrence of `Number of cells:`, starting from behind
    stdout_lines = list(map(lambda s: s.strip(), stdout.split("\n")))
    num_cells_line_id = None
    for line_id in range(len(stdout_lines) - 1, -1, -1):
        if stdout_lines[line_id].startswith("Number of cells:"):
            num_cells_line_id = line_id
            break

    # Starting from this line, get the number of cells for all lines until we meet a line that does not start with `$`
    num_cells_by_type = dict()
    num_cells_by_size = dict()
    for line_id in range(num_cells_line_id + 1, len(stdout_lines)):
        line = stdout_lines[line_id]
        if not line.startswith("$"):
            break
        splitted_line = line.split()
        # Get the cell type and the number of cells
        cell_type = '_'.join(splitted_line[0].split("_")[:-1])
        cell_size = splitted_line[0].split("_")[-1]
        num_cells_by_type[cell_type] = int(splitted_line[-1])
        num_cells_by_size[cell_size] = int(splitted_line[-1])

    return num_cells_by_type, num_cells_by_size

nums_cells_by_type = []
nums_cells_by_size = []

def gen_design_and_get_distribution(design_id: int):
    # Make sure there will be no duplicate (duplicates are not so common so it's not super critical for now)
    design = __gen_design()
    design_filepath = os.path.join(target_dirpath, f"design_{design_id}.v")
    with open(design_filepath, "w") as f:
        f.write(design)
    num_cells_by_type, num_cells_by_size = __get_cell_distribution(design_filepath)
    return num_cells_by_type, num_cells_by_size

with mp.Pool(mp.cpu_count()) as pool:
    nums_cells_by_type__nums_cells_by_size = pool.map(gen_design_and_get_distribution, range(num_testcases))

nums_cells_by_type = defaultdict(int)
nums_cells_by_size = defaultdict(int)

for num_cells_by_type, num_cells_by_size in nums_cells_by_type__nums_cells_by_size:
    for cell_type, num_cells in num_cells_by_type.items():
        nums_cells_by_type[cell_type] += num_cells
    for cell_size, num_cells in num_cells_by_size.items():
        nums_cells_by_size[cell_size] += num_cells

summary_path = os.path.join(target_dirpath, "cell_summary_verismith.json")
with open(summary_path, "w") as f:
    json.dump({"nums_cells_by_type": nums_cells_by_type, "nums_cells_by_size": nums_cells_by_size}, f, indent=4)
