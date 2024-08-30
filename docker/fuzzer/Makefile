# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

SIMLEN?=1000

rebuild_verilator: verilator_testbench_numcolumns.cc tmp/top.sv
	@verilator --cc --exe --build ../$< $(word 2,$^) -CFLAGS "-I../include" -j 10

build_verilator: verilator_testbench_numcolumns.cc tmp/top.sv
	verilator --cc --exe --build ../$< $(word 2,$^) -CFLAGS "-I../include -I../tmp" -j 10

.PHONY: run_verilator
run_verilator: build_verilator
	SIMLEN=$(SIMLEN) obj_dir/Vtop

.PHONY: purge
purge:
	rm -rf obj_dir* tmp*