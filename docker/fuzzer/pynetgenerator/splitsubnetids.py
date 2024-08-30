# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from pycommon.fuzzparams import FuzzerParams
from enum import Enum
import random

class ClkInType(Enum):
    C = 0
    L = 1
    E = 2
    R = 3
    S = 4
    def port_name_to_clkin_type(port_name: str):
        if port_name == 'C' or 'CLK' in port_name:
            return ClkInType.C
        elif port_name == 'L' or 'LOAD' in port_name:
            return ClkInType.L
        elif port_name == 'E' or 'EN' in port_name:
            return ClkInType.E
        # Actually 'R' can also be the clear signal of single-bit latches but the effect is exactly the same as a reset
        elif port_name == 'R' or 'RST' in port_name or 'CLR' in port_name:
            return ClkInType.R
        elif port_name == 'S' or 'SET' in port_name:
            return ClkInType.S
        else:
            assert False, f"Unknown clkin type {port_name}"
    def to_char(ClkInType):
        if ClkInType == ClkInType.C:
            return 'C'
        elif ClkInType == ClkInType.L:
            return 'L'
        elif ClkInType == ClkInType.E:
            return 'E'
        elif ClkInType == ClkInType.R:
            return 'R'
        elif ClkInType == ClkInType.S:
            return 'S'
        else:
            assert False, f"Unknown clkin type {ClkInType}"

# @param all_requesters_per_clkin_type: dict of ClkInType -> list of (subnet_id, cell_id)
def split_subnet_ids(all_requesters_per_clkin_type):
    orig_subnetids = list(all_requesters_per_clkin_type.keys())
    # Duplicate randomly some of the subnet ids
    # This structure could actually be flattened further.
    target_subnetids = {
        subnetid: [[] for _ in range(random.randint(1, FuzzerParams.MaxNumSubnetIdsPerClkinType))] for subnetid in orig_subnetids
    }
    for subnetid in orig_subnetids:
        for elem in range(len(all_requesters_per_clkin_type[subnetid])):
            target_subnetids[subnetid][random.randint(0, len(target_subnetids[subnetid]) - 1)].append(all_requesters_per_clkin_type[subnetid][elem])
    # Remove the potentially empry subnets
    for subnetid in orig_subnetids:
        for splitted_subnetid in range(len(target_subnetids[subnetid]) - 1, -1, -1):
            if len(target_subnetids[subnetid][splitted_subnetid]) == 0:
                del target_subnetids[subnetid][splitted_subnetid]
    return target_subnetids
