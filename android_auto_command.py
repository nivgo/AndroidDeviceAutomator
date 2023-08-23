import os
import json
import time
import shutil
import requests
import platform
import subprocess
from os import walk, listdir
from os.path import isfile, join

def run_command(command, directory=None):
    """Execute the given command in a subprocess and return the stdout."""

    # Sleep to give a buffer time before running a command
    time.sleep(1)

    # Running the command and capturing its output
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
    if result.returncode != 0:
        raise ProcessLookupError(f"Error: {result.stderr}" )
    return result.stdout.strip("\n") 

class ADB_Handler():
    """Handles ADB related operations such as checking ADB installation and installing ADB."""

    def adb_exists(self):
        """Check if adb is installed on the system."""
        if not os.path.exists(self.adb_folder):
            print("Failed to find adb")
            return False
        return True
    
   
    def install_adb(self):
        """Installs adb based on the system type using URLs from a downloads.json file."""
        print(f"Detected a {self.system_type} system \n Starting installation....")
        try:
            with open('downloads.json') as json_file:
                systems_urls_dict = json.load(json_file)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in downloads.json")

        if self.system_type not in systems_urls_dict:
            raise ValueError(f"No download URL found for system type: {self.system_type}")

        # Fetching the download URL for the given system type
        url = systems_urls_dict[self.system_type]

        # Requesting the zip file from the given URL
        response = requests.get(url, allow_redirects=True)
        
        if response.status_code != 200:
            raise ConnectionError(f"Failed to download ADB. HTTP Status Code: {response.status_code}")


        # Setting up paths for the zip file and extraction
        zip_file_path = f"{self.adb_folder}.zip"
        unpack_path = os.path.dirname(self.adb_folder)  # unpacking one level up to prevent nesting
        
        # Create the directory if it doesn't exist
        directory_path = os.path.dirname(zip_file_path)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        
        #  Save the file to the directory
        with open(zip_file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        if not os.path.exists(zip_file_path) or not shutil._UNPACK_FORMATS:
            raise FileNotFoundError(f"Invalid or corrupted archive: {zip_file_path}")

        # Informing user about the download location and unpacking the archive
        print(f"File downloaded to: {zip_file_path}")
        shutil.unpack_archive(zip_file_path, unpack_path)

    def __init__(self):
        """Initializes the ADB_Handler class, checks if ADB exists, and installs or starts ADB server as needed."""
        
        # Detecting the system type
        self.system_type = platform.system().lower()
        if self.system_type == "windows":
            self.adb_executable = "adb.exe"
        else:
            self.adb_executable = "adb"
        
        self.adb_folder = os.path.abspath(f"platform_tools_{self.system_type}/platform-tools")
        
        # Check if ADB exists, and if not, install it
        if not self.adb_exists():
            self.install_adb()
                
        # Start the ADB server
        adb_start_command = [os.path.join(self.adb_folder, self.adb_executable), "start-server"]
        run_command(adb_start_command, self.adb_folder)



class Android_commander():
    """Handles the execution of specific commands on an Android device using ADB."""

    def __init__(self,adb_folder):
        """Initializes the Android_commander class, waits for device connection, and runs commands."""
        self.system_type = platform.system().lower()
        self.device_serial = None
        if self.system_type == "windows":
            self.adb_executable = "adb.exe"
        else:
            self.adb_executable = "adb"
        self.adb_folder = adb_folder
                
        # Wait for device connection and run the commands
        self.await_connection()
        self.run_commands()
    
    #Check Cable is connected

    def await_connection(self):
        """Waits until an Android device is detected by adb."""

        adb_wait_for_device = [os.path.join(self.adb_folder, self.adb_executable), "wait-for-device"]
        print("Waiting for the device to be visible to adb...")
        ret = run_command(adb_wait_for_device, self.adb_folder)
        

    def run_commands(self):
        """Loads and runs the adb commands from a predefined JSON file."""
        # Get the directory of the current script
        script_directory = os.path.dirname(os.path.abspath(__file__))

        # Construct the path to commands_file.json relative to the script's location
        commands_file_path = os.path.join(script_directory,'commands_file.json')
        print(f"Loading adb commands....")

        try:
            with open(commands_file_path) as json_file:
                commands_list = json.load(json_file)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in commands_file.json")



        # Build and execute the commands
        commands = self.commands_builder(commands_list)
        for command in commands:
            run_command(command, self.adb_folder)

    def commands_builder(self,commands_list):
        """Builds adb commands based on their type (e.g., SMS, call, general)"""

        commands_queue = []
        for command in commands_list:
            if command['type'] == 'sms':
                commands_queue.extend(self.sms_builder(command['command']))
            elif command['type'] == 'call':
                commands_queue.extend(self.call_builder(command['command']))
            elif command['type'] == 'general':
                commands_queue.extend(self.general_builder(command['command']))
            else:
                raise ValueError("Command type not defined")

        return commands_queue

    # Additional helper methods for processing different types of commands
    def process_additional_commands(self,command_str):
        processed_command = command_str.split(" ")
        if self.system_type == "windows":
            processed_command[0] = os.path.join(self.adb_folder, self.adb_executable)
        return processed_command
    
    def sms_builder(self,command):
        sms_commands_stack = []
        """sms command structure: dtype:command['type'] = "sms" string
        command['command']['content'] = sms string content
        command['command']['phone'] = phone with prefix
        command['command']['additional_commands'] = List[str]"""
        #Handle windows full path requirment
        if self.system_type == "windows":
            initial = os.path.join(self.adb_folder, self.adb_executable)
        else:
            initial = self.adb_executable
        #Handle cases where text has spaces
        if len(command['content'].split(" ")) > 1:
            raise ValueError("Content should have no spaces")
        sms_command = [
        initial, "shell", "am", "start", "-a", "android.intent.action.SENDTO",
        "-d", f"sms:{command['phone']}", "--es", "sms_body", f"{command['content']}"
        ]
        sms_commands_stack.append(sms_command)
        if 'additional_commands' in command:
            for str_command in command['additional_commands']:
                sms_commands_stack.append(self.process_additional_commands(str_command))    
        return sms_commands_stack
    
    def call_builder(self,command):
        
        call_commands_stack = []
        """sms command structure: dtype:command['type'] = "call" string
        command['command']['phone'] = phone with prefix
        command['command']['additional_commands'] = List[str]"""
        if self.system_type == "windows":
            initial = os.path.join(self.adb_folder, self.adb_executable)
        else:
            initial = self.adb_executable
        if not self.device_serial:
            get_serial_command = [initial ,"get-serialno"]
            self.device_serial = run_command(get_serial_command, self.adb_folder)

        call_command = [
        initial, "-s",self.device_serial, "shell", "am", "start",
        "-a", "android.intent.action.CALL", f"tel:{command['phone']}"
        ]
        call_commands_stack.append(call_command)
        if 'additional_commands' in command:
            for str_command in command['additional_commands']:
                call_commands_stack.append(self.process_additional_commands(str_command))    
        return call_commands_stack
    
    def general_builder(self,command):
        
        general_command = []
        """sms command structure: dtype:command['type'] = "general" string
        command['command']['content'] = sms string content
        """
        if self.system_type == "windows":
            initial = os.path.join(self.adb_folder, self.adb_executable)
        else:
            initial = self.adb_executable
        general_command.extend([initial,"shell"])
        general_command.extend(command['content'].split(" "))
        return [general_command]
    
if __name__=="__main__":
    adb_handler = ADB_Handler()
    adb_path = adb_handler.adb_folder
    Android_commander(adb_path)

