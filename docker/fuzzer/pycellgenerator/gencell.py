# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import random
import numpy as np

from pycellgenerator.allcells import ALL_CELL_PORTS, ALL_CELL_PORTS_STATEFUL, CELL_PARAMS, get_port_size
from pydefs.cell import Cell
from pydefs.cellport import CellPort
from pycommon.fuzzparams import FuzzerParams

def __gen_random_parameters_for_cell(cell_type: str, cell_dimensions: list):
    if cell_type not in CELL_PARAMS:
        return []
    ret = []
    for param_size in CELL_PARAMS[cell_type]:
        assert isinstance(param_size, int) or param_size is None, f"Parameter size {param_size} is not an integer and not None for cell type {cell_type}"
        if isinstance(param_size, int):
            ret.append(random.getrandbits(param_size))
        else:
            if FuzzerParams.ResetMustBeZero:
                ret.append(0)
            else:
                ret.append(random.getrandbits(max(cell_dimensions)))
    return ret

def __gen_random_dimension(fuzzerstate):
    return 2 + np.random.geometric(1/8)
    # return random.randint(fuzzerstate.cell_min_dimension, fuzzerstate.cell_max_dimension)

# Gates only accept single-bit connections
def __is_cell_a_gate(cell_type: str):
    return cell_type[0] == '_' and cell_type[-1] != '_'

def __is_port_clkin(port_name: str, is_cell_stateful: bool):
    if not is_cell_stateful:
        return False
    return port_name in ('C', 'L', 'E', 'R') or 'CLK' in port_name or 'EN' in port_name or 'RST' in port_name or 'LOAD' in port_name or 'SET' in port_name or 'CLR' in port_name

# Returns a Cell object.
def gen_random_cell(fuzzerstate, can_be_stateful: bool):
    is_stateful = can_be_stateful and random.random() < FuzzerParams.ProbaPickStateful and len(fuzzerstate.authorized_stateful_cell_types)

    if is_stateful:
        cell_type = random.choice(fuzzerstate.authorized_stateful_cell_types)
        cell_port_tuples = ALL_CELL_PORTS_STATEFUL[cell_type]
    else:
        cell_type = random.choice(fuzzerstate.authorized_combinational_cell_types)
        cell_port_tuples = ALL_CELL_PORTS[cell_type]

    if __is_cell_a_gate(cell_type):
        cell_dimension = 1
    else:
        cell_dimension = __gen_random_dimension(fuzzerstate)

    cell_ports = []
    for cell_port_tuple in cell_port_tuples:
        port_size = get_port_size(cell_port_tuple, cell_dimension)
        cell_port = CellPort(cell_port_tuple[0], cell_port_tuple[1], __is_port_clkin(cell_port_tuple[0], is_stateful), port_size)
        cell_ports.append(cell_port)

    cell_params = __gen_random_parameters_for_cell(cell_type, [cell_dimension])

    return Cell(cell_type, cell_ports, cell_params)
