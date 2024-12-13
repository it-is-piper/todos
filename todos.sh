#!/usr/bin/env bash
set -eo pipefail

GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

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

json_format() {
    local file=$1
    local lines_with_numbers=$2

    while read -r line_with_number; do
        number=$(echo $line_with_number | cut -d: -f1)
        line=$(echo $line_with_number | cut -d: -f2-)
        jq -n --arg file $file --arg number $number --arg line "$line" '{ "file": $file, "number": $number, "line": $line }'
    done <<< "$lines_with_numbers"
}

format=''
parent='main'
unstaged=false
cached=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --format)
            if [[ -n "$2" && $2 != --* ]]; then
                format="$2"
                shift 2
            else
                echo "Error: --format requires an argument"
                exit 1
            fi
            ;;
        --parent)
            if [[ -n "$2" && $2 != --* ]]; then
                parent="$2"
                shift 2
            else
                echo "Error: --parent requires an argument"
                exit 1
            fi
            ;;
        --debug)
            set -x
            shift 1
            ;;
        --unstaged)
            unstaged=true
            shift 1
            ;;
        --cached)
            cached=true
            shift 1
            ;;
        *)
            echo "Error: Unknown option $1"
            exit 1
            ;;
    esac
done

root=$(git rev-parse --show-toplevel)
if [[ $unstaged == true ]] && [[ $cached == true ]]; then
    echo '--unstaged and --cached are mutually exclusive. Exiting.'
    exit 1
fi

branch=$(git rev-parse --abbrev-ref HEAD)
if [ $? -ne 0 ]; then
    echo "Must be within a git repository. Exiting."
    exit 1
fi

if [[ $format == json ]]; then
   ndjson=''
fi

commits=$(git cherry -v "$parent" | grep '^+' | cut -d' ' -f2)
earliest=$(echo $commits | cut -d' ' -f1)
left="${earliest}^"
right="$latest"
if [[ $unstaged == true ]]; then
    right=""
fi

for file in $(git diff --name-only -S"TODO" $left $right); do
    absolute_path="$root/$file"
    lines_with_numbers=$(git diff -U999999 "${earliest}^" -- "$absolute_path" \
        | tail -n+6 \
        | grep -n '^+' \
        | grep "TODO" \
        | sed -E 's/^([0-9]+):\+/\1:/')

    if [[ $format == json ]]; then
        ndjson="${ndjson}$(json_format "${file}" "${lines_with_numbers}")"
    elif [[ -t 1 ]]; then
        human_format "${absolute_path}" "${lines_with_numbers}"
    else
        machine_format "${absolute_path}" "${lines_with_numbers}"
    fi
done

# TODO yet another one!
# TODO look at that!
if [[ $format == json ]]; then
    echo -e "$ndjson" | jq -s '.'
fi
