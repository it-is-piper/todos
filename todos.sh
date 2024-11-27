#!/usr/bin/env bash

commits=$(git cherry -v main | grep '^+' | cut -d' ' -f2)
earliest=$(echo $commits | tail -n1)
latest=$(echo $commits | head -n1)

for file in $(git diff --name-only "${earliest}^" $latest); do
    git diff -U0 "${earliest}^" $latest -- $file | \
        grep -v "^+++" \
        | grep "^+" \
        | grep -e TODO -e FIXME \
        | sed 's/^+//' \
        | awk  '{print "'$file'" ": " $1}' \

done
