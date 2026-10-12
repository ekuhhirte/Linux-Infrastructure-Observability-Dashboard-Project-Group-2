#!/bin/bash

# Creates the named pipe path
PIPE_PATH="/var/run/observability/stress_pipe"

# Makes sure the pipe is working
if [ ! -p "$PIPE_PATH" ]; then
    mkdir -p /var/run/observability
    mkfifo "$PIPE_PATH"
    chmod 666 "$PIPE_PATH"
fi