# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from copy import deepcopy
import numpy as np

# Replaces all np.int64 with int in a dict
def __replace_int64_with_int(in_datastruct):
    if isinstance(in_datastruct, dict):
        my_iterable = in_datastruct.items()
    elif isinstance(in_datastruct, list) or isinstance(in_datastruct, tuple):
        my_iterable = enumerate(in_datastruct)
    else:
        raise ValueError(f"Instance of type {type(in_datastruct)} found")

    # We transform tuples into lists for simplicity. May be optimized in the future.
    if isinstance(in_datastruct, tuple):
        in_datastruct = list(in_datastruct)

    for key, value in my_iterable:
        if isinstance(value, dict):
            in_datastruct[key] = __replace_int64_with_int(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            in_datastruct[key] = __replace_int64_with_int(value)
        elif isinstance(value, np.int64):
            in_datastruct[key] = int(value)
    
    return in_datastruct


# Make the netlist JSON serializable
# @return the cleaned netlist
def cleanup_netlist(in_netlist: dict):
    ret = deepcopy(in_netlist)
    return __replace_int64_with_int(ret)
