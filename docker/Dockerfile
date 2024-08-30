# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

FROM ubuntu@sha256:b5a61709a9a44284d88fb12e5c48db0409cfad5b69d4ff8224077c57302df9cf
RUN apt-get update && apt-get install -y curl gnupg apt-utils && \
    echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee -a /etc/apt/sources.list.d/sbt.list && curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | apt-key add && \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    autoconf automake autotools-dev libmpc-dev libmpfr-dev libgmp-dev gawk build-essential \
    bison flex texinfo gperf libtool patchutils bc zlib1g-dev git perl python3 make g++ libfl2 \
    libfl-dev zlib1g zlib1g-dev git autoconf flex bison gtkwave python3.9 python3.9-venv clang \
    tcl-dev libreadline-dev jq libexpat-dev device-tree-compiler vim && \
    apt-get install -y sbt && \
    apt-get install -y software-properties-common  default-jdk default-jre gengetopt && \
    apt-get install -y patch diffstat texi2html subversion chrpath wget && \
    apt-get install -y libgtk-3-dev gettext && \
    apt-get install -y python3-pip python3.8-dev rsync libguestfs-tools expat ctags && \
    apt-get install -y libexpat1-dev libusb-dev libncurses5-dev cmake gtkwave help2man python3 python3-pip libmpc-dev libmpfr-dev libgmp-dev gawk ninja-build libglib2.0-dev libslirp-dev && \
    apt-get install -y libc6-dev libffi-dev xz-utils gnupg netbase && \
    apt-get install -y libboost-system-dev libboost-filesystem-dev libboost-chrono-dev libboost-program-options-dev libboost-test-dev libboost-thread-dev libboost-iostreams-dev && \
    apt-get install && add-apt-repository ppa:deadsnakes/ppa && apt-get update -y && apt-get install python3.12 -y


############################
# Install the MiRTL Yosys
############################

COPY mirtl-yosys/mirtl-yosys.tgz /mirtl-yosys.tgz
RUN bash -c "tar zxf mirtl-yosys.tgz && cd /mirtl-yosys && make -j 220 && make install" 

############################
# Install the default Verilator 5.022
############################

# 5.022
RUN bash -c "git clone https://github.com/verilator/verilator && unset VERILATOR_ROOT && cd verilator && git checkout v5.022 && autoconf && ./configure && make -j 220 && make install"

############################
# Install the default Icarus Verilog v12_0 
############################

# Some version reasonably not buggy
RUN bash -c "git clone https://github.com/steveicarus/iverilog && cd iverilog && git checkout 548010e36be386c3f68807df8323719e3ac24325 && autoconf && ./configure && make -j 220 && make install"

############################
# Evaluate the transfuzz circuit generator
############################

RUN bash -c "pip3 install matplotlib && pip3 install vcdvcd"
COPY fuzzer.tgz fuzzer.tgz
RUN bash -c "tar zxf fuzzer.tgz"
RUN bash -c "cd fuzzer && iverilog-vpi dpi_wallclock.c"

# Can modify the script file to run more iterations and to plot the graphs
# Might increase to range(1, 41)
RUN bash -c "cd fuzzer && python3 do_eval_execperf.py 100"
# Might increase to range(1, 41)
RUN bash -c "cd fuzzer && python3 do_eval_execperf_yosys.py 100"
# 10, 100, 250] might add 500]
RUN bash -c "cd fuzzer && python3 do_plot_rawperf.py 100"

############################
# Evaluate the cumulated toggle coverage of cell outputs
############################

RUN bash -c "cd fuzzer && python3 do_testtoggle.py 100"

############################
# Evaluate the toggle performance per simulator per length and circuit
############################

# 10, 100, 250] might add 500]
RUN bash -c "cd fuzzer && python3 do_plot_toggleperf.py 100"

############################
# Evaluate the abstract metric
############################

RUN bash -c "cd fuzzer && python3 do_testtoggle70.py 100"
RUN bash -c "cd fuzzer && python3 do_eval_execperf70.py 100"
RUN bash -c "cd fuzzer && python3 do_eval_execperf_yosys70.py 100"

# 10, 100, 250] might add 500]
RUN bash -c "cd fuzzer && python3 do_plot_netperf70.py 100"

############################
# Evaluate Verismith
############################

RUN bash -c "git clone https://github.com/ymherklotz/verismith.git"
RUN bash -c "mkdir -p /nix && curl -L https://nixos.org/nix/install | sh -s -- --daemon"

# The fork contains some fixes that allows building the thing without errors. Waiting for the PR to be merged.
RUN bash -c "rm -rf /verismith && git clone https://github.com/flaviens/verismith-fork.git /verismith"

# Fix one dependency issue that we encountered
RUN bash -c "sed -i 's/tasty-hedgehog >=1.0 && <1.2/tasty-hedgehog >=1.0/g' /verismith/verismith.cabal"
RUN bash -c "source /etc/profile.d/nix.sh && cd /verismith && nix-build"

COPY eval-verismith.tgz eval-verismith.tgz
RUN bash -c "tar zxf eval-verismith.tgz"
# TIMEOUT_SECONDS = 5 # Might change to 900
RUN bash -c "source /etc/profile.d/nix.sh && cd /eval-verismith && python3 eval_performance.py 10 100 /nix/store"

# COPY scripts/do_eval_cellthroughput.py /fuzzer/do_eval_cellthroughput.py
RUN bash -c "cd /fuzzer && python3 do_eval_cellthroughput.py 100"

# COPY scripts/do_plot_cellthroughput.py /fuzzer/do_plot_cellthroughput.py
RUN bash -c "cd /fuzzer && python3 do_plot_cellthroughput.py /fuzzer/perfpercell_transfuzz.json /eval-verismith/performance_results.json > /fuzzer/cellthroughput.log"

# Cell distributions for Verismith
RUN bash -c "source /etc/profile.d/nix.sh && cd /eval-verismith && python3 gen_manytestcases.py 100 100 /nix/store"
# Cell distributions for Transfuzz
RUN bash -c "cd /fuzzer && python3 do_eval_cellstats.py 100 100"

# Creates /fuzzer/celldistribs.png and /fuzzer/celldistribs_size.png
RUN bash -c "cd /fuzzer && python3 do_plotcelldistribs.py /fuzzer/eval_cellstats_simufuzz.json /eval-verismith/manytestcases/cell_summary_verismith.json"

############################
# Example fuzzing
############################

# The EDA tools to be tested are selectable in the script source.
# RUN bash -c "cd /fuzzer && python3 do_genonebyone.py 100 100 100"
