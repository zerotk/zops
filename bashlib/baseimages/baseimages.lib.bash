#!/bin/bash
set -eou pipefail

PACKER_VERSION="1.11"
MOTOINSIGHT_UTILS_VERSION="${MOTOINSIGHT_UTILS_VERSION:-v1.14.0}"

source <(curl -s https://raw.githubusercontent.com/zerotk/zops/main/bashlib/install.sh)
bashlib__include provisioner

#============================================================================== Functions

function env_check () {
  [[ $# -lt 1 ]] && echo "Usage: env_check <ENVIRONMENT VARIABLE>" && return 9
  local VALUE="${!1-x}"
  [[ "$VALUE" == "x" ]] && echo "env_check: ERROR: Missing environment variable: $1" && return 9
  [[ -z "$VALUE" ]] && echo "env_check: ERROR: Empty environment variable: $1" && return 9
  return 0
}

function baseimages__build_image () {
  if [[ "${1-}" == "" ]]; then
    echo "Usage: build-image <IMAGE_NAME> [<IMAGE_ARG>*]"
    exit 9
  fi

  FILENAME=$1;shift

  if [[ "$FILENAME" == *".Dockerfile" ]]; then
    baseimages__build_docker $FILENAME
  else
    baseimages__build_ami $FILENAME
  fi
}

function baseimages__provision () {
  TARGET=$1;shift
  SOURCE=$1;shift
  TARGET="./.build/$TARGET"

  mkdir -p "$(dirname $TARGET)"
  if [ "$SOURCE" == *"github.com"* ]; then
    URL="${SOURCE%\#*}"
    REF="${SOURCE#*\#}"
    rm -rf "$TARGET"
    if [ -d $TARGET/.git ]; then
      git clone --quiet --depth 1 --branch $REF $URL $TARGET
    else
      git -C $TARGET fetch --tags
      git -C $TARGET switch $REF
    fi
  elif [ "$SOURCE" == "s3"* ]; then
    UNARCHIVE $TARGET /opt/motoinsight
  else
    [ -d $TARGET ] && rm -rf $TARGET
    cp -R "$SOURCE" "$TARGET"
  fi
}

function baseimages__build_docker () {
  FILENAME=$1;shift

  env_check DOCKER_TAG

  # Obtain required arguments from the Dockerfile ARGs.
  DOCKERFILE_ARGS=$(baseimages___list_dockerfile_args $FILENAME)
  baseimages___check_vars $FILENAME "$DOCKERFILE_ARGS"

  # Add --build-arg option for each ARG found above.
  build_args=""
  for i in $DOCKERFILE_ARGS; do
    build_args="$build_args --build-arg $i"
  done

  # Build the image
  docker buildx build -f "$FILENAME" -t $DOCKER_TAG \
    --progress plain \
    $build_args \
    .
}

function baseimages__build_ami () {
  local VARS_TEMPLATE=$1;shift
  local VARS_FILENAME=.build/$(basename "${VARS_TEMPLATE%.*}").vars.hcl

  baseimages___check_vars $VARS_TEMPLATE "$(baseimages___list_ami_vars $VARS_TEMPLATE)"
  envsubst < $VARS_TEMPLATE > $VARS_FILENAME

  # Note that we may or may not be running packer in a container. We use the relative path to the
  # file so it will work in both cases.
  RELATIVE_SCRIPT_DIR=$(dirname ${BASH_SOURCE[0]})
  PACKER_FILEPATH=$RELATIVE_SCRIPT_DIR/build-image.pkr.hcl
  baseimages__run_packer init $PACKER_FILEPATH
  baseimages__run_packer build -var-file=$VARS_FILENAME "$@" $PACKER_FILEPATH
}

# Internals

function baseimages___list_ami_vars() {
  FILENAME=$1;shift
  python3 -c "
import re
result = re.findall('\{([A-Za-z_][A-Za-z_0-9]*)\}',open('$FILENAME','r').read())
print('\n'.join(sorted(set(result))))"
}

function baseimages___list_dockerfile_args() {
  FILENAME=$1;shift
  python3 -c "
import re
content = open('$FILENAME','r').read()
re_dockerfile_args = re.compile(r'^ARG\s+(\w+)(?:=(.*))?', re.MULTILINE)
result = re_dockerfile_args.findall(content)
print('\n'.join([i[0] for i in result]))
"
}

function baseimages___check_vars () {
  local VARS_TEMPLATE="$1"
  local ALL_VARS="${2:-}"

  [[ -z "$ALL_VARS" ]] && return

  missing_vars=0
  echo "baseimages: Checking template variables..."
  for i_var in $ALL_VARS; do
    if [[ -z ${!i_var-} ]]; then
      value='<NOT DEFINED>'
      ((missing_vars+=1))
    else
      value=${!i_var}
    fi
    echo "baseimages: - $i_var=${value}"
  done

  if [[ "$missing_vars" != 0 ]]; then
    echo "
baseimages: ERROR: Please define the missing variables before continuing.
baseimages:        For AMIs, check the .vars.template.hcl files for details of each variable.
baseimages:        For Dockerfiles, check the .Dockerfile ARGS.
" 1>&2
    exit $missing_vars
  fi
}

function baseimages__run_packer () {
  if type -p "docker" > /dev/null 2>&1; then
    docker run \
      -w /workspace \
      -v `pwd`:/workspace \
      -v $HOME/.aws:/root/.aws \
      -v build-image-packer_dir:/workspace/.packer.d \
      -e PACKER_LOG=0 \
      -e PACKER_PLUGIN_PATH=/workspace/.packer.d \
      hashicorp/packer:$PACKER_VERSION "$@"
  else
    PACKER_LOG=0
    PACKER_PLUGIN_PATH=.packer.d
    packer "$@"
  fi
}

# Bashlib protocol

function baseimages__assets () {
  echo "build-image.pkr.hcl"
}

# # CI
#
# function baseimages__ci_build_bookworm_docker () {
#   echo "*** build_bookworm_docker ${@}"
#   export IMAGE_NAME=$1;shift
#   local RELEASE_VER=$1;shift
#   local WEEK_VERSION=$1;shift
#   if [[ $IMAGE_NAME == "bookworm-python" ]]; then
#     local IMAGE_VERSION=$PYTHON_VER
#   elif [[ $IMAGE_NAME == "bookworm-runtime" ]]; then
#     local IMAGE_VERSION=py$PYTHON_VER
#   elif [[ $IMAGE_NAME == "bookworm-frontend" ]]; then
#     local IMAGE_VERSION=node$NODE_VER
#   elif [[ $IMAGE_NAME == "bookworm-app" ]]; then
#     local IMAGE_VERSION=py$PYTHON_VER-node$NODE_VER
#   else
#     echo "ERROR: Unknown IMAGE_NAME: $IMAGE_NAME"
#     exit 9
#   fi
#
#   echo "*** Building docker image $IMAGE_NAME:$IMAGE_VERSION"
#   baseimages__build_docker $IMAGE_NAME.Dockerfile $IMAGE_VERSION
#
#   PUSH_IMAGE_TAG=$IMAGE_VERSION
#   echo "*** Pushing docker image $IMAGE_NAME:$PUSH_IMAGE_TAG"
#   docker push 050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$PUSH_IMAGE_TAG
#
#   PUSH_IMAGE_TAG=$IMAGE_VERSION.$WEEK_VERSION
#   echo "*** Pushing docker image $IMAGE_NAME:$PUSH_IMAGE_TAG"
#   docker tag  050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$IMAGE_VERSION 050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$PUSH_IMAGE_TAG
#   docker push 050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$PUSH_IMAGE_TAG
# }
#
# function baseimages__ci_build_bookworm_base_ami () {
#   echo "*** build_bookworm_base_ami ${@}"
#   local RELEASE_VER=$1;shift
#   local WEEK_VERSION=$1;shift
#   # Build base AMI with docker and agents support.
#   export IMAGE_NAME="bookworm-base"
#   export IMAGE_VERSION="$RELEASE_VER.$WEEK_VERSION"
#
#   echo "*** Building AMI image $IMAGE_NAME-$IMAGE_VERSION"
#   baseimages__build_ami $IMAGE_NAME.ami $IMAGE_VERSION
# }
#
# function baseimages__ci_build_bookworm_app () {
#   echo "*** build_bookworm_app ${@}"
#   local RELEASE_VER=$1;shift
#   local WEEK_VERSION=$1;shift
#   local VARIATION_VERSION="py$PYTHON_VER-node$NODE_VER"
#   export IMAGE_NAME="bookworm-app"
#   export IMAGE_VERSION="$GITHUB_SHA"
#
#   # Build Docker
#   echo "*** Building docker image $IMAGE_NAME:$IMAGE_VERSION"
#   export BASEIMAGE="050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-bookworm-runtime:py$PYTHON_VER-$RELEASE_VER"
#   baseimages__build_docker $IMAGE_NAME.Dockerfile $IMAGE_VERSION
#
#   # Publish docker image without week version.
#   PUSH_IMAGE_TAG="$VARIATION_VERSION-$RELEASE_VER"
#   echo "*** Publishing docker image $IMAGE_NAME:$PUSH_IMAGE_TAG"
#   docker tag  050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$IMAGE_VERSION 050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$PUSH_IMAGE_TAG
#   docker push 050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$PUSH_IMAGE_TAG
#
#   # Publish docker image WITH week version.
#   PUSH_IMAGE_TAG="$VARIATION_VERSION-$RELEASE_VER.$WEEK_VERSION"
#   echo "*** Publishing docker image $IMAGE_NAME:$PUSH_IMAGE_TAG"
#   docker tag  050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$IMAGE_VERSION 050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$PUSH_IMAGE_TAG
#   docker push 050946403637.dkr.ecr.ca-central-1.amazonaws.com/mi-$IMAGE_NAME:$PUSH_IMAGE_TAG
#
#   # Build/publish AMI
#   export BASEIMAGE_VERSION="$RELEASE_VER.$WEEK_VERSION"
#   export IMAGE_VERSION="$VARIATION_VERSION-$RELEASE_VER.$WEEK_VERSION"
#   echo "*** Building ami image $IMAGE_NAME-$IMAGE_VERSION"
#   baseimages__build_ami $IMAGE_NAME.ami $IMAGE_VERSION
# }
