import os
import time
import json
import psutil
from pathlib import Path

PIPELINE_PATH = "/tmp/hardware_stats.fifo"

def get_hardware_stats():
        io_start = psutil.disk_io_counters()
        net_start = psutil.net_io_counters() # split like disk_io into sent and recieve, we will send seperate and allow recombination later
        # at the client or api side
        start_time = time.time()

        time.sleep(0.75) # Wait for 3/4 a second to collect data

        io_end = psutil.disk_io_counters()
        net_end = psutil.net_io_counters()
        end_time = time.time()

        elapsed_time = end_time - start_time

        #Disc

        read_per_second = (io_end.read_bytes - io_start.read_bytes) / elapsed_time
        write_per_second = (io_end.write_bytes - io_start.write_bytes) / elapsed_time

        #Network

        sent_per_second = (net_end.bytes_sent - net_start.bytes_sent) / elapsed_time
        received_per_second = (net_end.bytes_recv - net_start.bytes_recv) / elapsed_time

        return {
                "cpu_usage" : psutil.cpu_percent(interval=None),
                "memory_usage" : psutil.virtual_memory().percent,
                "disk_usage" : psutil.disk_usage('/').percent,
                "disk_read" : read_per_second,
                "disk_write" : write_per_second,
                "net_send" : sent_per_second,
                "net_received" : received_per_second
                }

def main():
        pipeline = Path(PIPELINE_PATH)
        # create the named pipe if it doesn't exist
        if not pipeline.exists():
                print(f"Creating named pipe at {PIPELINE_PATH}")
                os.mkfifo(PIPELINE_PATH)
        elif not pipeline.is_fifo():
                raise RuntimeError(f"Path {PIPELINE_PATH} exists but is not a named pipeline")

        print(f"Streaming data to {PIPELINE_PATH}. Waiting for a reader")

        while True:
                try: # used to catch overall errors and allow the user to shut down the python script as needed with the keyboard interupt
                        with open(PIPELINE_PATH, "w") as pipeline:
                                print("Reader Connected. Streaming Data...")
                                while True:

                                        stats = get_hardware_stats()

                                        json_data = json.dumps(stats) + "\n"

                                        pipeline.write(json_data)
                                        pipeline.flush()
                                        time.sleep(0.25)

                except BrokenPipeError:
                        #reader closed the connection
                        print("Reader closed the connection. Waiting for a new reader")
                        time.sleep(1)
                except KeyboardInterrupt:
                        #user shutdown of python script
                        print("\nStopping Measuring Sequence")
                        break

if __name__ == "__main__":
        ## Starts up script and initalizes cpu_percent once ahead of time to initalize the counter
        psutil.cpu_percent(interval=None)
        main()