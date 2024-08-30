# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import os

NOCELL_CODE = -1
INTF_WORD_WIDTH = 32

# Backend
TMP_DIRNAME = 'tmp'
PATH_TO_YOSYS_SCRIPT_STATS_OPT = 'yosys_script_stats_opt.ys.tcl'
PATH_TO_YOSYS_SCRIPT_STATS_NOOPT = 'yosys_script_stats_noopt.ys.tcl'
PATH_TO_YOSYS_SCRIPT_OPT = 'yosys_script_opt.ys.tcl'
PATH_TO_YOSYS_SCRIPT_NOOPT = 'yosys_script_noopt.ys.tcl'
VERILATOR_TB_FILENAME = 'tb_base.cc'
VERILATOR_TB_FILENAME_PROBES = 'tb_base_probes.cc'
PATH_TO_SV_TB_TEMPLATE = 'tb_icarus.sv.template'
PATH_TO_SV_TB_TEMPLATE_PROBES = 'tb_icarus_probes.sv.template'
PATH_TO_CXXRTL_TB_TEMPLATE = 'template_tb_cxxrtl_base.cc'
TEMPLATE_MODULE_NAME = 'template_module.sv'
TEMPLATE_MODULE_NAME_PROBES = 'template_module_probes.sv'
PATH_TO_YOSYS = os.path.join('/', 'mirtl-yosys', 'yosys')
