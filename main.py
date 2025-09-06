import os

import click

from todos import Format, Todos


@click.group()
def cli():
    pass


@click.command()
@click.argument("format", default=Format.HUMAN, type=click.Choice(Format))
@click.argument("unstaged", default=True, type=click.BOOL)
@click.argument("cached", default=False, type=click.BOOL)
def todos(format: str, unstaged: bool, cached: bool):
    _format = format
    todos = Todos(unstaged=True, cached=False)
    _, lines = todos.files_and_lines()

    if os.isatty(1) and _format == Format.HUMAN:
        Todos.human_format(lines)
    elif not os.isatty(1) or _format == Format.MACHINE:
        Todos.machine_format(lines)
    elif _format == Format.JSON:
        Todos.json_format(lines)


cli.add_command(todos)

if __name__ == "__main__":
    cli()
