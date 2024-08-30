# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from pyloop.loopinsert import pick_loop_source
from pycellgenerator.allcells import ALL_CELL_PORTS, ALL_CELL_PORTS_STATEFUL
import random

# In a combinational circuit, we should never be able to find a non-combinational loop
def unit_test_combinational():
    num_test_iterations = 10

    for iteration_id in range(num_test_iterations):
        curr_subnet_id = random.randrange(100)

        circuit_size = random.randrange(1, 100)
        cell_types = []
        for cell_id in range(circuit_size):
            # Only pick combinational cells
            cell_types.append(random.choice(list(ALL_CELL_PORTS.keys())))

        connections = []
        # Create a combinational circuit with few connections backward for each cell
        for cell_id in range(circuit_size):
            # Create a random number of connections
            num_connections = random.randrange(1, 3)
            for connection_id in range(1, num_connections):
                # Create a connection to a random previous cell
                orig_cell_id = random.randrange(connection_id)
                new_connection = (curr_subnet_id, cell_id, "doesntmatter", 0, curr_subnet_id, orig_cell_id, "alsodoesntmatter", 0, 1)
                connections.append(new_connection)

        # Now we have a combinational circuit with no possible stateful loops
        # Let's try multiple times to insert a loop
        for _ in range(10):
            start_cell_id = random.randrange(circuit_size)
            loop_source = pick_loop_source(curr_subnet_id, start_cell_id, {curr_subnet_id: cell_types}, connections)
            assert loop_source is None, f"Found a loop source {loop_source} in a combinational circuit"



def __unit_test_stateful_worker():
    curr_subnet_id = random.randrange(100)

    circuit_size = random.randrange(1, 1000)
    proba_pick_stateful = 0.1 + random.random()/4
    cell_types = []
    for cell_id in range(circuit_size):
        # Only pick combinational cells
        if random.random() < proba_pick_stateful:
            cell_types.append(random.choice(list(ALL_CELL_PORTS_STATEFUL.keys())))
        else:
            cell_types.append(random.choice(list(ALL_CELL_PORTS.keys())))

    connections = []
    # Create a combinational circuit with few connections backward for each cell
    for cell_id in range(circuit_size):
        # Create a random number of connections
        num_connections = random.randrange(1, 3)
        for connection_id in range(1, num_connections):
            # Create a connection to a random previous cell
            orig_cell_id = random.randrange(connection_id)
            new_connection = (curr_subnet_id, cell_id, "doesntmatter", 0, curr_subnet_id, orig_cell_id, "alsodoesntmatter", 0, 1)
            connections.append(new_connection)

    # Now we have a combinational circuit with no possible stateful loops
    # Let's try multiple times to insert a loop
    for _ in range(100):
        start_cell_id = random.randrange(circuit_size)
        loop_source = pick_loop_source(curr_subnet_id, start_cell_id, {curr_subnet_id: cell_types}, connections)

        if loop_source is not None:
            print(f"Found a loop source {loop_source} in a stateful circuit")


# Insert some stateful elements in the circuit (like a classical circuit), insert loops and check whether the loops are found
def unit_test_stateful():
    num_test_iterations = 100

    for iteration_id in range(num_test_iterations):
        __unit_test_stateful_worker()


def launch_tests():
    unit_test_combinational()
    unit_test_stateful()

