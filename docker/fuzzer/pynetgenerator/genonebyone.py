import random
import numpy as np
from collections import defaultdict
from functools import reduce
from operator import concat

from pycellgenerator.gencell import gen_random_cell
from pycellgenerator.allcells import ALL_CELL_PORTS, ALL_CELL_PORTS_STATEFUL
from pynetgenerator.splitsubnetids import ClkInType
from pycommon.defines import NOCELL_CODE
from pycommon.fuzzparams import FuzzerParams
from pycommon.runparams import SimulatorType
from pycommon.defines import INTF_WORD_WIDTH
from pydefs.netwire import NetWire
from pyloop.loopinsert import pick_loop_source_from_netwires


# Later, may introduce loops in the netlist. the netlist.

################
# Simple random sampling functions
################

def gen_total_num_cells(num_cells_min, num_cells_max):
    return random.randint(num_cells_min, num_cells_max)

################
# Connect cell to some wires of other levels
################

# @param all_cells: list of Cell objects. The new cell is the last element.
# @param state_driver_outputs: clock driver circuit cell output. Empty if no stateful cell.
# @return a pair (ret_wires, new_loop_reqs), where loop_reqs is a list of tuples, for a given cell: (port_name, offset_in_port, width)
def __connect_new_cell(curr_subnet_id: int, all_cells: list, input_width_words: int):
    # assert curr_subnet_id == 0 or all_cells_previous_subnet, "Only the first subnet does not have clock drivers"
    # assert all_cells_previous_subnet or all_cells[-1].type not in ALL_CELL_PORTS_STATEFUL, "Cannot connect a stateful cell if there is no clock driver circuit"

    # is_cell_stateful = all_cells[-1].type in ALL_CELL_PORTS_STATEFUL
    # cell_id = len(all_cells) - 1

    ret_wires = []
    loop_reqs = []

    candidate_ret_wires = defaultdict(list)
    port_widths = dict()

    # Connect each input port of the cell
    for port in all_cells[-1].ports:
        if not port.is_input:
            continue
        remaining_width_to_connect = port.width
        port_widths[port.name] = port.width
        if port.is_clkin:
            # Skip the clkin. We will connect it later.
            continue

        # For the moment, only single-bit inputs have the possibility to get the back-wire of loops. This simplifies the implementation a bit, and does not limit that much the overall freedom of the fuzzer in terms of loops.
        if remaining_width_to_connect == 1:
            if random.random() < FuzzerParams.ProbaReqLoop:
                # Create a loop request
                loop_reqs.append((port.name, 0, 1))
                remaining_width_to_connect -= 1

        while remaining_width_to_connect > 0:
            # This block is only executed if the cell is not stateful
            src_subnet_id = curr_subnet_id

            # In the future, should do the connection by first splitting the input port into multiple parts
            # Select an output port randomly. -1 represents the input words.
            candidate_cell_id = random.randint(-1, len(all_cells) - 2)
            if candidate_cell_id == -1:
                candidate_output_port_width = input_width_words * INTF_WORD_WIDTH
                candidate_output_port_name = 'I'
            else:
                candidate_output_port = all_cells[candidate_cell_id].get_random_output_id_and_port()[1]
                candidate_output_port_width = candidate_output_port.width
                candidate_output_port_name = candidate_output_port.name
                del candidate_output_port

            input_port_offset = port.width - remaining_width_to_connect
            candidate_connection_width = min(remaining_width_to_connect, candidate_output_port_width)
            output_port_offset = random.randint(0, candidate_output_port_width - candidate_connection_width)

            # Create a new wire
            new_wire = NetWire(curr_subnet_id, len(all_cells) - 1, port.name, input_port_offset, src_subnet_id, candidate_cell_id, candidate_output_port_name, output_port_offset, candidate_connection_width)
            candidate_ret_wires[port.name].append(new_wire)
            remaining_width_to_connect -= candidate_connection_width

            # if cell_id == 27:
            #     print(f"Created netwire curr_subnet_id: {curr_subnet_id}, cell_id: {cell_id}, port.name: {port.name}, input_port_offset: {input_port_offset}, src_subnet_id: {src_subnet_id}, candidate_cell_id: {candidate_cell_id}, candidate_output_port_name: {candidate_output_port_name}, output_port_offset: {output_port_offset}, candidate_connection_width: {candidate_connection_width}")


    # Check whether the new wire assignment is valid
    if all_cells[-1].type in ("div", "divfloor", "mod", "modfloor"):
        # The idea is to change the first bit of B if it matches the one of A
        if candidate_ret_wires['A'][0].src_cell_id == candidate_ret_wires['B'][0].src_cell_id \
            and candidate_ret_wires['A'][0].src_port_name == candidate_ret_wires['B'][0].src_port_name \
            and candidate_ret_wires['A'][0].src_port_offset == candidate_ret_wires['B'][0].src_port_offset:
            if candidate_ret_wires['B'][0].width > 1:
                candidate_ret_wires['B'][0].dst_port_offset = (candidate_ret_wires['B'][0].dst_port_offset + 1)
                candidate_ret_wires['B'][0].src_port_offset = (candidate_ret_wires['B'][0].src_port_offset + 1)
                candidate_ret_wires['B'][0].width -= 1
            else:
                del candidate_ret_wires['B'][0]
            # For the moment, just connect it to some bit of the input.
            if len(candidate_ret_wires['B']) and candidate_ret_wires['B'][0].src_port_name == 'I' and candidate_ret_wires['B'][0].src_cell_id == -1 and candidate_ret_wires['B'][0].src_port_offset == 0:
                candidate_ret_wires['B'].append(NetWire(curr_subnet_id, len(all_cells)-1, 'B', 0, curr_subnet_id, -1, 'I', 1, 1))
            else:
                candidate_ret_wires['B'].append(NetWire(curr_subnet_id, len(all_cells)-1, 'B', 0, curr_subnet_id, -1, 'I', 0, 1))

    # Connect the last division bit to VCC to ensure that the division is not by zero
    if all_cells[-1].type in ("div", "divfloor", "mod", "modfloor"):
        # Find the last wire
        last_wire_id = None
        for i in range(len(candidate_ret_wires['B']) - 1, -1, -1):
            if candidate_ret_wires['B'][i].dst_port_offset + candidate_ret_wires['B'][i].width == port_widths['B']:
                last_wire_id = i
                break
        assert last_wire_id is not None, "Could not find the last wire"

        if candidate_ret_wires['B'][last_wire_id].width > 1:
            candidate_ret_wires['B'][last_wire_id].width -= 1
        else:
            del candidate_ret_wires['B'][last_wire_id]
        candidate_ret_wires['B'].append(NetWire(curr_subnet_id, len(all_cells)-1, 'B', port_widths['B']-1, curr_subnet_id, -1, 'VCC', 0, 1))

    for port_name in candidate_ret_wires:
        ret_wires += candidate_ret_wires[port_name]

    return ret_wires, loop_reqs


