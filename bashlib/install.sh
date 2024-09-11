#!/bin/env bash

BASHLIB_DIR=.bashlib

function bashlib__include () {
  local BASHLIB_NAME=$1
  mkdir -p $BASHLIB_DIR
  bashlib__download $BASHLIB_NAME/$BASHLIB_NAME.lib.bash
  bashlib__source $BASHLIB_NAME/$BASHLIB_NAME.lib.bash

  local DOWNLOAD_FILES_ASSETS="${BASHLIB_NAME}__assets"
  if [[ $(type -t $DOWNLOAD_FILES_ASSETS) == function ]]; then
    for i in $($DOWNLOAD_FILES_ASSETS); do
      bashlib__download $BASHLIB_NAME/$i
    done
  fi
  declare -x "BASHLIB_${BASHLIB_NAME^}_DIR"="$BASHLIB_DIR/$BASHLIB_NAME"
}

function bashlib__download () {
  local FILEPATH=$1
  local SOURCE_URL=https://raw.githubusercontent.com/zerotk/zops/main/bashlib/$FILEPATH
  local TARGET_FILEPATH=$BASHLIB_DIR/$FILEPATH

  if [[ -f $TARGET_FILEPATH ]]; then
    echo "bashlib: $TARGET_FILEPATH: Reusing existing file."
    return
  fi

  echo "bashlib: $TARGET_FILEPATH: Downloading file..."
  mkdir -p $(dirname $TARGET_FILEPATH)
  curl -s -o $TARGET_FILEPATH $SOURCE_URL
}

function bashlib__source () {
  local FILEPATH="$BASHLIB_DIR/$1"
  echo "bashlib: $FILEPATH: Sourcing..."
  source "$FILEPATH"
}
