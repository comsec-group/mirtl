# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from pycommon.defines import PATH_TO_SV_TB_TEMPLATE, PATH_TO_SV_TB_TEMPLATE_PROBES, VERILATOR_TB_FILENAME, VERILATOR_TB_FILENAME_PROBES, PATH_TO_YOSYS, PATH_TO_YOSYS_SCRIPT_OPT, PATH_TO_YOSYS_SCRIPT_NOOPT, TEMPLATE_MODULE_NAME, TEMPLATE_MODULE_NAME_PROBES, PATH_TO_CXXRTL_TB_TEMPLATE, PATH_TO_YOSYS_SCRIPT_STATS_NOOPT, PATH_TO_YOSYS_SCRIPT_STATS_OPT
from pycommon.runparams import RunParams, SimulatorType
from pybackend.fixicarusbitselect import fix_icarus_bitselect
from collections import defaultdict
import os
import shutil
import subprocess

# @param input_probe_mask is a list of integers and must be defined if has_probes is True and simulator_type == SimulatorType.SIM_VERILATOR is True
def __create_template(fuzzerstate, data_dict: dict, simulator_type: SimulatorType, has_probes: bool, input_mask = None):
    if simulator_type == SimulatorType.SIM_VERILATOR:
        # Also dump metadata about the width of input and output data
        with open(os.path.join(fuzzerstate.workdir, 'interface_sizes.h'), 'w') as f:
            f.write('#pragma once\n')
            f.write('#define IN_DATA_WIDTH  {}\n'.format(data_dict['in_width']))
            f.write('#define FULL_RANDOM  {}\n'.format(int(fuzzerstate.is_input_full_random)))
            f.write('#define OUT_DATA_WIDTH {}\n'.format(data_dict['out_width']))
            # This one is not used by Verilator (which uses VM_TRACE), but we define it for consistency with CXXRTL
            f.write('#define DO_TRACE {}\n'.format(int(fuzzerstate.dotrace)))
            f.write('#define NUM_SUBNETS {}\n'.format(len(data_dict['cell_types'])))
            f.write('#define NUM_CLKINS {}\n'.format(len(data_dict['clkin_ports_names'])))
            if has_probes:
                f.write('#define PROBE_DATA_WIDTH {}\n'.format(data_dict['probe_width']))
            if input_mask is not None:
                # Write the input probe mask
                assert len(input_mask) == (data_dict['in_width']+31)//32
                f.write('#include <vector>\n')
                f.write('std::vector<uint32_t> input_mask = {')
                for i in range(len(input_mask)):
                    f.write('{}, '.format(hex(input_mask[i])))
                f.write('};\n')
    elif simulator_type == SimulatorType.SIM_ICARUS:
        # Icarus Verilog
        with open(PATH_TO_SV_TB_TEMPLATE if not has_probes else PATH_TO_SV_TB_TEMPLATE_PROBES, 'r') as f:
            template = f.read()
        template = template.replace('TEMPLATE_IN_DATA_WIDTH', str(data_dict['in_width']))
        template = template.replace('TEMPLATE_OUT_DATA_WIDTH', str(data_dict['out_width']))
        if has_probes:
            template = template.replace('TEMPLATE_PROBE_DATA_WIDTH', str(data_dict['probe_width']))
        template = template.replace('TEMPLATE_NUM_STEPS', str(fuzzerstate.simlen))
        template = template.replace('TEMPLATE_FULL_RANDOM', '`define FULL_RANDOM' if fuzzerstate.is_input_full_random else '`undef FULL_RANDOM')
        template = template.replace('TEMPLATE_DO_TRACE', '`define DO_TRACE' if fuzzerstate.dotrace else '`undef DO_TRACE')
        template = template.replace('TEMPLATE_PATH_TO_DUMP_FILE', os.path.join(fuzzerstate.workdir, 'icarus_dump.vcd'))
        template = template.replace('TEMPLATE_NUM_SUBNETS', f"`define NUM_SUBNETS {len(data_dict['cell_types'])}")
        template = template.replace('TEMPLATE_NUM_CLKIN_NETS', f"`define NUM_CLKIN_NETS {len(data_dict['clkin_ports_names'])}")
        template = template.replace('TEMPLATE_NO_CLKIN_NET', f"`define NO_CLKIN_NET" if len(data_dict['clkin_ports_names']) == 0 else f"`undef NO_CLKIN_NET")
        template = template.replace('TEMPLATE_PATH_TO_RANDOM_INPUTS_FILE', os.path.join(fuzzerstate.workdir, 'inputs.txt'))
        with open(os.path.join(fuzzerstate.workdir, 'tb_icarus.sv'), 'w') as f:
            f.write(template)
    elif simulator_type == SimulatorType.SIM_CXXRTL:
        # Create both the C++ wrapper and the Verilog wrapper to have many small inputs and outputs instead of a single one
        # The C++ header is identical to the Verilog header
        with open(os.path.join(fuzzerstate.workdir, 'interface_sizes.h'), 'w') as f:
            f.write('#pragma once\n')
            f.write('#define IN_DATA_WIDTH  {}\n'.format(data_dict['in_width']))
            f.write('#define FULL_RANDOM  {}\n'.format(int(fuzzerstate.is_input_full_random)))
            f.write('#define OUT_DATA_WIDTH {}\n'.format(data_dict['out_width']))
            # This one is not used by Verilator (which uses VM_TRACE), but we define it for consistency with CXXRTL
            f.write('#define DO_TRACE {}\n'.format(int(fuzzerstate.dotrace)))
            f.write('#define NUM_SUBNETS {}\n'.format(len(data_dict['cell_types'])))
            if has_probes:
                f.write('#define PROBE_DATA_WIDTH {}\n'.format(data_dict['probe_width']))
            if input_mask is not None:
                # Write the input probe mask
                assert len(input_mask) == (data_dict['in_width']+31)//32
                f.write('#include <vector>\n')
                f.write('std::vector<uint32_t> input_mask = {')
                for i in range(len(input_mask)):
                    f.write('{}, '.format(hex(input_mask[i])))
                f.write('};\n')
            f.write('#define PATH_TO_RANDOM_INPUTS_FILE "{}"\n'.format(os.path.join(fuzzerstate.workdir, 'inputs.txt')))
        # The Verilog wrapper is specific to CXXRTL
        with open(os.path.join(fuzzerstate.workdir, 'wrapper_cxxrtl.sv'), 'w') as f:
            num_clkin_signals = len(data_dict['clkin_ports_names'])
            num_input_signals = (data_dict['in_width']+31)//32
            num_output_signals = (data_dict['out_width']+31)//32

            if has_probes:
                raise NotImplementedError("Probes not yet implemented for CXXRTL")

            # Subnets are not yet implemented for CXXRTL because they are already known to be problematic
            num_subnets = len(data_dict['cell_types'])
            assert num_subnets == 1, "Subnets are not yet implemented for CXXRTL because they are already known to be problematic. See https://github.com/YosysHQ/yosys/issues/3549."

            f.write('module wrapper_cxxrtl(')
            for i in range(num_clkin_signals):
                f.write('input logic [31:0] clkin_{},'.format(i))
            for i in range(num_input_signals):
                f.write('input logic [31:0] in_{},'.format(i))
            for i in range(num_output_signals):
                f.write('output logic [31:0] out_{}{}'.format(i, ',' if i != num_output_signals-1 else ''))
            f.write(');\n')
            f.write('    logic [{}:0] clkin_;\n'.format(len(data_dict['clkin_ports_names'])*32-1))
            f.write('    logic [{}:0] in_;\n'.format(data_dict['in_width']-1))
            f.write('    logic [{}:0] out_;\n'.format(data_dict['out_width']-1))
            for i in range(num_clkin_signals):
                f.write('    assign clkin_[{}:{}] = clkin_{};\n'.format(32*(i+1)-1, 32*i, i))
            for i in range(num_input_signals):
                f.write('    assign in_[{}:{}] = in_{};\n'.format(32*(i+1)-1, 32*i, i))
            for i in range(num_output_signals):
                f.write('    assign out_{} = out_[{}:{}];\n'.format(i, 32*(i+1)-1, 32*i))
            f.write('    top top_i(clkin_, in_, out_);\n')
            f.write('endmodule\n')

        # The C++ template is specific to CXXRTL
        # Populate the template
        template_clkin_data_str = ""
        for clkin_port_id in range(num_clkin_signals):
            template_clkin_data_str += f"    if (actor_id_order[curr_id_in_actor_id_order] == {clkin_port_id + num_subnets})\n"
            template_clkin_data_str += f"    top.p_clkin__{clkin_port_id}.set<uint32_t>(inputs_from_file[curr_id_in_inputs_from_file++]);\n"
        template_in_data_str = f"    if (actor_id_order[curr_id_in_actor_id_order] == 0)" + " {\n"
        for i in range(num_input_signals):
            template_in_data_str += f"        top.p_in__{i}.set<uint32_t>(inputs_from_file[curr_id_in_inputs_from_file++]);\n"
        template_in_data_str += "    }\n"
        template_out_data_str = ""
        for i in range(num_output_signals):
            template_out_data_str += f"    cumulated_output += top.p_out__{i}.get<uint32_t>();\n"

        with open(PATH_TO_CXXRTL_TB_TEMPLATE, 'r') as f:
            cxxrtl_tb_template = f.read()
        assert cxxrtl_tb_template.count('TEMPLATE_CLKIN_DATA') == 1, f"Template contains {cxxrtl_tb_template.count('TEMPLATE_CLKIN_DATA')} TEMPLATE_CLKIN_DATA. It should contain exactly 1."
        assert cxxrtl_tb_template.count('TEMPLATE_IN_DATA') == 1, f"Template contains {cxxrtl_tb_template.count('TEMPLATE_IN_DATA')} TEMPLATE_IN_DATA. It should contain exactly 1."
        assert cxxrtl_tb_template.count('TEMPLATE_OUT_DATA') == 1, f"Template contains {cxxrtl_tb_template.count('TEMPLATE_OUT_DATA')} TEMPLATE_OUT_DATA. It should contain exactly 1."
        cxxrtl_tb_template = cxxrtl_tb_template.replace('TEMPLATE_CLKIN_DATA', template_clkin_data_str).replace('TEMPLATE_IN_DATA', template_in_data_str).replace('TEMPLATE_OUT_DATA', template_out_data_str)
        with open(os.path.join(fuzzerstate.workdir, 'tb_cxxrtl_base.cpp'), 'w') as f:
            f.write(cxxrtl_tb_template)
    else:
        raise NotImplementedError("Simulator type {} not implemented".format(simulator_type))