################
# Generate a complete onebyone netlist
################

# @return a pair (subnetlist: dict, random_inputs: list)
def gen_random_onebyone_netlist(fuzzerstate, subnet_id: int, num_cells: int):
    all_cells = []
    all_netwires = []
    loop_reqs_per_cell = []

    for cell_id in range(num_cells):
        all_cells.append(gen_random_cell(fuzzerstate, True))
        new_netwires, new_loop_reqs = __connect_new_cell(subnet_id, all_cells, fuzzerstate.num_input_words)

        all_netwires += new_netwires
        loop_reqs_per_cell.append(new_loop_reqs)

    # Connect the module output to the output of the last N cells
    for cell_id in range(1, min(fuzzerstate.num_output_words, len(all_cells) + 1)):
        random_output_port_id, random_output_port = all_cells[-cell_id].get_random_output_id_and_port()
        conn_width = min(INTF_WORD_WIDTH, random_output_port.width)
        new_wire = NetWire(subnet_id, -1, 'O', (cell_id - 1) * INTF_WORD_WIDTH, subnet_id, len(all_cells) - cell_id, random_output_port.name, random.randint(0, random_output_port.width - conn_width), conn_width)
        all_netwires.append(new_wire)

    # Create the requested loops
    for cell_id in range(len(all_cells)):
        for loop_req in loop_reqs_per_cell[cell_id]:
            loop_source_cell_id = pick_loop_source_from_netwires(subnet_id, cell_id, {subnet_id: list(map(lambda c: c.type, all_cells))}, all_netwires)

            if loop_source_cell_id is None:
                # Then take a random previous cell and proceed with that
                loop_source_cell_id = random.randrange(-1, cell_id)

            # Add a connection from the output of the loop source to the input of the loop requester
            loop_destination_cell_id = cell_id
            loop_destination_port_name = loop_req[0]
            loop_destination_port_offset = loop_req[1]
            loop_destination_connection_width = loop_req[2]
            assert loop_destination_connection_width == 1, "For the moment, only single-bit inputs can be loop requesters"

            if loop_source_cell_id == -1:
                # Then the source is the input
                loop_source_port_name = 'I'
                loop_source_port_offset = loop_destination_port_offset
            else:

                # loop_source_port_width = 1
                source_cell = all_cells[loop_source_cell_id]
                loop_source_port = source_cell.get_random_output_id_and_port()[1]
                loop_source_port_width = loop_source_port.width
                loop_source_port_offset = random.randint(0, loop_source_port_width - loop_destination_connection_width)
                loop_source_port_name = loop_source_port.name

            new_netwire = NetWire(subnet_id, loop_destination_cell_id, loop_destination_port_name, loop_destination_port_offset, subnet_id, loop_source_cell_id, loop_source_port_name, loop_source_port_offset, loop_destination_connection_width)
            all_netwires.append(new_netwire)

    return all_cells, all_netwires






