#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RESET='\033[0m' 

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ $? -ne 0 ]; then
    echo Must be within a git repository. Exiting. >&2
    exit 1
fi    

commits=$(git cherry -v main | grep '^+' | cut -d' ' -f2)
earliest=$(echo $commits | cut -d' ' -f1)
latest=$(echo $commits | rev | cut -d' ' -f1 | rev)

human_format() {
    local file=$1
    local lines_with_numbers=$2

    echo -e "$GREEN${file}$RESET"
    while read -r line_with_number; do
        number=$(echo $line_with_number | cut -d: -f1)
        line=$(echo $line_with_number | cut -d: -f2-)
        echo -e "$YELLOW$number$RESET:$line"
    done <<< "$lines_with_numbers"        
}

machine_format() {
    local file=$1
    local lines_with_numbers=$2

    while read -r line_with_number; do
        echo "${file}:${line_with_number}"
    done <<< "$lines_with_numbers"    
}

for file in $(git diff --name-only -S"TODO" "${earliest}^" $latest); do
    lines_with_numbers=$(git diff -U999999 "${earliest}^" $latest -- $file \
        | tail -n+6 \
        | grep -n '^+' \
        | grep "TODO" \
        | sed -E 's/^([0-9]+):\+/\1:/')

    if [[ -t 1 ]]; then
        human_format "${file}" "${lines_with_numbers}"
    else
        machine_format "${file}" "${lines_with_numbers}"
    fi
done