# @param template_input_port_tuples is a list of tuples (input_port_name, input_port_width)
def __run_yosys(work_dir: str, has_probes: bool, do_opt: bool, template_input_port_tuples: list):
    # Copy the script to the work directory
    path_to_yosys_script_local = PATH_TO_YOSYS_SCRIPT_OPT if do_opt else PATH_TO_YOSYS_SCRIPT_NOOPT
    path_to_yosys_script_absolute = os.path.join(os.path.join(work_dir, 'yosys_script.ys'))
    shutil.copyfile(path_to_yosys_script_local, path_to_yosys_script_absolute)

    cmd_str = PATH_TO_YOSYS + ' -c ' + path_to_yosys_script_absolute

    path_to_yosys_script_absolute = os.path.join(os.path.join(work_dir, 'yosys_script.ys'))

    path_to_template_module_relative = TEMPLATE_MODULE_NAME if not has_probes else TEMPLATE_MODULE_NAME_PROBES
    path_to_template_module_absolute = os.path.join(os.path.join(work_dir, TEMPLATE_MODULE_NAME if not has_probes else TEMPLATE_MODULE_NAME_PROBES))

    # Fill the template module
    with open(path_to_template_module_relative, 'r') as f:
        template_module = f.read()
    template_ports_lines = []
    for input_port_name, input_port_width in template_input_port_tuples:
        assert type(input_port_name) == str and type(input_port_width) == int, f"Invalid input_port_name {input_port_name} or input_port_width {input_port_width}"
        if input_port_width == 1:
            template_ports_lines.append(f"    logic {input_port_name};")
        else:
            template_ports_lines.append(f"    logic [{input_port_width-1}:0] {input_port_name};")
    template_module = template_module.replace('TEMPLATE_PORTS', '\n'.join(template_ports_lines))
    with open(path_to_template_module_absolute, 'w') as f:
        f.write(template_module)
        # Flush the file
        f.flush()

    # shutil.copyfile(path_to_template_module_relative, path_to_template_module_absolute)

    # Add the environment variables
    new_env = os.environ.copy()
    new_env["VERILOG_INPUT"] = path_to_template_module_absolute
    new_env["VERILOG_OUTPUT"] = os.path.join(work_dir, 'top.sv')
    new_env["PATH_TO_JSON"] = os.path.join(work_dir, 'netlist.json')
    # new_env["YOSYS_OPT_TCL_LINE"] = 'yosys opt -purge -fine' if do_opt else ''

    # Run the command and stream stdout to the console
    if RunParams.YOSYS_VERBOSE or RunParams.BACKEND_COMMAND_VERBOSE:
        print('{}'.format('VERILOG_INPUT=' + new_env["VERILOG_INPUT"] + ' '
            + 'VERILOG_OUTPUT=' + new_env["VERILOG_OUTPUT"] + ' '
            + 'PATH_TO_JSON=' + new_env["PATH_TO_JSON"] + ' '
            # + 'YOSYS_OPT_TCL_LINE="' + new_env["YOSYS_OPT_TCL_LINE"] + '" '
            + cmd_str))
    if RunParams.BACKEND_COMMAND_LOG:
        with open(os.path.join(work_dir, 'commands.log'), 'w') as f:
            f.write('{}'.format('VERILOG_INPUT=' + new_env["VERILOG_INPUT"] + ' '
                + 'VERILOG_OUTPUT=' + new_env["VERILOG_OUTPUT"] + ' '
                + 'PATH_TO_JSON=' + new_env["PATH_TO_JSON"] + ' '
                # + 'YOSYS_OPT_TCL_LINE="' + new_env["YOSYS_OPT_TCL_LINE"] + '" '
                + cmd_str))
            f.write('\n')

    if RunParams.YOSYS_VERBOSE:
        yosys_out = []
        process = subprocess.Popen(cmd_str, stdout=subprocess.PIPE, shell=True, env=new_env)
        for line in iter(process.stdout.readline, b''):
            decoded_line = line.decode('utf-8')
            print(decoded_line, end='')
            yosys_out.append(decoded_line)
    else:
        try:
            yosys_out = subprocess.run(cmd_str, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=new_env).stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            print("Yosys failed with error code {}".format(e.returncode))
            print("Command: {}".format(f'VERILOG_INPUT={new_env["VERILOG_INPUT"]} VERILOG_OUTPUT={new_env["VERILOG_OUTPUT"]} PATH_TO_JSON={new_env["PATH_TO_JSON"]} {cmd_str}'))
            print("Output: {}".format(e.output))
            print("Stderr: {}".format(e.stderr))
            raise e

    return yosys_out


