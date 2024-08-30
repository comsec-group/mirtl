# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import os

class FuzzerParams:
    MinInputWidthWords = 3
    MinOutputWidthWords = 3
    ProportionFinalCellsConnectedToOutputMin = 0.00
    ProportionFinalCellsConnectedToOutputMax = 0.10
    CellMinDimension = 1
    CellMaxDimension = 40 # Might increase again to 300
    ProbaReqLoop = 0 # 0.001 # We dont make it very likely because we haven't seen cases where it was necessary. Although loops are not expensive.
    ProbaToggleSubnet = 0.8 # As opposed to toggling a clkin
    ProbaForceConnectToUnconnectedOutput = 0.4
    ProbaPickOffsetInUnconnectedOutput = 0.1
    ProbaPickStateful = 0.05
    AuthorizePickStatefulGates = False
    MaxNumSubnetIdsPerClkinType = 2
    ResetMustBeZero = True # Useful for CXXRTL or for fuzzing Yosys
    ProbaSecondSubnet = 1 # Must be 0 for cxxrtl, see https://github.com/YosysHQ/yosys/issues/3549. This feature has not been critical yet, but could be, who knows.
    MaxNumCellsNonPrimarySubnet = 20

class FuzzerState:
    # @param is_input_full_random if every single input word is randomized, or just one word per cycle.
    def __init__(self, workdir: str, cell_min_dimension: int, cell_max_dimension: int, is_input_full_random: int, num_cells_min: int, num_cells_max: int, num_input_words: int, num_output_words: int, simlen: int, dotrace: bool, authorized_combinational_cell_types: list, authorized_stateful_cell_types: list) -> None:
        assert cell_min_dimension >= 1, "cell_min_dimension must be >= 1"
        assert cell_max_dimension >= cell_min_dimension, "cell_max_dimension must be >= cell_min_dimension"
        assert num_cells_min >= 1, "num_cells_min must be >= 1"
        assert num_cells_max >= num_cells_min, "num_cells_max must be >= num_cells_min"
        assert num_input_words >= 3, "num_input_words must be >= 3"
        assert num_output_words >= 3, "num_output_words must be >= 3"
        assert simlen >= 1, "simlen must be >= 1"

        self.set_workdir(workdir)

        self.cell_min_dimension = cell_min_dimension
        self.cell_max_dimension = cell_max_dimension
        self.is_input_full_random = is_input_full_random

        self.num_cells_min = num_cells_min
        self.num_cells_max = num_cells_max

        self.num_input_words = num_input_words
        self.num_output_words = num_output_words

        self.simlen = simlen
        self.dotrace = dotrace
        self.authorized_combinational_cell_types = authorized_combinational_cell_types
        self.authorized_stateful_cell_types = authorized_stateful_cell_types

    def set_tracefile(self, tracefile: str) -> None:
        self.tracefile = os.path.join(self.workdir, 'trace.vcd')
    def get_tracefile(self) -> None:
        return self.tracefile

    def set_inputsfile(self, inputsfile: str) -> None:
        self.inputsfile = os.path.join(self.workdir, 'inputs.txt')
    def get_inputsfile(self) -> None:
        return self.inputsfile

    def set_workdir(self, workdir: str) -> None:
        self.workdir = workdir
        if workdir is not None:
            os.makedirs(self.workdir, exist_ok=True)
            self.set_tracefile('trace.vcd')
            self.set_inputsfile('inputs.txt')
        else:
            self.tracefile = None
            self.inputsfile = None
