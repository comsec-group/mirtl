# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from collections import defaultdict
from pycellgenerator.allcells import ALL_CELL_PORTS_STATEFUL
import random

# Inserts non-combinational loops in destinations (cell inputs) that were already marked in advance
# @return create_successors_dict: dict[subnet_id][orig_cell_id] = {dest_cell_ids}
def create_successors_dict(connections):
    successors_dict = defaultdict(lambda: defaultdict(set))

    for connection in connections:
        connection_destination_subnet_id = connection[0]
        connection_destination_cell_id = connection[1]
        connection_destination_port_name = connection[2]
        connection_destination_port_offset = connection[3]
        connection_origin_subnet_id = connection[4]
        connection_origin_cell_id = connection[5]
        connection_origin_port_name = connection[6]
        connection_origin_port_offset = connection[7]
        connection_origin_port_width = connection[8]

        # Do not consider asynchronous connections, i.e., connections between different subnets
        if connection_origin_subnet_id != connection_destination_subnet_id:
            continue
        # Ignore input or output ports
        if connection_destination_cell_id == -1 or connection_origin_cell_id == -1:
            continue
        successors_dict[connection_origin_subnet_id][connection_origin_cell_id].add(connection_destination_cell_id)

    return successors_dict

# @param cell_types is useful to find out whether this is a stateful cell
def pick_loop_source(start_cell_subnet_id, start_cell_id, cell_types_per_subnet, connections):
    is_start_cell_stateful = cell_types_per_subnet[start_cell_subnet_id][start_cell_id] in ALL_CELL_PORTS_STATEFUL

    # First, build a dict[subnet_id][orig_cell_id] = {dest_cell_ids}
    successor_cells_dict = create_successors_dict(connections)

    # These are pairs (subnet_id, cell_id)
    green_ids = set()
    red_ids = set()

    if is_start_cell_stateful:
        new_green_ids = {(start_cell_subnet_id, start_cell_id)}
        new_red_ids = set()
    else:
        new_green_ids = set()
        new_red_ids = {(start_cell_subnet_id, start_cell_id)}

    # Now treat the reds
    while new_red_ids:
        curr_subnet_id, curr_new_red_id = new_red_ids.pop()
        assert curr_subnet_id == start_cell_subnet_id, f"Unexpected change of subnet. Expected {start_cell_subnet_id}, got {curr_subnet_id}"

        # Mark all the successor cells accordingly
        for successor_cell_id in successor_cells_dict[curr_subnet_id][curr_new_red_id]:
            assert (curr_subnet_id, successor_cell_id) not in green_ids or cell_types_per_subnet[curr_subnet_id][successor_cell_id] in ALL_CELL_PORTS_STATEFUL, f"{(curr_subnet_id, successor_cell_id)} is a green but now said to be a successor of a red. Its type is {cell_types_per_subnet[curr_subnet_id][successor_cell_id]}"
            assert (curr_subnet_id, successor_cell_id) not in new_green_ids or cell_types_per_subnet[curr_subnet_id][successor_cell_id] in ALL_CELL_PORTS_STATEFUL, f"{(curr_subnet_id, successor_cell_id)} is a new green but now said to be a successor of a red"

            # This successor has already been seen
            if (curr_subnet_id, successor_cell_id) in red_ids or \
                (curr_subnet_id, successor_cell_id) in new_red_ids:
                continue

            # If the successor is stateful, then it must be green
            if cell_types_per_subnet[curr_subnet_id][successor_cell_id] in ALL_CELL_PORTS_STATEFUL:
                new_green_ids.add((curr_subnet_id, successor_cell_id))
            else:
                new_red_ids.add((curr_subnet_id, successor_cell_id))
    
        red_ids.add((curr_subnet_id, curr_new_red_id))

    # Now treat the greens
    while new_green_ids:
        curr_subnet_id, curr_new_red_id = new_green_ids.pop()
        for successor_cell_id in successor_cells_dict[curr_subnet_id][curr_new_red_id]:

            # This successor has already been seen
            if (curr_subnet_id, successor_cell_id) in red_ids or \
                (curr_subnet_id, successor_cell_id) in green_ids or \
                (curr_subnet_id, successor_cell_id) in new_green_ids or \
                (curr_subnet_id, successor_cell_id) in new_red_ids:
                continue

            # The non-red successor of a green is always green
            if cell_types_per_subnet[curr_subnet_id][successor_cell_id] in ALL_CELL_PORTS_STATEFUL:
                new_green_ids.add((curr_subnet_id, successor_cell_id))

        green_ids.add((curr_subnet_id, curr_new_red_id))

    assert not new_red_ids
    assert not new_green_ids

    # Take only the greens that have a cell ID strictly higher than the current
    candidate_greens = []
    for green_subnet_id, green_cell_id in green_ids:
        assert green_subnet_id == start_cell_subnet_id
        if green_cell_id > start_cell_id:
            candidate_greens.append(green_cell_id)
        # else:
        #     print(f"Green is smaller: {green_cell_id} <= {start_cell_id}")

    # Select a random candidate if there is one.
    if candidate_greens:
        return random.choice(candidate_greens)

    else:
        return None



def pick_loop_source_from_netwires(start_cell_subnet_id, start_cell_id, cell_types_per_subnet, connections_netwires):
    connections = []
    for netwire in connections_netwires:
        connections.append((netwire.dst_subnet_id, netwire.dst_cell_id, netwire.dst_port_name, netwire.dst_port_offset, netwire.src_subnet_id, netwire.src_cell_id, netwire.src_port_name, netwire.src_port_offset, netwire.width))

    return pick_loop_source(start_cell_subnet_id, start_cell_id, cell_types_per_subnet, connections)
