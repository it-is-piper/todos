from argparse import ArgumentParser
from tofix import Tofix, Format
import os


def app():
    parser = ArgumentParser()
    parser.add_argument(
        "--format",
        choices=[Format.HUMAN, Format.MACHINE, Format.JSON],
        default=Format.HUMAN,
    )
    parser.add_argument("--cached", action="store_true")
    parser.add_argument("--unstaged", action="store_true")
    args = parser.parse_args()

    todos = Tofix(unstaged=args.unstaged, cached=args.cached)
    _, lines = todos.files_and_lines()

    if os.isatty(1) and args.format == Format.HUMAN:
        Tofix.human_format(lines)
    elif not os.isatty(1) or args.format == Format.MACHINE:
        Tofix.machine_format(lines)
    elif args.format == Format.JSON:
        Tofix.json_format(lines)


if __name__ == "__main__":
    app()
