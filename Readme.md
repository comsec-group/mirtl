# Experimental implementation for paper for Lost in Translation: Enabling Confused Deputy Attacks on EDA Software with TransFuzz (USENIX Sec'25)

Welcome to an experimental implementation of TransFuzz!
Disclaimer: there might be imperfections, issues or incompletenesses.
Please feel free to contribute!

For more information about TransFuzz and the security implications of the findings, visit https://comsec.ethz.ch/mirtl

We provide a Docker image that you can collect running the command:
```
docker pull docker.io/ethcomsec/mirtl-artifacts
```

To build the docker image yourself:
```
cd docker
bash rebuild_push.sh
```

To differentially fuzz simulators run the command below after selecting the desired `FirstSimulator` and `SecondSimulator` in the same Python script.
```
cd fuzzer
python3 do_genonebyone.py 100 100 70
```

This execution will log many lines looking like
```
Match             0xc0 wl          1197512
Match           0x2b09 wl          1095014
Match             0x9c wl          1015013
Match            0x204 wl          1042512
Match             0x55 wl          1180015
Match            0x312 wl          1210015
Match             0x7d wl          1012515
Match             0xce wl          1085014
Match             0x69 wl          1122514
Match           0x1745 wl          1207515
Match          0x2edb3 wl          1062515
Match             0x66 wl          1097515
Match         0x31e0ac wl          1125015
Match          0x29493 wl          1117515
Match          0x1a49b wl          1150015
Match            0x1ca wl          1140015
Match              0x8 wl          1167515
Match           0x2a62 wl          1165013
Match             0x96 wl          1107514
Match             0xe2 wl          1132515
Match              0x0 wl          1127512
Match             0x98 wl          1212514
Match             0xce wl          1182515
Match             0x30 wl          1155013
Match              0x0 wl          1052515
Match         0x107eba wl          1000014
```
Each row represents one hardware circuit.
The hexadecimal number represents the cumulative signature.
The decimal number represents the workload identifier.
Any mismatch between the tools would report a mismatch instead of a "Match" line.

To fuzz Yosys, execute:
```
cd fuzzer
python3 do_genonebyone_fuzzyosys.py 100 500 70
```
