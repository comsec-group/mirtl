# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

class CellPort:
    def __init__(self, name, is_input, is_clkin, width):
        self.name = name
        self.is_input = is_input
        self.is_clkin = is_clkin
        self.width = width
