# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import random

class Cell:
    def __init__(self, cell_type, ports, params):
        self.type = cell_type
        self.ports = ports
        self.params = params

    # @return (port_id, port)
    def get_random_output_id_and_port(self):
        candidate_output_ids_and_ports = []
        for port_id, port in enumerate(self.ports):
            if not port.is_input:
                candidate_output_ids_and_ports.append((port_id, port))
        assert len(candidate_output_ids_and_ports) > 0, "No output port found for cell: {}".format(self.type)
        if len(candidate_output_ids_and_ports) == 1:
            return candidate_output_ids_and_ports[0]
        return random.choice(candidate_output_ids_and_ports)
