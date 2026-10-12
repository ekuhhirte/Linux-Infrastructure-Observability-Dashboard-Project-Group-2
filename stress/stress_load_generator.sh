#!/bin/bash

# Creates the named pipe path
PIPE_PATH="/var/run/observability/stress_pipe"

# Makes sure the pipe is working
if [ ! -p "$PIPE_PATH" ]; then
    mkdir -p /var/run/observability
    mkfifo "$PIPE_PATH"
    chmod 666 "$PIPE_PATH"
fi

while true; do
    # 1. CPU Stress (Class 1)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - START: CPU Stress" > "$PIPE_PATH"
    stress-ng --cpu 2 --cpu-load 85 --timeout 30s --quiet
    sleep 5

    # 2. Virtual Memory Stress (Class 2)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - START: Memory Stress" > "$PIPE_PATH"
    stress-ng --vm 1 --vm-bytes 512M --timeout 45s --quiet
    sleep 5

    # 3. Filesystem / HDD Stress (Class 3)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - START: Filesystem HDD Stress" > "$PIPE_PATH"
    stress-ng --hdd 2 --hdd-bytes 100M --timeout 20s --quiet
    sleep 5

    # 4. Synchronous I/O Stress (Class 4)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - START: I/O Stress" > "$PIPE_PATH"
    stress-ng --io 2 --timeout 25s --quiet
    sleep 5

    # 5. Network Traffic Stress (Class 5)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - START: Network Stress" > "$PIPE_PATH"
    stress-ng --net 1 --timeout 15s --quiet
    sleep 10
done