import json
import subprocess
import time


def shell(command, cwd=None):
    """
    REF: https://stackoverflow.com/a/40139101/212997
    """
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        cwd=cwd,
    )
    # Read stdout from subprocess until the buffer is empty !
    for line in iter(p.stdout.readline, b""):
        line = line.decode("UTF-8")
        line = line.rstrip("\n")
        print(line)
    # This ensures the process has completed, AND sets the 'returncode' attr
    while p.poll() is None:
        time.sleep(0.1)  # Don't waste CPU-cycles
    # Empty STDERR buffer
    err = p.stderr.read()
    if p.returncode != 0:
        # The run_command() function is responsible for logging STDERR
        print("Error: " + str(err))
        return False
    return True


def packer(
    cmd, filename, builder=None, on_error=None, vars=None, yes=False, cwd=None
):
    """
    Executes external packer tool.
    """

    def format_var(i, j):
        if isinstance(j, (list, set)):
            j = json.dumps(list(j))
        return f"{i}={j}"

    cmd_line = [
        "packer",
        cmd,
    ]
    if on_error is not None:
        cmd_line += [f"-on-error={on_error}"]
    if builder is not None:
        cmd_line += [f"-only={builder}.image"]
    if vars is not None:
        cmd_line_vars = []
        for i, j in vars.items():
            cmd_line_vars += ["--var", format_var(i, j)]
        if cmd_line_vars:
            cmd_line += cmd_line_vars

    cmd_line.append(filename)

    if yes:
        return shell(cmd_line, cwd=cwd)
    else:
        print(f"$ {' '.join(cmd_line)}")
        return True
