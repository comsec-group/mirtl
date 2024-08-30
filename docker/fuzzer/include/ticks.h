// Copyright 2024 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

#pragma once

#include <chrono>

#include <iostream>
#include <cassert>
#include <sstream>

static int get_sim_length_cycles(int lead_time_cycles)
{
  const char* simlen_env = std::getenv("SIMLEN");
  if(simlen_env == NULL) { std::cerr << "SIMLEN environment variable not set." << std::endl; exit(1); }
  int simlen = atoi(simlen_env);
  assert(lead_time_cycles >= 0);
  assert(simlen > 0);
  assert(simlen > lead_time_cycles);
  std::cout << "SIMLEN set to " << simlen << " ticks." << std::endl;
  return simlen - lead_time_cycles;
}

static const char *cl_get_tracefile(void)
{
#if VM_TRACE
  const char *trace_env = std::getenv("TRACEFILE");
  if(trace_env == NULL) { std::cerr << "TRACEFILE environment variable not set." << std::endl; exit(1); }
  return trace_env;
#else
  return "";
#endif
}

static const char *cl_get_inputs_file(void)
{
  const char *trace_env = std::getenv("INPUTS_FILE");
  if(trace_env == NULL) { std::cerr << "INPUTS_FILE environment variable not set." << std::endl; exit(1); }
  return trace_env;
}
