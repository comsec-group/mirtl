# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

class NetWire:
    def __init__(self, dst_subnet_id, dst_cell_id, dst_port_name, dst_port_offset, src_subnet_id, src_cell_id, src_port_name, src_port_offset, width):
        self.dst_subnet_id = dst_subnet_id
        self.dst_cell_id = dst_cell_id
        self.dst_port_name = dst_port_name
        self.dst_port_offset = dst_port_offset
        self.src_subnet_id = src_subnet_id
        self.src_cell_id = src_cell_id
        self.src_port_name = src_port_name
        self.src_port_offset = src_port_offset
        self.width = width
        # Bit ranges are tuples (start, width).
        self.taken_bit_ranges = []

    def take_bit_range(self, start, width):
        assert start >= 0, "Invalid start: {}".format(start)
        assert width >= 0, "Invalid width: {}".format(width)
        assert start + width <= self.width, "Invalid start, width: {}, {}".format(start, width)

        # Check whether we should merge the new bit range into an existing one
        # Should be optimized in the future.
        self.taken_bit_ranges = sorted(self.taken_bit_ranges + [(start, width)])

        # Merge overlapping ranges
        for i in range(len(self.taken_bit_ranges) - 1):
            if self.taken_bit_ranges[i][0] + self.taken_bit_ranges[i][1] >= self.taken_bit_ranges[i+1][0]:
                self.taken_bit_ranges[i] = (self.taken_bit_ranges[i][0], max(self.taken_bit_ranges[i][1], self.taken_bit_ranges[i+1][0] + self.taken_bit_ranges[i+1][1] - self.taken_bit_ranges[i][0]))
                del self.taken_bit_ranges[i+1]
                # Do not break: there can be two overlaps.
                i -= 1

    def equals_except_dst_port(self, other):
        if isinstance(other, NetWire):
            return self.dst_cell_subnet_id == self.dst_cell_subnet_id and self.dst_cell_id == other.dst_cell_id and self.dst_port_offset == other.dst_port_offset and self.src_cell_id == other.src_cell_id and self.src_port_name == other.src_port_name and self.src_port_offset == other.src_port_offset and self.width == other.width

    def __str__(self):
        return "NetWire(dst_subnet_id={}, dst_cell_id={}, dst_port_name={}, dst_port_offset={}, src_subnet_id={}, src_cell_id={}, src_port_name={}, src_port_offset={}, width={}, taken_bit_ranges={})".format(self.dst_subnet_id, self.dst_cell_id, self.dst_port_name, self.dst_port_offset, self.src_subnet_id, self.src_cell_id, self.src_port_name, self.src_port_offset, self.width, self.taken_bit_ranges)