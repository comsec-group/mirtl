# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import random

def get_port_size(cell_port_tuple, cell_dimension):
    port_size_decl = cell_port_tuple[2]
    if port_size_decl is None:
        port_size = cell_dimension
    elif isinstance(port_size_decl, int):
        port_size = port_size_decl
    else:
        raise ValueError("Invalid port size declaration: {}".format(port_size_decl))
    return port_size

def randomize_authorized_combinational_cell_types(forbidden_cell_type_ids: list):
    num_authorized_cell_types = random.randint(1, len(ALL_CELL_PORTS))
    weights = [1] * len(ALL_CELL_PORTS)
    for forbidden_cell_type_id in forbidden_cell_type_ids:
        weights[forbidden_cell_type_id] = 0
    return random.choices(list(ALL_CELL_PORTS.keys()), weights, k=num_authorized_cell_types)

def randomize_authorized_stateful_cell_types(authorize_pick_stateful_gates: bool, forbidden_cell_type_ids: list):
    all_candidates = list(ALL_CELL_PORTS_STATEFUL.keys())
    # Remove the elements of forbidden_cell_type_ids
    for forbidden_cell_type_id in reversed(sorted(forbidden_cell_type_ids)):
        del all_candidates[forbidden_cell_type_id]
    if not authorize_pick_stateful_gates:
        all_candidates = list(filter(lambda x: x[0] != '_', all_candidates))
    num_authorized_cell_types = random.randint(1, len(all_candidates))
    weights = [1] * len(all_candidates)
    return random.choices(all_candidates, weights, k=num_authorized_cell_types)

