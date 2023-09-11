import argparse
import os
import sys
import subprocess

import adbinstaller
import player
import recorder


def main(*args):
    def list_of_items(arg):
        return arg.split(',')

    parser = argparse.ArgumentParser(
        description='Record or play Android device events across multiple devices.')
    parser.add_argument('-d', '--devices', type=list_of_items,
                        help='List of participating devices serials, separated by commas (e.g., a1sac7,a1sabr3,l1ds4asd).')
    parser.add_argument('-e', '--events', type=list_of_items,
                        help='List of event numbers to record or play, separated by commas (e.g., 1,2,3).')
    parser.add_argument('-p', '--path', type=str, required=True,
                        help='Path to the file where events will be recorded or from which events will be played.')
    parser.add_argument('-l', '--loop', action='store_true',
                        help='Loop the playback of the events continuously.')
    parser.add_argument('-a', '--activity', choices=['record', 'play'], required=True,
                        help='Choose whether to record or play events.')
    parser.add_argument('-s', '--slowdown', type=float, default=1.0,
                        help='Factor by which to slow down the playback. 1.0 is real-time, 2.0 is half speed, etc.')

    args = parser.parse_args()

    devices_list = [] if not args.devices else args.devices

    path = args.path

    if not os.path.isfile(path) and args.activity == "play":
        print(f"Error: File does not exist in the location {path}!")
        raise SystemError(
            f"Verify that the record/play file exists in the location specified {path}")

    matching_events = args.events
    print("Verifying ADB is installed on the system...")
    
    adb_installer = adbinstaller.AdbChecker()
    adb_full_path = adb_installer.get_adb_path()
    print(f"ADB Path found at: {adb_full_path}")

    if args.activity == "record":
        adb_recorder = recorder.AdbEventRecorder(adb=adb_full_path)
        adb_recorder.record(path, matching_events)
    else:
        if args.loop:
            print("Playback will loop continuously.")
        adb_player = player.AdbExecutor(adb_full_path=path, adb_ip="127.0.0.1", adb_port=5037, devices=devices_list)
        adb_player.execute_commands(path, repeat=args.loop, replay_slowdown_factor=args.slowdown)


if __name__ == '__main__':
    main(*sys.argv)
