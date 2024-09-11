#!/usr/bin/env bash

set -eou pipefail

IS_DOCKER=${IS_DOCKER:-false}
( $IS_DOCKER ) && IS_AMI=false || IS_AMI=true

function SETUP () {
  ( $IS_AMI ) && exec > >(tee /tmp/provisioner-$(whoami).log) 2>&1

  export MOTOINSIGHT_UTILS_VERSION=${MOTOINSIGHT_UTILS_VERSION:-v1.13.0}

  if [[ -n ${AWS_CREDENTIALS-} ]]; then
    export AWS_ACCESS_KEY_ID=${AWS_CREDENTIALS%,*}
    export AWS_SECRET_ACCESS_KEY=${AWS_CREDENTIALS#*,}
  fi
  export AWS_EC2_METADATA_DISABLED=1
  export AWS_DEFAULT_REGION=ca-central-1

  #============================================================================== Non-interactive
  # Configure non-interactive
  # REF: https://stackoverflow.com/questions/34773745/debconf-unable-to-initialize-frontend-dialog
  echo 'debconf debconf/frontend select Noninteractive' | SUDO debconf-set-selections
  export DEBIAN_FRONTEND=noninteractive
}

function SUDO () {
  if [[ "$(whoami)" == "root" ]]; then
    CMD=""
  else
    CMD="sudo"
  fi
  $CMD "$@"
}

#============================================================================== provisioner.lib

INSTALL_DIR=""
function START () {
  _FINISH
  INSTALL_DIR="/tmp/$1"
  echo "#============================================================================== $1"
  install --mode=0777 -d $INSTALL_DIR
  cd $INSTALL_DIR
}

function FINISH () {
  echo "#============================================================================== FINISH"
  _FINISH
}

function _FINISH () {
  if [[ -n $INSTALL_DIR ]]; then
    SUDO rm -rf $INSTALL_DIR
    cd $HOME
    INSTALL_DIR=""
  fi
}

function DOWNLOAD () {
  if [[ "$1" = "s3://"* ]]; then
    AWS_ACCESS_KEY_ID=${AWS_CREDENTIALS%,*} AWS_SECRET_ACCESS_KEY=${AWS_CREDENTIALS#*,} aws s3 cp $1 ${1##*/}
  else
    wget --no-verbose "$@"
  fi
}

function INSTALL_APT_SOURCE () {
  NAME=$1;shift
  KEY_URL=$1;shift
  SOURCE_LIST=$1;shift
  KEYRING_DIR=/etc/share/keyrings
  GPG_FILEPATH=$KEYRING_DIR/$NAME.gpg

  SUDO install -m 0755 -d $KEYRING_DIR
  curl -fsSL $KEY_URL | SUDO gpg --dearmor -o $GPG_FILEPATH
  SUDO chmod a+r $GPG_FILEPATH
  echo \
    "deb [arch="$(dpkg --print-architecture)" signed-by=$GPG_FILEPATH] $SOURCE_LIST" | \
    SUDO tee /etc/apt/sources.list.d/$NAME.list > /dev/null
  SUDO apt-get update -qq
}

function INSTALL () {
  local PACKAGE=$1;
  if [[ $PACKAGE = *".deb" ]]; then
    shift
    if [[ $PACKAGE == @("http:"*|"https:"*|"s3://"*) ]]; then
      DOWNLOAD $PACKAGE
      PACKAGE=$(basename $PACKAGE)
    fi
    SUDO dpkg -i $PACKAGE $@
  else
    SUDO apt-get update -qq
    SUDO apt-get install -qq --no-install-recommends -y $@
    SUDO rm -rf /var/lib/apt/lists/*
  fi
}

PROVISIONER__INSTALL_TMP=0

function INSTALL_TMP () {
  PROVISIONER__INSTALL_TMP="$(apt-mark showmanual)"
  apt-get update -qq
  apt-get install -y --no-install-recommends "$@"
}

function UNINSTALL_TMP () {
  apt-mark auto '.*' > /dev/null
  apt-mark manual $PROVISIONER__INSTALL_TMP
  find /usr/local -type f -executable -not \( -name '*tkinter*' \) -exec ldd '{}' ';' \
    | awk '/=>/ { so = $(NF-1); if (index(so, "/usr/local/") == 1) { next }; gsub("^/(usr/)?", "", so); printf "*%s\n", so }' \
    | sort -u \
    | xargs -r dpkg-query --search \
    | cut -d: -f1 \
    | sort -u \
    | xargs -r apt-mark manual \
  ;
  apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false
  rm -rf /var/lib/apt/lists/*
  PROVISIONER__INSTALL_TMP=0
}

function UNARCHIVE () {
  local ARCHIVE=$1; shift
  local OUTPUT_DIR=${1-}
  if [[ $ARCHIVE == @("http:"*|"https:"*|"s3://"*) ]]; then
    DOWNLOAD $ARCHIVE
    ARCHIVE=$(basename $ARCHIVE)
  fi

  [[ -n $OUTPUT_DIR ]] && SUDO mkdir -p $OUTPUT_DIR

  local OUTPUT_PARAMS=""
  if [[ $ARCHIVE == *".zip" ]]; then
    [[ -n $OUTPUT_DIR ]] && OUTPUT_PARAMS="-d $OUTPUT_DIR"
    SUDO unzip -qq $ARCHIVE $OUTPUT_PARAMS
  else
    [[ -n $OUTPUT_DIR ]] && OUTPUT_PARAMS="-C $OUTPUT_DIR"
    SUDO tar xf $ARCHIVE $OUTPUT_PARAMS
  fi
}
