import os
import sys

from colorama import Fore

from utils.ods_app_config import readValuefromAppConfig

def userInputWrapper(inputStr,isSingleInputEnabled=False):
    userInput = userInputWithEscWrapper(inputStr,isSingleInputEnabled)
    if userInput == "99":
        exit(0)
    return userInput

# Moving to different branch -f param
def userInputWrapper1(inputStr):
    userInput = ""
    cmd = ''
    cmdlist = list(cmd)
    n = len(sys.argv)
    for i in range(1, n):
        cmdlist.append(sys.argv[i])
    if cmdlist.__contains__("-f"):
        userInput = "y"
    else:
        userInput = userInputWrapper(inputStr)
    print(cmdlist)
    return userInput

#Reverting ESC changes
def userInputWithEscWrapper(inputStr,isSingleInputEnabled=False):
    isEsc = str(readValuefromAppConfig("app.functionality.esc"))
    if(isEsc == 'True'):
        try:
            print(Fore.YELLOW + inputStr)
            keyPressed = userInputWithEsc(isSingleInputEnabled)
            os.system('stty sane')
            os.system("stty erase ^H")
            return keyPressed
        except (KeyboardInterrupt, SystemExit):
            os.system('stty sane')
            os.system("stty erase ^H")
            return "99"
    else:
        userInput = input(inputStr)
        return userInput


def userInputWithEsc(isSingleInputEnabled=False):
    import sys, tty, os, termios
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    # verboseHandle = LogManager(os.path.basename(__file__))

    key_mapping = {
        10: 'return',
        27: 'esc',
        127: 'backspace'
    }
    # if str is not None:
    # verboseHandle.printConsoleWarning(str)
    # print(str)
    user_input = []
    while True:
        b = os.read(sys.stdin.fileno(), 3).decode()
        if len(b) == 3:
            k = ord(b[2])
        else:
            k = ord(b)
        this_key = key_mapping.get(k, chr(k))
        if this_key == 'return':
            sys.stdout.write("\n")
            break
        if this_key == 'esc':
            user_input.clear()
            #            user_input.append('esc')
            user_input.append('99')
            break
        if this_key == 'backspace':
            sys.stdout.write("\033[K")
            if len(user_input) > 0:
                user_input.pop()
        else:
            user_input.append(this_key)
        print(''.join(user_input), end="\r")
        if isSingleInputEnabled:
            break;
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    # print(''.join(user_input))
    return ''.join(user_input)