def gen_netlist_from_cells_and_netwires(fuzzerstate, all_cells_list, all_netwires_lists, splitted_requesters_per_clkin_type):

    # Generate the netlist dict
    in_width = fuzzerstate.num_input_words * INTF_WORD_WIDTH
    out_width = fuzzerstate.num_output_words * INTF_WORD_WIDTH
    cell_types_per_subnet_id = []

    for subnet_id in range(len(all_cells_list)):
        cell_types_per_subnet_id.append(list(map(lambda c: c.type, all_cells_list[subnet_id])))

    cell_params_per_subnet_id = []
    for subnet_id in range(len(all_cells_list)):
        cell_params_per_subnet_id.append(list(map(lambda c: c.params, all_cells_list[subnet_id])))

    cell_dimensions_per_subnet_id = []
    for subnet_id in range(len(all_cells_list)):
        cell_dimensions_per_subnet_id.append(list(map(lambda c: list(map(lambda p: p.width, c.ports)), all_cells_list[subnet_id])))

    connections = []

    for netwire in reduce(concat, all_netwires_lists):
        connections.append((netwire.dst_subnet_id, netwire.dst_cell_id, netwire.dst_port_name, netwire.dst_port_offset, netwire.src_subnet_id, netwire.src_cell_id, netwire.src_port_name, netwire.src_port_offset, netwire.width))

    all_subnet_ids_dbg = set()

    # Add the connections to the external clocks
    for clkin_type in splitted_requesters_per_clkin_type:
        for clkin_subnet_id, clkin_subnet in enumerate(splitted_requesters_per_clkin_type[clkin_type]):
            for clkin_cell in clkin_subnet:
                curr_subnet_id  = clkin_cell[0]
                curr_cell_id    = clkin_cell[1]
                curr_port_name  = clkin_cell[2]
                curr_port_width = clkin_cell[3]

                curr_offset = 0
                clkinport = f"{ClkInType.to_char(clkin_type)}{clkin_subnet_id}"
                connections.append((curr_subnet_id, curr_cell_id, curr_port_name, curr_offset, -1, -1, clkinport, 0, curr_port_width))
                # all_subnet_ids_dbg.add(curr_subnet_id)

    # Generate the tuples for the clkin-type inputs
    input_port_pairs = []
    for clkin_type in splitted_requesters_per_clkin_type:
        for clkin_subnet_id, clkin_subnet in enumerate(splitted_requesters_per_clkin_type[clkin_type]):
            input_port_pairs.append((f"{ClkInType.to_char(clkin_type)}{clkin_subnet_id}", max(map(lambda c: c[3], clkin_subnet))))
    clkin_ports_names   = list(map(lambda p: p[0], input_port_pairs))
    clkin_ports_widths  = list(map(lambda p: p[1], input_port_pairs))

    return {
        'in_width': in_width,
        'out_width': out_width,
        'clkin_ports_names': clkin_ports_names,
        'clkin_ports_widths': clkin_ports_widths,
        # 'num_subnets': num_subnets, Actually this is already available through len(cell_types) for example
        'cell_types': cell_types_per_subnet_id,
        'cell_params': cell_params_per_subnet_id,
        'cell_dimensions': cell_dimensions_per_subnet_id,
        'connections': connections}


