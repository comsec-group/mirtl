# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

if { [info exists ::env(VERILOG_INPUT)] }       { set VERILOG_INPUT $::env(VERILOG_INPUT) }       else { puts "Please set VERILOG_INPUT environment variable"; exit 1 }
if { [info exists ::env(VERILOG_OUTPUT)] }      { set VERILOG_OUTPUT $::env(VERILOG_OUTPUT) }     else { puts "Please set VERILOG_OUTPUT environment variable"; exit 1 }
if { [info exists ::env(PATH_TO_JSON)] }        { set PATH_TO_JSON $::env(PATH_TO_JSON) }         else { puts "Please set PATH_TO_JSON environment variable"; exit 1 }
if { [info exists ::env(YOSYS_PROC)] }          { set YOSYS_PROC $::env(YOSYS_PROC) }             else { set YOSYS_PROC 1 }

# set VERILOG_INPUT "template_module.sv"
# set VERILOG_OUTPUT "tmp/top.sv"
# set PATH_TO_JSON "tmp/test.json"

yosys read_verilog -defer -sv $VERILOG_INPUT
yosys hierarchy -top top -check

yosys simufuzz -verbose -json-path $PATH_TO_JSON

if {$YOSYS_PROC == 1} {
    yosys proc
}

yosys opt -purge -fine

yosys write_verilog -sv -noattr $VERILOG_OUTPUT