# Values are tuples of the form (port_name, is_input, computation_port_width (None if same width as first port or if is input port, int if constant, else a function of the first input)). If clock, add an additional True
ALL_CELL_PORTS = {
    # Add the parameters for such cells
    # '_ALDFFE_NNN_': (('D', True, None), ('C', True, 1, True), ('L', True, 1), ('AD', True, None), ('E', True, 1), ('Q', False, None)),
    # '_ALDFFE_NNP_':
    # '_ALDFFE_NPN_':
    # '_ALDFFE_NPP_':
    # '_ALDFFE_PNN_':
    # '_ALDFFE_PNP_':
    # '_ALDFFE_PPN_':
    # '_ALDFFE_PPP_':
    # '_ALDFF_NN_':
    # '_ALDFF_NP_':
    # '_ALDFF_PN_':
    # '_ALDFF_PP_':
    '_ANDNOT_': (('A', True, 1), ('B', True, 1), ('Y', False, 1)),
    '_AND_': (('A', True, 1), ('B', True, 1), ('Y', False, 1)),
    '_AOI3_': (('A', True, 1), ('B', True, 1), ('C', True, 1), ('Y', False, 1)),
    '_AOI4_': (('A', True, 1), ('B', True, 1), ('C', True, 1), ('D', True, 1), ('Y', False, 1)),
    # '_BUF_': (('A', True, 1), ('Y', False, 1)),
    # Must add the parameters for such cells.
    # '_DFFE_NN0N_': (('C', True, 1, True), ('D', True, None), ('R', True, 1), ('E', True, 1), ('Q', False, None)),
    # '_DFFE_NN0P_': (('D', True, None), ('C', True, 1, True), ('R', True, 1), ('E', True, 1), ('Q', False, None)),
    # '_DFFE_NN1N_': (('D', True, None), ('C', True, 1, True), ('R', True, 1), ('E', True, 1), ('Q', False, None)),
    # '_DFFE_NN1P_': (('D', True, None), ('C', True, 1, True), ('R', True, 1), ('E', True, 1), ('Q', False, None)),
    # '_DFFE_NN_':
    # '_DFFE_NP0N_':
    # '_DFFE_NP0P_':
    # '_DFFE_NP1N_':
    # '_DFFE_NP1P_':
    # '_DFFE_NP_':
    # '_DFFE_PN0N_':
    # '_DFFE_PN0P_':
    # '_DFFE_PN1N_':
    # '_DFFE_PN1P_':
    # '_DFFE_PN_':
    # '_DFFE_PP0N_':
    # '_DFFE_PP0P_':
    # '_DFFE_PP1N_':
    # '_DFFE_PP1P_':
    # '_DFFE_PP_':
    # '_DFFSRE_NNNN_':
    # '_DFFSRE_NNNP_':
    # '_DFFSRE_NNPN_':
    # '_DFFSRE_NNPP_':
    # '_DFFSRE_NPNN_':
    # '_DFFSRE_NPNP_':
    # '_DFFSRE_NPPN_':
    # '_DFFSRE_NPPP_':
    # '_DFFSRE_PNNN_':
    # '_DFFSRE_PNNP_':
    # '_DFFSRE_PNPN_':
    # '_DFFSRE_PNPP_':
    # '_DFFSRE_PPNN_':
    # '_DFFSRE_PPNP_':
    # '_DFFSRE_PPPN_':
    # '_DFFSRE_PPPP_':
    # '_DFFSR_NNN_':
    # '_DFFSR_NNP_':
    # '_DFFSR_NPN_':
    # '_DFFSR_NPP_':
    # '_DFFSR_PNN_':
    # '_DFFSR_PNP_':
    # '_DFFSR_PPN_':
    # '_DFFSR_PPP_':
    # '_DFF_NN0_':
    # '_DFF_NN1_':
    # '_DFF_NP0_':
    # '_DFF_NP1_':
    # '_DFF_N_':
    # '_DFF_PN0_':
    # '_DFF_PN1_':
    # '_DFF_PP0_':
    # '_DFF_PP1_':
    # '_DFF_P_':
    # '_DLATCHSR_NNN_':
    # '_DLATCHSR_NNP_':
    # '_DLATCHSR_NPN_':
    # '_DLATCHSR_NPP_':
    # '_DLATCHSR_PNN_':
    # '_DLATCHSR_PNP_':
    # '_DLATCHSR_PPN_':
    # '_DLATCHSR_PPP_':
    # '_DLATCH_NN0_':
    # '_DLATCH_NN1_':
    # '_DLATCH_NP0_':
    # '_DLATCH_NP1_':
    # '_DLATCH_N_':
    # '_DLATCH_PN0_':
    # '_DLATCH_PN1_':
    # '_DLATCH_PP0_':
    # '_DLATCH_PP1_':
    # '_DLATCH_P_':
    # '_FF_': (('A', True, None), ('Y', False, None)),
    # '_MUX16_':
    # '_MUX4_':
    # '_MUX8_':
    '_MUX_': (('A', True, 1), ('B', True, 1), ('S', True, 1), ('Y', False, 1)),
    '_NAND_': (('A', True, 1), ('B', True, 1), ('Y', False, 1)),
    '_NMUX_': (('A', True, 1), ('B', True, 1), ('S', True, 1), ('Y', False, 1)),
    '_NOR_': (('A', True, 1), ('B', True, 1), ('Y', False, 1)),
    '_NOT_': (('A', True, 1), ('Y', False, 1)),
    '_OAI3_': (('A', True, 1), ('B', True, 1), ('C', True, 1), ('Y', False, 1)),
    '_OAI4_': (('A', True, 1), ('B', True, 1), ('C', True, 1), ('D', True, 1), ('Y', False, 1)),
    '_ORNOT_': (('A', True, 1), ('B', True, 1), ('Y', False, 1)),
    '_OR_': (('A', True, 1), ('B', True, 1), ('Y', False, 1)),
    # '_SDFFCE_NN0N_':
    # '_SDFFCE_NN0P_':
    # '_SDFFCE_NN1N_':
    # '_SDFFCE_NN1P_':
    # '_SDFFCE_NP0N_':
    # '_SDFFCE_NP0P_':
    # '_SDFFCE_NP1N_':
    # '_SDFFCE_NP1P_':
    # '_SDFFCE_PN0N_':
    # '_SDFFCE_PN0P_':
    # '_SDFFCE_PN1N_':
    # '_SDFFCE_PN1P_':
    # '_SDFFCE_PP0N_':
    # '_SDFFCE_PP0P_':
    # '_SDFFCE_PP1N_':
    # '_SDFFCE_PP1P_':
    # '_SDFFE_NN0N_':
    # '_SDFFE_NN0P_':
    # '_SDFFE_NN1N_':
    # '_SDFFE_NN1P_':
    # '_SDFFE_NP0N_':
    # '_SDFFE_NP0P_':
    # '_SDFFE_NP1N_':
    # '_SDFFE_NP1P_':
    # '_SDFFE_PN0N_':
    # '_SDFFE_PN0P_':
    # '_SDFFE_PN1N_':
    # '_SDFFE_PN1P_':
    # '_SDFFE_PP0N_':
    # '_SDFFE_PP0P_':
    # '_SDFFE_PP1N_':
    # '_SDFFE_PP1P_':
    # '_SDFF_NN0_':
    # '_SDFF_NN1_':
    # '_SDFF_NP0_':
    # '_SDFF_NP1_':
    # '_SDFF_PN0_':
    # '_SDFF_PN1_':
    # '_SDFF_PP0_':
    # '_SDFF_PP1_':
    # '_SR_NN_':
    # '_SR_NP_':
    # '_SR_PN_':
    # '_SR_PP_':
    # '_TBUF_':
    '_XNOR_': (('A', True, 1), ('B', True, 1), ('Y', False, 1)),
    '_XOR_': (('A', True, 1), ('B', True, 1), ('Y', False, 1)),
    'add': (('A', True, None), ('B', True, None), ('Y', False, None)),
    # 'adff': (('CLK', True, 1, True), ('ARST', True, 1), ('D', True, None), ('Q', False, None)),
    # 'adffe': (('CLK', True, 1, True),  True, None), ('Q', ('ARST', True, 1), ('EN', True, 1), ('D, False, None)),
    # 'adlatch':
    # 'aldff':
    # 'aldffe':
    # 'allconst':
    # 'allseq':
    # 'alu':
    'and': (('A', True, None), ('B', True, None), ('Y', False, None)),
    # 'anyconst':
    # 'anyinit':
    # 'anyseq':
    # 'assert':
    # 'assume':
    # 'bmux':
    # 'bweqx':
    # 'bwmux':
    # 'concat':
    # 'cover':
    # 'demux': (('A', True, None), ('S', True, 4), ('Y', False, None)),
    # 'dff':
    # 'dffe':
    # 'dffsr':
    # 'dffsre':
    'div': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'divfloor': (('A', True, None), ('B', True, None), ('Y', False, None)),
    # 'dlatch':
    # 'dlatchsr':
    'eq': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    # 'equiv': (('A', True, 1), ('B', True, 1), ('Y', False, 1)),
    'eqx': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    # 'fa':
    # 'fair':
    # 'ff':
    # 'fsm':
    'ge': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    'gt': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    # 'initstate':
    # 'lcu':
    'le': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    # 'live':
    'logic_and': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    'logic_not': (('A', True, None), ('Y', False, 1)),
    'logic_or': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    'lt': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    # 'lut':
    # 'macc': (('A', True, None), ('B', True, None), ('Y', False, None)), # This cell causes wire dimension mismatches for the output
    # 'mem':
    # 'mem_v2':
    # 'meminit':
    # 'meminit_v2':
    # 'memrd':
    # 'memrd_v2':
    # 'memwr':
    # 'memwr_v2':
    'mod': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'modfloor': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'mul': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'mux': (('A', True, None), ('B', True, None), ('S', True, 1), ('Y', False, None)),
    'ne': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    'neg': (('A', True, None), ('Y', False, None)),
    'nex': (('A', True, None), ('B', True, None), ('Y', False, 1)),
    'not': (('A', True, None), ('Y', False, None)),
    'or': (('A', True, None), ('B', True, None), ('Y', False, None)),
    # 'pmux':
    # pos is not a very useful one ^^'
    # 'pos': (('A', True, None), ('Y', False, None)),
    # The pow cell is problematic for CXXRTL
    # 'pow': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'reduce_and': (('A', True, None), ('Y', False, 1)),
    'reduce_bool': (('A', True, None), ('Y', False, 1)),
    'reduce_or': (('A', True, None), ('Y', False, 1)),
    'reduce_xnor': (('A', True, None), ('Y', False, 1)),
    'reduce_xor': (('A', True, None), ('Y', False, 1)),
    # 'sdff':
    # 'sdffce':
    # 'sdffe':
    'shift': (('A', True, None), ('B', True, None), ('Y', False, None)),
    # 'shiftx': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'shl': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'shr': (('A', True, None), ('B', True, None), ('Y', False, None)),
    # 'slice': (('A', True, None), ('Y', False, "+1")),
    # 'sop':
    # 'specify2':
    # 'specify3':
    # 'specrule':
    # 'sr':
    'sshl': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'sshr': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'sub': (('A', True, None), ('B', True, None), ('Y', False, None)),
    # 'tribuf':
    'xnor': (('A', True, None), ('B', True, None), ('Y', False, None)),
    'xor': (('A', True, None), ('B', True, None), ('Y', False, None)),
}

