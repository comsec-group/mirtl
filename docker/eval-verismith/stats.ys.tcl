# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

if { [info exists ::env(VERILOG_INPUT)] }     { set VERILOG_INPUT $::env(VERILOG_INPUT) }         else { puts "Please set VERILOG_INPUT environment variable"; exit 1 }
if { [info exists ::env(TOP_MODULE)] }        { set TOP_MODULE $::env(TOP_MODULE) }               else { puts "Please set TOP_MODULE environment variable"; exit 1 }

yosys read_verilog -sv $VERILOG_INPUT
yosys hierarchy -top $TOP_MODULE
yosys memory
yosys proc
yosys opt_clean

yosys stat -width

