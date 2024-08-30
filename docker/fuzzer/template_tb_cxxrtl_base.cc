// Copyright 2024 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

#include "ticks.h"
#include "cxxrtl.cpp"

#include <iostream>
#include <stdlib.h>
#include <chrono>
#include <fstream>
#include <cassert>
#include <vector>

// This is a generated header
#include "interface_sizes.h"

size_t curr_id_in_inputs_from_file = 0;
size_t curr_id_in_actor_id_order = 0;
std::vector<uint32_t> inputs_from_file;
std::vector<uint32_t> actor_id_order;

int read_inputs_from_file(std::string input_filepath) {
  // Make sure we call this function only once
  assert(inputs_from_file.size() == 0);

  std::ifstream in_file(input_filepath);
  uint64_t next_actor_id, next_random_input;
  std::string next_actor_id_str, next_random_input_str;
  uint64_t num_32bit_inputs;
  in_file >> num_32bit_inputs;

  uint64_t remaining_lines_to_read = num_32bit_inputs;
  int simlen = 0;
  while(remaining_lines_to_read--) {
    simlen++;
    in_file >> next_actor_id_str;
    next_actor_id = std::stoul(next_actor_id_str, nullptr, 16);
    in_file >> next_random_input_str;
    next_random_input = std::stoul(next_random_input_str, nullptr, 16);

    actor_id_order.push_back(next_actor_id);

    inputs_from_file.push_back(next_random_input);

    // Check whether we were reading the subnet id or the subnet input
    if (next_actor_id < NUM_SUBNETS) {
      for (int i = 1; i < IN_DATA_WIDTH / 32; i++) {
        in_file >> next_random_input_str;
        next_random_input = std::stoul(next_random_input_str, nullptr, 16);
        inputs_from_file.push_back(next_random_input);
      }
    }
    else {
      // Nothing special to do for clkins
    }
  }
  return simlen;
}

void randomize_inputs(cxxrtl_design::p_wrapper__cxxrtl &top) {
#if FULL_RANDOM == 1
TEMPLATE_IN_DATA
TEMPLATE_CLKIN_DATA
curr_id_in_actor_id_order++;
  // for (int i = 0; i < IN_DATA_WIDTH / 32; i++) {
    // Found by experimenting compiling corresponding code with CXXRTL
// my_module->in_data[i] = inputs_from_file[curr_id_in_inputs_from_file++];
  // }
#else
  std::cout << "Error: FULL_RANDOM == 0 not implemented for cxxrtl." << std::endl;
  exit(1);
#endif
}

/**
 * Runs the testbench.
 *
 * @param tb a pointer to a testbench instance
 * @param simlen the number of cycles to run
 */
std::pair<long, uint64_t> run_test(cxxrtl_design::p_wrapper__cxxrtl &top, int simlen, const std::string trace_filename) {

#if DO_TRACE
  cxxrtl::vcd_writer vcd;
  cxxrtl::debug_items debug;
  test.debug_info(debug);
  vcd.timescale(1, "us");
  vcd.add(debug);
#endif // DO_TRACE

  srand(time(NULL)); // set random seed to current time
  uint64_t cumulated_output = 0;
  auto start = std::chrono::steady_clock::now();

#if DO_TRACE
  vcd.sample(0);
#endif

  for (int tick_id = 0; tick_id < simlen; tick_id++) {
    randomize_inputs(top);
    top.step();
    top.step();

#if DO_TRACE
  vcd.sample(tick_id+1);
#endif

TEMPLATE_OUT_DATA
  }

  auto stop = std::chrono::steady_clock::now();
  long ret = std::chrono::duration_cast<std::chrono::milliseconds>(stop - start).count();

#if DO_TRACE
  std::ofstream outfile("cxxrtl_trace.vcd", std::ios::out);
  outfile << vcd.buffer;
  outfile.close();
#endif // DO_TRACE

  return std::make_pair(ret, cumulated_output);
}

int main() {

  cxxrtl_design::p_wrapper__cxxrtl top;

  ////////
  // Get the env vars.
  ////////

  std::string vcd_filepath = cl_get_tracefile();
  std::string input_filepath = cl_get_inputs_file();
  int simlen = read_inputs_from_file(input_filepath);

  ////////
  // Run the experiment.
  ////////

  std::pair<long, uint64_t> duration_and_output = run_test(top, simlen, vcd_filepath);
  long duration = duration_and_output.first;
  uint64_t cumulated_output = duration_and_output.second;

  std::cout << "Testbench complete!" << std::endl;
  std::cout << "Output signature: " << std::dec << cumulated_output << "." << std::endl;
  std::cout << "Elapsed time: " << std::dec << duration << "." << std::endl;

  return 0;
}
