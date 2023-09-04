import json
import os
import ipdb
import re
import subprocess
import time
import concurrent.futures
from ppadb.client import Client as AdbClient

COMMAND_BUILDER_TIMEOUT = 1



def run_command(command, directory=None):
    """Execute the given command in a subprocess and return the stdout."""
    time.sleep(1)
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"Error: {result.stderr}")
    return result.stdout.strip("\n")

def get_serial(device):
    return device.serial

class AdbPlayer:
    def __init__(self, adb_full_path, adb_ip="127.0.0.1", adb_port=5037, devices=[]):
        print("Initializing ADB Player...")
        self.devices_list = devices
        self.adb_client = AdbClient(host=adb_ip, port=adb_port)
        self.adb_folder = os.path.dirname(adb_full_path)
        self.adb_full_path = adb_full_path

        adb_connected_devices = [device for device in self.adb_client.devices()]
        if not self.devices_list:
            print("No devices provided. Using all connected devices.")
            self.adb_controlled_devices = adb_connected_devices
        else:
            self.adb_controlled_devices = [device for device in adb_connected_devices if device.serial in self.devices_list]
            if not self.adb_controlled_devices:
                raise ValueError(f"None of the specified devices is connected to the ADB server")
        print(f"Devices under control: {len(self.adb_controlled_devices)}")
    def send_adb_command(self, device, cmd, sleep_interval=None):
        if sleep_interval is not None and sleep_interval != 0.0:
            time.sleep(sleep_interval)
        cmd_str = " ".join(cmd)
        device.shell(cmd_str)
        print(f"Sent command to {device.serial}: {cmd_str}")
        
    def multi_threaded_play_command(self, cmd, sleep_interval=None):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.send_adb_command, self.adb_controlled_devices, [cmd] * len(self.adb_controlled_devices),[sleep_interval]* len(self.adb_controlled_devices))

    @staticmethod
    def check_commands_type(fpath):
        print(f"Checking command type for file: {fpath}")
        if fpath.endswith('.json'):
            with open(fpath, 'r') as file:
                line = file.readline().strip()
                # Check if the file starts with a JSON object (for NDJSON support)
                if line.startswith('{'):
                    return "timed_commands"
            return "builder_commands"
        else:
            raise ValueError("Unsupported file type. Refer to README for required types.")

    def play(self, fpath, repeat=False, replay_slowdown_factor=4.0):
        commands_type = self.check_commands_type(fpath)
        initial_ts = None

        if commands_type == "builder_commands":
            print("Executing builder commands...")
            commands_builder_obj = AndroidCommandsBuilder(self.adb_full_path)
            commands_list = commands_builder_obj.built_commands
            while True:
                for command in commands_list:
                    self.multi_threaded_play_command(command,COMMAND_BUILDER_TIMEOUT * replay_slowdown_factor)

                if not repeat:
                    break
        else:
            print(f"""Sending data to the following devices-{list(map(get_serial,self.adb_controlled_devices))}""")
            while True:
                last_ts = None
                initial_ts = None
                with open(fpath) as fp:
                    for line in fp:
                        # Parse the NDJSON line
                        event_data = json.loads(line.strip())
                        ts = event_data["millis"]
                        dev = "/dev/input/" + event_data["dev"]
                        etype, ecode, data = event_data["etype"], event_data["ecode"], event_data["data"]

                        if initial_ts is None:
                            initial_ts = ts
                            relative_ts = 0
                        else:
                            relative_ts = replay_slowdown_factor*((ts - last_ts)/1000)
                            
                        last_ts = ts
                        cmd = ['sendevent', dev, str(etype), str(ecode), str(data)]
                        self.multi_threaded_play_command(cmd, relative_ts)
                if not repeat:
                    break
        print("Playback complete.")
        return 0


import os
import json


class AndroidCommandsBuilder:
    """Handles the execution of specific commands on an Android device using ADB."""

    def __init__(self, adb_full_path):
        """Initialize the AndroidCommandsBuilder class and build commands."""
        self.device_serial = None
        self.adb_folder = os.path.dirname(adb_full_path)
        self.adb_full_path = adb_full_path
        self.built_commands = self._build_commands()

    def _build_commands(self):
        """Load and execute the adb commands from a predefined JSON file."""
        script_directory = os.path.dirname(os.path.abspath(__file__))
        commands_file_path = os.path.join(script_directory, 'commands_file.json')
        print("Loading adb commands...")

        try:
            with open(commands_file_path) as json_file:
                commands_list = json.load(json_file)
        except ValueError:
            raise ValueError("Invalid JSON format in commands_file.json")
        return self._commands_builder(commands_list)

    def _commands_builder(self, commands_list):
        """Build adb commands based on their type (e.g., SMS, call, general)."""
        commands_queue = []

        for command in commands_list:
            command_type = command['type']
            if command_type == 'sms':
                commands_queue.extend(self._sms_builder(command['command']))
            elif command_type == 'call':
                commands_queue.extend(self._call_builder(command['command']))
            elif command_type == 'general':
                commands_queue.extend(self._general_builder(command['command']))
            else:
                raise ValueError("Command type not defined")

        return commands_queue

    def _process_additional_commands(self, command_str):
        """Process and return the additional commands."""
        processed_command = command_str.split()
        processed_command[0] = self.adb_full_path
        return processed_command

    def _sms_builder(self, command):
        """Build SMS commands based on the given command structure.
        
        command structure:
        type: "sms" string
        command:
            content: SMS string content (spaces allowed)
            phone: phone number with prefix
            additional_commands: list of string commands
        """
        sms_commands_stack = []

        # Encapsulate the content in double quotes to handle spaces
        sms_content = f'"{command["content"]}"'

        sms_command = [
            "am", "start", "-a", "android.intent.action.SENDTO",
            "-d", f"sms:{command['phone']}", "--es", "sms_body", sms_content
        ]
        sms_commands_stack.append(sms_command)

        if 'additional_commands' in command:
            for str_command in command['additional_commands']:
                sms_commands_stack.append(self._process_additional_commands(str_command))

        return sms_commands_stack


    def _call_builder(self, command):
        """Build call commands based on the given command structure.
        
        command structure:
        type: "call" string
        command:
            phone: phone number with prefix
            additional_commands: list of string commands
        """
        call_commands_stack = []

        call_command = [
            "am", "start", "-a", "android.intent.action.CALL", f"tel:{command['phone']}"
        ]
        call_commands_stack.append(call_command)

        if 'additional_commands' in command:
            for str_command in command['additional_commands']:
                call_commands_stack.append(self._process_additional_commands(str_command))

        return call_commands_stack

    def _general_builder(self, command):
        """Build general commands based on the given command structure.
        
        command structure:
        type: "general" string
        command:
            content: general ADB command string
        """
        return command['content'].split()


