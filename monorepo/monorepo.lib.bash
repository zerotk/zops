#!/bin/bash

REBASE_SUCCESS="monorepo-success"
REBASE_CURSOR="monorepo-cursor"

MONOREPO_ORIGINS=(centralpanel-cluster creditapp-cluster is-cluster mi-cluster peb-cluster pi-cluster t3can-cluster t3usa-cluster tf-aws-main-account tf-github-motoinsight tf_newrelic_alerts tier1-cluster unhaggle-cluster)

pushd () {
  command pushd "$@" > /dev/null
}

popd () {
  command popd "$@" > /dev/null
}


MONOREPO_COLOR='\033[0;34m'
MONOREPO_RESET='\033[0m'

function monorepo__title () {
  echo -e "${MONOREPO_COLOR}monorepo: ************************************************************************ $*${MONOREPO_RESET}"
}

function monorepo__rebase_it () {
  local hash=$1
  local origin=$2

  REBASE_START="$origin-source_start"
  REBASE_END="$origin-source_end"

  monorepo__title "- $origin/$hash"
  git branch -f $REBASE_CURSOR $hash
  git switch -q $REBASE_CURSOR

  if [[ $(git branch --list "$REBASE_START") == "" ]]; then
    git branch -f "$REBASE_START" main
  else
    git branch -f "$REBASE_START" "$REBASE_END"
  fi
  git branch -f "$REBASE_END" $hash
  monorepo__title "Rebase $REBASE_CURSOR [$(git rev-parse --short $REBASE_CURSOR)] starting on $REBASE_START [$(git rev-parse --short $REBASE_START)] onto $REBASE_SUCCESS [$(git rev-parse --short $REBASE_SUCCESS)]"
  git rebase --rebase-merges=rebase-cousins $REBASE_START --onto=$REBASE_SUCCESS &> /tmp/$REBASE_CURSOR.log  || true
  
  local ERRORED_COMMIT=$(gawk '/Could not apply/ { print(substr($4, 0, 7)) }' /tmp/$REBASE_CURSOR.log)
  local LOOP_COUNT=1
  local LOOP_MAX=20
  while [[ $ERRORED_COMMIT != "" ]]; do
    monorepo__title "Fixing conflict on commit $ERRORED_COMMIT (loop $LOOP_COUNT/$LOOP_MAX)"

    monorepo__title " - Source commit changes..."
    git show --no-abbrev-commit --name-status $ERRORED_COMMIT > /tmp/monorepo-errored.status.log

    monorepo__title " - Source checkout..."
    git checkout $ERRORED_COMMIT -- .
    ERRORED_COMMIT=""

    monorepo__title " - Source deletions..."
    gawk '/^D[ 	]/ { print $2 }' /tmp/monorepo-errored.status.log > /tmp/monorepo-errored.delete-files.log
    for i_filename in $(cat /tmp/monorepo-errored.delete-files.log); do
      monorepo__title "   - git rm $i_filename"
      git rm $i_filename >> /dev/null || true
    done

    git st > /tmp/monorepo.status.log
    git st >> /tmp/monorepo.debug.log

    monorepo__title " - Merge conflict deletions..."
    gawk '/^DU / { print $2 }' /tmp/monorepo.status.log > /tmp/monorepo.delete-files.log
    gawk '/^DD / { print $2 }' /tmp/monorepo.status.log >> /tmp/monorepo.delete-files.log
    gawk '/^UD / { print $2 }' /tmp/monorepo.status.log >> /tmp/monorepo.delete-files.log
    for i_filename in $(cat /tmp/monorepo.delete-files.log); do
      monorepo__title "   - git rm $i_filename"
      git rm $i_filename >> /dev/null || true
    done

    monorepo__title " - Merge conflict additions..."
    gawk '/^AU / { print $2 }' /tmp/monorepo.status.log > /tmp/monorepo.add-files.log
    for i_filename in $(cat /tmp/monorepo.add-files.log); do
      # monorepo__title "   - git add $i_filename"
      git add $i_filename
    done

    # This replaces "git rebase --continue" but without asking for the commit message.
    # monorepo__title "Continue rebase..."
    git commit -m"$(cat .git/MERGE_MSG)"  &> /tmp/monorepo.log
    git rebase --skip                     &>> /tmp/monorepo.log  || true
    ERRORED_COMMIT=$(gawk '/Could not apply/ { print(substr($4, 0, 7)) }' /tmp/monorepo.log)

    (( LOOP_COUNT += 1 ))
    if (( $LOOP_COUNT >= $LOOP_MAX )); then
      monorepo__title " CRITIAL: INFINITE LOOP SAFE EXIT"
      break
    fi
  done

  git update-ref refs/heads/$REBASE_SUCCESS HEAD
  git switch -q $REBASE_SUCCESS
}

