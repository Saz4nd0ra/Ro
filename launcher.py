from __future__ import print_function
import os
import sys
import subprocess
try:
    import urllib.request                   
    from importlib.util import find_spec    
except ImportError:
    pass
import platform
import webbrowser
import hashlib
import argparse
import shutil
import stat
import time
try:
    import pip
except ImportError:
    pip = None
REQS_DIR = "lib"
sys.path.insert(0, REQS_DIR)
REQS_TXT = "requirements.txt"
REQS_NO_AUDIO_TXT = "requirements_no_audio.txt"

INTRO = ("=============\n"
         "Ro - Launcher\n"
         "=============\n")

IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_64BIT = platform.machine().endswith("64")
INTERACTIVE_MODE = not len(sys.argv) > 1  # CLI flags = non-interactive
PYTHON_OK = sys.version_info >= (3, 8)


def parse_cli_arguments():
    parser = argparse.ArgumentParser(description="Ro's launcher")
    parser.add_argument("--start", "-s",
                        help="Starts Ro",
                        action="store_true")
    parser.add_argument("--auto-restart",
                        help="Autorestarts Ro in case of issues",
                        action="store_true")
    parser.add_argument("--update-ro",
                        help="Updates Ro (git)",
                        action="store_true")
    parser.add_argument("--update-reqs",
                        help="Updates requirements (w/ audio)",
                        action="store_true")
    parser.add_argument("--update-reqs-no-audio",
                        help="Updates requirements (w/o audio)",
                        action="store_true")
    parser.add_argument("--repair",
                        help="Issues a git reset --hard",
                        action="store_true")
    return parser.parse_args()


def install_reqs(audio):
    remove_reqs_readonly()
    interpreter = sys.executable

    if interpreter is None:
        print("Python interpreter not found.")
        return

    txt = REQS_TXT if audio else REQS_NO_AUDIO_TXT

    args = [
        interpreter, "-m",
        "pip", "install",
        "--upgrade",
        "--target", REQS_DIR,
        "-r", txt
    ]

    if IS_MAC: # --target is a problem on Homebrew. See PR #552
        args.remove("--target")
        args.remove(REQS_DIR)

    code = subprocess.call(args)

    if code == 0:
        print("\nRequirements setup completed.")
    else:
        print("\nAn error occurro and the requirements setup might "
              "not be completed. Consult the docs.\n")


def update_pip():
    interpreter = sys.executable

    if interpreter is None:
        print("Python interpreter not found.")
        return

    args = [
        interpreter, "-m",
        "pip", "install",
        "--upgrade", "pip"
    ]

    code = subprocess.call(args)

    if code == 0:
        print("\nPip has been updated.")
    else:
        print("\nAn error occurro and pip might not have been updated.")


def update_ro():
    try:
        code = subprocess.call(("git", "pull", "--ff-only"))
    except FileNotFoundError:
        print("\nError: Git not found. It's either not installed or not in "
              "the PATH environment variable like requested in the guide.")
        return
    if code == 0:
        print("\nRo has been updated")
    else:
        print("\nRo could not update properly. If this is caused by edits "
              "you have made to the code you can try the repair option from "
              "the Maintenance submenu")


def reset_ro(config=False, git_reset=False):
    if config:
        try:
            os.remove("config/options.ini")
            shutil.copyfile("config/example_options.ini", "config/options.ini")
            print("config has been wiped.")
        except FileNotFoundError:
            pass
        except Exception as e:
            print("An error occurred when trying to wipe the config: "
                  "{}".format(e))

    if git_reset:
        code = subprocess.call(("git", "reset", "--hard"))
        if code == 0:
            print("Ro has been restored to the last local commit.")
        else:
            print("The repair has failed.")


def verify_requirements():
    sys.path_importer_cache = {}
    basic = find_spec("discord")
    audio = find_spec("nacl")
    if not basic:                
        return None
    elif not audio:
        return False
    else:
        return True


