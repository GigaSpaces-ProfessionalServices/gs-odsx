def update_app_config_file(linePatternToReplace, inputMsg):
    file_name = "app.config"
    lines = open(file_name, 'r').readlines()
    lineNo = -1
    for line in lines:
        lineNo = lineNo + 1
        if line.startswith("#"):
            continue
        elif line.__contains__(linePatternToReplace):
            break
    selectedValue = str(input(
        inputMsg + " (current " + lines[lineNo].replace("\n", "").replace(linePatternToReplace + "=",
                                                                          "") + ") : "))
    if (selectedValue != ""):
        lines[lineNo] = ""
        lines[lineNo] = linePatternToReplace + "=" + selectedValue + "\n"
    out = open(file_name, 'w')
    out.writelines(lines)
    out.close()