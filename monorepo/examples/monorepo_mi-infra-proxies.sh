#!/bin/bash

set -e

source ./monorepo.lib.bash

monorepo__main mi-infra-proxies \
  git@github.com:unhaggle/dev_proxy,dev-proxy \
  git@github.com:unhaggle/vw-proxy#main,vw-proxy
