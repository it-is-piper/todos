# `todos`

A tool to find all `TODO` and `FIXME` comments introduced on your dev branch. No more
polluting your task list with those left by previous developers in the codebase. Just the
changes *you* made.

## usage

Run `./todos.sh` anywhere in a git repository while on a non-`main` branch. If outputting
to a terminal, it gives a nice, human-readable format.

```bash
> ./todos.sh
README.md
7:TODO write an intro
8:TODO write an outro
todos.sh
48:for file in $(git diff --name-only -S"TODO" "${earliest}^" $latest); do
52: | grep "TODO" \
```

If piped to another command (e.g., [`fpp`](https://github.com/facebook/PathPicker)), it
uses a machine-readable format:

```bash
> ./todos.sh | fpp
README.md:7:TODO write an intro
README.md:8:TODO write an outro
todos.sh:48:for file in $(git diff --name-only -S"TODO" "${earliest}^" $latest); do
todos.sh:52:        | grep "TODO" \

________________________________________________________________________________________________________
[f|A] selection, [down|j|up|k|space|b] navigation, [enter] open, [x] quick select mode, [c] command mode
```

Both of these formats are inspired by the output of
[`ag`](https://github.com/mizuno-as/silversearcher-ag).

## future work

- [ ] rely less on the specific text output format of `git diff`
- [ ] `json` formatting option
- [ ] `emacs` integration
- [ ] `vscode` integration
