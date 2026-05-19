import subprocess, time, shutil, os, threading
from pathlib import Path
from typing import List, Optional
from .command_result import CommandResult
from .exceptions import ExecutableNotFoundError
from .logger import get_logger
logger = get_logger()
class Transport:
    def __init__(self, platform_tools_path: Optional[str] = None):
        self.adb_path = self._find_executable('adb', platform_tools_path)
        self.fastboot_path = self._find_executable('fastboot', platform_tools_path)
    def _find_executable(self, name, custom_path):
        if custom_path:
            candidate = Path(custom_path) / name
            if candidate.is_file(): return str(candidate)
            if os.name=='nt' and not candidate.suffix:
                candidate = candidate.with_suffix('.exe')
                if candidate.is_file(): return str(candidate)
        which = shutil.which(name)
        if which: return which
        bundled = Path('./platform-tools') / (name + ('.exe' if os.name=='nt' else ''))
        if bundled.is_file(): return str(bundled)
        raise ExecutableNotFoundError(f'{name} not found.')
    def _run(self, cmd, timeout=30):
        start = time.time()
        proc = None
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', shell=False)
            def kill_proc():
                if proc.poll() is None: proc.terminate()
            timer = threading.Timer(timeout, kill_proc)
            timer.start()
            stdout, stderr = proc.communicate()
            timer.cancel()
            return CommandResult(success=proc.returncode==0, stdout=stdout.strip(), stderr=stderr.strip(), returncode=proc.returncode, duration=time.time()-start, command=' '.join(cmd))
        except Exception as e:
            if proc: proc.terminate()
            return CommandResult(success=False, stdout='', stderr=str(e), returncode=-1, duration=time.time()-start, command=' '.join(cmd))
    def adb(self, args, timeout=30): return self._run([self.adb_path]+args, timeout)
    def fastboot(self, args, timeout=30): return self._run([self.fastboot_path]+args, timeout)
