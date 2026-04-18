import subprocess
import sys

subprocess.Popen(["cmd.exe", "/c", "run_on_edge.bat"], creationflags=0x00000008, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
