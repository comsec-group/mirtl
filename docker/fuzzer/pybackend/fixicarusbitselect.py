# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import re

def gen_new_signal_name(new_signal_widths_and_names_len: int):
    return f"my_new_signal_{new_signal_widths_and_names_len}"

# @param signal_name_maybe_surrounded_by_operators may contain something like [N:M] or [N], preceded by alphanumeric and underscore characters.
# @return a pair (new signal name)
def replace_signal_name(signal_name_maybe_surrounded_by_operators: str, is_driver_of_always_ff: bool, new_signal_widths_and_names_list: list):
    found_signal_slice = re.search(r"([a-zA-Z0-9_]+)\[([0-9]+)(?::([0-9]+))?\]", signal_name_maybe_surrounded_by_operators)
    if found_signal_slice is None:
        # Do not do anything
        return signal_name_maybe_surrounded_by_operators, new_signal_widths_and_names_list
    else:
        signal_name = found_signal_slice.group(1)
        signal_slice_begin = int(found_signal_slice.group(2))
        signal_slice_end = int(found_signal_slice.group(3)) if found_signal_slice.group(3) is not None else signal_slice_begin

        new_signal_name = gen_new_signal_name(len(new_signal_widths_and_names_list))
        new_signal_widths_and_names_list.append((new_signal_name, signal_name, signal_slice_begin, signal_slice_end, is_driver_of_always_ff))

        return re.sub(r"([a-zA-Z0-9_]+)\[([0-9]+)(?::([0-9]+))?\]", new_signal_name, signal_name_maybe_surrounded_by_operators), new_signal_widths_and_names_list

