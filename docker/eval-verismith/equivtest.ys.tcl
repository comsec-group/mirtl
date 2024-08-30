# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

if { [info exists ::env(VERILOG_INPUT_FIRST)] }     { set VERILOG_INPUT_FIRST $::env(VERILOG_INPUT_FIRST) }         else { puts "Please set VERILOG_INPUT_FIRST environment variable"; exit 1 }
if { [info exists ::env(VERILOG_INPUT_SECOND)] }    { set VERILOG_INPUT_SECOND $::env(VERILOG_INPUT_SECOND) }       else { puts "Please set VERILOG_INPUT_SECOND environment variable"; exit 1 }
if { [info exists ::env(VERILOG_INPUT_TOP)] }       { set VERILOG_INPUT_TOP $::env(VERILOG_INPUT_TOP) }             else { puts "Please set VERILOG_TOP_SECOND environment variable"; exit 1 }

yosys read_verilog -sv $VERILOG_INPUT_FIRST $VERILOG_INPUT_SECOND $VERILOG_INPUT_TOP
yosys hierarchy -top top_equiv
yosys memory
yosys proc

yosys opt_clean
yosys flatten
yosys clk2fflogic

yosys sat -prove y_a y_b -tempinduct
