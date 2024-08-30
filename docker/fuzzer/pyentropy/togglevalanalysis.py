# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from vcdvcd import VCDVCD
from collections import defaultdict

def popcount(n):
    binary_representation = bin(n)
    return binary_representation.count('1')

def toggleval_coverage(path_to_vcd, duration):
    vcd = VCDVCD(path_to_vcd)

    # Get the toggle increases per time

    coverage_increase_times_per_signal = defaultdict(list)

    visited_vals_per_signal = defaultdict(set)

    for signal_name in vcd.signals:
        if ".in_data" in signal_name:
            continue

        for timeval, valstr in vcd[signal_name].tv[1:]:
            val = int(valstr.replace('z', '0'), 2)
            if val not in visited_vals_per_signal[signal_name]:
                visited_vals_per_signal[signal_name].add(val)
                coverage_increase_times_per_signal[signal_name].append(timeval)

    # Get the cumulated toggle increases

    incremental_coverages = []
    cursors = defaultdict(int)

    for step in range(0, duration):
        incremental_coverages.append(0)
        for signal_name in vcd.signals:
            if ".in_data" in signal_name:
                continue
            # if (cursors[signal_name] < len(coverage_increase_times_per_signal[signal_name])):
            #     print(f"Condition ok for signal {signal_name} with cursor {cursors[signal_name]} and len {len(coverage_increase_times_per_signal[signal_name])}")
            if cursors[signal_name] < len(coverage_increase_times_per_signal[signal_name]) and coverage_increase_times_per_signal[signal_name][cursors[signal_name]] <= step:
                assert coverage_increase_times_per_signal[signal_name][cursors[signal_name]] == step, f"Expected {coverage_increase_times_per_signal[signal_name][cursors[signal_name]]} to be {step}"
                incremental_coverages[step] += 1
                cursors[signal_name] += 1

    return incremental_coverages
