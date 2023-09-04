# AndroidDeviceAutomator

AndroidDeviceAutomator is a python toolkit for automating interactions with Android devices using the Android Debug Bridge. It supports functionalities such as sending SMS, making calls, executing general commands, recording & playing back device events.

## Overview

This Python utility is designed to:

- Detect the operating system and ensure the Android Debug Bridge (ADB) is available.
- Record specific Android device events to a file.
- Play back Android device events from a file, with an option to adjust the playback speed using a slowdown factor.
- Send SMS, make calls, and execute general commands on the connected Android device.

## Setup & Installation

1. **Clone the Repository:**
    ```
    git clone https://github.com/nivgo/AndroidDeviceAutomator.git
    ```

2. **Install the Dependencies:** 
    - Navigate to the directory containing the script.
    ```
    pip install -r requirements.txt
    ```

3. **Setup JSON Files:**  
    - For manual command execution, create a commands_file.json like file in the path Repo\<your_file>.json with commands you wish to run on the Android device.
    - For recording device events, no json setup is needed. The program will save the recorded events as json strings in the specified output file.
      A record file is available as an example.
4. **Phone-side Preparation:**  
    - Ensure your Android device is connected to your computer with "USB Debugging" enabled.
    - Switch the phone to MTP mode.
    - Allow screen prompt to finish the setup.

5. **Run the Script:**  
    ```
    python main.py -a [record/play] -p [path_to_file] [-d device_serials] [-e event_numbers] [--loop] [--slowdown FACTOR]
    ```
    Note:
    - The `--slowdown` argument allows you to slow down the playback speed. For instance, a slowdown factor of 1.0 is real-time, 2.0 is half speed, and so on.
    - Playing records was tested and can be used only for rooted devices.

## Contributing

Suggestions, improvements, or bug reports are always welcome. 
Open an issue to start a discussion!

## Support

Encounter any challenges or issues? Please open an issue on this repository for assistance.