CELL_PARAMS = {
    'slice': (
        1, # offset
    ),

    # Flip-flops
    'adff': (
        None, # arst_value, will be limited to 32 bits for now in reality
        1, # clk_polarity
        1, # arst_polarity
    ),
    'adffe': (
        None, # arst_value, will be limited to 32 bits for now in reality
        1, # clk_polarity
        1, # en_polarity
        1, # arst_polarity
    ),
    'aldff': (
        1, # clk_polarity
        1, # aload_polarity
    ),
    'aldffe': (
        1, # clk_polarity
        1, # en_polarity
        1, # aload_polarity
    ),
    'dff': (
        1, # clk_polarity
    ),
    'dffe': (
        1, # clk_polarity
        1, # en_polarity
    ),
    'dffsr': (
        1, # clk_polarity
        1, # set_polarity
        1, # clr_polarity
    ),
    'dffsre': (
        1, # clk_polarity
        1, # en_polarity
        1, # set_polarity
        1, # clr_polarity
    ),
    'ff': tuple(),
    'sdff': (
        None, # srst_value, will be limited to 32 bits for now in reality
        1, # clk_polarity
        1, # srst_polarity
    ),
    'sdffce': (
        None, # srst_value, will be limited to 32 bits for now in reality
        1, # clk_polarity
        1, # en_polarity
        1, # srst_polarity
    ),
    'sdffe': (
        None, # srst_value, will be limited to 32 bits for now in reality
        1, # clk_polarity
        1, # en_polarity
        1, # srst_polarity
    ),

    # Latches
    'adlatch': (
        None, # arst_value, will be limited to 32 bits for now in reality
        1, # en_polarity
        1, # arst_polarity
    ),
    'dlatch': (
        1, # en_polarity
    ),
    'dlatchsr': (
        1, # en_polarity
        1, # set_polarity
        1, # clr_polarity
    ),

    # The gates like '_DLATCHSR_NNN_' take no parameter.
}

