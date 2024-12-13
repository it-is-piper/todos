import os
from git import Git
from typing import List


class Todos:
    base_branch: str
    g: git.Git

    def __init__(self, base_branch: str = "main"):
        self.base_branch = base_branch
        self.g = Git(os.getcwd())

    def _commits(self) -> List[str]:
        cherries = self.g.cherry(["-v", self.base_branch])
        
    def _earliest(self, commits: List[str]) -> str:
        return 

    def _latest(self) -> str:


if __name__ == "__main__":
    print("[TODO] things are going to happen here")

    # TODO we're just going to start with default behavior of comparing the current tree
    # to main
