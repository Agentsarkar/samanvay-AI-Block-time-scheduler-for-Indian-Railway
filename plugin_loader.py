import importlib
import pkgutil
from pathlib import Path
from fastapi import FastAPI
import routers.plugins

def register_plugins(app: FastAPI):
    """
    Auto-discovers and registers all plugin APIRouters in the routers/plugins directory.
    Teammates can simply drop a python router file inside routers/plugins/ and it will be auto-loaded!
    """
    plugins_dir = Path(routers.plugins.__file__).parent
    loaded_plugins = []

    for _, module_name, _ in pkgutil.iter_modules([str(plugins_dir)]):
        try:
            mod = importlib.import_module(f"routers.plugins.{module_name}")
            if hasattr(mod, "router"):
                app.include_router(mod.router)
                loaded_plugins.append(module_name)
                print(f"[PLUGIN] Automatically registered team plugin: '{module_name}'")
        except Exception as e:
            print(f"[WARN] Failed to load team plugin '{module_name}': {e}")

    return loaded_plugins
