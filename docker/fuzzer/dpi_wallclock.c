// Copyright 2024 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

#include <vpi_user.h>
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <stdbool.h>

uint64_t start_wallclocktime;
bool is_wallclock_started;

// VPI-C function to measure wallclock time
static unsigned long long measureWallclockTime(void) {
    struct timespec my_timespec;
    clock_gettime(CLOCK_MONOTONIC, &my_timespec);
    return my_timespec.tv_sec * 1000ULL + my_timespec.tv_nsec / 1000000ULL;
}

static int wallclocktime_start_compiletf(char *user_data)
{
      return 0;
}
static int wallclocktime_end_compiletf(char *user_data)
{
      return 0;
}

static int wallclocktime_start_calltf(char *user_data)
{
    is_wallclock_started = true;
    start_wallclocktime = measureWallclockTime();
    return 0;
}
static int wallclocktime_end_calltf(char *user_data)
{
    uint64_t end_wallclocktime = measureWallclockTime();

    if (!is_wallclock_started)
        vpi_printf("Warning: wallclocktime_end called before wallclocktime_start.\n");
    else
        vpi_printf("Elapsed time: %llu.\n", end_wallclocktime - start_wallclocktime);
    return 0;
}

void wallclocktime_start_register(void)
{
    is_wallclock_started = false;

    s_vpi_systf_data tf_data;

    tf_data.type      = vpiSysTask;
    tf_data.tfname    = "$wallclocktime_start";
    tf_data.calltf    = wallclocktime_start_calltf;
    tf_data.compiletf = wallclocktime_start_compiletf;
    tf_data.sizetf    = 0;
    tf_data.user_data = 0;
    vpi_register_systf(&tf_data);
}
void wallclocktime_end_register(void)
{
    s_vpi_systf_data tf_data;

    tf_data.type      = vpiSysTask;
    tf_data.tfname    = "$wallclocktime_end";
    tf_data.calltf    = wallclocktime_end_calltf;
    tf_data.compiletf = wallclocktime_end_compiletf;
    tf_data.sizetf    = 0;
    tf_data.user_data = 0;
    vpi_register_systf(&tf_data);
}

void (*vlog_startup_routines[])(void) = {
    wallclocktime_start_register,
    wallclocktime_end_register,
    0
};
