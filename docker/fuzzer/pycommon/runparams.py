# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from enum import IntEnum

class SimulatorType(IntEnum):
    SIM_VERILATOR = 0
    SIM_ICARUS = 1
    SIM_CXXRTL = 2

class RunParams:
    YOSYS_VERBOSE = False
    EXECUTION_VERBOSE = False
    BACKEND_COMMAND_VERBOSE = False
    BACKEND_COMMAND_LOG = True
    DO_TRACE = False
    VERILATOR_COMPILATION_JOBS = 4
