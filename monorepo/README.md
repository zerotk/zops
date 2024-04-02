# zops.monorepo

### Usage:

```
$ source monorepo.lib.bash
$ monorepo__main <TARGET> [<SOURCE>]+
```

where:

* `TARGET`: The name of the target (monorepo) repository.
* `SOURCE`: A string with the format: `<REPO_URL>[#<REPO_BRANCH],TARGET_DIR>`
  * `REPO_URL`: The full URL for this source repository.
  * `REPO_BRANCH`: Optional branch. Defaults to master.
  * `TARGET_DIR`: The target directory in the monorepo.

example:

```
$ monorepo__main zops-monorepo  \
  git@github.com/zops.monorepo.git#main,monorepo 
  git@github.com/zops.aws.git,aws
  git@github.com/zops.anatomy.git,anatomy
```

This would create a target repository with three sub directories. Each sub directory with all the contents of each source repository.

```
/target
  /anatomy
  /aws
  /monorepo
```` 
