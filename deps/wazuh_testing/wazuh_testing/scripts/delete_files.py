import os
import argparse
import sys
if sys.platform == 'win32':
    import win32api
    import win32con
    import pywintypes

monitored_directory = os.path.join("C:", os.sep, "stress_test") if sys.platform == 'win32' else os.path.join("/" "stress_test")
if sys.platform == 'win32':
    registry_parser = {
        'HKEY_LOCAL_MACHINE': win32con.HKEY_LOCAL_MACHINE
    }

    registry_class_name = {
        win32con.HKEY_LOCAL_MACHINE: 'HKEY_LOCAL_MACHINE'
    }

    registry_value_type = {
        win32con.REG_SZ: 'REG_SZ'
    }

    REG_SZ = win32con.REG_SZ
    KEY_WOW64_64KEY = win32con.KEY_WOW64_64KEY
    KEY_ALL_ACCESS = win32con.KEY_ALL_ACCESS
    RegOpenKeyEx = win32api.RegOpenKeyEx
    KEY = "HKEY_LOCAL_MACHINE"

testreg = os.path.join('SOFTWARE', 'testreg', 'testreg')
reg_value = 'value_name'


def delete_registry(key, subkey, arch):
    """Delete a registry key.

    Args:
        key (pyHKEY): the key of the registry (HKEY_* constants).
        subkey (str): the subkey (name) of the registry.
        arch (int): architecture of the registry (KEY_WOW64_32KEY or KEY_WOW64_64KEY).
    """
    if sys.platform == 'win32':

        try:
            key_h = win32api.RegOpenKeyEx(key, subkey, 0, win32con.KEY_ALL_ACCESS | arch)
            win32api.RegDeleteTree(key_h, None)
            win32api.RegDeleteKeyEx(key, subkey, samDesired=arch)
        except OSError as e:
            print(f"Couldn't remove registry key {str(os.path.join(registry_class_name[key], subkey))}: {e}")
        except pywintypes.error as e:
            print(f"Couldn't remove registry key {str(os.path.join(registry_class_name[key], subkey))}: {e}")


def main(num_files):
    test_files = [f"Testing{i}.txt" for i in range(1, num_files+1)]

    if sys.platform == 'win32':
        for n_registry in range(1, num_files+1):
            delete_registry(registry_parser[KEY], f'{testreg}{n_registry}', KEY_WOW64_64KEY)
    else:
        if os.path.exists(monitored_directory):
            for filename in test_files:
                os.remove(os.path.join(monitored_directory, filename))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='File deletion script')
    parser.add_argument('--num-files', type=int, default=5, help='Number of files to create')
    args = parser.parse_args()

    main(args.num_files)
