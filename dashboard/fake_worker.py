"""
fake_worker.py - Pretends to be 3 worker VMs so the dashboard can be built
without the real servers.

It copies the behaviour of Ethan's API.py exactly:
  * plain TCP server (no HTTP)
  * one JSON object per line, ending in "\n", about once per second
  * same 7 field names, same units (percent / bytes per second)
  * only ONE client per worker at a time

Run:   python fake_worker.py
Then:  type 1, 2 or 3 and press Enter to KILL / REVIVE that worker
       (this is how you test the dashboard's OFFLINE + auto-reconnect logic)
"""

import json
import random
import socket
import threading
import time

HOST = "127.0.0.1"                 # only reachable from this computer
PORTS = {1: 5001, 2: 5002, 3: 5003}  # fake worker number -> port

alive = {n: True for n in PORTS}     # flipped by typing 1/2/3


def fake_reading(t, worker_num):
    """Make up one reading. Every ~30s a 10s 'stress event' spikes one metric."""
    cycle = int(t // 30) + worker_num          # which metric to spike this window
    stressing = (t % 30) < 10                  # spike for the first 10s of each 30s
    spike = cycle % 4 if stressing else -1     # 0=cpu 1=mem 2=disk 3=net, -1=none

    return {
        "cpu_usage":    round(random.uniform(85, 99) if spike == 0 else random.uniform(1, 15), 1),
        "memory_usage": round(random.uniform(75, 90) if spike == 1 else random.uniform(35, 42), 1),
        "disk_usage":   40.5,                  # disk % barely moves on a real VM either
        "disk_read":    random.uniform(2e7, 3e7) if spike == 2 else random.uniform(0, 5e4),
        "disk_write":   random.uniform(5e6, 2e7) if spike == 2 else random.uniform(0, 7e4),
        "net_send":     random.uniform(1e6, 5e6) if spike == 3 else random.uniform(100, 10000),
        "net_received": random.uniform(1e6, 5e6) if spike == 3 else random.uniform(100, 10000),
    }


def serve(worker_num, port):
    """Accept one client at a time and stream readings to it."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, port))
    server.listen(1)
    print(f"[fake worker {worker_num}] listening on {HOST}:{port}")

    while True:
        client, addr = server.accept()
        if not alive[worker_num]:              # 'dead' worker: hang up immediately
            client.close()
            continue
        print(f"[fake worker {worker_num}] client connected from {addr}")
        try:
            while alive[worker_num]:
                line = json.dumps(fake_reading(time.time(), worker_num)) + "\n"
                client.sendall(line.encode("utf-8"))
                time.sleep(1)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            print(f"[fake worker {worker_num}] client disconnected")
        finally:
            client.close()


if __name__ == "__main__":
    for n, p in PORTS.items():
        threading.Thread(target=serve, args=(n, p), daemon=True).start()

    print("Type 1, 2 or 3 + Enter to kill/revive a worker. Ctrl+C to quit.")
    try:
        while True:
            choice = input().strip()
            if choice.isdigit() and int(choice) in alive:
                n = int(choice)
                alive[n] = not alive[n]
                print(f"[fake worker {n}] is now {'ALIVE' if alive[n] else 'DEAD'}")
    except (KeyboardInterrupt, EOFError):
        print("\nfake workers stopped")
