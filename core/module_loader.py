import importlib
import os
from core.base_module import BaseModule

def discover_modules(modules_dir="modules"):
    """Find all module classes in modules/ folder."""
    modules = []
    if not os.path.exists(modules_dir):
        return modules
    for file in os.listdir(modules_dir):
        if file.endswith("_module.py"):
            module_name = file[:-3]
            try:
                mod = importlib.import_module(f"modules.{module_name}")
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseModule) and attr != BaseModule:
                        modules.append(attr())
            except Exception as e:
                print(f"Failed to load module {file}: {e}")
    return modules