# @param template_input_port_tuples is a list of tuples (input_port_name, input_port_width)
def __run_yosys_stats(work_dir: str, has_probes: bool, do_opt: bool, template_input_port_tuples: list):
    # Copy the script to the work directory
    path_to_yosys_script_local = PATH_TO_YOSYS_SCRIPT_STATS_OPT if do_opt else PATH_TO_YOSYS_SCRIPT_STATS_NOOPT
    path_to_yosys_script_absolute = os.path.join(os.path.join(work_dir, 'yosys_script.ys'))
    shutil.copyfile(path_to_yosys_script_local, path_to_yosys_script_absolute)

    cmd_str = PATH_TO_YOSYS + ' -c ' + path_to_yosys_script_absolute

    path_to_yosys_script_absolute = os.path.join(os.path.join(work_dir, 'yosys_script.ys'))

    path_to_template_module_relative = TEMPLATE_MODULE_NAME if not has_probes else TEMPLATE_MODULE_NAME_PROBES
    path_to_template_module_absolute = os.path.join(os.path.join(work_dir, TEMPLATE_MODULE_NAME if not has_probes else TEMPLATE_MODULE_NAME_PROBES))

    # Fill the template module
    with open(path_to_template_module_relative, 'r') as f:
        template_module = f.read()
    template_ports_lines = []
    for input_port_name, input_port_width in template_input_port_tuples:
        assert type(input_port_name) == str and type(input_port_width) == int, f"Invalid input_port_name {input_port_name} or input_port_width {input_port_width}"
        if input_port_width == 1:
            template_ports_lines.append(f"    logic {input_port_name};")
        else:
            template_ports_lines.append(f"    logic [{input_port_width-1}:0] {input_port_name};")
    template_module = template_module.replace('TEMPLATE_PORTS', '\n'.join(template_ports_lines))
    with open(path_to_template_module_absolute, 'w') as f:
        f.write(template_module)
        # Flush the file
        f.flush()

    # shutil.copyfile(path_to_template_module_relative, path_to_template_module_absolute)

    # Add the environment variables
    new_env = os.environ.copy()
    new_env["VERILOG_INPUT"] = path_to_template_module_absolute
    new_env["VERILOG_OUTPUT"] = os.path.join(work_dir, 'top.sv')
    new_env["PATH_TO_JSON"] = os.path.join(work_dir, 'netlist.json')
    # new_env["YOSYS_OPT_TCL_LINE"] = 'yosys opt -purge -fine' if do_opt else ''

    # Run the command and stream stdout to the console
    if RunParams.YOSYS_VERBOSE or RunParams.BACKEND_COMMAND_VERBOSE:
        print('{}'.format('VERILOG_INPUT=' + new_env["VERILOG_INPUT"] + ' '
            + 'VERILOG_OUTPUT=' + new_env["VERILOG_OUTPUT"] + ' '
            + 'PATH_TO_JSON=' + new_env["PATH_TO_JSON"] + ' '
            # + 'YOSYS_OPT_TCL_LINE="' + new_env["YOSYS_OPT_TCL_LINE"] + '" '
            + cmd_str))
    if RunParams.BACKEND_COMMAND_LOG:
        with open(os.path.join(work_dir, 'commands.log'), 'w') as f:
            f.write('{}'.format('VERILOG_INPUT=' + new_env["VERILOG_INPUT"] + ' '
                + 'VERILOG_OUTPUT=' + new_env["VERILOG_OUTPUT"] + ' '
                + 'PATH_TO_JSON=' + new_env["PATH_TO_JSON"] + ' '
                # + 'YOSYS_OPT_TCL_LINE="' + new_env["YOSYS_OPT_TCL_LINE"] + '" '
                + cmd_str))
            f.write('\n')

    if RunParams.YOSYS_VERBOSE:
        yosys_out = []
        process = subprocess.Popen(cmd_str, stdout=subprocess.PIPE, shell=True, env=new_env)
        for line in iter(process.stdout.readline, b''):
            decoded_line = line.decode('utf-8')
            print(decoded_line, end='')
            yosys_out.append(decoded_line)
        yosys_out = ''.join(yosys_out)
    else:
        try:
            yosys_out = subprocess.run(cmd_str, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=new_env).stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            print("Yosys failed with error code {}".format(e.returncode))
            print("Command: {}".format(f'VERILOG_INPUT={new_env["VERILOG_INPUT"]} VERILOG_OUTPUT={new_env["VERILOG_OUTPUT"]} PATH_TO_JSON={new_env["PATH_TO_JSON"]} {cmd_str}'))
            print("Output: {}".format(e.output))
            print("Stderr: {}".format(e.stderr))
            raise e

    return yosys_out


