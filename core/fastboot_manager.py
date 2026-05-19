from typing import Optional, List, Dict
from .transport import Transport
class FastbootManager:
    def __init__(self, transport):
        self.transport = transport
    def devices(self):
        res = self.transport.fastboot(['devices'])
        return [line.split()[0] for line in res.stdout.splitlines() if line.strip()] if res.success else []
    def getvar(self, var, serial=None):
        args = ['getvar', var]
        if serial: args = ['-s', serial] + args
        res = self.transport.fastboot(args)
        combined = res.stdout + '\n' + res.stderr
        for line in combined.splitlines():
            if f'({var}):' in line or f' {var}:' in line:
                parts = line.split(':',1)
                if len(parts)==2: return parts[1].strip()
        return None

    def get_all_vars(self, serial: Optional[str] = None) -> Dict[str, str]:
        args = ["getvar", "all"]
        if serial:
            args = ["-s", serial] + args
        res = self.transport.fastboot(args)
        combined = res.stdout + "\n" + res.stderr
        vars_dict = {}
        for line in combined.splitlines():
            if ":" not in line:
                continue
            line = line.replace("(bootloader)", "").strip()
            key, value = line.split(":", 1)
            vars_dict[key.strip()] = value.strip()
        return vars_dict


    def _run(self, args: List[str], serial: Optional[str] = None, timeout: int = 30):
        full_args = []
        if serial:
            full_args += ["-s", serial]
        full_args += args
        return self.transport.fastboot(full_args, timeout=timeout)
