# Copyright 2024 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

set -e
IMAGE_TAG=ethcomsec/mirtl:mirtl-artifacts
echo building $IMAGE_TAG
tar zcf eval-verismith.tgz eval-verismith # Comment out to avoid accidents :)
tar zcf fuzzer.tgz fuzzer # Comment out to avoid accidents :)
docker build -f Dockerfile -t $IMAGE_TAG .
echo "To push image, do:"
echo "docker push $IMAGE_TAG"
