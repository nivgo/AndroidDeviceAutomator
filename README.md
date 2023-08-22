# AndroidDeviceAutomator
AndroidDeviceAutomator: A Python-based toolkit for automating and executing a series of ADB commands on Android devices. Supports SMS, call functionalities, and general command execution.

Overview

This Python script is a utility designed to interact with Android devices using the Android Debug Bridge (ADB). It provides features to detect the operating system, install ADB if not available, and execute various commands on a connected Android device.

Setup & Installation
1.Clone the Repository:
    git clone YOUR_REPOSITORY_LINK_HERE


2.Install the Dependencies: 
    Navigate to the directory containing the script and run:
    pip install -r requirements.txt


3.Setup JSON Files:
    Set up a commands_file.json at the path Repo\commands_file.json containing commands you intend to run on the Android device.

4.Phone side preparation:
    Connect Your Android Device: Make sure your Android device is connected to your computer with "USB Debugging" enabled.
    Make sure the phone is in MTP mode.
    Follow any on-screen prompts to complete the process.

5.Run the Script:
    Navigate to the directory containing the script and run:
    python android_auto_command.py


Contributing
If you have suggestions for how this script could be improved, or want to report a bug, open an issue! We'd love all and any contributions.

For direct contributions:

    Fork the repository.
    Clone your fork: git clone YOUR_FORK_LINK_HERE
    Make your changes.
    Submit a pull request.

Support
    If you run into any problems or issues, please open an issue on this repository.


