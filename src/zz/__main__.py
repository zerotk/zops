import click
from zz.cli import aws, tf, codegen

@click.group()
def main():
    pass

main.add_command(aws.main)
main.add_command(tf.main)
main.add_command(codegen.main)

if __name__ == '__main__':
    main()
