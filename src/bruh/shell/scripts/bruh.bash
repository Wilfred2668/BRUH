#!/usr/bin/env bash
# Bruh Shell Integration for Bash
# Captures previous command outcomes without manual piping

__bruh_precmd() {
    local exit_code=$?
    local last_cmd

    # Get last command from history
    last_cmd=$(HISTTIMEFORMAT= history 1 | sed 's/^[ ]*[0-9]*[ ]*//')

    if [[ -z "$last_cmd" || "$last_cmd" =~ ^bruh ]]; then
        return
    fi

    mkdir -p "$HOME/.bruh" 2>/dev/null
    local timestamp
    timestamp=$(date +%s 2>/dev/null || echo 0)
    local session_file="$HOME/.bruh/last_session.json"

    # Write json session locally
    cat <<EOF > "$session_file"
{
  "command": $(printf '%s' "$last_cmd" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || printf '"%s"' "$last_cmd"),
  "exit_code": $exit_code,
  "output": "",
  "cwd": "$PWD",
  "timestamp": $timestamp,
  "shell": "bash"
}
EOF
}

if [[ -z "$PROMPT_COMMAND" ]]; then
    PROMPT_COMMAND="__bruh_precmd"
elif [[ "$PROMPT_COMMAND" != *"__bruh_precmd"* ]]; then
    PROMPT_COMMAND="__bruh_precmd; $PROMPT_COMMAND"
fi
