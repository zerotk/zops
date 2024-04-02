#!/bin/bash

set -e

source ./monorepo.lib.bash

monorepo__main \
  mi-infra-iac#main  \
  git@github.com:unhaggle/centralpanel-cluster,apps/centralpanel \
  git@github.com:unhaggle/creditapp-cluster,apps/creditapp \
  git@github.com:unhaggle/peb-cluster,apps/peb \
  git@github.com:unhaggle/pi-cluster,apps/pi \
  git@github.com:unhaggle/t3can-cluster,apps/t3can \
  git@github.com:unhaggle/t3usa-cluster,apps/t3usa \
  git@github.com:unhaggle/tier1-cluster,apps/tier1 \
  git@github.com:unhaggle/unhaggle-cluster,apps/unhaggle \
  git@github.com:unhaggle/is-cluster,internal/is \
  git@github.com:unhaggle/mi-cluster,internal/mi \
  git@github.com:unhaggle/tf-aws-main-account#main,internal/main \
  git@github.com:unhaggle/tf-github-motoinsight#main,internal/github \
  git@github.com:unhaggle/tf_newrelic_alerts,internal/newrelic \
  git@github.com:unhaggle/uh_conf,_archive/uh_conf \
  git@github.com:unhaggle/audi-cluster,_archive/audi \
  git@github.com:unhaggle/bp-cluster,_archive/bp \
  git@github.com:unhaggle/gaus-cluster,_archive/gaus \
  git@github.com:unhaggle/honda-cluster,_archive/honda \
  git@github.com:unhaggle/nomad-cluster,_archive/nomad \
  git@github.com:unhaggle/polestar-cluster,_archive/polestar \
  git@github.com:unhaggle/sso-cluster,_archive/sso \
  git@github.com:unhaggle/vw-cluster,_archive/vw

# BRANCHES:
# * t3can-cluster#infra_1635
# * t3can-cluster#infra_2068
# * tier1-cluster#infra_2046
