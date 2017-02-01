# zops

ZOPS is an extendable command line utility intended to centralize and reuse software development solutions and
processes.

## Creating ZOPS commands in your project

Using project `alpha` as example:

```
/
  /alpha
    __init__.py
    zops.py
  setup.py
```

### ./alpha/zops.py

```python
import click

@click.group(name='alpha')
def main():
    pass

@main.command()
def my_command():
    """
    This is my command.

    $ zops alpha my_command
    """
    click.echo('my command')
```

### ./setup.py

```python

# ...

setup(

    # ...

    entry_points="""
    [zops.plugins]
    alpha=alpha.zops:main
    """,
)

```

## Creating a ZOPS extension library

```
/
  /zops
    /bravo
      cli.py
  setup.py
```

### ./zops/bravo/cli.py
