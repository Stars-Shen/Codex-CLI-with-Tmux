#!/usr/bin/env bash
# Create a workspace once; reconnect without restarting its Codex processes.
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    printf 'Usage: %s [session-name] [working-directory]\n' "$0"
    printf 'Defaults: session codex, current directory. Existing sessions are reused.\n'
    exit 0
fi
if (( $# > 2 )); then
    printf 'Usage: %s [session-name] [working-directory]\n' "$0" >&2
    exit 2
fi
command -v tmux >/dev/null || { printf 'tmux is required.\n' >&2; exit 1; }
session="${1:-codex}"

if ! tmux has-session -t "=$session" 2>/dev/null; then
    command -v codex >/dev/null || { printf 'codex must be available in PATH.\n' >&2; exit 1; }
    workdir=$(cd -- "${2:-$PWD}" && pwd)
    shell="${SHELL:-/bin/bash}"
    start_env=(env -u NO_COLOR "SHELL=$shell")
    if command -v infocmp >/dev/null && infocmp tmux-256color >/dev/null 2>&1; then
        start_env+=(TERM=tmux-256color)
    fi

    tmux new-session -d -s "$session" -n shell -c "$workdir" "${start_env[@]}" "$shell"
    tmux set-option -t "$session" mouse on \; \
        set-option -t "$session" status on \; \
        set-option -t "$session" status-position bottom \; \
        set-option -t "$session" status-left '[#S] ' \; \
        set-option -t "$session" base-index 1 \; \
        set-option -t "$session" renumber-windows on \; \
        set-environment -t "$session" PATH "$PATH" \; \
        set-environment -r -t "$session" NO_COLOR
    if [[ "${start_env[*]}" == *TERM=tmux-256color* ]]; then
        tmux set-option -t "$session" default-terminal tmux-256color
    fi
    tmux move-window -r -t "$session:"
    for name in paper code debug experiment; do
        tmux new-window -d -t "$session:" -n "$name" -c "$workdir" \
            "${start_env[@]}" "$shell" -c 'codex; exec "$SHELL"'
    done
    for name in shell paper code debug experiment; do
        tmux set-window-option -t "$session:$name" automatic-rename off \; \
            set-window-option -t "$session:$name" pane-base-index 1 \; \
            set-window-option -t "$session:$name" window-status-format ' #I:#W ' \; \
            set-window-option -t "$session:$name" window-status-current-format ' [#I:#W] '
    done
    tmux select-window -t "$session:code"
fi

if [[ -n "${TMUX:-}" ]]; then
    exec tmux switch-client -t "=$session"
else
    exec tmux attach-session -t "=$session"
fi
