import os


def helpUsage(path):
    filePath = "../csv/" + path + "_help.txt"
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    abs_file_path = os.path.join(script_dir, filePath)
    if (os.path.isfile(abs_file_path)):
        f = open(abs_file_path, "r")
        print(f.read())
        optional_parameter_help = "../csv/optional_parameter_help.txt"
        abs_file_path = os.path.join(script_dir, optional_parameter_help)
        f = open(abs_file_path, "r")
        print(f.read())
    else:
        print("Not valid help command")

#help("menu_settings_snapshot")
#help("menu_settings")
#help1("menu")
