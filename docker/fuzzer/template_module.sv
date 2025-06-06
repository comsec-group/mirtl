// Copyright 2024 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

module top(
    input logic [31:0] clkin_data,
    input logic [31:0] in_data,
    output logic [31:0] out_data
);
TEMPLATE_PORTS

    // Dummy operation to prevent the module from being ignored by Yosys
    assign out_data = in_data;

endmodule