def is_git_installed():
    try:
        subprocess.call(["git", "--version"], stdout=subprocess.DEVNULL,
                                              stdin =subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return False
    else:
        return True


def requirements_menu():
    clear_screen()
    while True:
        print(INTRO)
        print("Main requirements:\n")
        print("1. Install basic + audio requirements (recommended)")
        print("2. Install basic requirements")
        print("\nq Go back")
        choice = user_choice()
        if choice == "1":
            install_reqs(audio=True)
            wait()
        elif choice == "2":
            install_reqs(audio=False)
            wait()
        elif choice == "q":
            break
        clear_screen()


def update_menu():
    clear_screen()
    while True:
        print(INTRO)
        reqs = verify_requirements()
        if reqs is None:
            status = "No requirements installed"
        elif reqs is False:
            status = "Basic requirements installed (no audio)"
        else:
            status = "Basic + audio requirements installed"
        print("Status: " + status + "\n")
        print("Update:\n")
        print("Ro:")
        print("1. Update Ro + requirements (recommended)")
        print("2. Update Ro")
        print("3. Update requirements")
        print("\nOthers:")
        print("4. Update pip (might require admin privileges)")
        print("\nq Go back")
        choice = user_choice()
        if choice == "1":
            update_ro()
            print("Updating requirements...")
            reqs = verify_requirements()
            if reqs is not None:
                install_reqs(audio=reqs)
            else:
                print("The requirements haven't been installed yet.")
            wait()
        elif choice == "2":
            update_ro()
            wait()
        elif choice == "3":
            reqs = verify_requirements()
            if reqs is not None:
                install_reqs(audio=reqs)
            else:
                print("The requirements haven't been installed yet.")
            wait()
        elif choice == "4":
            update_pip()
            wait()
        elif choice == "q":
            break
        clear_screen()


def maintenance_menu():
    clear_screen()
    while True:
        print(INTRO)
        print("Maintenance:\n")
        print("1. Repair Ro (discards code changes, keeps data intact)")
        print("2. Wipe config")
        print("3. Factory reset")
        print("\nq. Go back")
        choice = user_choice()
        if choice == "1":
            print("Any code modification you have made will be lost. Data/"
                  "non-default cogs will be left intact. Are you sure?")
            if user_pick_yes_no():
                reset_ro(git_reset=True)
                wait()
        elif choice == "2":
            print("Are you sure that you want to wipe the config?")
            if user_pick_yes_no():
                reset_ro(config=True)
                wait()
        elif choice == "3":
            print("Are you sure? This will wipe ALL your Ro's installation "
                  "data.\nYou'll lose all your settings, cogs and any "
                  "modification you have made.\nThere is no going back.")
            if user_pick_yes_no():
                reset_ro(config=True, git_reset=True)
                wait()
        elif choice == "q":
            break
        clear_screen()


def run_ro(autorestart):
    interpreter = sys.executable

    if interpreter is None: # This should never happen
        raise RuntimeError("Couldn't find Python's interpreter")

    if verify_requirements() is None:
        print("You don't have the requirements to start Ro. "
              "Install them from the launcher.")
        if not INTERACTIVE_MODE:
            exit(1)

    cmd = (interpreter, "run.py")

    while True:
        try:
            code = subprocess.call(cmd)
        except KeyboardInterrupt:
            code = 0
            break
        else:
            if code == 0:
                break
            elif code == 26:
                print("Restarting Ro...")
                continue
            else:
                if not autorestart:
                    break

    print("Ro has been terminated. Exit code: %d" % code)

    if INTERACTIVE_MODE:
        wait()


def clear_screen():
    if IS_WINDOWS:
        os.system("cls")
    else:
        os.system("clear")


def wait():
    if INTERACTIVE_MODE:
        input("Press enter to continue.")


def user_choice():
    return input("> ").lower().strip()


def user_pick_yes_no():
    choice = None
    yes = ("yes", "y")
    no = ("no", "n")
    while choice not in yes and choice not in no:
        choice = input("Yes/No > ").lower().strip()
    return choice in yes


def remove_readonly(func, path, excinfo):
    os.chmod(path, 0o755)
    func(path)


def remove_reqs_readonly():
    """Workaround for issue #569"""
    if not os.path.isdir(REQS_DIR):
        return
    os.chmod(REQS_DIR, 0o755)
    for root, dirs, files in os.walk(REQS_DIR):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            os.chmod(os.path.join(root, f), 0o755)


def calculate_md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def main():
    print("Verifying git installation...")
    has_git = is_git_installed()
    is_git_installation = os.path.isdir(".git")
    if IS_WINDOWS:
        os.system("TITLE Ro Discord Bot - Launcher")
    clear_screen()

    while True:
        print(INTRO)

        if not is_git_installation:
            print("WARNING: It doesn't look like Ro has been "
                  "installed with git.\nThis means that you won't "
                  "be able to update and some features won't be working.\n"
                  "A reinstallation is recommended.")

        if not has_git:
            print("WARNING: Git not found. This means that it's either not "
                  "installed or not in the PATH environment variable like "
                  "requested in the guide.\n")

        print("1. Run Ro /w autorestart in case of issues")
        print("2. Run Ro")
        print("3. Update")
        print("4. Install requirements")
        print("5. Maintenance (repair, reset...)")
        print("\nq Quit")
        choice = user_choice()
        if choice == "1":
            run_ro(autorestart=True)
        elif choice == "2":
            run_ro(autorestart=False)
        elif choice == "3":
            update_menu()
        elif choice == "4":
            requirements_menu()
        elif choice == "5":
            maintenance_menu()
        elif choice == "q":
            break
        clear_screen()

args = parse_cli_arguments()

if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    # Sets current directory to the script's
    os.chdir(dirname)
    if not PYTHON_OK:
        print("Ro needs Python 3.8 or superior. Install the requiro "
              "version.\nPress enter to continue.")
        if INTERACTIVE_MODE:
            wait()
        exit(1)
    if pip is None:
        print("Ro cannot work without the pip module. Please make sure to "
              "install Python without unchecking any option during the setup")
        wait()
        exit(1)
    if args.repair:
        reset_ro(git_reset=True)
    if args.update_ro:
        update_ro()
    if args.update_reqs:
        install_reqs(audio=True)
    elif args.update_reqs_no_audio:
        install_reqs(audio=False)
    if INTERACTIVE_MODE:
        main()
    elif args.start:
        print("Starting Ro...")
        run_ro(autorestart=args.auto_restart)
