import os
from argparse import ArgumentParser

from todos import Format, Todos


def main():
    # TODO test a thing
    parser = ArgumentParser()
    parser.add_argument(
        "--format",
        choices=[Format.HUMAN, Format.MACHINE, Format.JSON],
        default=Format.HUMAN,
    )
    # TODO add validation that these aren't passed together
    # TODO also can't remember how to set things as flags
    # parser.add_argument("--cached", default=False)
    # parser.add_argument("--unstaged", default=False))
    args = parser.parse_args()

    # TODO switch back to using args once I have them
    todos = Todos(unstaged=True, cached=False)
    _, lines = todos.files_and_lines()

    if os.isatty(1) and args.format == Format.HUMAN:
        Todos.human_format(lines)
    elif not os.isatty(1) or args.format == Format.MACHINE:
        Todos.machine_format(lines)
    elif args.format == Format.JSON:
        Todos.json_format(lines)


if __name__ == "__main__":
    main()
