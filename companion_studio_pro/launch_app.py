from __future__ import annotations

import os, socket, subprocess, sys, time, webbrowser
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CREATE_NO_WINDOW=0x08000000 if os.name=="nt" else 0

def free_port(port:int):
    with socket.socket() as sock:
        try: sock.bind(("127.0.0.1",port)); return True
        except OSError: return False

def wait_port(port:int,seconds=45):
    end=time.time()+seconds
    while time.time()<end:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1",port))==0:return True
        time.sleep(.3)
    return False

def main():
    py=ROOT/(".venv/Scripts/python.exe" if os.name=="nt" else ".venv/bin/python")
    if not py.exists():
        print("Run full_install.py first."); input("Press Enter to close…"); return 1
    backend=None; frontend=None
    if free_port(8765): backend=subprocess.Popen([str(py),"-m","uvicorn","local_api.main:app","--host","127.0.0.1","--port","8765"],cwd=ROOT,creationflags=CREATE_NO_WINDOW)
    npm="npm.cmd" if os.name=="nt" else "npm"
    if free_port(3000): frontend=subprocess.Popen([npm,"run","dev","--","--host","127.0.0.1","--port","3000"],cwd=ROOT,creationflags=CREATE_NO_WINDOW)
    if wait_port(3000): webbrowser.open("http://127.0.0.1:3000")
    else: print("The interface did not start. Run npm run dev to inspect the error.")
    try:
        while True: time.sleep(2)
    except KeyboardInterrupt:
        for proc in (frontend,backend):
            if proc: proc.terminate()
    return 0

if __name__=="__main__": raise SystemExit(main())