def gen_netlist_from_cells_and_netwires_multisubnet(fuzzerstate, all_cells_list, all_netwires_lists, splitted_requesters_per_clkin_type):

    # Generate the netlist dict
    in_width = fuzzerstate.num_input_words * INTF_WORD_WIDTH
    out_width = fuzzerstate.num_output_words * INTF_WORD_WIDTH
    cell_types_per_subnet_id = []

    for subnet_id in range(len(all_cells_list)):
        cell_types_per_subnet_id.append(list(map(lambda c: c.type, all_cells_list[subnet_id])))

    cell_params_per_subnet_id = []
    for subnet_id in range(len(all_cells_list)):
        cell_params_per_subnet_id.append(list(map(lambda c: c.params, all_cells_list[subnet_id])))

    cell_dimensions_per_subnet_id = []
    for subnet_id in range(len(all_cells_list)):
        cell_dimensions_per_subnet_id.append(list(map(lambda c: list(map(lambda p: p.width, c.ports)), all_cells_list[subnet_id])))

    connections = []

    for netwire in reduce(concat, all_netwires_lists):
        connections.append((netwire.dst_subnet_id, netwire.dst_cell_id, netwire.dst_port_name, netwire.dst_port_offset, netwire.src_subnet_id, netwire.src_cell_id, netwire.src_port_name, netwire.src_port_offset, netwire.width))

    all_subnet_ids_dbg = set()

    # Add the connections to the external clocks
    for clkin_type in splitted_requesters_per_clkin_type:
        for clkin_subnet_id, clkin_subnet in enumerate(splitted_requesters_per_clkin_type[clkin_type]):
            for clkin_cell in clkin_subnet:
                curr_subnet_id  = clkin_cell[0]
                curr_cell_id    = clkin_cell[1]
                curr_port_name  = clkin_cell[2]
                curr_port_width = clkin_cell[3]

                curr_offset = 0
                clkinport = f"{ClkInType.to_char(clkin_type)}{clkin_subnet_id}"
                connections.append((curr_subnet_id, curr_cell_id, curr_port_name, curr_offset, -1, -1, clkinport, 0, curr_port_width))
                # all_subnet_ids_dbg.add(curr_subnet_id)

    # Generate the tuples for the clkin-type inputs
    input_port_pairs = []
    for clkin_type in splitted_requesters_per_clkin_type:
        for clkin_subnet_id, clkin_subnet in enumerate(splitted_requesters_per_clkin_type[clkin_type]):
            input_port_pairs.append((f"{ClkInType.to_char(clkin_type)}{clkin_subnet_id}", max(map(lambda c: c[3], clkin_subnet))))
    clkin_ports_names   = list(map(lambda p: p[0], input_port_pairs))
    clkin_ports_widths  = list(map(lambda p: p[1], input_port_pairs))

    return {
        'in_width': in_width,
        'out_width': out_width,
        'clkin_ports_names': clkin_ports_names,
        'clkin_ports_widths': clkin_ports_widths,
        # 'num_subnets': num_subnets, Actually this is already available through len(cell_types) for example
        'cell_types': cell_types_per_subnet_id,
        'cell_params': cell_params_per_subnet_id,
        'cell_dimensions': cell_dimensions_per_subnet_id,
        'connections': connections}





# Return a dict[signal_type] = list of tuples (subnet_id, cell_id, port_name, port_width)
def find_requesters_per_clkin_type(all_cells_lists, subnet_ids):
    assert len(all_cells_lists) == len(subnet_ids), f"Length mismatch: all_cells_lists: {len(all_cells_lists)}, subnet_ids: {len(subnet_ids)}"
    requesters_per_clkin_type = defaultdict(list)
    for all_cells_list_id, all_cells in enumerate(all_cells_lists):
        for cell_id, cell in enumerate(all_cells):
            if cell.type in ALL_CELL_PORTS_STATEFUL:
                for port in cell.ports:
                    if port.is_clkin:
                        requesters_per_clkin_type[ClkInType.port_name_to_clkin_type(port.name)].append((subnet_ids[all_cells_list_id], cell_id, port.name, port.width))
    return requesters_per_clkin_type
