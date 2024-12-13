"""
Implements the `todos` application. See `todos.Todos` for more information.
"""

from argparse import ArgumentParser
from dataclasses import dataclass
from enum import Enum
import os
import json
from typing import List, Optional, Any, Tuple
from git import Git


def _remove_nones(values: List[Optional[Any]]) -> List[Any]:
    """Remove all None values from a list."""
    return [v for v in values if v is not None]


class Format(str, Enum):
    """Formatting options for stdout."""
    HUMAN = "human"
    MACHINE = "machine"
    JSON = "json"


@dataclass
class Line:
    """Dataclass for a line containing the "todo" key."""
    path: str
    number: int
    text: str

    def to_dict(self):
        """Represent as a dict."""
        return {
            "file": self.path,
            "line": self.number,
            "text": self.text
        }


class Todos:
    """Implements the `todos` application.

    Exposes one method `files_and_lines` which returns a list of raw file paths and `Line`
    objects for every line in the currently checked out branch that contains a specified
    "todo" `key`.

    Uses `gitpython` under the hood to run the necessary `git cherry` and `git diff`
    commands.
    """
    base_branch: str
    key: str
    cached: bool
    unstaged: bool
    g: Git

    def __init__(self,
                 base_branch: str = "main",
                 key: str = "TODO",
                 cached: bool = False,
                 unstaged: bool = False):
        self.base_branch = base_branch
        self.key = key
        self.cached = cached
        self.unstaged = unstaged
        self.g = Git(os.getcwd())

        if self.cached and self.unstaged:
            # TODO use a more specific exception type
            raise Exception(
                "cached and unstaged are mutually exclusive options")

    def _commits(self) -> List[str]:
        # cherry outputs each commit that's in one branch but not the other
        cherry_output = self.g.cherry(["-v", self.base_branch])
        all_cherries = cherry_output.split("\n")

        # git diff appends a "+ " in front of commits in the current branch that are not
        # in the base branch"
        added_cherries = [c for c in all_cherries if c[:2] == "+ "]

        # there's a space between the "+" and the commit hash
        hashes = [c.split(" ")[1] for c in added_cherries]
        return hashes

    def _files(self, left: str, right: Optional[str] = None) -> List[str]:
        # Get names of files that changed in this commit range that have the key in them
        flags = ["--name-only", f"-S\"{self.key}\""]
        if self.cached:
            flags.append("--cached")
        diff_args = _remove_nones([*flags, left, right])

        # TODO For some reason this returns an empty change set when left is 1 commit before
        # right, but the verbatim command succeeds when run from a shell.
        diff_output = self.g.diff(diff_args)
        files_with_keys = [
            line for line in diff_output.split("\n") if line != '']
        return files_with_keys

    def _files_and_lines(self, left: str, right: Optional[str]) -> Tuple[List[str], List[Line]]:
        flags = ["-U999999"]
        if self.cached:
            flags.append("--cached")

        paths = self._files(left, right)
        result: List[Line] = []

        for path in paths:
            diff_args = _remove_nones([*flags, left, right, "--", path])
            diff_output = self.g.diff(diff_args)

            # ignore the first 6 lines, which display metadata
            diff_lines = diff_output.split("\n")[6:]

            # we need to figure out what the line number is for each added line
            lines_with_key = [
                Line(path=path, number=number, text=text)
                for number, text in enumerate(diff_lines)
                if text[:1] == "+" and self.key in text
            ]
            result += lines_with_key

        return paths, result

    def files_and_lines(self) -> Tuple[List[str], List[Line]]:
        """Return a list of `Line` objects for added line containing `self.key`."""
        commits = self._commits()

        # We want to diff with the commit *before* the first one we added in our branch
        left = f"{commits[0]}^"

        # The right side of the diff should be empty unless we're only looking at
        # committed files
        right = None if self.cached or self.unstaged else commits[-1]

        return self._files_and_lines(left, right)

    @staticmethod
    def human_format(files: List[str], lines: List[Line]):
        """Print the lines in a format comparable to that of `ack` and `ag`."""
        print("human format is unsupported")

    @staticmethod
    def machine_format(files: List[str], lines: List[Line]):
        """Print the lines in a format consumable by `fpp`."""
        print("machine format is unsupported")

    @staticmethod
    def json_format(files: List[str], lines: List[Line]):
        """Print the lines as a json array to stdout."""
        objects = [line.to_dict() for line in lines]
        output = json.dumps(objects, indent=2)
        print(output)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--format",
        choices=[Format.HUMAN, Format.MACHINE, Format.JSON],
        default=Format.JSON
    )
    # TODO add validation that these aren't passed together
    # TODO also can't remember how to set things as flags
    # parser.add_argument("--cached", default=False)
    # parser.add_argument("--unstaged", default=False))
    args = parser.parse_args()

    # TODO switch back to using args once I have them
    todos = Todos(unstaged=True, cached=False)
    files, lines = todos.files_and_lines()

    if args.format == Format.HUMAN:
        Todos.human_format(files, lines)
    elif args.format == Format.MACHINE:
        Todos.machine_format(files, lines)
    elif args.format == Format.JSON:
        Todos.json_format(files, lines)
