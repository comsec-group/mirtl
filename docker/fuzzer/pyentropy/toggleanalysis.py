# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from vcdvcd import VCDVCD
from collections import defaultdict
import numpy as np

def popcount(n):
    binary_representation = bin(n)
    return binary_representation.count('1')

def toggle_coverage(path_to_vcd, duration):
    vcd = VCDVCD(path_to_vcd)

    # Get the toggle increases per time

    coverage_increases_per_signal = defaultdict(list)
    coverage_masks = defaultdict(int)

    for signal_name in vcd.signals:
        if ".in_data" in signal_name:
            continue

        for timeval, valstr in vcd[signal_name].tv[1:]:
            val = int(valstr.replace('z', '0'), 2)

            new_cov = popcount(val & ~coverage_masks[signal_name])
            coverage_masks[signal_name] |= val
            coverage_increases_per_signal[signal_name].append(new_cov)

    # Get the cumulated toggle increases

    incremental_toggles = []
    cursors = defaultdict(int)

    for step in range(0, duration):
        incremental_toggles.append(0)
        for signal_name in vcd.signals:
            if ".in_data" in signal_name:
                continue
            if cursors[signal_name] < len(coverage_increases_per_signal[signal_name]) and coverage_increases_per_signal[signal_name][cursors[signal_name]] > 0:
                incremental_toggles[step] += coverage_increases_per_signal[signal_name][cursors[signal_name]]
            cursors[signal_name] += 1

    return incremental_toggles

