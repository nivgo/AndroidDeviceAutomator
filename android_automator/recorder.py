import argparse
import os
import re
import subprocess
import json
import time
from subprocess import PIPE
from ppadb.client import Client as AdbClient
import ipdb

EVENT_LINE_RE = re.compile(r'\[\s*(\d+\.\d+)\]\s*/dev/input/(event\d+):\s*(\w+)\s*(\w+)\s*(\w+)')
RECONNECTION_RETRIES_LIMIT = 5
RETRIES_SLEEP_TIMER = 20

class AdbEventRecorder:
    # TODO: Support for devices to run multiple at the same time
    def __init__(self, adb, adb_ip="127.0.0.1", adb_port=5037):
        print("Initializing AdbEventRecorder...")
        self.adb_command = adb
        self.adb_client = AdbClient(host=adb_ip, port=adb_port)
        adb_connected_devices = [device for device in self.adb_client.devices()]
        connection_retries = 1
        while not adb_connected_devices:
            if connection_retries < RECONNECTION_RETRIES_LIMIT:
                print(f"Retrying device connection check {connection_retries}...")
                adb_connected_devices = [device for device in self.adb_client.devices()]
                connection_retries += 1
                time.sleep(RETRIES_SLEEP_TIMER)
            else:
                raise ConnectionError("No Device is connected to the adb server, please make sure to connect device before recording")
        print("Device successfully connected!")
        self.adb_shell_command = [adb] + ["shell"]

    def record(self, fpath, eventNum=None):
        print(f"Recording events to {fpath}...")
        record_command = self.adb_shell_command + ['getevent -tq']
        adb = subprocess.Popen(record_command,
                               stdin=PIPE, stdout=PIPE,
                               stderr=PIPE)
        try:
            with open(fpath, 'w') as outputFile:
                while adb.poll() is None:
                    line = adb.stdout.readline().decode('utf-8', 'replace').strip()
                    match = EVENT_LINE_RE.match(line)
                    if match:
                        millis_float, dev, etype, ecode, data = match.groups()
                        millis = int(round(float(millis_float) * 1000))

                        # Filter event
                        if eventNum is not None and 'event%s' % eventNum != dev:
                            continue
                    
                        # Save data in dictionary format for easier conversion to JSON
                        event_data = {
                            "millis": millis,
                            "dev": dev,
                            "etype": int(etype, 16),
                            "ecode": int(ecode, 16),
                            "data": int(data, 16)
                        }
                        # Write the dictionary as a JSON string, followed by a newline
                        outputFile.write(json.dumps(event_data) + '\n')
                        print(f"Recorded event: {event_data}")
                    
                    if not line:
                        break
        except KeyboardInterrupt:
            print("Recording interrupted by the user.")
        finally:
            adb.terminate()
            adb.wait()
            print("Recording completed.")