ALL_CELL_PORTS_STATEFUL = {
    # Flip-flops
    # '_ALDFFE_NNN_':  (),
    # '_ALDFFE_NNP_':  (),
    # '_ALDFFE_NPN_':  (),
    # '_ALDFFE_NPP_':  (),
    # '_ALDFFE_PNN_':  (),
    # '_ALDFFE_PNP_':  (),
    # '_ALDFFE_PPN_':  (),
    # '_ALDFFE_PPP_':  (),
    # '_ALDFF_NN_':    (),
    # '_ALDFF_NP_':    (),
    # '_ALDFF_PN_':    (),
    # '_ALDFF_PP_':    (),
    # '_DFFE_NN0N_':   (),
    # '_DFFE_NN0P_':   (),
    # '_DFFE_NN1N_':   (),
    # '_DFFE_NN1P_':   (),
    # '_DFFE_NN_':     (),
    # '_DFFE_NP0N_':   (),
    # '_DFFE_NP0P_':   (),
    # '_DFFE_NP1N_':   (),
    # '_DFFE_NP1P_':   (),
    # '_DFFE_NP_':     (),
    # '_DFFE_PN0N_':   (),
    # '_DFFE_PN0P_':   (),
    # '_DFFE_PN1N_':   (),
    # '_DFFE_PN1P_':   (),
    # '_DFFE_PN_':     (),
    # '_DFFE_PP0N_':   (),
    # '_DFFE_PP0P_':   (),
    # '_DFFE_PP1N_':   (),
    # '_DFFE_PP1P_':   (),
    # '_DFFE_PP_':     (),
    # '_DFFSRE_NNNN_': (),
    # '_DFFSRE_NNNP_': (),
    # '_DFFSRE_NNPN_': (),
    # '_DFFSRE_NNPP_': (),
    # '_DFFSRE_NPNN_': (),
    # '_DFFSRE_NPNP_': (),
    # '_DFFSRE_NPPN_': (),
    # '_DFFSRE_NPPP_': (),
    # '_DFFSRE_PNNN_': (),
    # '_DFFSRE_PNNP_': (),
    # '_DFFSRE_PNPN_': (),
    # '_DFFSRE_PNPP_': (),
    # '_DFFSRE_PPNN_': (),
    # '_DFFSRE_PPNP_': (),
    # '_DFFSRE_PPPN_': (),
    # '_DFFSRE_PPPP_': (),
    # '_DFFSR_NNN_':   (),
    # '_DFFSR_NNP_':   (),
    # '_DFFSR_NPN_':   (),
    # '_DFFSR_NPP_':   (),
    # '_DFFSR_PNN_':   (),
    # '_DFFSR_PNP_':   (),
    # '_DFFSR_PPN_':   (),
    # '_DFFSR_PPP_':   (),
    # '_DFF_NN0_':     (),
    # '_DFF_NN1_':     (),
    # '_DFF_NP0_':     (),
    # '_DFF_NP1_':     (),
    # '_DFF_N_':       (),
    # '_DFF_PN0_':     (),
    # '_DFF_PN1_':     (),
    # '_DFF_PP0_':     (),
    # '_DFF_PP1_':     (),
    # '_DFF_P_':       (),
    # '_FF_':          (),
    # '_SDFFCE_NN0N_': (),
    # '_SDFFCE_NN0P_': (),
    # '_SDFFCE_NN1N_': (),
    # '_SDFFCE_NN1P_': (),
    # '_SDFFCE_NP0N_': (),
    # '_SDFFCE_NP0P_': (),
    # '_SDFFCE_NP1N_': (),
    # '_SDFFCE_NP1P_': (),
    # '_SDFFCE_PN0N_': (),
    # '_SDFFCE_PN0P_': (),
    # '_SDFFCE_PN1N_': (),
    # '_SDFFCE_PN1P_': (),
    # '_SDFFCE_PP0N_': (),
    # '_SDFFCE_PP0P_': (),
    # '_SDFFCE_PP1N_': (),
    # '_SDFFCE_PP1P_': (),
    # '_SDFFE_NN0N_':  (),
    # '_SDFFE_NN0P_':  (),
    # '_SDFFE_NN1N_':  (),
    # '_SDFFE_NN1P_':  (),
    # '_SDFFE_NP0N_':  (),
    # '_SDFFE_NP0P_':  (),
    # '_SDFFE_NP1N_':  (),
    # '_SDFFE_NP1P_':  (),
    # '_SDFFE_PN0N_':  (),
    # '_SDFFE_PN0P_':  (),
    # '_SDFFE_PN1N_':  (),
    # '_SDFFE_PN1P_':  (),
    # '_SDFFE_PP0N_':  (),
    # '_SDFFE_PP0P_':  (),
    # '_SDFFE_PP1N_':  (),
    # '_SDFFE_PP1P_':  (),
    # '_SDFF_NN0_':    (),
    # '_SDFF_NN1_':    (),
    # '_SDFF_NP0_':    (),
    # '_SDFF_NP1_':    (),
    # '_SDFF_PN0_':    (),
    # '_SDFF_PN1_':    (),
    # '_SDFF_PP0_':    (),
    # '_SDFF_PP1_':    (('A', True, None), ('B', True, None), ('Y', False, 1)),
    'adff':   (('CLK', True, 1), ('ARST', True, 1), ('D', True, None), ('Q', False, None)),
    # 'adffe':  (('CLK', True, 1), ('EN', True, 1), ('ARST', True, 1), ('D', True, None), ('Q', False, None)),
    # # 'aldff':  (('CLK', True, 1), ('ALOAD', True, 1), ('D', True, None), ('Q', False, None), ('AD', True, None)),
    # # 'aldffe': (('CLK', True, 1), ('EN', True, 1), ('ALOAD', True, 1), ('D', True, None), ('Q', False, None), ('AD', True, None)),
    # # 'dff':    (('CLK', True, 1), ('D', True, None), ('Q', False, None)),
    # # 'dffe':   (('CLK', True, 1), ('EN', True, 1), ('D', True, None), ('Q', False, None)),
    # 'dffsr':  (('CLK', True, 1), ('SET', True, None), ('CLR', True, None), ('D', True, None), ('Q', False, None)),
    # 'dffsre': (('CLK', True, 1), ('EN', True, 1), ('SET', True, None), ('CLR', True, None), ('D', True, None), ('Q', False, None)),
    # # 'ff':     (('D', True, None), ('Q', False, None)),
    # 'sdff':   (('CLK', True, 1), ('SRST', True, 1), ('D', True, None), ('Q', False, None)),
    # 'sdffce': (('CLK', True, 1), ('SRST', True, 1), ('EN', True, 1), ('D', True, None), ('Q', False, None)),
    # 'sdffe':  (('CLK', True, 1), ('EN', True, 1), ('SRST', True, 1), ('D', True, None), ('Q', False, None)),

    # Latches
    # '_DLATCHSR_NNN_':  (('E', True, 1), ('S', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCHSR_NNP_':  (('E', True, 1), ('S', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCHSR_NPN_':  (('E', True, 1), ('S', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCHSR_NPP_':  (('E', True, 1), ('S', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCHSR_PNN_':  (('E', True, 1), ('S', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCHSR_PNP_':  (('E', True, 1), ('S', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCHSR_PPN_':  (('E', True, 1), ('S', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCHSR_PPP_':  (('E', True, 1), ('S', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_NN0_':    (('E', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_NN1_':    (('E', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_NP0_':    (('E', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_NP1_':    (('E', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_N_':      (('E', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_PN0_':    (('E', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_PN1_':    (('E', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_PP0_':    (('E', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_PP1_':    (('E', True, 1), ('R', True, 1), ('D', True, 1), ('Q', False, 1)),
    # '_DLATCH_P_':      (('E', True, 1), ('D', True, 1), ('Q', False, 1)),
    'adlatch':  (('EN', True, 1), ('ARST', True, 1), ('D', True, None), ('Q', False, None)),
    # # 'dlatch':   (('EN', True, 1), ('D', True, None), ('Q', False, None)),
    # 'dlatchsr': (('EN', True, 1), ('SET', True, None), ('CLR', True, None), ('D', True, None), ('Q', False, None))
}

CELLS_WITH_RESET = {
    'adff',
    'adffe',
    'aldff',
    'aldffe',
    # 'dffsr',
    # 'dffsre',
    'sdff',
    'sdffce',
    'sdffe',
    'dlatchsr',
}

ALL_CELL_NAMES_TRANSMITTERS = set(ALL_CELL_PORTS.keys())
# {
#     # '_NOT_',
#     # '_XNOR_',
#     # '_XOR_',
#     # 'add',
#     # 'neg',
#     # 'nex',
#     # 'not',
#     # 'pos',
#     # 'reduce_xnor',
#     # 'reduce_xor',
#     # 'sub',
#     # 'xnor',
#     'xor',
# }