# Fix the bitselects in the always_ff blocks
# @return the fixed text
def fix_icarus_bitselect(src_text: str):
    # If there is no clkin (we set it then to a single bit), then there is nothing to do
    if 'input clkin_data;' in src_text:
        return src_text

    # First, fix the bitselects like \out_data_bit[32]
    all_backslash_guys = re.findall(r"\\[a-zA-Z0-9_]+\[[0-9]+\]", src_text)
    all_backslash_guys = list(set(all_backslash_guys)) # Remove duplicates
    for backslash_guy in all_backslash_guys:
        src_text = src_text.replace(backslash_guy, 'mybackslash_'+backslash_guy.replace('[', '').replace(']', '').replace('\\', ''))

    src_lines = src_text.split("\n")

    # Pairs of (line_id, signal_with_bitselect) that are interesting
    # all_interesting_signals = []

    # Find the always_ff blocks
    # always_ff_blocks_lines = []
    line_id = 0

    new_signal_widths_and_names = []
    last_driven_width_and_name = None

    # Insert newlines before the always_ff blocks (this simplifies the algorithm a bit)
    for line_id in range(len(src_lines)-1, -1, -1):
        line = src_lines[line_id]
        if line.strip().startswith("always_ff") or line.strip().startswith("always_latch"):
            src_lines.insert(line_id, '')
            line_id += 1

    while True:
        if line_id >= len(src_lines):
            break
        line = src_lines[line_id]

        if line.strip().startswith("always_ff") or line.strip().startswith("always_latch"):
            if line.strip().startswith("always_ff"):
                # always_ff_blocks_lines.append(line)
                # always_ff_line = line.replace(',', '').replace('(', '').replace(')', '').replace('always_ff', '').replace('@', '')
                always_ff_line = line.replace(',', ' , ').replace('(', ' ( ').replace(')', ' ) ').replace('@', ' @ ')
                always_ff_line_tokens = always_ff_line.split()
                for token_id, token in enumerate(always_ff_line_tokens):
                    if token.startswith("posedge") or token.startswith("negedge"):
                        # all_interesting_signals.append((line_id, always_ff_line_tokens[token_id + 1]))
                        new_tokencontent, new_signal_widths_and_names = replace_signal_name(always_ff_line_tokens[token_id + 1], True, new_signal_widths_and_names)
                        always_ff_line_tokens[token_id + 1] = new_tokencontent
                        src_lines[line_id] = ' '.join(always_ff_line_tokens)
                        continue
                    elif token.startswith("begin"):
                        assert False, "It is assumed to not have a 'begin' keyword"

            else:
                assert line.strip() == "always_latch", "Unexpected: always_latch starter line already contains information"
            # Advance until the end of the block
            while (True):
                line_id += 1
                line = src_lines[line_id]
                if line == 'endmodule':
                    break
                if not line:
                    break
                # As long as the line starts with `if` or `else if`, we are still in the block.
                if 'begin' in line or 'end' in line:
                    raise NotImplementedError(f"Unexpected begin/end in basic always_ff block in line {line_id}:\n{line}")
                line_tokens = line.split()

                if line_tokens[0] == 'if' or (len(line_tokens) > 2 and line_tokens[0] == 'else' and line_tokens[1] == 'if'):
                    if_id = 0 if line_tokens[0] == 'if' else 1
                    new_tokencontent, new_signal_widths_and_names = replace_signal_name(line_tokens[if_id + 1], True, new_signal_widths_and_names)
                    line_tokens[if_id + 1] = new_tokencontent
                    src_lines[line_id] = ' '.join(line_tokens)

                    if len(line_tokens) < if_id + 3:
                        continue

                    if line_tokens[if_id + 2] == '{':
                        raise NotImplementedError("Found destination concatenation, but is not implemented yet.")

                    # The destination signal
                    size_before = len(new_signal_widths_and_names) # To check if we found a new signal
                    new_tokencontent, new_signal_widths_and_names = replace_signal_name(line_tokens[if_id + 2], False, new_signal_widths_and_names)
                    if size_before != len(new_signal_widths_and_names):
                        # To avoid duplicates, which would cause multi-driven issues
                        if last_driven_width_and_name is None or tuple(new_signal_widths_and_names[-1][1:]) != tuple(last_driven_width_and_name[1:]):
                            line_tokens[if_id + 2] = new_tokencontent
                            last_driven_width_and_name = new_signal_widths_and_names[-1]
                        else:
                            line_tokens[if_id + 2] = new_tokencontent.replace(new_signal_widths_and_names[-1][0], last_driven_width_and_name[0])
                            last_driven_width_and_name = tuple([last_driven_width_and_name[0]] + list(new_signal_widths_and_names[-1][1:]))
                            new_signal_widths_and_names = new_signal_widths_and_names[:-1]
                        src_lines[line_id] = ' '.join(line_tokens)
                    
                    if line_tokens[if_id + 4] == '{':
                        for token_id, token in enumerate(line_tokens[if_id + 5:]):
                            if token == ',':
                                continue
                            if token in ('}', '};'):
                                break
                            new_tokencontent, new_signal_widths_and_names = replace_signal_name(token, True, new_signal_widths_and_names)
                            line_tokens[if_id + 5 + token_id] = new_tokencontent
                            src_lines[line_id] = ' '.join(line_tokens)

                    else:
                        # The source signal
                        new_tokencontent, new_signal_widths_and_names = replace_signal_name(line_tokens[if_id + 4], True, new_signal_widths_and_names)
                        line_tokens[if_id + 4] = new_tokencontent
                        src_lines[line_id] = ' '.join(line_tokens)
                
                elif line_tokens[0] == 'else':
                    if line_tokens[1] == '{':
                        raise NotImplementedError("Found destination concatenation, but is not implemented yet.")
                    else:
                        # The destination signal
                        size_before = len(new_signal_widths_and_names)
                        new_tokencontent, new_signal_widths_and_names = replace_signal_name(line_tokens[1], False, new_signal_widths_and_names)
                        if size_before != len(new_signal_widths_and_names):
                            # To avoid duplicates, which would cause multi-driven issues
                            if last_driven_width_and_name is None or tuple(new_signal_widths_and_names[-1][1:]) != tuple(last_driven_width_and_name[1:]):
                                line_tokens[1] = new_tokencontent
                                last_driven_width_and_name = new_signal_widths_and_names[-1]
                            else:
                                line_tokens[1] = new_tokencontent.replace(new_signal_widths_and_names[-1][0], last_driven_width_and_name[0])
                                last_driven_width_and_name = tuple([last_driven_width_and_name[0]] + list(new_signal_widths_and_names[-1][1:]))
                                new_signal_widths_and_names = new_signal_widths_and_names[:-1]
                            src_lines[line_id] = ' '.join(line_tokens)
                        
                        if line_tokens[3] == '{':
                            for token_id, token in enumerate(line_tokens[4:]):
                                if token == ',':
                                    continue
                                if token in ('}', '};'):
                                    break
                                new_tokencontent, new_signal_widths_and_names = replace_signal_name(token, True, new_signal_widths_and_names)
                                line_tokens[4 + token_id] = new_tokencontent
                                src_lines[line_id] = ' '.join(line_tokens)


        else:
            line_id += 1

    # Create the lines for the new signals, say, just before the first always_ff block
    first_always_fl_line_id = None
    for line_id, line in enumerate(src_lines):
        if line.strip().startswith("always_ff") or line.strip().startswith("always_latch"):
            first_always_fl_line_id = line_id
            break
    assert not new_signal_widths_and_names or first_always_fl_line_id is not None, "No always_ff or always_latch block found but new signals are to be created"

    # Add the wire declarations and assignments
    if first_always_fl_line_id is not None:

        # Create the wire declarations
        wire_declarations = []
        for new_signal_width_and_name in new_signal_widths_and_names:
            new_signal_name = new_signal_width_and_name[0]
            new_signal_width = new_signal_width_and_name[2] - new_signal_width_and_name[3] + 1
            if new_signal_width == 1:
                wire_declarations.append(f"logic {new_signal_name};")
            else:
                wire_declarations.append(f"logic [{new_signal_width-1}:0] {new_signal_name};")
        # Create the assignments
        assignments = []
        for new_signal_width_and_name in new_signal_widths_and_names:
            new_signal_name = new_signal_width_and_name[0]
            new_signal_width = new_signal_width_and_name[2] - new_signal_width_and_name[3] + 1
            new_signal_is_driver_of_always_ff = new_signal_width_and_name[4]
            if new_signal_is_driver_of_always_ff:
                if new_signal_width == 1:
                    assignments.append(f"assign {new_signal_name} = {new_signal_width_and_name[1]}[{new_signal_width_and_name[2]}];")
                else:
                    assignments.append(f"assign {new_signal_name} = {new_signal_width_and_name[1]}[{new_signal_width_and_name[2]}:{new_signal_width_and_name[3]}];")
            else:
                assignments.append(f"assign {new_signal_width_and_name[1]}[{new_signal_width_and_name[2]}:{new_signal_width_and_name[3]}] = {new_signal_name};")

        # Insert the wire declarations and assignments
        src_lines.insert(first_always_fl_line_id, '')
        src_lines.insert(first_always_fl_line_id, '// New signals created by fix_icarus_bitselect')
        src_lines.insert(first_always_fl_line_id, '')
        src_lines.insert(first_always_fl_line_id, '')
        src_lines.insert(first_always_fl_line_id, '\n'.join(assignments))
        src_lines.insert(first_always_fl_line_id, '\n'.join(wire_declarations))
        src_lines.insert(first_always_fl_line_id, '')
        src_lines.insert(first_always_fl_line_id, '')

    dst_text = '\n'.join(src_lines)
    return dst_text