function monorepo__initialization () {
  monorepo__title "initialization"
  # Stop any ongoing process and cleanup
  git rebase --abort &>> /dev/null || true
  git reset --hard &>> /dev/null
  git switch -q "$1"
  monorepo__cleanup
  
  # Start in the given commit
  git branch -f $REBASE_SUCCESS "$1"
  git switch -q $REBASE_SUCCESS
  
#  for i_origin in ${MONOREPO_ORIGINS[@]}; do
#    monorepo__title "init $i_origin-master"
#
#    git rev-parse --verify "$i_origin/main" &> /dev/null && branch="main" || branch="master"
#    git branch -f $i_origin-master $i_origin/$branch
#
#    FIRST_COMMIT=$(git log --oneline $i_origin/$branch --format="%H" | tail -1)
#    git branch -f $i_origin-source_end $FIRST_COMMIT
#  done
}

#function monorepo__rebased () {
#  for i_origin in ${MONOREPO_ORIGINS[@]}; do
#    monorepo__title "init $i_origin-rebased"
#
#    monorepo__initialization main
#
#    # Create xxx-master
#    git rev-parse --verify "$i_origin/main" &> /dev/null && branch="main" || branch="master"
#    git branch -f $i_origin-master $i_origin/$branch
#
#    # Create xxx-rebased (xxx-master rebased on "main")
#    monorepo__rebase_it $i_origin-master $i_origin
#    git checkout -b $i_origin-rebased
#
#    monorepo__title "Checking ..."
#  done
#}

function monorepo__check () {
  local origin=$1
  local path=$2
  echo git diff --name-status "$origin-master" "$origin-rebased" -- $path
  git diff --name-status "$origin-master" "$origin-rebased" -- $path
}

function monorepo__cleanup () {
  monorepo__title cleanup
  git branch --list "monorepo__*" | xargs git branch -D >> /dev/null || true
}


function monorepo__clone () {
  local repo_url=$1
  local repo_local=$2
  local repo_path=$3

  monorepo__title "monorepo__clone: $repo_local"
  if [[ ! -d $repo_local ]]; then
    monorepo__title "monorepo__clone: cloning... $repo_path"
    git clone $repo_url $repo_local
  else
    monorepo__title "monorepo__clone: updating... $repo_path"
    pushd $repo_local
    git sync
    popd $repo_local
  fi
  if [[ -n $repo_path ]]; then
    pushd $repo_local
    git filter-repo --to-subdirectory-filter=$repo_path
    popd
  fi
}

function monorepo__check () {
  monorepo__title "monorepo__check: STARTING"
  pushd target
  for i in "$@"; do
    repo_url=${i%,*}
    repo_branch=${repo_url#*\#}
    if [[ "$repo_branch" == "" || "$repo_branch" == "$repo_url" ]]; then
      repo_branch=master
    fi
    repo_path=${i#*,}
    repo_path=${repo_path/-/_}
    repo_origin="monorepo__${repo_path/\//_}"

    monorepo__title "monorepo__check: checking... $repo_path"
    echo git diff "$repo_origin/$repo_branch" --name-status -- $repo_path
    git diff "$repo_origin/$repo_branch" --name-status -- $repo_path
  done
  popd
  monorepo__title "monorepo__check: FINISHED"
}

function monorepo__main () {
  REPO_NAME=$1
  shift

  monorepo__title "Creating directories"
  mkdir -p sources
  mkdir -p logs
  rm -rf target

  monorepo__title "Creating target repository (monorepo)"
  mkdir -p target
  pushd target
    git init --initial-branch=main .
    echo $REPO_NAME >> README.md
    git add .
    git commit -am "Initial commit."
  popd

  monorepo__title "Creating source repositories"
  for i in "$@"; do
    repo_url=${i%,*}
    repo_branch=${repo_url#*\#}
    if [[ "$repo_branch" == "" || "$repo_branch" == "$repo_url" ]]; then
      repo_branch=master
    fi
    repo_url=${repo_url%\#*}
    repo_path=${i#*,}
    repo_path=${repo_path/-/_}
    repo_origin="monorepo__${repo_path/\//_}"
    repo_local=sources/$(basename $repo_url)

    monorepo__title "- $repo_url#$repo_branch -> target/$repo_path"
    monorepo__clone $repo_url $repo_local $repo_path
    pushd target
      monorepo__title "Add remote: $repo_origin"
      git remote add $repo_origin ../$repo_local
      git fetch $repo_origin

      monorepo__title "Generate logs: logs/$repo_origin.log"
      git log --oneline --graph --pretty=format:'%aI %h "%s"' $repo_origin/$repo_branch | gawk '/^\* +[0-9]{4}\-/ { $1=""; ; print $0 }' > ../logs/$repo_origin.log
    popd
  done

  monorepo__title "Generate monorepo_script: ./monorepo-autogen.sh"
  ./monorepo.py logs/*.log > ./monorepo-autogen.sh

  bash ./monorepo-autogen.sh

  monorepo__check "$@"
}
