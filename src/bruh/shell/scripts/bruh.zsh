#!/usr/bin/env zsh
# Bruh Shell Integration for Zsh
# Captures previous command outcomes without manual piping

autoload -Uz add-zsh-hook

typeset -g __bruh_last_cmd=""

__bruh_preexec() {
    __bruh_last_cmd="$1"
}

__bruh_precmd() {
    local exit_code=$?
    local last_cmd="$__bruh_last_cmd"

    if [[ -z "$last_cmd" || "$last_cmd" =~ ^bruh ]]; then
        return
    fi

    mkdir -p "$HOME/.bruh" 2>/dev/null
    local timestamp
    timestamp=$(date +%s 2>/dev/null || echo 0)
    local session_file="$HOME/.bruh/last_session.json"

    cat <<EOF > "$session_file"
{
  "command": $(printf '%s' "$last_cmd" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || printf '"%s"' "$last_cmd"),
  "exit_code": $exit_code,
  "output": "",
  "cwd": "$PWD",
  "timestamp": $timestamp,
  "shell": "zsh"
}
EOF
}

add-zsh-hook preexec __bruh_preexec
add-zsh-hook precmd __bruh_precmd
