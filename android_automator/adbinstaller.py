import os
import time
import platform
import json
import requests
import shutil
import ipdb

from utilities import run_command

REQUEST_RETRIES_LIMIT = 3

class AdbChecker():
    """Handles ADB related operations such as checking ADB installation and installing ADB."""
    
    def __init__(self):
        """Initializes the ADB_Handler class, checks if ADB exists, and installs or starts ADB server as needed."""
        self.system_type = platform.system().lower()
        if self.system_type == "windows":
            self.adb_executable = "adb.exe"
        else:
            self.adb_executable = "adb"
        
        self.adb_folder = os.path.abspath(f"platform_tools_{self.system_type}/platform-tools")
        self.adb_full_path = os.path.join(self.adb_folder, self.adb_executable)

        if not self.adb_exists():
            self.install_adb()
        else:
            print("ADB already exists, ensuring server is started...")

        adb_start_command = [os.path.join(self.adb_folder, self.adb_executable), "start-server"]
        run_command(adb_start_command, self.adb_folder)
        print("ADB server started successfully.")

    def adb_exists(self):
        """Check if adb is installed on the system."""
        if not os.path.exists(self.adb_folder):
            print("Failed to find adb in the system. Installation required.")
            return False
        return True
    
    def install_adb(self):
        """Installs adb based on the system type using URLs from a downloads.json file."""
        print(f"Detected a {self.system_type} system. Starting installation...")
        try:
            with open('downloads.json') as json_file:
                systems_urls_dict = json.load(json_file)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in downloads.json")

        if self.system_type not in systems_urls_dict:
            raise ValueError(f"No download URL found for system type: {self.system_type}")

        url = systems_urls_dict[self.system_type]
        
        retries = 0
        while retries < REQUEST_RETRIES_LIMIT:
            try:
                response = requests.get(url, allow_redirects=True)
                # Break out of the loop if the request was successful
                if response.status_code == 200:
                    break
                else:
                    print(f"Unexpected HTTP status: {response.status_code}. Retrying...")
                    retries += 1
            except requests.exceptions.Timeout:
                print("Request timed out... retrying")
                retries += 1
            except requests.exceptions.RequestException as e:
                # Catastrophic error. Bail.
                raise SystemExit(e)

        # Check if we successfully received a response
        if not response or response.status_code != 200:
            raise ConnectionError(f"Failed to download ADB. HTTP Status Code: {response.status_code if response else 'No Response'}")

        zip_file_path = f"{self.adb_folder}.zip"
        unpack_path = os.path.dirname(self.adb_folder)

        if not os.path.exists(unpack_path):
            os.makedirs(unpack_path)
        
        with open(zip_file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        if not os.path.exists(zip_file_path) or not shutil._UNPACK_FORMATS:
            raise FileNotFoundError(f"Invalid or corrupted archive: {zip_file_path}")

        print(f"File downloaded to: {zip_file_path}. Now extracting...")
        shutil.unpack_archive(zip_file_path, unpack_path)
        print("Extraction completed.")

        # Verify ADB installation after unpacking
        self.verify_adb_installation()

        # Cleanup remove the temp downloaded file
        os.remove(zip_file_path)
        print("Cleanup complete.")
    
    def get_adb_path(self):
        tries = 4
        counter = 0
        while True:
            if self.adb_full_path:
                print("ADB path found successfully.")
                break  # exit the loop if adb_full_path is found
            elif counter == tries:
                raise TimeoutError("ADB checker initialization timeout, couldn't receive ADB full path.")
            else:
                print("Waiting for ADB checker to finish initialization...")
                time.sleep(2)
                counter += 1
        return self.adb_full_path
    
    def verify_adb_installation(self):
        """Verifies that ADB is operational by running a simple command."""
        adb_version_command = [os.path.join(self.adb_folder, self.adb_executable), "version"]
        try:
            output = run_command(adb_version_command, self.adb_folder)
            if "Android Debug Bridge version" not in output:
                raise ValueError("ADB verification failed. Unexpected output from adb version command.")
            else:
                print("ADB installation verified successfully.")
        except Exception as e:
            raise RuntimeError(f"ADB verification failed with error: {e}")
