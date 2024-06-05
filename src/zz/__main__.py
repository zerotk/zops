import click

from zz.cli import aws
from zz.cli import codegen
from zz.cli import tf
from zz.cli import git

@click.group()
def main():
    pass


main.add_command(aws.main)
main.add_command(tf.main)
main.add_command(codegen.main)
main.add_command(git.main)

if __name__ == "__main__":
    main()