def __build_executable(simulator_type: SimulatorType, work_dir: str, has_probes: bool, do_trace: bool, verilator_fno_flags: str = ''):
    # Second, build the executable
    if simulator_type == SimulatorType.SIM_VERILATOR:
        cmd_str = f"verilator --cc {'--trace --trace-underscore' if do_trace else ''} --exe --Wno-MULTIDRIVEN --Wno-UNOPTFLAT --Wno-NOLATCH --Wno-WIDTHTRUNC --Wno-CMPCONST --Wno-WIDTHEXPAND --Wno-UNSIGNED {verilator_fno_flags} --build {os.path.join(os.getcwd(), VERILATOR_TB_FILENAME if not has_probes else VERILATOR_TB_FILENAME_PROBES)} {os.path.join(work_dir, 'top.sv')} -CFLAGS '-I{os.path.join(os.getcwd(), 'include')} -I{work_dir} -g' --Mdir {os.path.join(work_dir, 'obj_dir')} --build-jobs {RunParams.VERILATOR_COMPILATION_JOBS}"

    elif simulator_type == SimulatorType.SIM_ICARUS:
        os.makedirs(os.path.join(work_dir, 'icarus_obj_dir'), exist_ok=True)
        target_executable_path = os.path.join(work_dir, 'icarus_obj_dir', 'Vtop')

        with open(os.path.join(work_dir, 'top.sv'), 'r') as f:
            top_sv = f.read()

        # For Icarus, make everything 2-bit
        top_sv = top_sv.replace('logic', 'bit').replace('wire', 'bit').replace('reg', 'bit')
        top_sv = fix_icarus_bitselect(top_sv)
        with open(os.path.join(work_dir, 'top_2state.sv'), 'w') as f:
            f.write(top_sv)

        cmd_str = f"rm -f {target_executable_path} && iverilog -g2012 -o {target_executable_path} {os.path.join(work_dir, 'top_2state.sv')} {os.path.join(work_dir, 'tb_icarus.sv')}"

    elif simulator_type == SimulatorType.SIM_CXXRTL:
        os.makedirs(os.path.join(work_dir, 'cxxrtl_obj_dir'), exist_ok=True)
        target_executable_path = os.path.join(work_dir, 'cxxrtl_obj_dir', 'Vtop')

        yosys_cmd_str = f"yosys -p 'read_verilog -sv {os.path.join(work_dir, 'wrapper_cxxrtl.sv')} {os.path.join(work_dir, 'top.sv')}; write_cxxrtl {os.path.join(work_dir, 'cxxrtl_obj_dir', 'cxxrtl.cpp')}'"
        cxx_cmd_str = f"g++ -g -O3 -std=c++14 -I`yosys-config --datdir`/include/backends/cxxrtl/runtime -I{os.path.join(os.getcwd(), 'include')} -I{work_dir} -I{os.path.join(work_dir, 'cxxrtl_obj_dir')} {os.path.join(work_dir, 'tb_cxxrtl_base.cpp')} -o {target_executable_path}"
        cmd_str = f"{yosys_cmd_str} && {cxx_cmd_str}"

    else:
        raise NotImplementedError("Simulator type {} not implemented".format(simulator_type))

    if RunParams.BACKEND_COMMAND_VERBOSE:
        print(cmd_str)
    if RunParams.BACKEND_COMMAND_LOG:
        with open(os.path.join(work_dir, f"commands_{simulator_type}.log"), 'a') as f:
            f.write(cmd_str)
            f.write('\n')

    if RunParams.EXECUTION_VERBOSE:
        subprocess.run(cmd_str, check=True, shell=True)
    else:
        subprocess.run(cmd_str, check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Returns a tuple of (elapsed_time, output_signature, stderr)
def __run_executable(fuzzerstate, simulator_type: SimulatorType, timeout_seconds: int):
    # Second, run the executable
    if simulator_type == SimulatorType.SIM_VERILATOR:
        if fuzzerstate.get_tracefile() is None or fuzzerstate.get_inputsfile() is None:
            raise ValueError(f"fuzzerstate.get_tracefile() and fuzzerstate.get_inputsfile() must be defined. fuzzerstate.get_tracefile(): {fuzzerstate.get_tracefile()}, fuzzerstate.get_inputsfile(): {fuzzerstate.get_inputsfile()}")
        cmd_str = f"TRACEFILE={fuzzerstate.get_tracefile()} INPUTS_FILE={fuzzerstate.get_inputsfile()} SIMLEN={fuzzerstate.simlen} {os.path.join('.', os.path.join(fuzzerstate.workdir, 'obj_dir', 'Vtop'))}"
    elif simulator_type == SimulatorType.SIM_ICARUS:
        # Icarus Verilog
        # -M .: Look for the VPI object file in the current directory
        # -mdpi_wallclock: Use the DPI wallclock function
        cmd_str = f"vvp -M . -mdpi_wallclock {os.path.join(fuzzerstate.workdir, 'icarus_obj_dir', 'Vtop')} {'+vcd' if fuzzerstate.dotrace else ''}"
        # Check that the file exists
        assert os.path.exists(os.path.join(fuzzerstate.workdir, 'icarus_obj_dir', 'Vtop')), f"File {os.path.join(fuzzerstate.workdir, 'icarus_obj_dir', 'Vtop')} does not exist"
        # cmd_str = f"vvp -M . {os.path.join(fuzzerstate.workdir, 'icarus_obj_dir', 'Vtop')} {'+vcd' if fuzzerstate.dotrace else ''}"
    elif simulator_type == SimulatorType.SIM_CXXRTL:
        cmd_str = f"INPUTS_FILE={fuzzerstate.get_inputsfile()} {os.path.join(fuzzerstate.workdir, 'cxxrtl_obj_dir', 'Vtop')}"
    else:
        raise NotImplementedError("Simulator type {} not implemented for __run_executable".format(simulator_type))
    if RunParams.BACKEND_COMMAND_VERBOSE:
        print(cmd_str)
    if RunParams.BACKEND_COMMAND_LOG:
        with open(os.path.join(fuzzerstate.workdir, f"commands_{simulator_type}.log"), 'a') as f:
            f.write(cmd_str)
            f.write('\n')
    # Add simlen to the environment
    new_env = os.environ.copy()
    new_env["SIMLEN"] = str(fuzzerstate.simlen)
    new_env["TRACEFILE"] = fuzzerstate.get_tracefile()
    new_env["INPUTS_FILE"] = fuzzerstate.get_inputsfile()

    # Check whether the file exists
    process_out = subprocess.run(cmd_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=new_env, shell=True, check=True, timeout=timeout_seconds)
    elapsed_time_line = None
    output_signature_line = None
    probe_tuples = []
    recorded_lines = []
    for line in process_out.stdout.splitlines():
        recorded_lines.append(line)
        if line.startswith(b'Output signature:'):
            output_signature_line = line
        elif line.startswith(b'Probe step'):
            # The line format is Probe step %d word %d: %
            probe_step = line.decode('utf-8').split()[2]
            probe_word = line.decode('utf-8').split()[4]
            probe_value = line.decode('utf-8').split()[6]
            probe_tuples.append((probe_step, probe_word, probe_value))
        elif line.startswith(b'Elapsed time:'):
            elapsed_time_line = line
            break

    elapsed_time = None if elapsed_time_line is None else elapsed_time_line.decode('utf-8').split()[2][:-1]
    output_signature = None if output_signature_line is None else output_signature_line.decode('utf-8').split()[2][:-1]
    stderr = process_out.stderr
    stderr = stderr.decode('utf-8')
    # Close the process
    # Parse the elapsed time. The line is of the form "Elapsed time: <time>."
    if elapsed_time is None or output_signature is None:
        # if elapsed_time is None:
        #     print("Missing elapsed time")
        # if output_signature is None:
        #     print("Missing output signature")
        print(f"Something went wrong with command '{cmd_str}'")
        pass
    return elapsed_time, output_signature, probe_tuples, stderr

def __extract_yosys_stats(yosys_out: str):
    # Write the Yosys out
    with open('yosys_out.log', 'w') as f:
        f.write(yosys_out)

    # Find the last occurrence of `Number of cells:`, starting from behind
    stdout_lines = list(map(lambda s: s.strip(), yosys_out.split("\n")))
    num_cells_line_id = None
    for line_id in range(len(stdout_lines) - 1, -1, -1):
        if stdout_lines[line_id].startswith("Number of cells:"):
            num_cells_line_id = line_id
            break

    # Starting from this line, get the number of cells for all lines until we meet a line that does not start with `$`
    num_cells_by_type = defaultdict(int)
    num_cells_by_size = defaultdict(int)
    for line_id in range(num_cells_line_id + 1, len(stdout_lines)):
        line = stdout_lines[line_id]
        if not line.startswith("$"):
            break
        splitted_line = line.split()
        # Get the cell type and the number of cells
        if line.startswith("$_"):
            cell_type = splitted_line[0]
            cell_size = 1
        else:
            cell_type = '_'.join(splitted_line[0].split("_")[:-1])
            cell_size = splitted_line[0].split("_")[-1]
        num_cells_by_type[cell_type] += int(splitted_line[-1])
        num_cells_by_size[cell_size] += int(splitted_line[-1])

    return num_cells_by_type, num_cells_by_size


def build_yosys(fuzzerstate, netlist_dict: dict, simulator_type: SimulatorType, has_probes: bool, do_opt: bool, template_input_port_tuples: list, input_mask = None):
    __create_template(fuzzerstate, netlist_dict, simulator_type, has_probes, input_mask)
    return __run_yosys(fuzzerstate.workdir, has_probes, do_opt, template_input_port_tuples)

def build_yosys_stats(fuzzerstate, netlist_dict: dict, simulator_type: SimulatorType, has_probes: bool, do_opt: bool, template_input_port_tuples: list, input_mask = None):
    __create_template(fuzzerstate, netlist_dict, simulator_type, has_probes, input_mask)
    return __run_yosys_stats(fuzzerstate.workdir, has_probes, do_opt, template_input_port_tuples)

# Returns nothing
def build_executable_worker(fuzzerstate, netlist_dict: dict, simulator_type: SimulatorType, has_probes: bool, do_opt: bool, template_input_port_tuples: list, input_mask = None, verilator_fno_flags: str = ''):
    build_yosys(fuzzerstate, netlist_dict, simulator_type, has_probes, do_opt, template_input_port_tuples, input_mask)
    # __replace_signames(fuzzerstate.workdir)
    __build_executable(simulator_type, fuzzerstate.workdir, has_probes, fuzzerstate.dotrace, verilator_fno_flags)

def get_cell_stats(fuzzerstate, netlist_dict: dict, simulator_type: SimulatorType, has_probes: bool, do_opt: bool, template_input_port_tuples: list, input_mask = None):
    yosys_out = build_yosys_stats(fuzzerstate, netlist_dict, simulator_type, has_probes, do_opt, template_input_port_tuples, input_mask)
    return __extract_yosys_stats(yosys_out)

def run_executable_worker(fuzzerstate, simulator_type: SimulatorType, timeout_seconds: int = None):
    elapsed_time, output_signature, probe_tuples, stderr = __run_executable(fuzzerstate, simulator_type, timeout_seconds)
    return elapsed_time, output_signature, probe_tuples, stderr
