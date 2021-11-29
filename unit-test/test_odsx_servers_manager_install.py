#!/usr/bin/env python3
import  os
import subprocess
import platform

def test_case_1():
    ip = "18.222.185.155"
    current_os = platform.system().lower()
    if current_os == "windows":
        parameter = "-n"
    else:
        parameter = "-c"
    exit_code = os.system(f"ping {parameter} 1 -w2 {ip} > /dev/null 2>&1")
    if(exit_code == 0):
        print("Test-case-1: Pass")
    else:
        print("Test-case-1: Fail")
def test_case_2():
    out = subprocess.Popen(['echo','${GS_HOME}'],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    print(out)
    stdout,stderr = out.communicate()
    print(stdout)
    #3503 my_text_file.txt
    print(stderr)
    stdout.split()[0]
    #None
    pass
def test_case_3():
    pass

if __name__ == '__main__':
    test_case_1()
    #test_case_2()
    #test_case_3()
