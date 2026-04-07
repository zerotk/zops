# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync --dev

# Run all tests
uv run pytest

# Run a single test file
uv run pytest src/zerotk/deps/_tests/test_deps.py

# Run a single test
uv run pytest src/zerotk/deps/_tests/test_deps.py::test_factory

# Lint
uv run flake8 src/
uv run isort src/
uv run black src/

# Run CLI tools
zops <command>
zz <command>
```

## Architecture

This is **zerotk.zops** ("Zero Operations Toolbox"), a Python CLI toolkit for DevOps operations. It exposes two CLI entrypoints:

- **`zops`** — legacy CLI, AWS-focused, uses direct Click commands (`src/zops/`)
- **`zz`** — new CLI built on `zerotk.deps` DI system (`src/zz/`), with subcommands: `codegen`, `tf`, `git`, `aws`

### Three packages (all under `src/`)

- **`zerotk/`** — foundational utilities: the `deps` DI framework, YAML helpers, path utilities, gitignored helpers
- **`zops/`** — legacy AWS CLI implementation
- **`zz/`** — new CLI and service layer

### Core pattern: `zerotk.deps` dependency injection

This is the central architectural pattern used throughout. Classes are decorated with `@deps.define` and declare dependencies as class attributes:

```python
@deps.define
class MyService:
    console = deps.Singleton(Console)       # shared singleton in the tree
    item_factory = deps.Factory(Item)       # creates new instances via partial
    sub_cmd = deps.Command(SubCli)          # wires click subcommands
```

- `deps.Singleton` — one instance shared across the entire dependency tree (keyed by class+name)
- `deps.Factory` — returns a `functools.partial` constructor so you call `self.item_factory(arg=val)`
- `deps.Command` — wires Click commands/groups into the CLI tree
- Sharing is controlled by passing the same `deps.Deps()` instance at construction time
- `instance.main()` is auto-generated and builds the Click group/command tree for CLI entry

### Finding command implementations

The `zz` CLI commands are implemented as methods decorated with `@click.command(...)` inside `@deps.define` classes in `src/zz/cli/`:

| CLI subcommand | Class | File |
|---|---|---|
| `zz aws` | `AwsCli` | `src/zz/cli/aws.py` |
| `zz codegen` | `CodegenCli` | `src/zz/cli/codegen.py` |
| `zz tf` | `TerraformCli` | `src/zz/cli/tf.py` |
| `zz git` | `GitCli` | `src/zz/cli/git.py` |

Each method decorated with `@click.command("<name>")` maps directly to `zz <subcommand> <name>`. For example, `zz aws ec2.list` is implemented by the `ec2_list` method in `AwsCli`.

The entry point wiring is in `src/zz/__main__.py`, which assembles all CLI classes via `deps.Command`.

### `zz` service layer (`src/zz/services/`)

Singleton services injected throughout the app:
- `Console` — rich output, titles, items, errors
- `FileSystem` — path and YAML I/O wrapper
- `TemplateEngine` — Jinja2 with many custom filters (`dashcase`, `camelcase`, `combine`, `dedup`, `dmustache`, `env_var`, `to_json`, etc.)
- `SubProcess` — async subprocess with execution logging
- `Terraform` — async terraform plan/apply runner
- `AwsProvider` / `Cloud` / `AwsLocal` — boto3 wrappers for EC2, ECS, RDS, SSM, autoscaling, secrets

### Codegen system (`src/zz/codegen/`, `src/zz/anatomy/`)

- **CodegenEngine**: finds `*.codegen.yml` playbooks recursively, renders Jinja2 templates from a `templates/` sibling directory against datasets defined in the playbook YAML
- **AnatomyEngine**: finds `anatomy-playbook.yml` files, loads feature registries from `anatomy-features.yml` (searched upward), applies feature templates
- For YAML template files (`.yml`/`.yaml`), the template engine uses alternate delimiters: `{{{var}}}` for variables and `{{%...%}}` for blocks (avoids conflicts with YAML/HCL `{{ }}` syntax)

### Template engine custom filters

Key non-standard Jinja2 filters defined in `TemplateEngine.run()`:
- `expandit` — recursive variable expansion
- `dashcase`, `camelcase`, `spinalcase`, `pascalcase` — case conversion
- `combine` — deep-merge dictionaries (Ansible-style)
- `dedup` — deduplicate list of dicts by key
- `dmustache` — wrap in `{{ }}` (for output that contains literal mustaches)
- `env_var` — wrap in `${ }` for HCL env var syntax
- `is_enabled` — checks `enabled` field with str2bool evaluation
