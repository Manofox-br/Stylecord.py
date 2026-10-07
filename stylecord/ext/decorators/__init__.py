import importlib, inspect, os, pkgutil

_BLACKLIST = {"__init__"}
__all__ = []

base_path = os.path.dirname(__file__)

def load_modules_recursively(path, package_name):
    for loader, module_name, is_pkg in pkgutil.iter_modules([path]):
        if module_name.startswith("_") or module_name in _BLACKLIST:
            continue

        full_name = f"{package_name}.{module_name}"
        module = importlib.import_module(full_name)

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_"):
                globals()[name] = obj
                __all__.append(name)

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not name.startswith("_"):
                globals()[name] = obj
                __all__.append(name)

        if is_pkg:
            sub_path = os.path.join(path, module_name)
            load_modules_recursively(sub_path, full_name)

load_modules_recursively(base_path, __name__)