// Copyright 2024 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

#include "Vtop.h"
#include "verilated.h"
#include "ticks.h"

#include <iostream>
#include <stdlib.h>
#include <chrono>
#include <fstream>
#include <cassert>

// This is a generated header
#include "interface_sizes.h"

typedef Vtop Module;

#define PATH_TO_METADATA "tmp/metadata.log"

size_t curr_id_in_random_inputs_from_file = 0;
std::vector<uint32_t> random_inputs_from_file;

void read_random_inputs_from_file(int simlen)
{
  // Make sure we call this function only once
  assert(random_inputs_from_file.size() == 0);

  std::ifstream in_file(PATH_TO_RANDOM_INPUTS_FILE);
  int expected_num_ints = FULL_RANDOM ? simlen * IN_DATA_WIDTH / 32 : simlen;
  uint64_t next_random_input = 0;
  while (in_file >> next_random_input && random_inputs_from_file.size() < expected_num_ints)
  {
    random_inputs_from_file.push_back(next_random_input);
  }
  std::cout << "Read " << random_inputs_from_file.size() << " random inputs from file." << std::endl;
  std::cout << "Expected " << expected_num_ints << " random inputs." << std::endl;
  assert(random_inputs_from_file.size() == expected_num_ints);
}

void randomize_inputs(Module *my_module)
{
#if FULL_RANDOM == 1
  for (int i = 0; i < IN_DATA_WIDTH / 32; i++)
  {
    my_module->in_data[i] = random_inputs_from_file[curr_id_in_random_inputs_from_file++];
  }
#else
  int random_input = random_inputs_from_file[curr_id_in_random_inputs_from_file++];
  for (int i = 0; i < IN_DATA_WIDTH / 32; i++)
    my_module->in_data[i] = random_input + i;
#endif
}

/**
 * Runs the testbench.
 *
 * @param tb a pointer to a testbench instance
 * @param simlen the number of cycles to run
 */
std::pair<long, uint64_t> run_test(Module *my_module, int simlen)
{

  srand(time(NULL)); // set random seed to current time
  uint64_t cumulated_output = 0;
  auto start = std::chrono::steady_clock::now();

  for (int tick_id = 0; tick_id < simlen; tick_id++)
  {
    randomize_inputs(my_module);
    my_module->eval();

#if VM_TRACE
    trace_ = new VerilatedVcdC;
    module_->trace(trace_, kTraceLevel);
    VerilatedVcdC * trace_->open(trace_filename.c_str());
#endif // VM_TRACE

    for (int i = 0; i < OUT_DATA_WIDTH / 32; i++)
    {
      cumulated_output += my_module->out_data[i];
    }

#if PROBE_DATA_WIDTH < 64
      std::cout << "Probe step " << tick_id << " word " << i << " : " << std::hex << my_module->probe_data << std::endl;
#else
    for (int i = 0; i < PROBE_DATA_WIDTH / 32; i++)
      std::cout << "Probe step " << tick_id << " word " << i << " : " << std::hex << my_module->probe_data[i] << std::endl;
#endif
  }

  auto stop = std::chrono::steady_clock::now();
  long ret = std::chrono::duration_cast<std::chrono::milliseconds>(stop - start).count();
  return std::make_pair(ret, cumulated_output);
}

int main(int argc, char **argv, char **env)
{

  Verilated::commandArgs(argc, argv);
  Verilated::traceEverOn(VM_TRACE);

  ////////
  // Instantiate the module.
  ////////

  Module *my_module = new Module;

  int simlen = get_sim_length_cycles(0);
  read_random_inputs_from_file(simlen);

  ////////
  // Run the experiment.
  ////////

  std::pair<long, uint64_t> duration_and_output = run_test(my_module, simlen);
  long duration = duration_and_output.first;
  uint64_t cumulated_output = duration_and_output.second;

  std::cout << "Testbench complete!" << std::endl;
  std::cout << "Output signature: " << std::dec << cumulated_output << "." << std::endl;
  std::cout << "Elapsed time: " << std::dec << duration << "." << std::endl;

  delete my_module;
  exit(0);
}
