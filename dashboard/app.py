import json
import socket
import threading
import time
from collections import deque
from datetime import datetime

from dash import Dash, html, dcc, Input, Output

# our primary workers
REAL_WORKERS = {
    "stress-worker-1": ("34.122.20.176", 5000),
    "stress-worker-2": ("34.31.209.66", 5000),
    "stress-worker-3": ("34.70.180.38", 5000),
}

WORKERS = REAL_WORKERS

HISTORY_LEN = 60 # time history
READ_TIMEOUT = 5
RECONNECT_DELAY = 3

history = {name: deque(maxlen=HISTORY_LEN) for name in WORKERS}
status = {name: "connecting" for name in WORKERS}
lock = threading.Lock()


def listen(name, host, port):
    while True:
        try:
            with socket.create_connection((host, port), timeout=READ_TIMEOUT) as sock:
                for line in sock.makefile("r", encoding="utf-8"):
                    reading = json.loads(line)
                    reading["time"] = datetime.now()
                    with lock:
                        history[name].append(reading)
                        status[name] = "online"
            with lock:
                status[name] = "offline"
        except (OSError, ValueError):
            with lock:
                status[name] = "offline"
        time.sleep(RECONNECT_DELAY)


def start_collectors():
    for name, (host, port) in WORKERS.items():
        threading.Thread(target=listen, args=(name, host, port), daemon=True).start()


def get_cpu(r):
    return r["cpu_usage"]

def get_mem(r):
    return r["memory_usage"]

def get_disk(r):
    return r["disk_usage"]

def get_io(r):
    return (r["disk_read"] + r["disk_write"]) / 1024

def get_net(r):
    return (r["net_send"] + r["net_received"]) / 1024


# Primary graph skeleton
def make_figure(title, get_value, y_range, threshold):
    lines = []
    for name in WORKERS:
        with lock:
            readings = list(history[name])
        lines.append({
            "x": [r["time"] for r in readings],
            "y": [get_value(r) for r in readings],
            "type": "scatter",
            "mode": "lines",
            "name": name,
        })
    if y_range:
        yaxis = {"range": y_range}
    else:
        yaxis = {"rangemode": "tozero"}
    shapes = []
    if threshold is not None:
        shapes.append({
            "type": "line", "xref": "paper", "x0": 0, "x1": 1,
            "y0": threshold, "y1": threshold,
            "line": {"color": "red", "dash": "dash"},
        })
    return {
        "data": lines,
        "layout": {"title": {"text": title}, "yaxis": yaxis, "height": 300, "shapes": shapes},
    }


def check(label, get_value, threshold, unit, alerts):
    if threshold is None:
        return
    for name in WORKERS:
        with lock:
            if status[name] != "online" or not history[name]:
                continue
            latest = history[name][-1]
        value = get_value(latest)
        if value > threshold:
            alerts.append(f"{name}: {label} {value:.1f}{unit} is above {threshold}{unit}")

# Layout
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Group 2 Observability Dashboard"),
    html.Div(id="status"),
    html.Div(id="alerts"),

    html.Label("CPU alert above (%)"),
    dcc.Slider(id="cpu-threshold", min=0, max=100, step=1, value=80),
    dcc.Graph(id="cpu-graph"),

    html.Label("Memory alert above (%)"),
    dcc.Slider(id="mem-threshold", min=0, max=100, step=1, value=80),
    dcc.Graph(id="mem-graph"),

    html.Label("Disk usage alert above (%)"),
    dcc.Slider(id="disk-threshold", min=0, max=100, step=1, value=90),
    dcc.Graph(id="disk-graph"),

    html.Label("Disk I/O alert above (KB/s) "),
    dcc.Input(id="io-threshold", type="number", min=0, value=8000, debounce=True),
    dcc.Graph(id="io-graph"),

    html.Label("Network alert above (KB/s) "),
    dcc.Input(id="net-threshold", type="number", min=0, value=80, debounce=True),
    dcc.Graph(id="net-graph"),

    dcc.Interval(id="timer", interval=1000),
])

#live dashboard

@app.callback(
    Output("cpu-graph", "figure"),
    Output("mem-graph", "figure"),
    Output("disk-graph", "figure"),
    Output("io-graph", "figure"),
    Output("net-graph", "figure"),
    Output("alerts", "children"),
    Output("alerts", "style"),
    Output("status", "children"),
    Input("timer", "n_intervals"),
    Input("cpu-threshold", "value"),
    Input("mem-threshold", "value"),
    Input("disk-threshold", "value"),
    Input("io-threshold", "value"),
    Input("net-threshold", "value"),
)
def update_graphs(n, cpu_t, mem_t, disk_t, io_t, net_t):
    alerts = []
    check("CPU",      get_cpu,  cpu_t,  "%",     alerts)
    check("Memory",   get_mem,  mem_t,  "%",     alerts)
    check("Disk",     get_disk, disk_t, "%",     alerts)
    check("Disk I/O", get_io,   io_t,   " KB/s", alerts)
    check("Network",  get_net,  net_t,  " KB/s", alerts)

    if alerts:
        banner = [html.Div("⚠ " + a) for a in alerts]
        style = {"backgroundColor": "#d62728", "color": "white", "padding": "10px", "fontWeight": "bold"}
    else:
        banner = "All metrics normal"
        style = {"backgroundColor": "#2ca02c", "color": "white", "padding": "10px", "fontWeight": "bold"}

    status_line = []
    for name in WORKERS:
        with lock:
            state = status[name]
        color = "green" if state == "online" else "gray"
        status_line.append(html.Span(f"{name}: {state.upper()}   ",
                                     style={"color": color, "fontWeight": "bold", "marginRight": "20px"}))

    return (
        make_figure("CPU Usage (%)",    get_cpu,  [0, 100], cpu_t),
        make_figure("Memory Usage (%)", get_mem,  [0, 100], mem_t),
        make_figure("Disk Usage (%)",   get_disk, [0, 100], disk_t),
        make_figure("Disk I/O (KB/s)",  get_io,   None,     io_t),
        make_figure("Network (KB/s)",   get_net,  None,     net_t),
        banner,
        style,
        status_line,
    )

if __name__ == "__main__":
    start_collectors()
    app.run(debug=True, use_reloader=False)