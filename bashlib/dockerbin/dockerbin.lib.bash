#!/bin/bash
#==============================================================================
# mi-infra-dockerbin v0.2.0
#==============================================================================
set -eou pipefail

function dockerbin__setup () {
  SCRIPT_DIR=$( cd ${0%/*} && pwd -P )
  DOCKER_DIR=$(dirname "$SCRIPT_DIR")
  REPO_DIR=$(dirname $DOCKER_DIR)
  cd $DOCKER_DIR

  export IMAGE_REPO="${IMAGE_REPO:-050946403637.dkr.ecr.ca-central-1.amazonaws.com}"
  export IMAGE_NAME="$IMAGE_REPO/$1"
  export IMAGE_TAG=${IMAGE_TAG:-$(git rev-parse --abbrev-ref HEAD)}
}

function dockerbin__docker_compose () {
  exec docker compose -f docker-compose.yml "${@}"
}

function dockerbin__docker () {
  exec docker "${@}"
}

function dockerbin__docker_build () {
  GITHUB_CREDENTIALS_TMP_FILENAME=/tmp/dockerbin.secrets.txt
  cat >$GITHUB_CREDENTIALS_TMP_FILENAME << EOF
export GITHUB_USER=$GITHUB_USER
export GITHUB_TOKEN=$GITHUB_TOKEN
EOF
  function __github_credentials_cleanup () {
    rm $GITHUB_CREDENTIALS_TMP_FILENAME
  }
  trap __github_credentials_cleanup EXIT

  exec docker build --progress plain  \
    -t $IMAGE_NAME:$IMAGE_TAG  \
    -f Dockerfile  \
    --secret id=secrets,src=/tmp/dockerbin.secrets.txt  \
    "${@}"  \
    ".."
}

function dockerbin__download_from_sso () {
  ARCHIVE_FILEPATH=$1
  FILEPATH=$2
  if [[ -f $FILEPATH ]]; then
    echo "$FILEPATH: File already exists. Skip download and extraction."
    return 0
  fi

  if [[ -f $ARCHIVE_FILEPATH ]]; then
    echo "$ARCHIVE_FILEPATH: Archive already exists. Skip download."
  else
    echo "$ARCHIVE_FILEPATH: Downloading archive."
    curl --fail --silent --show-error -L "https://$GITHUB_USER:$GITHUB_TOKEN@sso.motoinsight.com/file-server/download/$(basename $ARCHIVE_FILEPATH)" -o $ARCHIVE_FILEPATH
  fi

  echo "$ARCHIVE_FILEPATH: Extracting archive."
  gunzip -c $ARCHIVE_FILEPATH > $FILEPATH
}
