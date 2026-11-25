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
            return userInputWithEsc(isSingleInputEnabled)
        except (KeyboardInterrupt, SystemExit):
            return "99"
    else:
        userInput = input(inputStr)
        return userInput


def userInputWithEsc(isSingleInputEnabled=False):
    import tty, termios, select, codecs
    fd = sys.stdin.fileno()
    if not os.isatty(fd):
        # piped / scripted input: no terminal to put in cbreak mode
        return input()

    key_mapping = {
        10: 'return',
        13: 'return',
        27: 'esc',
        127: 'backspace',
        8: 'backspace'
    }
    decoder = codecs.getincrementaldecoder('utf-8')(errors='ignore')
    old_settings = termios.tcgetattr(fd)
    user_input = []
    try:
        # TCSANOW: switch immediately and keep keys already typed ahead
        tty.setcbreak(fd, termios.TCSANOW)
        while True:
            b = os.read(fd, 1)
            if not b:                      # EOF
                break
            if b == b'\x1b':
                # escape sequence (arrow keys etc.) arrives as one burst;
                # a lone ESC has nothing following it
                if select.select([fd], [], [], 0.05)[0]:
                    seq = os.read(fd, 1)
                    if seq in (b'[', b'O'):
                        # consume up to the final byte of the sequence
                        while select.select([fd], [], [], 0.05)[0]:
                            c = os.read(fd, 1)
                            if c and (c.isalpha() or c == b'~'):
                                break
                    continue               # ignore the sequence
                user_input.clear()
                user_input.append('99')
                break
            ch = decoder.decode(b)
            if not ch:                     # incomplete multi-byte character
                continue
            this_key = key_mapping.get(ord(ch), ch)
            if this_key == 'return':
                sys.stdout.write("\n")
                break
            if this_key == 'backspace':
                sys.stdout.write("\033[K")
                if len(user_input) > 0:
                    user_input.pop()
            else:
                user_input.append(this_key)
            print(''.join(user_input), end="\r")
            if isSingleInputEnabled:
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ''.join(user_input)
