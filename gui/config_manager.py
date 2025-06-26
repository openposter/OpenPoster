import json
import os
from pathlib import Path
from typing import Any, Dict, List

class ConfigManager:
    config_dir: str
    config_file: str
    default_config: Dict[str, Any]
    config: Dict[str, Any]

    def __init__(self):
        self.config_dir = os.path.join(Path.home(), ".openposter")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.default_config: Dict[str, Any] = {
            "ui": {
                "splitters": {
                    "mainSplitter": [],
                    "layersSplitter": []
                },
                "window": {
                    "size": [1200, 800],
                    "position": [100, 100],
                    "maximized": False,
                    "remember_size": True
                },
                "langu": "en_US",
                "filename_display_mode": "Toggle",
                "theme": "system"
            },
            "shortcuts": {
                "export": "Ctrl+E",
                "zoom_in": "Ctrl+=",
                "zoom_out": "Ctrl+-",
                "close_window": "Ctrl+W"
            },
            "nugget": {
                "exe_path": "",
                "open_after_export": False
            },
            "language": "en_US"
        }
        self.config: Dict[str, Any] = {}
        self.ensure_config_dir()
        self.load_config()
    
    def ensure_config_dir(self) -> None:
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def load_config(self) -> None:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                    
                self.ensure_default_keys()
            else:
                self.config = self.default_config.copy()
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.default_config.copy()
    
    def ensure_default_keys(self) -> None:
        def update_nested_dict(d: Dict[str, Any], u: Dict[str, Any]) -> None:
            for k, v in u.items():
                if k not in d:
                    d[k] = v
                elif isinstance(v, dict) and isinstance(d[k], dict):
                    update_nested_dict(d[k], v)
        
        update_nested_dict(self.config, self.default_config)
    
    def save_config(self) -> None:
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_splitter_sizes(self, splitter_name: str) -> List[Any]:
        try:
            return self.config.get("ui", {}).get("splitters", {}).get(splitter_name, [])
        except Exception:
            return []
    
    def save_splitter_sizes(self, splitter_name: str, sizes: List[Any]) -> None:
        if "ui" not in self.config:
            self.config["ui"] = {}
        if "splitters" not in self.config["ui"]:
            self.config["ui"]["splitters"] = {}
        
        self.config["ui"]["splitters"][splitter_name] = sizes
        self.save_config()
    
    def get_window_geometry(self) -> Dict[str, Any]:
        try:
            window = self.config.get("ui", {}).get("window", {})
            return {
                "size": window.get("size", self.default_config["ui"]["window"]["size"]),
                "position": window.get("position", self.default_config["ui"]["window"]["position"]),
                "maximized": window.get("maximized", self.default_config["ui"]["window"]["maximized"]),
                "remember_size": window.get("remember_size", self.default_config["ui"]["window"]["remember_size"])
            }
        except Exception:
            return {
                "size": self.default_config["ui"]["window"]["size"],
                "position": self.default_config["ui"]["window"]["position"],
                "maximized": self.default_config["ui"]["window"]["maximized"],
                "remember_size": self.default_config["ui"]["window"]["remember_size"]
            }
    
    def save_window_geometry(self, size: List[int], position: List[int], maximized: bool) -> None:
        if "ui" not in self.config:
            self.config["ui"] = {}
        if "window" not in self.config["ui"]:
            self.config["ui"]["window"] = {}
        
        remember = self.config["ui"]["window"].get("remember_size", True)
        if remember:
            self.config["ui"]["window"]["size"] = size
            self.config["ui"]["window"]["position"] = position
            self.config["ui"]["window"]["maximized"] = maximized
            self.save_config()
    
    def set_remember_window_size(self, remember: bool) -> None:
        if "ui" not in self.config:
            self.config["ui"] = {}
        if "window" not in self.config["ui"]:
            self.config["ui"]["window"] = {}
        
        self.config["ui"]["window"]["remember_size"] = remember
        self.save_config()
    
    def reset_to_defaults(self) -> None:
        self.config = self.default_config.copy()
        self.save_config()

    # Nugget Stuff
    def get_nugget_exec_path(self) -> str:
        """Get the configured path to the Nugget executable."""
        return self.config.get("nugget", {}).get("exe_path", "")

    def set_nugget_exec_path(self, path: str) -> None:
        """Set the path to the Nugget executable."""
        if "nugget" not in self.config:
            self.config["nugget"] = {}
        self.config["nugget"]["exe_path"] = path
        self.save_config()

    def get_open_in_nugget(self) -> bool:
        """Return whether to open exported file in Nugget automatically."""
        return self.config.get("nugget", {}).get("open_after_export", False)

    def set_open_in_nugget(self, open_after: bool) -> None:
        """Set whether to open exported file in Nugget automatically."""
        if "nugget" not in self.config:
            self.config["nugget"] = {}
        self.config["nugget"]["open_after_export"] = open_after
        self.save_config()

    def get_export_shortcut(self) -> str:
        return self.config.get("shortcuts", {}).get("export", "Ctrl+E")

    def set_export_shortcut(self, sequence: str) -> None:
        if "shortcuts" not in self.config:
            self.config["shortcuts"] = {}
        self.config["shortcuts"]["export"] = sequence
        self.save_config()

    def get_zoom_in_shortcut(self) -> str:
        return self.config.get("shortcuts", {}).get("zoom_in", "Ctrl+=")

    def set_zoom_in_shortcut(self, seq: str) -> None:
        if "shortcuts" not in self.config:
            self.config["shortcuts"] = {}
        self.config["shortcuts"]["zoom_in"] = seq
        self.save_config()

    def get_zoom_out_shortcut(self) -> str:
        return self.config.get("shortcuts", {}).get("zoom_out", "Ctrl+-")

    def set_zoom_out_shortcut(self, seq: str) -> None:
        if "shortcuts" not in self.config:
            self.config["shortcuts"] = {}
        self.config["shortcuts"]["zoom_out"] = seq
        self.save_config()

    def get_close_window_shortcut(self) -> str:
        return self.config.get("shortcuts", {}).get("close_window", "Ctrl+W")

    def set_close_window_shortcut(self, sequence: str) -> None:
        if "shortcuts" not in self.config:
            self.config["shortcuts"] = {}
        self.config["shortcuts"]["close_window"] = sequence
        self.save_config()

    def get_shortcuts(self) -> Dict[str, str]:
        """Get the entire shortcuts configuration dictionary."""
        default_shortcuts = self.default_config.get("shortcuts", {})
        return self.config.get("shortcuts", default_shortcuts).copy() # Return a copy to prevent direct modification

    def get_current_language(self) -> str:
        """Get the configured language."""
        return self.config.get("language", "en_US")

    def get_languages(self) -> List[str]:
        """Get the list of available languages."""
        return ["en_US", "en_GB", "en_AU", "vi", "zh", "ja", "ko", "th", "fr", "it"]

    def set_language(self, lang: str) -> None:
        """Set the configured language."""
        self.config["language"] = lang
        self.save_config()

    def get_filename_display_mode(self) -> str:
        return self.config.get("ui", {}).get("filename_display_mode", "Toggle")

    def set_filename_display_mode(self, value: str) -> None:
        if "ui" not in self.config:
            self.config["ui"] = {}
        self.config["ui"]["filename_display_mode"] = value
        self.save_config()

    def get_theme(self) -> str:
        return self.config.get("ui", {}).get("theme", "system")

    def set_theme(self, theme: str) -> None:
        if "ui" not in self.config:
            self.config["ui"] = {}
        self.config["ui"]["theme"] = theme
        self.save_config()