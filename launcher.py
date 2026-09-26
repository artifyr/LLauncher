import os
import sys
import re
import time
import json
import queue
import ctypes
import datetime
import subprocess
import threading
import webbrowser
import collections
import urllib.request
import urllib.error
import customtkinter as ctk
from tkinter import filedialog

try:
    import pywinstyles
    HAS_PYWINSTYLES = True
except ImportError:
    HAS_PYWINSTYLES = False

try:
    import pystray
    from PIL import Image
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def apply_mica_style(window):
    """Apply native Windows 11 Mica styling via pywinstyles."""
    if not HAS_PYWINSTYLES:
        window.configure(fg_color=THEME["bg"])
        return
    try:
        pywinstyles.apply_style(window, style="mica")
        hwnd = pywinstyles.py_win_style.detect(window)

        try:
            backdrop = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop)
            )
        except Exception:
            pass

        try:
            dark_mode = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode)
            )
        except Exception:
            pass

        try:
            pywinstyles.change_header_color(window, "#121215")
        except Exception:
            pass
        try:
            pywinstyles.change_border_color(window, "#27272a")
        except Exception:
            pass
    except Exception:
        window.configure(fg_color=THEME["bg"])


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

THEME = {
    "bg": "#0a0a0c",
    "card_bg": "#121215",
    "card_border": "#27272a",
    "dropdown_bg": "#18181b",
    "input_bg": "#18181b",
    "input_border": "#27272a",
    "input_focus": "#e4e4e7",
    "modal_bg": "#121215",
    "text_primary": "#ffffff",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    "badge_bg": "#18181b",
    "badge_border": "#27272a",
    "slider_knob": "#e4e4e7",
    "slider_knob_hover": "#ffffff",
    "slider_progress": "#71717a",
    "slider_track": "#222226",
    "checkbox_active": "#52525b",
    "checkbox_hover": "#71717a",
    "checkbox_border": "#3f3f46",
    "primary_btn_bg": "#f4f4f5",
    "primary_btn_hover": "#ffffff",
    "primary_btn_border": "#ffffff",
    "primary_btn_text": "#09090b",
    "secondary_btn_bg": "#e4e4e7",
    "secondary_btn_hover": "#ffffff",
    "secondary_btn_border": "#d4d4d8",
    "secondary_btn_text": "#09090b",
}

# Pre-defined step ladders
CTX_STEPS = [2048, 4096, 8192, 16384, 24576, 32768, 49152, 65536, 98304, 131072]
BATCH_STEPS = [128, 256, 512, 1024, 2048, 4096]
UBATCH_STEPS = [128, 256, 512, 1024, 2048]
KV_CACHE_TYPES = ["q8_0", "q4_0", "q4_1", "f16"]

# Path to persistent profiles configuration
PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")
RECENT_MODELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recent_models.json")

DEFAULT_PROFILES = [
    {
        "name": "Max Quality",
        "ngl": 99,
        "ctx": 131072,
        "port": "8082",
        "threads": "8",
        "batch": 1024,
        "ubatch": 256,
        "ctk": "f16",
        "ctv": "f16",
        "temp": "0.7",
        "topp": "0.95",
        "minp": "0.05",
        "fa": True,
        "jinja": True,
        "opts": {
            "mlock": {"enabled": True, "val": "mlock"},
            "tb": {"enabled": False, "val": "8"},
            "fit_target": {"enabled": True, "val": "1024"},
            "cache_reuse": {"enabled": True, "val": "256"},
            "parallel": {"enabled": False, "val": "1"},
            "cache_ram": {"enabled": True, "val": "8192"},
            "cpu_moe": {"enabled": False, "val": "16"},
        },
    },
    {
        "name": "Balanced",
        "ngl": 99,
        "ctx": 131072,
        "port": "8082",
        "threads": "8",
        "batch": 1024,
        "ubatch": 256,
        "ctk": "q8_0",
        "ctv": "q8_0",
        "temp": "0.5",
        "topp": "0.95",
        "minp": "0.05",
        "fa": True,
        "jinja": True,
        "opts": {
            "mlock": {"enabled": False, "val": "mlock"},
            "tb": {"enabled": False, "val": "8"},
            "fit_target": {"enabled": False, "val": "1024"},
            "cache_reuse": {"enabled": False, "val": "256"},
            "parallel": {"enabled": False, "val": "1"},
            "cache_ram": {"enabled": False, "val": "8192"},
            "cpu_moe": {"enabled": False, "val": "16"},
        },
    },
    {
        "name": "Max Performance",
        "ngl": 99,
        "ctx": 32768,
        "port": "8082",
        "threads": "8",
        "batch": 2048,
        "ubatch": 512,
        "ctk": "q4_0",
        "ctv": "q4_0",
        "temp": "0.5",
        "topp": "0.9",
        "minp": "0.05",
        "fa": True,
        "jinja": True,
        "opts": {
            "mlock": {"enabled": True, "val": "mlock"},
            "tb": {"enabled": True, "val": "8"},
            "fit_target": {"enabled": True, "val": "1024"},
            "cache_reuse": {"enabled": True, "val": "256"},
            "parallel": {"enabled": True, "val": "1"},
            "cache_ram": {"enabled": True, "val": "8192"},
            "cpu_moe": {"enabled": False, "val": "16"},
        },
    },
]


class RenameProfileDialog(ctk.CTkInputDialog):
    """Dialog to rename a profile."""

    def __init__(self, curr_name: str, master=None):
        self._initial_name = curr_name
        self._parent = master
        super().__init__(
            title="Rename Profile",
            text=f"Enter custom name for '{curr_name}':",
            fg_color=THEME["modal_bg"],
            text_color=THEME["text_primary"],
            button_fg_color=THEME["secondary_btn_bg"],
            button_hover_color=THEME["secondary_btn_hover"],
            button_text_color=THEME["secondary_btn_text"],
            entry_fg_color=THEME["input_bg"],
            entry_border_color=THEME["input_border"],
            entry_text_color=THEME["text_primary"],
        )

        ico_file = resource_path(os.path.join("assets", "llauncher.ico"))
        if not os.path.exists(ico_file):
            ico_file = resource_path("llauncher.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        apply_mica_style(self)

        if master:
            try:
                self.update_idletasks()
                m_x = master.winfo_x()
                m_y = master.winfo_y()
                m_w = master.winfo_width()
                m_h = master.winfo_height()
                d_w, d_h = 360, 180
                pos_x = max(0, m_x + (m_w - d_w) // 2)
                pos_y = max(0, m_y + (m_h - d_h) // 2)
                self.geometry(f"{d_w}x{d_h}+{pos_x}+{pos_y}")
            except Exception:
                pass

    def _create_widgets(self):
        super()._create_widgets()

        if hasattr(self, "_label"):
            self._label.configure(
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=THEME["text_primary"],
            )

        if hasattr(self, "_entry"):
            self._entry.configure(
                corner_radius=6,
                border_width=1,
                border_color=THEME["input_border"],
                fg_color=THEME["input_bg"],
                text_color=THEME["text_primary"],
                font=ctk.CTkFont(family="Segoe UI", size=12),
            )
            if self._initial_name:
                self._entry.insert(0, self._initial_name)
                self._entry.select_range(0, "end")

        if hasattr(self, "_ok_button"):
            self._ok_button.configure(
                fg_color=THEME["secondary_btn_bg"],
                hover_color=THEME["secondary_btn_hover"],
                border_width=1,
                border_color=THEME["secondary_btn_border"],
                text_color=THEME["secondary_btn_text"],
                corner_radius=6,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            )

        if hasattr(self, "_cancel_button"):
            self._cancel_button.configure(
                fg_color="#27272a",
                hover_color="#3f3f46",
                border_width=1,
                border_color="#3f3f46",
                text_color="#e4e4e7",
                corner_radius=6,
                font=ctk.CTkFont(family="Segoe UI", size=12),
            )


class ClientConfigDialog(ctk.CTkToplevel):
    """Modal dialog displaying one-click configuration snippets for popular frontends."""

    def __init__(self, port: str, model_path: str, master=None):
        super().__init__(master)
        self.port = port or "8082"
        self.model_path = model_path or "Loaded Model"
        self.model_name = os.path.basename(self.model_path) if self.model_path else "default"
        self.title("Client & Frontend Integrations")
        self.geometry("640x510")
        self.minsize(580, 440)
        self.configure(fg_color=THEME["modal_bg"])
        self.transient(master)
        self.grab_set()

        ico_file = resource_path(os.path.join("assets", "llauncher.ico"))
        if not os.path.exists(ico_file):
            ico_file = resource_path("llauncher.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        apply_mica_style(self)

        if master:
            try:
                self.update_idletasks()
                m_x = master.winfo_x()
                m_y = master.winfo_y()
                m_w = master.winfo_width()
                m_h = master.winfo_height()
                d_w, d_h = 640, 510
                pos_x = max(0, m_x + (m_w - d_w) // 2)
                pos_y = max(0, m_y + (m_h - d_h) // 2)
                self.geometry(f"{d_w}x{d_h}+{pos_x}+{pos_y}")
            except Exception:
                pass

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header,
            text="Client & Frontend Configurations",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")

        self.copied_badge = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#4ade80",
        )
        self.copied_badge.pack(side="right", padx=4)

        ctk.CTkLabel(
            container,
            text="Copy pre-configured endpoints and setup JSON for OpenAI-compatible tools and chat UIs:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        self.tabview = ctk.CTkTabview(
            container,
            fg_color=THEME["card_bg"],
            segmented_button_fg_color="#18181b",
            segmented_button_selected_color=THEME["primary_btn_bg"],
            segmented_button_selected_hover_color=THEME["primary_btn_hover"],
            segmented_button_unselected_color="#18181b",
            segmented_button_unselected_hover_color="#27272a",
            text_color="#ffffff",
            corner_radius=8,
            border_width=1,
            border_color=THEME["card_border"],
            command=self._update_tab_colors,
        )
        self.tabview._segmented_button.configure(
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        self.tabview.pack(fill="both", expand=True, pady=(0, 12))

        # Define clients and snippet generators
        clients = [
            ("Open WebUI", self._get_openwebui_snippet()),
            ("SillyTavern", self._get_sillytavern_snippet()),
            ("Continue / Cline", self._get_continue_snippet()),
            ("Hermes", self._get_hermes_snippet()),
        ]

        for title, snippet in clients:
            tab = self.tabview.add(title)
            txt = ctk.CTkTextbox(
                tab,
                fg_color=THEME["input_bg"],
                border_color=THEME["input_border"],
                border_width=1,
                text_color=THEME["text_primary"],
                font=ctk.CTkFont(family="Consolas", size=11),
                corner_radius=6,
                wrap="none",
            )
            txt.insert("1.0", snippet)
            txt.configure(state="disabled")
            txt.pack(fill="both", expand=True, padx=4, pady=(4, 8))

            copy_btn = ctk.CTkButton(
                tab,
                text="📋  Copy Configuration",
                height=30,
                fg_color=THEME["secondary_btn_bg"],
                hover_color=THEME["secondary_btn_hover"],
                border_width=1,
                border_color=THEME["secondary_btn_border"],
                text_color=THEME["secondary_btn_text"],
                corner_radius=6,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                command=lambda s=snippet, n=title: self._copy_to_clipboard(s, n),
            )
            copy_btn.pack(anchor="e", padx=4, pady=(0, 4))

        self._update_tab_colors()

        # Bottom close button
        ctk.CTkButton(
            container,
            text="Close",
            height=32,
            fg_color="#27272a",
            hover_color="#3f3f46",
            border_width=1,
            border_color="#3f3f46",
            text_color="#e4e4e7",
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.destroy,
        ).pack(fill="x")

    def _update_tab_colors(self):
        """Ensure unselected tabs have crisp white bold text and selected tab has black text."""
        if hasattr(self, "tabview") and hasattr(self.tabview, "_segmented_button"):
            seg = self.tabview._segmented_button
            current_tab = self.tabview.get()
            if hasattr(seg, "_buttons_dict"):
                for name, btn in seg._buttons_dict.items():
                    btn.configure(font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"))
                    if name == current_tab:
                        btn.configure(text_color=THEME["primary_btn_text"])
                    else:
                        btn.configure(text_color="#ffffff")

    def _copy_to_clipboard(self, text: str, name: str):
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
            self.copied_badge.configure(text=f"✓ Copied {name} config!")
            self.after(2500, lambda: self.copied_badge.configure(text=""))
        except Exception:
            pass

    def _get_openwebui_snippet(self):
        return (
            f"=== Open WebUI Configuration ===\n"
            f"Go to: Admin Panel -> Settings -> Connections -> OpenAI API\n\n"
            f"API URL:      http://127.0.0.1:{self.port}/v1\n"
            f"API Key:      not-needed (or enter any string)\n\n"
            f"Model ID:     {self.model_name}\n"
            f"Context Window: Matches your configured Context slider in LLauncher\n"
        )

    def _get_sillytavern_snippet(self):
        return (
            f"=== SillyTavern Configuration ===\n"
            f"API Selection:   Chat Completion\n"
            f"API Type:        OpenAI\n"
            f"Server URL:      http://127.0.0.1:{self.port}/v1\n"
            f"API Key:         any (e.g. 'llauncher')\n\n"
            f"Reverse Proxy:   Leave blank\n"
            f"Model Selection: Click 'Connect' -> select '{self.model_name}'\n"
        )

    def _get_continue_snippet(self):
        config_obj = {
            "models": [
                {
                    "title": self.model_name,
                    "provider": "openai",
                    "model": self.model_name,
                    "apiBase": f"http://127.0.0.1:{self.port}/v1",
                    "apiKey": "any"
                }
            ],
            "tabAutocompleteModel": {
                "title": f"{self.model_name} (FIM)",
                "provider": "openai",
                "model": self.model_name,
                "apiBase": f"http://127.0.0.1:{self.port}/v1",
                "apiKey": "any"
            }
        }
        return (
            f"// ~/.continue/config.json or Cline settings\n"
            f"{json.dumps(config_obj, indent=2)}\n"
        )

    def _get_hermes_snippet(self):
        config_obj = {
            "endpoint": f"http://127.0.0.1:{self.port}/v1",
            "api_key": "not-needed",
            "model": self.model_name,
            "system_prompt": "You are a helpful, precise assistant with advanced reasoning and tool usage capabilities.",
            "temperature": 0.7,
            "max_tokens": 4096
        }
        return (
            f"=== Hermes Agent / Function Calling Integration ===\n\n"
            f"# Configuration JSON (or environment variables):\n"
            f"{json.dumps(config_obj, indent=2)}\n\n"
            f"# Python SDK Connection (OpenAI Client Compatible):\n"
            f"from openai import OpenAI\n\n"
            f"client = OpenAI(\n"
            f"    base_url='http://127.0.0.1:{self.port}/v1',\n"
            f"    api_key='not-needed'\n"
            f")\n\n"
            f"response = client.chat.completions.create(\n"
            f"    model='{self.model_name}',\n"
            f"    messages=[{{'role': 'user', 'content': 'Hello from Hermes!'}}]\n"
            f")\n"
            f"print(response.choices[0].message.content)\n"
        )


class EndpointTesterDialog(ctk.CTkToplevel):
    """Modal dialog to test /v1/models and /v1/chat/completions endpoints."""

    def __init__(self, port: str, master=None):
        super().__init__(master)
        self.port = port or "8082"
        self.title("API Endpoint Health Check & Tester")
        self.geometry("640x510")
        self.minsize(580, 440)
        self.configure(fg_color=THEME["modal_bg"])
        self.transient(master)
        self.grab_set()

        ico_file = resource_path(os.path.join("assets", "llauncher.ico"))
        if not os.path.exists(ico_file):
            ico_file = resource_path("llauncher.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        apply_mica_style(self)

        if master:
            try:
                self.update_idletasks()
                m_x = master.winfo_x()
                m_y = master.winfo_y()
                m_w = master.winfo_width()
                m_h = master.winfo_height()
                d_w, d_h = 640, 510
                pos_x = max(0, m_x + (m_w - d_w) // 2)
                pos_y = max(0, m_y + (m_h - d_h) // 2)
                self.geometry(f"{d_w}x{d_h}+{pos_x}+{pos_y}")
            except Exception:
                pass

        self._build_ui()
        # Automatically run test on open
        self.after(200, self._test_models_endpoint)

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        top_frame = ctk.CTkFrame(container, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_frame,
            text=f"API Tester (http://127.0.0.1:{self.port})",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")

        self.status_pill = ctk.CTkLabel(
            top_frame,
            text="● TESTING...",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=THEME["text_muted"],
        )
        self.status_pill.pack(side="right")

        # Action Buttons Row
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))

        self.test_models_btn = ctk.CTkButton(
            btn_row,
            text="🔍  Ping /v1/models",
            height=30,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._test_models_endpoint,
        )
        self.test_models_btn.pack(side="left", padx=(0, 8))

        self.test_chat_btn = ctk.CTkButton(
            btn_row,
            text="💬  Test /v1/chat/completions",
            height=30,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._test_chat_endpoint,
        )
        self.test_chat_btn.pack(side="left")

        # Response Output Box
        self.log_box = ctk.CTkTextbox(
            container,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=6,
        )
        self.log_box.pack(fill="both", expand=True, pady=(0, 10))

        # Bottom close button
        ctk.CTkButton(
            container,
            text="Close",
            height=32,
            fg_color="#27272a",
            hover_color="#3f3f46",
            border_width=1,
            border_color="#3f3f46",
            text_color="#e4e4e7",
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.destroy,
        ).pack(fill="x")

    def _append_log(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _test_models_endpoint(self):
        self._clear_log()
        self.status_pill.configure(text="● QUERYING /v1/models...", text_color="#facc15")
        self._append_log(f"GET http://127.0.0.1:{self.port}/v1/models ...\n")

        def worker():
            url = f"http://127.0.0.1:{self.port}/v1/models"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "LLauncher"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    status = resp.status
                    data = resp.read().decode("utf-8")
                    parsed = json.loads(data)
                    formatted = json.dumps(parsed, indent=2)
                    self.after(0, lambda: self._on_test_success(f"HTTP {status} OK\n\n{formatted}"))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self._on_test_failure(f"Connection Failed: {err_msg}"))

        threading.Thread(target=worker, daemon=True).start()

    def _test_chat_endpoint(self):
        self._clear_log()
        self.status_pill.configure(text="● QUERYING /v1/chat/completions...", text_color="#facc15")
        self._append_log(f"POST http://127.0.0.1:{self.port}/v1/chat/completions ...\nPrompt: 'Ping!'\n")

        def worker():
            url = f"http://127.0.0.1:{self.port}/v1/chat/completions"
            payload = json.dumps({
                "messages": [{"role": "user", "content": "Ping! Reply with 'Pong!'"}],
                "max_tokens": 16,
                "temperature": 0.1
            }).encode("utf-8")
            try:
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json", "User-Agent": "LLauncher"}
                )
                with urllib.request.urlopen(req, timeout=6.0) as resp:
                    status = resp.status
                    data = resp.read().decode("utf-8")
                    parsed = json.loads(data)
                    formatted = json.dumps(parsed, indent=2)
                    self.after(0, lambda: self._on_test_success(f"HTTP {status} OK\n\n{formatted}"))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self._on_test_failure(f"Chat Completion Failed: {err_msg}"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_test_success(self, text: str):
        self.status_pill.configure(text="● ONLINE / RESPONSIVE", text_color="#4ade80")
        self._append_log(text)

    def _on_test_failure(self, text: str):
        self.status_pill.configure(text="● OFFLINE / NO RESPONSE", text_color="#f87171")
        self._append_log(text)
        self._append_log("\nEnsure the llama-server is currently running in LLauncher.")


class LlamaLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # Off-screen construction eliminates launch stutter and flicker
        self.title("LLauncher - llama.cpp Server Launcher")
        self.geometry("1184x625")
        self.minsize(1120, 560)
        self.resizable(True, True)
        self.configure(fg_color="black")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Window Icon
        ico_file = resource_path(os.path.join("assets", "llauncher.ico"))
        if not os.path.exists(ico_file):
            ico_file = resource_path("llauncher.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        self.llama_exe = r"E:\LLAMACPP\llama.cpp\build\bin\Release\llama-server.exe"

        self.font_title = ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Segoe UI", size=12)
        self.font_section = ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        self.font_label = ctk.CTkFont(family="Segoe UI", size=12)
        self.font_badge = ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        self.font_btn = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        self.font_sm = ctk.CTkFont(family="Segoe UI", size=11)

        self.device_map = {
            "Vulkan0: AMD Radeon RX 9070 XT": "Vulkan0",
            "Vulkan1: AMD Radeon(TM) Graphics": "Vulkan1",
            "none: CPU Only": "none",
        }

        self.profiles = []
        self.active_profile_idx = 0
        self._load_profiles()

        self.recent_models = []
        self._load_recent_models()

        # Process management & desktop ergonomics state
        self.log_queue = queue.Queue()
        self.log_buffer = collections.deque(maxlen=2000)
        self.log_drawer_expanded = False
        self.auto_restart_var = ctk.BooleanVar(value=False)
        self.external_console_var = ctk.BooleanVar(value=False)
        self.minimize_to_tray_var = ctk.BooleanVar(value=True)
        self.log_autoscroll_var = ctk.BooleanVar(value=True)
        self.manual_stop = False
        self.crash_count = 0
        self.last_crash_time = 0
        self.tray_icon = None

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=16, pady=10)

        self._build_header()
        self._build_paths_card()

        cols_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        cols_container.pack(fill="both", expand=True, pady=(0, 8))
        cols_container.columnconfigure(0, weight=1)
        cols_container.columnconfigure(1, weight=1)
        cols_container.columnconfigure(2, weight=1)
        cols_container.rowconfigure(0, weight=1)

        self._build_hardware_column(cols_container)
        self._build_batch_sampling_column(cols_container)
        self._build_optimizations_column(cols_container)
        self._build_launch_action()
        self._build_log_drawer()

        self._apply_profile(self.profiles[self.active_profile_idx])
        apply_mica_style(self)
        self._init_tray()
        self.after(50, self._process_log_queue)
        self.deiconify()
        self._detect_devices()

    def _load_profiles(self):
        """Load profiles from profiles.json or initialize with defaults."""
        self.profiles = []
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        self.profiles = data[:3]
            except Exception:
                pass

        if len(self.profiles) < 3:
            for i in range(len(self.profiles), 3):
                self.profiles.append(dict(DEFAULT_PROFILES[i]))
            self._persist_profiles()

        self.active_profile_idx = 0

    def _persist_profiles(self):
        """Save profiles to profiles.json."""
        try:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=2)
        except Exception:
            pass

    def _load_recent_models(self):
        """Load recent model paths from recent_models.json."""
        self.recent_models = []
        if os.path.exists(RECENT_MODELS_FILE):
            try:
                with open(RECENT_MODELS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.recent_models = [m for m in data if isinstance(m, str) and m.strip()]
            except Exception:
                pass

    def _persist_recent_models(self):
        """Save recent model paths to recent_models.json."""
        try:
            with open(RECENT_MODELS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.recent_models, f, indent=2)
        except Exception:
            pass

    def _add_recent_model(self, model_path: str):
        """Add model path to recent history and refresh UI dropdown."""
        if not model_path or not model_path.strip():
            return
        norm_path = os.path.normpath(model_path.strip())
        if norm_path in self.recent_models:
            self.recent_models.remove(norm_path)
        self.recent_models.insert(0, norm_path)
        self.recent_models = self.recent_models[:15]
        self._persist_recent_models()
        self._refresh_recent_models_menu()

    def _refresh_recent_models_menu(self):
        """Update recent models dropdown menu values."""
        if not hasattr(self, "recent_models_menu"):
            return
        options = ["Recent Models..."]
        for p in self.recent_models:
            options.append(os.path.basename(p))
        if len(self.recent_models) > 0:
            options.append("Clear History")
        self.recent_models_menu.configure(values=options)
        self.recent_models_menu.set("Recent Models...")

    def _on_recent_model_selected(self, choice: str):
        """Handle selection from recent models dropdown."""
        if choice == "Recent Models...":
            return
        if choice == "Clear History":
            self.recent_models = []
            self._persist_recent_models()
            self._refresh_recent_models_menu()
            self._flash_badge("● HISTORY CLEARED")
            return

        # Find matching path by filename
        matched_path = None
        for p in self.recent_models:
            if os.path.basename(p) == choice:
                matched_path = p
                break

        if matched_path:
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, matched_path)
            self._add_recent_model(matched_path)
            self._auto_detect_vision_mmproj(matched_path)

    def _auto_detect_vision_mmproj(self, model_path: str):
        """Auto-detect matching vision mmproj in model directory if model is vision-capable."""
        if not model_path:
            return
        clean_path = os.path.normpath(model_path)
        filename = os.path.basename(clean_path).lower()

        vision_keywords = [
            "vision", "-vl", "_vl", "llava", "minicpm", "ovis", "internvl",
            "pixtral", "cogvlm", "florence", "mplug", "points", "glvm"
        ]
        is_vision_model = any(kw in filename for kw in vision_keywords)

        model_dir = os.path.dirname(clean_path)
        if not os.path.isdir(model_dir):
            return

        # Search directory for mmproj files
        candidates = []
        try:
            for item in os.listdir(model_dir):
                if item.lower().endswith(".gguf") and "mmproj" in item.lower():
                    candidates.append(os.path.normpath(os.path.join(model_dir, item)))
        except Exception:
            return

        if not candidates:
            return

        # Sort candidate to pick best match (e.g., matching f16 or similar prefix)
        best_match = candidates[0]
        for c in candidates:
            c_name = os.path.basename(c).lower()
            if "f16" in c_name:
                best_match = c
                break

        # If vision model keywords detected or mmproj directly in directory
        if is_vision_model:
            self.vision_var.set(True)
            self.mmproj_entry.delete(0, "end")
            self.mmproj_entry.insert(0, best_match)
            self._toggle_vision()
            self._flash_badge(f"● AUTO-DETECTED MMPROJ: {os.path.basename(best_match)[:22]}")

    def _build_header(self):
        header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))

        # Left: App Brand & Subtitle
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")

        # App Brand Logo & Title
        logo_file = resource_path(os.path.join("assets", "logoClear.png"))
        if not os.path.exists(logo_file):
            logo_file = resource_path("logoClear.png")

        if os.path.exists(logo_file):
            try:
                from PIL import Image
                pil_logo = Image.open(logo_file)
                self.brand_logo_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(24, 24))
                logo_lbl = ctk.CTkLabel(left, text="", image=self.brand_logo_img)
                logo_lbl.pack(side="left", padx=(0, 8))
            except Exception:
                pass

        title = ctk.CTkLabel(
            left,
            text="LLauncher",
            font=self.font_title,
            text_color=THEME["text_primary"],
        )
        title.pack(side="left", padx=(0, 10))

        sub = ctk.CTkLabel(
            left,
            text="Local LLM Inference Engine",
            font=self.font_subtitle,
            text_color=THEME["text_muted"],
        )
        sub.pack(side="left", pady=(3, 0))

        # Far Right: Status Badge
        badge = ctk.CTkFrame(
            header,
            fg_color=THEME["badge_bg"],
            corner_radius=14,
            border_width=1,
            border_color=THEME["badge_border"],
        )
        badge.pack(side="right")
        self.badge_label = ctk.CTkLabel(
            badge,
            text="● ENGINE READY",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=THEME["text_primary"],
            padx=10,
            pady=3,
        )
        self.badge_label.pack()

        # Center-Right: Profile System Switcher & Actions
        prof_box = ctk.CTkFrame(header, fg_color="transparent")
        prof_box.pack(side="right", padx=(0, 14))

        ctk.CTkLabel(
            prof_box,
            text="Profile:",
            font=self.font_label,
            text_color=THEME["text_secondary"],
        ).pack(side="left", padx=(0, 6))

        profile_names = [p["name"] for p in self.profiles]
        self.profile_seg = ctk.CTkSegmentedButton(
            prof_box,
            values=profile_names,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#18181b",
            selected_color=THEME["primary_btn_bg"],
            selected_hover_color=THEME["primary_btn_hover"],
            unselected_color="#18181b",
            unselected_hover_color="#27272a",
            text_color=THEME["text_primary"],
            border_width=1,
            corner_radius=6,
            command=self._on_profile_selected,
            height=28,
        )
        self.profile_seg.set(self.profiles[self.active_profile_idx]["name"])
        self.profile_seg.pack(side="left", padx=(0, 6))
        self._update_profile_seg_colors(self.profiles[self.active_profile_idx]["name"])

        self.save_prof_btn = ctk.CTkButton(
            prof_box,
            text="💾 Save",
            width=62,
            height=28,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._save_current_profile,
        )
        self.save_prof_btn.pack(side="left", padx=(0, 4))

        self.rename_prof_btn = ctk.CTkButton(
            prof_box,
            text="✏️ Rename",
            width=74,
            height=28,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._rename_current_profile,
        )
        self.rename_prof_btn.pack(side="left")

    def _update_profile_seg_colors(self, selected_name):
        """Update segmented button active text color for clean contrast."""
        if hasattr(self, "profile_seg") and hasattr(self.profile_seg, "_buttons_dict"):
            for name, btn in self.profile_seg._buttons_dict.items():
                if name == selected_name:
                    btn.configure(text_color=THEME["primary_btn_text"])
                else:
                    btn.configure(text_color=THEME["text_secondary"])

    def _flash_badge(self, text, is_alert=False):
        """Show temporary feedback on status badge."""
        color = THEME["text_primary"] if not is_alert else "#f87171"
        self.badge_label.configure(text=text, text_color=color)
        self.after(2200, lambda: self.badge_label.configure(text="● ENGINE READY", text_color=THEME["text_primary"]))

    def _on_profile_selected(self, selected_name):
        """Switch active profile without altering chosen model path."""
        for idx, p in enumerate(self.profiles):
            if p["name"] == selected_name:
                self.active_profile_idx = idx
                self._apply_profile(p)
                self._update_profile_seg_colors(selected_name)
                self._flash_badge(f"● LOADED: {selected_name.upper()}")
                break

    def _save_current_profile(self):
        """Save current UI hardware, generation and optimization parameters into active profile."""
        idx = self.active_profile_idx
        p = self.profiles[idx]

        ctx_idx = int(round(self.ctx_slider.get()))
        b_idx = int(round(self.batch_slider.get()))
        ub_idx = int(round(self.ubatch_slider.get()))

        p["ngl"] = int(round(self.ngl_slider.get()))
        p["ctx"] = CTX_STEPS[ctx_idx]
        p["batch"] = BATCH_STEPS[b_idx]
        p["ubatch"] = UBATCH_STEPS[ub_idx]
        p["port"] = self.port_entry.get().strip()
        p["threads"] = self.threads_entry.get().strip()
        p["ctk"] = self.ctk_dropdown.get()
        p["ctv"] = self.ctv_dropdown.get()
        p["temp"] = self.temp_entry.get().strip()
        p["topp"] = self.topp_entry.get().strip()
        p["minp"] = self.minp_entry.get().strip()
        p["fa"] = self.fa_var.get()
        p["jinja"] = self.jinja_var.get()
        p["vision"] = self.vision_var.get() if hasattr(self, "vision_var") else False
        p["mmproj"] = self.mmproj_entry.get().strip() if hasattr(self, "mmproj_entry") else ""

        p["opts"] = {}
        for k in self.opt_vars:
            p["opts"][k] = {
                "enabled": self.opt_vars[k].get(),
                "val": self.opt_str_vars[k].get().strip(),
            }

        self._persist_profiles()
        self._flash_badge(f"● SAVED: {p['name'].upper()}")

    def _rename_current_profile(self):
        """Prompt to rename the current profile slot."""
        idx = self.active_profile_idx
        curr_name = self.profiles[idx]["name"]

        dialog = RenameProfileDialog(curr_name, master=self)
        new_name = dialog.get_input()

        if new_name and new_name.strip():
            new_name = new_name.strip()
            self.profiles[idx]["name"] = new_name
            self._persist_profiles()

            names = [p["name"] for p in self.profiles]
            self.profile_seg.configure(values=names)
            self.profile_seg.set(new_name)
            self._flash_badge(f"● RENAMED: {new_name.upper()}")

    def _apply_profile(self, profile):
        """Apply profile values to all UI inputs without modifying model file path."""
        ngl_val = profile.get("ngl", 99)
        self.ngl_slider.set(ngl_val)
        self._on_ngl_change(ngl_val)

        ctx_tokens = profile.get("ctx", 131072)
        ctx_idx = CTX_STEPS.index(ctx_tokens) if ctx_tokens in CTX_STEPS else len(CTX_STEPS) - 1
        self.ctx_slider.set(ctx_idx)
        self._on_ctx_change(ctx_idx)

        batch_val = profile.get("batch", 1024)
        b_idx = BATCH_STEPS.index(batch_val) if batch_val in BATCH_STEPS else BATCH_STEPS.index(1024)
        self.batch_slider.set(b_idx)
        self._on_batch_change(b_idx)

        ubatch_val = profile.get("ubatch", 256)
        ub_idx = UBATCH_STEPS.index(ubatch_val) if ubatch_val in UBATCH_STEPS else UBATCH_STEPS.index(256)
        self.ubatch_slider.set(ub_idx)
        self._on_ubatch_change(ub_idx)

        self.port_entry.delete(0, "end")
        self.port_entry.insert(0, str(profile.get("port", "8082")))

        self.threads_entry.delete(0, "end")
        self.threads_entry.insert(0, str(profile.get("threads", "8")))

        if profile.get("ctk") in KV_CACHE_TYPES:
            self.ctk_dropdown.set(profile["ctk"])
        if profile.get("ctv") in KV_CACHE_TYPES:
            self.ctv_dropdown.set(profile["ctv"])

        self.temp_entry.delete(0, "end")
        self.temp_entry.insert(0, str(profile.get("temp", "0.5")))

        self.topp_entry.delete(0, "end")
        self.topp_entry.insert(0, str(profile.get("topp", "0.95")))

        self.minp_entry.delete(0, "end")
        self.minp_entry.insert(0, str(profile.get("minp", "0.05")))

        self.fa_var.set(profile.get("fa", True))
        self.jinja_var.set(profile.get("jinja", True))

        if hasattr(self, "vision_var"):
            self.vision_var.set(profile.get("vision", False))
            if hasattr(self, "mmproj_entry") and "mmproj" in profile:
                val = profile.get("mmproj", r"D:\HF Models\mmproj-f16.gguf")
                if val:
                    self.mmproj_entry.delete(0, "end")
                    self.mmproj_entry.insert(0, val)
            self._toggle_vision()

        opts = profile.get("opts", {})
        for k in self.opt_vars:
            opt_cfg = opts.get(k, {})
            self.opt_vars[k].set(opt_cfg.get("enabled", False))
            if "val" in opt_cfg:
                self.opt_str_vars[k].set(str(opt_cfg["val"]))
            self._toggle_opt_widget(k)

    def _build_paths_card(self):
        card = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["card_border"],
        )
        card.pack(fill="x", pady=(0, 8))
        card.columnconfigure(1, weight=1)

        # Row 0: llama-server.exe
        ctk.CTkLabel(
            card,
            text="llama-server.exe",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=115,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(12, 4), pady=(8, 4))

        self.exe_entry = ctk.CTkEntry(
            card,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=30,
            font=self.font_sm,
        )
        self.exe_entry.insert(0, self.llama_exe)
        self.exe_entry.grid(row=0, column=1, sticky="ew", padx=(4, 8), pady=(8, 4))

        self.browse_exe_btn = ctk.CTkButton(
            card,
            text="Browse",
            width=85,
            height=30,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.browse_exe,
        )
        self.browse_exe_btn.grid(row=0, column=2, sticky="e", padx=(0, 12), pady=(8, 4))

        # Row 1: Model GGUF + Vision Checkbox
        model_lbl_frame = ctk.CTkFrame(card, fg_color="transparent")
        model_lbl_frame.grid(row=1, column=0, sticky="w", padx=(12, 4), pady=(0, 6))

        ctk.CTkLabel(
            model_lbl_frame,
            text="Model GGUF",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(side="left")

        self.vision_var = ctk.BooleanVar(value=False)
        self.vision_chk = ctk.CTkCheckBox(
            model_lbl_frame,
            text="Vision",
            variable=self.vision_var,
            command=self._toggle_vision,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_primary"],
            fg_color=THEME["checkbox_active"],
            hover_color=THEME["checkbox_hover"],
            border_color=THEME["checkbox_border"],
            border_width=2,
            corner_radius=4,
            height=18,
            width=18,
            checkbox_width=16,
            checkbox_height=16,
        )
        self.vision_chk.pack(side="left", padx=(10, 0))

        # Model input container: Entry + Recent Models Dropdown
        model_input_frame = ctk.CTkFrame(card, fg_color="transparent")
        model_input_frame.grid(row=1, column=1, sticky="ew", padx=(4, 8), pady=(0, 6))
        model_input_frame.columnconfigure(0, weight=1)

        self.model_entry = ctk.CTkEntry(
            model_input_frame,
            placeholder_text="Path to .gguf weights file",
            placeholder_text_color=THEME["text_muted"],
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=30,
            font=self.font_sm,
        )
        self.model_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        initial_history_values = ["Recent Models..."]
        for p in self.recent_models:
            initial_history_values.append(os.path.basename(p))
        if len(self.recent_models) > 0:
            initial_history_values.append("Clear History")

        self.recent_models_menu = ctk.CTkOptionMenu(
            model_input_frame,
            values=initial_history_values,
            command=self._on_recent_model_selected,
            fg_color=THEME["input_bg"],
            button_color="#27272a",
            button_hover_color="#3f3f46",
            text_color=THEME["text_secondary"],
            dropdown_fg_color=THEME["dropdown_bg"],
            dropdown_text_color=THEME["text_primary"],
            dropdown_hover_color="#27272a",
            corner_radius=6,
            height=30,
            width=140,
            font=self.font_sm,
        )
        self.recent_models_menu.set("Recent Models...")
        self.recent_models_menu.grid(row=0, column=1, sticky="e")

        self.browse_btn = ctk.CTkButton(
            card,
            text="Browse",
            width=85,
            height=30,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.browse_model,
        )
        self.browse_btn.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=(0, 6))

        # Row 2: Vision mmproj (Conditionally displayed when Vision checkbox is checked)
        self.mmproj_label = ctk.CTkLabel(
            card,
            text="Vision mmproj",
            font=self.font_label,
            text_color=THEME["text_primary"],
            width=115,
            anchor="w",
        )

        self.mmproj_entry = ctk.CTkEntry(
            card,
            placeholder_text=r"D:\HF Models\mmproj-f16.gguf",
            placeholder_text_color=THEME["text_muted"],
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=30,
            font=self.font_sm,
        )
        self.mmproj_entry.insert(0, r"D:\HF Models\mmproj-f16.gguf")

        self.mmproj_browse_btn = ctk.CTkButton(
            card,
            text="Browse",
            width=85,
            height=30,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.browse_mmproj,
        )

    def _toggle_vision(self):
        """Show or hide mmproj row below GGUF selector based on Vision checkbox."""
        if hasattr(self, "mmproj_label") and hasattr(self, "vision_var"):
            if self.vision_var.get():
                self.mmproj_label.grid(row=2, column=0, sticky="w", padx=(12, 4), pady=(0, 8))
                self.mmproj_entry.grid(row=2, column=1, sticky="ew", padx=(4, 8), pady=(0, 8))
                self.mmproj_browse_btn.grid(row=2, column=2, sticky="e", padx=(0, 12), pady=(0, 8))
            else:
                self.mmproj_label.grid_remove()
                self.mmproj_entry.grid_remove()
                self.mmproj_browse_btn.grid_remove()

    def browse_mmproj(self):
        f = filedialog.askopenfilename(
            filetypes=[("GGUF Files", "*.gguf"), ("All Files", "*.*")],
            title="Select Vision mmproj (.gguf)"
        )
        if f:
            self.mmproj_entry.delete(0, "end")
            self.mmproj_entry.insert(0, f)

    def _detect_devices(self, on_done=None):
        """Detect GPU devices asynchronously via llama-server --list-devices to prevent launch lag."""
        def worker():
            exe = self.exe_entry.get().strip() if hasattr(self, "exe_entry") else self.llama_exe
            new_map = {}
            try:
                no_window_flag = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                proc = subprocess.run(
                    [exe, "--list-devices"],
                    capture_output=True,
                    text=True,
                    timeout=4,
                    creationflags=no_window_flag,
                )
                for line in proc.stdout.splitlines():
                    line = line.strip()
                    if not line or line.lower().startswith("available"):
                        continue
                    if ":" in line:
                        dev_id = line.split(":", 1)[0].strip()
                        desc = line.split(":", 1)[1].strip()
                        clean_desc = re.sub(r"\s*\(\d+\s*MiB.*?\)", "", desc).strip()
                        new_map[f"{dev_id}: {clean_desc}"] = dev_id
            except Exception:
                pass

            if new_map:
                if not any(v == "none" for v in new_map.values()):
                    new_map["none: CPU Only"] = "none"

                def apply_results():
                    self.device_map = new_map
                    if hasattr(self, "device_dropdown"):
                        options = list(self.device_map.keys())
                        curr = self.device_dropdown.get()
                        self.device_dropdown.configure(values=options)
                        if curr in self.device_map:
                            self.device_dropdown.set(curr)
                        else:
                            self.device_dropdown.set(self._get_default_device_display())
                    if on_done:
                        on_done()

                self.after(0, apply_results)
            else:
                if on_done:
                    self.after(0, on_done)

        threading.Thread(target=worker, daemon=True).start()

    def _refresh_devices(self):
        if hasattr(self, "detect_btn"):
            self.detect_btn.configure(text="Detecting...", state="disabled")

        def finish():
            if hasattr(self, "detect_btn"):
                self.detect_btn.configure(text="Detect GPUs", state="normal")

        self._detect_devices(on_done=finish)

    def _get_default_device_display(self):
        for disp, dev_id in self.device_map.items():
            if dev_id == "Vulkan0":
                return disp
        return list(self.device_map.keys())[0]

    def _build_hardware_column(self, parent):
        """Column 1: Hardware & Compute Parameters."""
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["card_border"],
        )
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        card.columnconfigure(0, weight=0, minsize=80)
        card.columnconfigure(1, weight=1)
        card.columnconfigure(2, weight=0, minsize=55)

        ctk.CTkLabel(
            card,
            text="HARDWARE & ACCELERATION",
            font=self.font_section,
            text_color=THEME["text_primary"],
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 6))

        ctk.CTkLabel(
            card,
            text="Device",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(12, 4), pady=(0, 6))

        self.device_dropdown = ctk.CTkOptionMenu(
            card,
            values=list(self.device_map.keys()),
            fg_color=THEME["input_bg"],
            button_color="#27272a",
            button_hover_color="#3f3f46",
            text_color=THEME["text_primary"],
            dropdown_fg_color=THEME["dropdown_bg"],
            dropdown_text_color=THEME["text_primary"],
            dropdown_hover_color="#27272a",
            corner_radius=6,
            height=28,
            font=self.font_sm,
        )
        self.device_dropdown.set(self._get_default_device_display())
        self.device_dropdown.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=(0, 6))

        ctk.CTkLabel(
            card,
            text="Layers (-ngl)",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=(12, 4), pady=(0, 6))

        self.ngl_slider = ctk.CTkSlider(
            card,
            from_=0,
            to=99,
            number_of_steps=99,
            button_color=THEME["slider_knob"],
            button_hover_color=THEME["slider_knob_hover"],
            progress_color=THEME["slider_progress"],
            fg_color=THEME["slider_track"],
            height=16,
            command=self._on_ngl_change,
        )
        self.ngl_slider.set(99)
        self.ngl_slider.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=(0, 6))

        self.ngl_badge = ctk.CTkLabel(
            card,
            text="99 (All)",
            font=self.font_badge,
            text_color=THEME["text_primary"],
            width=55,
            anchor="e",
        )
        self.ngl_badge.grid(row=2, column=2, sticky="e", padx=(0, 12), pady=(0, 6))

        ctk.CTkLabel(
            card,
            text="Context (-c)",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=(12, 4), pady=(0, 8))

        self.ctx_slider = ctk.CTkSlider(
            card,
            from_=0,
            to=len(CTX_STEPS) - 1,
            number_of_steps=len(CTX_STEPS) - 1,
            button_color=THEME["slider_knob"],
            button_hover_color=THEME["slider_knob_hover"],
            progress_color=THEME["slider_progress"],
            fg_color=THEME["slider_track"],
            height=16,
            command=self._on_ctx_change,
        )
        self.ctx_slider.set(len(CTX_STEPS) - 1)
        self.ctx_slider.grid(row=3, column=1, sticky="ew", padx=(0, 6), pady=(0, 8))

        self.ctx_badge = ctk.CTkLabel(
            card,
            text="131K",
            font=self.font_badge,
            text_color=THEME["text_primary"],
            width=55,
            anchor="e",
        )
        self.ctx_badge.grid(row=3, column=2, sticky="e", padx=(0, 12), pady=(0, 8))

        # Port & Threads (Subgrid)
        pt_frame = ctk.CTkFrame(card, fg_color="transparent")
        pt_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 8))
        pt_frame.columnconfigure(1, weight=1)
        pt_frame.columnconfigure(3, weight=1)

        ctk.CTkLabel(
            pt_frame,
            text="Port",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=36,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(0, 4))

        self.port_entry = ctk.CTkEntry(
            pt_frame,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=28,
            font=self.font_sm,
        )
        self.port_entry.insert(0, "8082")
        self.port_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ctk.CTkLabel(
            pt_frame,
            text="Threads (-t)",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=70,
            anchor="w",
        ).grid(row=0, column=2, sticky="w", padx=(0, 4))

        self.threads_entry = ctk.CTkEntry(
            pt_frame,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=28,
            font=self.font_sm,
        )
        self.threads_entry.insert(0, "8")
        self.threads_entry.grid(row=0, column=3, sticky="ew")

        # Row 5: Detect GPUs Action Button (Placed below Ports & Threads)
        self.detect_btn = ctk.CTkButton(
            card,
            text="Detect GPUs",
            height=28,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._refresh_devices,
        )
        self.detect_btn.grid(row=5, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 8))

    def _on_ngl_change(self, val):
        v = int(round(val))
        self.ngl_badge.configure(text="99 (All)" if v == 99 else ("0 (CPU)" if v == 0 else str(v)))

    def _on_ctx_change(self, val):
        tokens = CTX_STEPS[int(round(val))]
        self.ctx_badge.configure(text=f"{tokens // 1024}K")

    def _build_batch_sampling_column(self, parent):
        """Column 2: Batching, KV Types, Sampling & Core Toggles."""
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["card_border"],
        )
        card.grid(row=0, column=1, sticky="nsew", padx=4)
        card.columnconfigure(0, weight=0, minsize=75)
        card.columnconfigure(1, weight=1)
        card.columnconfigure(2, weight=0, minsize=48)

        ctk.CTkLabel(
            card,
            text="BATCHING & GENERATION",
            font=self.font_section,
            text_color=THEME["text_primary"],
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 6))

        ctk.CTkLabel(
            card,
            text="Batch (-b)",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(12, 4), pady=(0, 5))

        self.batch_slider = ctk.CTkSlider(
            card,
            from_=0,
            to=len(BATCH_STEPS) - 1,
            number_of_steps=len(BATCH_STEPS) - 1,
            button_color=THEME["slider_knob"],
            button_hover_color=THEME["slider_knob_hover"],
            progress_color=THEME["slider_progress"],
            fg_color=THEME["slider_track"],
            height=16,
            command=self._on_batch_change,
        )
        self.batch_slider.set(BATCH_STEPS.index(1024))
        self.batch_slider.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=(0, 5))

        self.batch_badge = ctk.CTkLabel(
            card,
            text="1024",
            font=self.font_badge,
            text_color=THEME["text_primary"],
            width=48,
            anchor="e",
        )
        self.batch_badge.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=(0, 5))

        ctk.CTkLabel(
            card,
            text="Micro (-ub)",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=(12, 4), pady=(0, 6))

        self.ubatch_slider = ctk.CTkSlider(
            card,
            from_=0,
            to=len(UBATCH_STEPS) - 1,
            number_of_steps=len(UBATCH_STEPS) - 1,
            button_color=THEME["slider_knob"],
            button_hover_color=THEME["slider_knob_hover"],
            progress_color=THEME["slider_progress"],
            fg_color=THEME["slider_track"],
            height=16,
            command=self._on_ubatch_change,
        )
        self.ubatch_slider.set(UBATCH_STEPS.index(256))
        self.ubatch_slider.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=(0, 6))

        self.ubatch_badge = ctk.CTkLabel(
            card,
            text="256",
            font=self.font_badge,
            text_color=THEME["text_primary"],
            width=48,
            anchor="e",
        )
        self.ubatch_badge.grid(row=2, column=2, sticky="e", padx=(0, 12), pady=(0, 6))

        # KV Type K and V Dropdowns
        kv_box = ctk.CTkFrame(card, fg_color="transparent")
        kv_box.grid(row=3, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 6))
        kv_box.columnconfigure(1, weight=1)
        kv_box.columnconfigure(3, weight=1)

        ctk.CTkLabel(
            kv_box,
            text="KV K",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=36,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(0, 4))

        self.ctk_dropdown = ctk.CTkOptionMenu(
            kv_box,
            values=KV_CACHE_TYPES,
            fg_color=THEME["input_bg"],
            button_color="#27272a",
            button_hover_color="#3f3f46",
            text_color=THEME["text_primary"],
            dropdown_fg_color=THEME["dropdown_bg"],
            dropdown_text_color=THEME["text_primary"],
            dropdown_hover_color="#27272a",
            corner_radius=6,
            height=28,
            font=self.font_sm,
        )
        self.ctk_dropdown.set("q8_0")
        self.ctk_dropdown.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(
            kv_box,
            text="KV V",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=36,
            anchor="w",
        ).grid(row=0, column=2, sticky="w", padx=(0, 4))

        self.ctv_dropdown = ctk.CTkOptionMenu(
            kv_box,
            values=KV_CACHE_TYPES,
            fg_color=THEME["input_bg"],
            button_color="#27272a",
            button_hover_color="#3f3f46",
            text_color=THEME["text_primary"],
            dropdown_fg_color=THEME["dropdown_bg"],
            dropdown_text_color=THEME["text_primary"],
            dropdown_hover_color="#27272a",
            corner_radius=6,
            height=28,
            font=self.font_sm,
        )
        self.ctv_dropdown.set("q8_0")
        self.ctv_dropdown.grid(row=0, column=3, sticky="ew")

        # Sampling (Temp, Top-P, Min-P)
        samp_box = ctk.CTkFrame(card, fg_color="transparent")
        samp_box.grid(row=4, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 6))
        samp_box.columnconfigure(1, weight=1)
        samp_box.columnconfigure(3, weight=1)
        samp_box.columnconfigure(5, weight=1)

        ctk.CTkLabel(
            samp_box,
            text="Temp",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=34,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(0, 3))
        self.temp_entry = ctk.CTkEntry(
            samp_box,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=28,
            font=self.font_sm,
        )
        self.temp_entry.insert(0, "0.5")
        self.temp_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))

        ctk.CTkLabel(
            samp_box,
            text="Top-P",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=38,
            anchor="w",
        ).grid(row=0, column=2, sticky="w", padx=(0, 3))
        self.topp_entry = ctk.CTkEntry(
            samp_box,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=28,
            font=self.font_sm,
        )
        self.topp_entry.insert(0, "0.95")
        self.topp_entry.grid(row=0, column=3, sticky="ew", padx=(0, 6))

        ctk.CTkLabel(
            samp_box,
            text="Min-P",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=38,
            anchor="w",
        ).grid(row=0, column=4, sticky="w", padx=(0, 3))
        self.minp_entry = ctk.CTkEntry(
            samp_box,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=28,
            font=self.font_sm,
        )
        self.minp_entry.insert(0, "0.05")
        self.minp_entry.grid(row=0, column=5, sticky="ew")

        # Core Toggles (Flash Attention, Jinja)
        tog_box = ctk.CTkFrame(card, fg_color="transparent")
        tog_box.grid(row=5, column=0, columnspan=3, sticky="ew", padx=12, pady=(2, 8))

        self.fa_var = ctk.BooleanVar(value=True)
        self.jinja_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            tog_box,
            text="Flash Attention (-fa)",
            variable=self.fa_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_primary"],
            fg_color=THEME["checkbox_active"],
            hover_color=THEME["checkbox_hover"],
            border_color=THEME["checkbox_border"],
            border_width=2,
            corner_radius=4,
            height=22,
        ).pack(side="left", padx=(0, 12))

        ctk.CTkCheckBox(
            tog_box,
            text="Jinja Template (--jinja)",
            variable=self.jinja_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_primary"],
            fg_color=THEME["checkbox_active"],
            hover_color=THEME["checkbox_hover"],
            border_color=THEME["checkbox_border"],
            border_width=2,
            corner_radius=4,
            height=22,
        ).pack(side="left")

    def _on_batch_change(self, val):
        self.batch_badge.configure(text=str(BATCH_STEPS[int(round(val))]))

    def _on_ubatch_change(self, val):
        self.ubatch_badge.configure(text=str(UBATCH_STEPS[int(round(val))]))

    def _build_optimizations_column(self, parent):
        """Column 3: Hardware profile options."""
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["card_border"],
        )
        card.grid(row=0, column=2, sticky="nsew", padx=(4, 0))
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)

        ctk.CTkLabel(
            card,
            text="9070 XT & 32GB PROFILE",
            font=self.font_section,
            text_color=THEME["text_primary"],
        ).grid(row=0, column=0, sticky="w", padx=(12, 4), pady=(8, 4))

        ctk.CTkLabel(
            card,
            text="(Check to edit)",
            font=ctk.CTkFont(family="Segoe UI", size=10, slant="italic"),
            text_color=THEME["text_muted"],
        ).grid(row=0, column=1, sticky="e", padx=(0, 12), pady=(8, 4))

        self.opt_vars = {}
        self.opt_str_vars = {}
        self.opt_widgets = {}

        opts_config = [
            ("mlock", "Lock in RAM (--load-mode)", "dropdown", "mlock", ["mlock", "mmap+mlock"]),
            ("tb", "Prompt Threads (-tb)", "entry", "8", None),
            ("fit_target", "VRAM Margin (--fit-target MiB)", "entry", "1024", None),
            ("cache_reuse", "KV Cache Reuse (--cache-reuse)", "entry", "256", None),
            ("parallel", "Dedicated Slot (-np)", "entry", "1", None),
            ("cache_ram", "System RAM Cache (--cache-ram MiB)", "entry", "8192", None),
            ("cpu_moe", "CPU MoE Experts (--n-cpu-moe)", "entry", "16", None),
        ]

        for idx, (key, label, w_type, default_val, options) in enumerate(opts_config, start=1):
            self.opt_vars[key] = ctk.BooleanVar(value=False)
            self.opt_str_vars[key] = ctk.StringVar(value=default_val)

            chk = ctk.CTkCheckBox(
                card,
                text=label,
                variable=self.opt_vars[key],
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=THEME["text_primary"],
                fg_color=THEME["checkbox_active"],
                hover_color=THEME["checkbox_hover"],
                border_color=THEME["checkbox_border"],
                border_width=2,
                corner_radius=4,
                height=24,
                command=lambda k=key: self._toggle_opt_widget(k),
            )
            chk.grid(row=idx, column=0, sticky="w", padx=(12, 4), pady=2)

            if w_type == "dropdown":
                widget = ctk.CTkOptionMenu(
                    card,
                    values=options,
                    variable=self.opt_str_vars[key],
                    fg_color=THEME["input_bg"],
                    button_color="#27272a",
                    button_hover_color="#3f3f46",
                    text_color=THEME["text_primary"],
                    dropdown_fg_color=THEME["dropdown_bg"],
                    dropdown_text_color=THEME["text_primary"],
                    dropdown_hover_color=THEME["secondary_btn_hover"],
                    corner_radius=6,
                    height=24,
                    width=92,
                    font=ctk.CTkFont(family="Segoe UI", size=10),
                    state="disabled",
                )
            else:
                widget = ctk.CTkEntry(
                    card,
                    textvariable=self.opt_str_vars[key],
                    fg_color=THEME["input_bg"],
                    border_color=THEME["input_border"],
                    border_width=1,
                    text_color=THEME["text_muted"],
                    corner_radius=6,
                    height=24,
                    width=68,
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    state="disabled",
                )

            widget.grid(row=idx, column=1, sticky="e", padx=(0, 12), pady=2)
            self.opt_widgets[key] = widget

    def _toggle_opt_widget(self, key):
        is_active = self.opt_vars[key].get()
        widget = self.opt_widgets[key]

        if is_active:
            widget.configure(state="normal")
            if isinstance(widget, ctk.CTkEntry):
                widget.configure(text_color=THEME["text_primary"])
        else:
            if isinstance(widget, ctk.CTkEntry):
                widget.configure(text_color=THEME["text_muted"])
            widget.configure(state="disabled")

    def _build_launch_action(self):
        self.server_proc = None

        action_row = ctk.CTkFrame(self.main_container, fg_color="transparent")
        action_row.pack(fill="x", padx=2, pady=(2, 0))
        action_row.columnconfigure(0, weight=3)
        action_row.columnconfigure(1, weight=1)
        action_row.columnconfigure(2, weight=1)
        action_row.columnconfigure(3, weight=1)
        action_row.columnconfigure(4, weight=1)
        action_row.columnconfigure(5, weight=1)

        self.start_btn = ctk.CTkButton(
            action_row,
            text="🚀  Start Model Server",
            height=42,
            fg_color=THEME["primary_btn_bg"],
            hover_color=THEME["primary_btn_hover"],
            border_width=1,
            border_color=THEME["primary_btn_border"],
            font=self.font_btn,
            text_color=THEME["primary_btn_text"],
            corner_radius=8,
            command=self.toggle_server,
        )
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.open_webui_btn = ctk.CTkButton(
            action_row,
            text="🌐  Open Web UI",
            height=42,
            fg_color="#18181b",
            hover_color="#27272a",
            border_width=1,
            border_color="#3f3f46",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["text_muted"],
            corner_radius=8,
            command=self.open_web_ui,
            state="disabled",
        )
        self.open_webui_btn.grid(row=0, column=1, sticky="ew", padx=(0, 6))

        self.client_configs_btn = ctk.CTkButton(
            action_row,
            text="⚙️  Client Configs",
            height=42,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["secondary_btn_text"],
            corner_radius=8,
            command=self.open_client_configs,
        )
        self.client_configs_btn.grid(row=0, column=2, sticky="ew", padx=(0, 6))

        self.api_tester_btn = ctk.CTkButton(
            action_row,
            text="🔍  API Tester",
            height=42,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["secondary_btn_text"],
            corner_radius=8,
            command=self.open_api_tester,
        )
        self.api_tester_btn.grid(row=0, column=3, sticky="ew", padx=(0, 6))

        self.export_script_btn = ctk.CTkButton(
            action_row,
            text="💾  Export .ps1",
            height=42,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["secondary_btn_text"],
            corner_radius=8,
            command=self.export_script,
        )
        self.export_script_btn.grid(row=0, column=4, sticky="ew", padx=(0, 6))

        self.import_script_btn = ctk.CTkButton(
            action_row,
            text="📥  Import .ps1",
            height=42,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["secondary_btn_text"],
            corner_radius=8,
            command=self.import_settings,
        )
        self.import_script_btn.grid(row=0, column=5, sticky="ew")

    def _build_log_drawer(self):
        """Build bottom collapsible log drawer and desktop ergonomics toolbar."""
        self.drawer_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.drawer_container.pack(fill="x", padx=2, pady=(6, 0))

        # Bottom Ergonomics & Drawer Control Toolbar
        self.drawer_bar = ctk.CTkFrame(self.drawer_container, fg_color="transparent")
        self.drawer_bar.pack(fill="x")

        # Toggle Button on the left
        self.drawer_toggle_btn = ctk.CTkButton(
            self.drawer_bar,
            text="📝  Log Console (▲ Expand)",
            height=28,
            width=180,
            fg_color="#18181b",
            hover_color="#27272a",
            border_width=1,
            border_color="#3f3f46",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#e4e4e7",
            corner_radius=6,
            command=self.toggle_log_drawer,
        )
        self.drawer_toggle_btn.pack(side="left", padx=(0, 10))

        # Watchdog & window mode checkboxes
        self.auto_restart_chk = ctk.CTkCheckBox(
            self.drawer_bar,
            text="🔄 Auto-Restart on Crash",
            variable=self.auto_restart_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_primary"],
            fg_color=THEME["checkbox_active"],
            hover_color=THEME["checkbox_hover"],
            border_color=THEME["checkbox_border"],
            border_width=2,
            corner_radius=4,
            height=24,
        )
        self.auto_restart_chk.pack(side="left", padx=(0, 12))

        self.external_console_chk = ctk.CTkCheckBox(
            self.drawer_bar,
            text="🪟 External CMD Window",
            variable=self.external_console_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_primary"],
            fg_color=THEME["checkbox_active"],
            hover_color=THEME["checkbox_hover"],
            border_color=THEME["checkbox_border"],
            border_width=2,
            corner_radius=4,
            height=24,
        )
        self.external_console_chk.pack(side="left", padx=(0, 12))

        self.tray_close_chk = ctk.CTkCheckBox(
            self.drawer_bar,
            text="📥 Minimize to Tray on Close",
            variable=self.minimize_to_tray_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_primary"],
            fg_color=THEME["checkbox_active"],
            hover_color=THEME["checkbox_hover"],
            border_color=THEME["checkbox_border"],
            border_width=2,
            corner_radius=4,
            height=24,
        )
        self.tray_close_chk.pack(side="left", padx=(0, 10))

        # Tray quick button on the right
        self.tray_btn = ctk.CTkButton(
            self.drawer_bar,
            text="📌  Minimize to Tray",
            height=28,
            width=135,
            fg_color="#18181b",
            hover_color="#27272a",
            border_width=1,
            border_color="#3f3f46",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#a1a1aa",
            corner_radius=6,
            command=self.hide_to_tray,
        )
        self.tray_btn.pack(side="right")

        # Collapsible Drawer Body (hidden by default)
        self.drawer_body = ctk.CTkFrame(
            self.drawer_container,
            fg_color=THEME["card_bg"],
            corner_radius=8,
            border_width=1,
            border_color=THEME["card_border"],
        )

        # Header within drawer body: Search / Filter & Actions
        filter_row = ctk.CTkFrame(self.drawer_body, fg_color="transparent")
        filter_row.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            filter_row,
            text="🔍 Filter:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(side="left", padx=(0, 6))

        self.log_filter_entry = ctk.CTkEntry(
            filter_row,
            placeholder_text="Filter logs by keyword or regex...",
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            placeholder_text_color=THEME["text_muted"],
            corner_radius=6,
            height=26,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self.log_filter_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.log_filter_entry.bind("<KeyRelease>", self._on_log_filter_changed)

        ctk.CTkCheckBox(
            filter_row,
            text="Auto-Scroll",
            variable=self.log_autoscroll_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_secondary"],
            fg_color=THEME["checkbox_active"],
            hover_color=THEME["checkbox_hover"],
            border_color=THEME["checkbox_border"],
            border_width=2,
            corner_radius=4,
            height=24,
            width=20,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            filter_row,
            text="📋 Copy",
            height=26,
            width=65,
            fg_color="#18181b",
            hover_color="#27272a",
            border_width=1,
            border_color="#3f3f46",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#e4e4e7",
            corner_radius=6,
            command=self.copy_logs,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            filter_row,
            text="🗑️ Clear",
            height=26,
            width=65,
            fg_color="#18181b",
            hover_color="#27272a",
            border_width=1,
            border_color="#3f3f46",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#e4e4e7",
            corner_radius=6,
            command=self.clear_logs,
        ).pack(side="left")

        # Terminal text box
        self.log_textbox = ctk.CTkTextbox(
            self.drawer_body,
            height=140,
            fg_color="#0e0e11",
            border_color="#222226",
            border_width=1,
            text_color="#e4e4e7",
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=6,
            wrap="none",
        )
        self.log_textbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log_textbox.insert("1.0", "[SYSTEM] Log console initialized. Ready to stream llama-server engine output.\n")
        self.log_textbox.configure(state="disabled")

    def toggle_log_drawer(self):
        """Expand or collapse the in-window embedded log drawer."""
        self.log_drawer_expanded = not self.log_drawer_expanded
        curr_w = self.winfo_width()
        curr_h = self.winfo_height()

        if self.log_drawer_expanded:
            self.drawer_body.pack(fill="both", expand=True, pady=(6, 0))
            self.drawer_toggle_btn.configure(text="📝  Log Console (▼ Collapse)")
            if curr_h < 750:
                self.geometry(f"{max(curr_w, 1184)}x{max(curr_h + 175, 795)}")
        else:
            self.drawer_body.pack_forget()
            self.drawer_toggle_btn.configure(text="📝  Log Console (▲ Expand)")
            if curr_h >= 750:
                self.geometry(f"{max(curr_w, 1184)}x{max(curr_h - 175, 625)}")

    def open_log_console(self):
        """Bring window to foreground and ensure log drawer is open."""
        self.show_window()
        if not self.log_drawer_expanded:
            self.toggle_log_drawer()

    def _on_log_filter_changed(self, event=None):
        """Filter log lines in real-time according to search text or regex."""
        if not hasattr(self, "log_textbox") or not hasattr(self, "log_filter_entry"):
            return
        query = self.log_filter_entry.get().strip().lower()
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        for line in self.log_buffer:
            if not query or query in line.lower():
                self.log_textbox.insert("end", line)
        self.log_textbox.configure(state="disabled")
        if self.log_autoscroll_var.get():
            try:
                self.log_textbox.see("end")
            except Exception:
                pass

    def _process_log_queue(self):
        """Pull real-time stdout lines from worker queue and stream to textbox."""
        lines_added = False
        query = self.log_filter_entry.get().strip().lower() if hasattr(self, "log_filter_entry") else ""

        while True:
            try:
                line = self.log_queue.get_nowait()
                self.log_buffer.append(line)
                if not query or query in line.lower():
                    self._append_to_log_textbox(line)
                    lines_added = True
            except queue.Empty:
                break

        if lines_added and self.log_autoscroll_var.get() and hasattr(self, "log_textbox"):
            try:
                self.log_textbox.see("end")
            except Exception:
                pass

        self.after(50, self._process_log_queue)

    def _append_to_log_textbox(self, line: str):
        if not hasattr(self, "log_textbox"):
            return
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", line)
        self.log_textbox.configure(state="disabled")

    def _log_system(self, msg: str):
        """Write a formatted system/launcher notification line to the log console."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}\n"
        self.log_queue.put(formatted)

    def clear_logs(self):
        """Clear current buffer and log textbox contents."""
        self.log_buffer.clear()
        if hasattr(self, "log_textbox"):
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")
            self.log_textbox.configure(state="disabled")

    def copy_logs(self):
        """Copy all visible logs to the Windows clipboard."""
        if hasattr(self, "log_textbox"):
            content = self.log_textbox.get("1.0", "end-1c")
            try:
                self.clipboard_clear()
                self.clipboard_append(content)
                self.update()
                self._flash_badge("✓ COPIED ALL LOGS")
            except Exception:
                pass

    def open_web_ui(self):
        """Open local llama-server web UI in the default browser."""
        port = self.port_entry.get().strip() if hasattr(self, "port_entry") else "8082"
        url = f"http://127.0.0.1:{port}"
        try:
            webbrowser.open(url)
            self._flash_badge(f"● OPENED BROWSER: PORT {port}")
            self._log_system(f"🌐 Opened browser to {url}")
        except Exception as e:
            self._flash_badge(f"⚠ FAILED TO OPEN BROWSER: {e}", is_alert=True)
            self._log_system(f"⚠ Failed to open browser: {e}")

    def open_client_configs(self):
        """Open the Client & Frontend Integrations configuration dialog."""
        port = self.port_entry.get().strip() if hasattr(self, "port_entry") else "8082"
        model_path = self.model_entry.get().strip() if hasattr(self, "model_entry") else ""
        ClientConfigDialog(port=port, model_path=model_path, master=self)

    def open_api_tester(self):
        """Open the API Endpoint Tester & Health Check dialog."""
        port = self.port_entry.get().strip() if hasattr(self, "port_entry") else "8082"
        EndpointTesterDialog(port=port, master=self)

    def browse_exe(self):
        f = filedialog.askopenfilename(
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")],
            title="Select llama-server.exe"
        )
        if f:
            self.exe_entry.delete(0, "end")
            self.exe_entry.insert(0, os.path.normpath(f))
            self._refresh_devices()

    def browse_model(self):
        f = filedialog.askopenfilename(filetypes=[("GGUF Files", "*.gguf")])
        if f:
            norm_path = os.path.normpath(f)
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, norm_path)
            self._add_recent_model(norm_path)
            self._auto_detect_vision_mmproj(norm_path)

    def _build_command_args(self):
        """Validate input paths and construct full argument list for llama-server."""
        exe_raw = self.exe_entry.get().strip().strip('"').strip("'")
        model_raw = self.model_entry.get().strip().strip('"').strip("'")
        if not model_raw:
            self._flash_badge("⚠ SELECT MODEL GGUF", is_alert=True)
            return None

        exe = os.path.normpath(exe_raw)
        model = os.path.normpath(model_raw)

        if not os.path.exists(exe):
            self._flash_badge("⚠ INVALID LLAMA-SERVER PATH", is_alert=True)
            return None

        # Vision Model mmproj validation
        mmproj = ""
        if self.vision_var.get():
            mmproj_raw = self.mmproj_entry.get().strip().strip('"').strip("'")
            if not mmproj_raw:
                self._flash_badge("⚠ SELECT MMPROJ GGUF", is_alert=True)
                return None
            mmproj = os.path.normpath(mmproj_raw)

        selected_device_display = self.device_dropdown.get()
        device_id = self.device_map.get(selected_device_display, "Vulkan0")

        gpu_layers = str(int(round(self.ngl_slider.get())))
        ctx_tokens = str(CTX_STEPS[int(round(self.ctx_slider.get()))])
        batch_size = str(BATCH_STEPS[int(round(self.batch_slider.get()))])
        micro_batch = str(UBATCH_STEPS[int(round(self.ubatch_slider.get()))])

        cmd = [
            exe,
            "-m", model,
        ]

        if self.vision_var.get() and mmproj:
            cmd.extend(["--mmproj", mmproj])

        cmd.extend([
            "--device", device_id,
            "-ngl", gpu_layers,
            "-c", ctx_tokens,
            "-t", self.threads_entry.get().strip(),
            "-b", batch_size,
            "-ub", micro_batch,
            "-ctk", self.ctk_dropdown.get(),
            "-ctv", self.ctv_dropdown.get(),
            "--host", "127.0.0.1",
            "--port", self.port_entry.get().strip(),
            "--temp", self.temp_entry.get().strip(),
            "--top-p", self.topp_entry.get().strip(),
            "--min-p", self.minp_entry.get().strip(),
        ])

        if self.fa_var.get():
            cmd.extend(["-fa", "on"])
        if self.jinja_var.get():
            cmd.append("--jinja")

        if self.opt_vars["mlock"].get():
            val = self.opt_str_vars["mlock"].get().strip() or "mlock"
            cmd.extend(["--load-mode", val])
        if self.opt_vars["tb"].get():
            val = self.opt_str_vars["tb"].get().strip() or "8"
            cmd.extend(["-tb", val])
        if self.opt_vars["fit_target"].get():
            val = self.opt_str_vars["fit_target"].get().strip() or "1024"
            cmd.extend(["--fit-target", val])
        if self.opt_vars["cache_reuse"].get():
            val = self.opt_str_vars["cache_reuse"].get().strip() or "256"
            cmd.extend(["--cache-reuse", val])
        if self.opt_vars["parallel"].get():
            val = self.opt_str_vars["parallel"].get().strip() or "1"
            cmd.extend(["-np", val])
        if self.opt_vars["cache_ram"].get():
            val = self.opt_str_vars["cache_ram"].get().strip() or "8192"
            cmd.extend(["--cache-ram", val])
        if self.opt_vars.get("cpu_moe") and self.opt_vars["cpu_moe"].get():
            val = self.opt_str_vars["cpu_moe"].get().strip() or "16"
            cmd.extend(["--n-cpu-moe", val])

        return cmd

    def _build_current_settings_dict(self) -> dict:
        """Serialize the current launcher GUI state to a JSON-compatible dictionary."""
        ctx_idx = int(round(self.ctx_slider.get()))
        batch_idx = int(round(self.batch_slider.get()))
        ubatch_idx = int(round(self.ubatch_slider.get()))

        return {
            "version": "1.3.0",
            "exported_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exe": self.exe_entry.get().strip().strip('"').strip("'"),
            "model": self.model_entry.get().strip().strip('"').strip("'"),
            "vision_enabled": bool(self.vision_var.get()) if hasattr(self, "vision_var") else False,
            "mmproj": self.mmproj_entry.get().strip().strip('"').strip("'") if hasattr(self, "mmproj_entry") and self.vision_var.get() else "",
            "device": self.device_dropdown.get() if hasattr(self, "device_dropdown") else "Vulkan0",
            "ngl": int(round(self.ngl_slider.get())),
            "ctx_index": ctx_idx,
            "ctx_tokens": CTX_STEPS[ctx_idx],
            "batch_index": batch_idx,
            "batch_size": BATCH_STEPS[batch_idx],
            "ubatch_index": ubatch_idx,
            "ubatch_size": UBATCH_STEPS[ubatch_idx],
            "threads": self.threads_entry.get().strip(),
            "port": self.port_entry.get().strip(),
            "ctk": self.ctk_dropdown.get() if hasattr(self, "ctk_dropdown") else "q8_0",
            "ctv": self.ctv_dropdown.get() if hasattr(self, "ctv_dropdown") else "q8_0",
            "temp": self.temp_entry.get().strip(),
            "topp": self.topp_entry.get().strip(),
            "minp": self.minp_entry.get().strip(),
            "flash_attention": bool(self.fa_var.get()) if hasattr(self, "fa_var") else True,
            "jinja": bool(self.jinja_var.get()) if hasattr(self, "jinja_var") else True,
            "optimizations": {
                k: {
                    "enabled": bool(self.opt_vars[k].get()),
                    "value": self.opt_str_vars[k].get().strip()
                }
                for k in self.opt_vars
            }
        }

    def export_script(self):
        """Export current settings & CLI launcher to a PowerShell (.ps1) script wherever the user chooses."""
        cmd_args = self._build_command_args()
        if not cmd_args:
            return

        exe = cmd_args[0]
        args_list = cmd_args[1:]
        model_raw = self.model_entry.get().strip().strip('"').strip("'")
        model_name = os.path.basename(model_raw) if model_raw else "model.gguf"
        suggested_name = f"run_{os.path.splitext(model_name)[0]}"

        file_path = filedialog.asksaveasfilename(
            title="Export Settings to PowerShell Script",
            initialfile=suggested_name,
            defaultextension=".ps1",
            filetypes=[
                ("PowerShell Script (*.ps1)", "*.ps1"),
                ("Batch Script (*.bat)", "*.bat"),
                ("All Files (*.*)", "*.*"),
            ]
        )
        if not file_path:
            return

        is_ps1 = file_path.lower().endswith(".ps1")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare embedded settings JSON
        settings_dict = self._build_current_settings_dict()
        formatted_json = json.dumps(settings_dict, indent=2)

        if is_ps1:
            ps_args = "\n    ".join([f'"{arg}"' for arg in args_list])
            commented_json = "\n".join([f"# {line}" for line in formatted_json.splitlines()])
            content = (
                f"# =====================================================================\n"
                f"# LLauncher - Exported llama-server PowerShell Script & Configuration\n"
                f"# Model: {model_name}\n"
                f"# Generated: {timestamp}\n"
                f"# =====================================================================\n\n"
                f"$env:GGML_VK_DISABLE_PINNED = '1'\n\n"
                f"$llamaExe = \"{exe}\"\n\n"
                f"$serverArgs = @(\n"
                f"    {ps_args}\n"
                f")\n\n"
                f"Write-Host \"Starting llama-server for {model_name}...\" -ForegroundColor Cyan\n"
                f"& $llamaExe @serverArgs\n\n"
                f"# =====================================================================\n"
                f"# LLauncher Embedded Settings (For importing back into LLauncher)\n"
                f"# <LLAUNCHER_SETTINGS_JSON>\n"
                f"{commented_json}\n"
                f"# </LLAUNCHER_SETTINGS_JSON>\n"
                f"# =====================================================================\n"
            )
        else:
            bat_cmd = f'"{exe}" ' + " ".join([f'"{a}"' if ' ' in a else a for a in args_list])
            rem_json = "\n".join([f"REM {line}" for line in formatted_json.splitlines()])
            content = (
                f"@echo off\n"
                f"REM =====================================================================\n"
                f"REM LLauncher - Exported llama-server Batch Script & Configuration\n"
                f"REM Model: {model_name}\n"
                f"REM Generated: {timestamp}\n"
                f"REM =====================================================================\n\n"
                f"set \"GGML_VK_DISABLE_PINNED=1\"\n\n"
                f"echo Starting llama-server for {model_name}...\n"
                f"{bat_cmd}\n\n"
                f"REM =====================================================================\n"
                f"REM LLauncher Embedded Settings (For importing back into LLauncher)\n"
                f"REM <LLAUNCHER_SETTINGS_JSON>\n"
                f"{rem_json}\n"
                f"REM </LLAUNCHER_SETTINGS_JSON>\n"
                f"REM =====================================================================\n\n"
                f"pause\n"
            )

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._flash_badge(f"✓ EXPORTED: {os.path.basename(file_path)}")
            self._log_system(f"💾 Exported settings script to: {file_path}")
        except Exception as e:
            self._flash_badge(f"⚠ EXPORT FAILED: {e}", is_alert=True)
            self._log_system(f"⚠ Export failed: {e}")

    export_settings = export_script

    def import_settings(self):
        """Import launcher settings from an exported PowerShell (.ps1) script or batch file."""
        file_path = filedialog.askopenfilename(
            title="Import Settings from Script",
            filetypes=[
                ("PowerShell Script (*.ps1)", "*.ps1"),
                ("Batch Script (*.bat)", "*.bat"),
                ("All Supported Scripts", "*.ps1;*.bat"),
                ("All Files (*.*)", "*.*"),
            ]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            self._flash_badge(f"⚠ FAILED TO READ: {e}", is_alert=True)
            self._log_system(f"⚠ Failed to read script: {e}")
            return

        # Check for embedded LLAUNCHER_SETTINGS_JSON block
        json_match = re.search(r'(?:#|REM)\s*<LLAUNCHER_SETTINGS_JSON>\s*\n(.*?)\n(?:#|REM)\s*</LLAUNCHER_SETTINGS_JSON>', content, re.DOTALL)
        if json_match:
            try:
                raw_lines = json_match.group(1).splitlines()
                cleaned_lines = []
                for line in raw_lines:
                    l = line.strip()
                    if l.startswith("REM"):
                        l = l[3:].strip()
                    elif l.startswith("#"):
                        l = l[1:].strip()
                    cleaned_lines.append(l)
                cleaned_json = "\n".join(cleaned_lines)
                settings = json.loads(cleaned_json)
                self._apply_imported_settings_dict(settings)
                self._flash_badge(f"✓ IMPORTED: {os.path.basename(file_path)}")
                self._log_system(f"📥 Imported settings from: {file_path}")
                return
            except Exception as e:
                self._log_system(f"⚠ Embedded JSON parse failed, falling back to CLI argument parser: {e}")

        # Fallback: parse command arguments directly from script text
        success = self._parse_and_apply_script_args(content)
        if success:
            self._flash_badge(f"✓ IMPORTED: {os.path.basename(file_path)}")
            self._log_system(f"📥 Imported CLI parameters from: {file_path}")
        else:
            self._flash_badge("⚠ NO SETTINGS FOUND", is_alert=True)
            self._log_system("⚠ Could not detect valid llama-server parameters in selected file.")

    import_script = import_settings

    def _apply_imported_settings_dict(self, s: dict):
        """Apply a deserialized settings dictionary to the UI elements."""
        if s.get("exe") and hasattr(self, "exe_entry"):
            self.exe_entry.delete(0, "end")
            self.exe_entry.insert(0, s["exe"])
            self._refresh_devices()

        if s.get("model") and hasattr(self, "model_entry"):
            norm_m = os.path.normpath(s["model"])
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, norm_m)
            self._add_recent_model(norm_m)

        if hasattr(self, "vision_var"):
            self.vision_var.set(s.get("vision_enabled", False))
            if hasattr(self, "mmproj_entry"):
                self.mmproj_entry.delete(0, "end")
                if s.get("mmproj"):
                    self.mmproj_entry.insert(0, s["mmproj"])
            self._toggle_vision()

        if s.get("device") and hasattr(self, "device_dropdown"):
            dev_str = s["device"]
            for k in self.device_map:
                if self.device_map[k] == dev_str or k == dev_str:
                    self.device_dropdown.set(k)
                    break

        if "ngl" in s and hasattr(self, "ngl_slider"):
            ngl_val = int(s["ngl"])
            self.ngl_slider.set(ngl_val)
            self._on_ngl_change(ngl_val)

        if hasattr(self, "ctx_slider"):
            if "ctx_index" in s:
                ctx_idx = int(s["ctx_index"])
            elif "ctx_tokens" in s:
                tokens = int(s["ctx_tokens"])
                ctx_idx = min(range(len(CTX_STEPS)), key=lambda i: abs(CTX_STEPS[i] - tokens))
            else:
                ctx_idx = len(CTX_STEPS) - 1
            self.ctx_slider.set(ctx_idx)
            self._on_ctx_change(ctx_idx)

        if hasattr(self, "batch_slider"):
            if "batch_index" in s:
                b_idx = int(s["batch_index"])
            elif "batch_size" in s:
                bs = int(s["batch_size"])
                b_idx = min(range(len(BATCH_STEPS)), key=lambda i: abs(BATCH_STEPS[i] - bs))
            else:
                b_idx = BATCH_STEPS.index(1024) if 1024 in BATCH_STEPS else 0
            self.batch_slider.set(b_idx)
            self._on_batch_change(b_idx)

        if hasattr(self, "ubatch_slider"):
            if "ubatch_index" in s:
                ub_idx = int(s["ubatch_index"])
            elif "ubatch_size" in s:
                ubs = int(s["ubatch_size"])
                ub_idx = min(range(len(UBATCH_STEPS)), key=lambda i: abs(UBATCH_STEPS[i] - ubs))
            else:
                ub_idx = UBATCH_STEPS.index(256) if 256 in UBATCH_STEPS else 0
            self.ubatch_slider.set(ub_idx)
            self._on_ubatch_change(ub_idx)

        if hasattr(self, "port_entry") and "port" in s:
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, str(s["port"]))

        if hasattr(self, "threads_entry") and "threads" in s:
            self.threads_entry.delete(0, "end")
            self.threads_entry.insert(0, str(s["threads"]))

        if hasattr(self, "ctk_dropdown") and s.get("ctk") in KV_CACHE_TYPES:
            self.ctk_dropdown.set(s["ctk"])
        if hasattr(self, "ctv_dropdown") and s.get("ctv") in KV_CACHE_TYPES:
            self.ctv_dropdown.set(s["ctv"])

        if hasattr(self, "temp_entry") and "temp" in s:
            self.temp_entry.delete(0, "end")
            self.temp_entry.insert(0, str(s["temp"]))

        if hasattr(self, "topp_entry") and "topp" in s:
            self.topp_entry.delete(0, "end")
            self.topp_entry.insert(0, str(s["topp"]))

        if hasattr(self, "minp_entry") and "minp" in s:
            self.minp_entry.delete(0, "end")
            self.minp_entry.insert(0, str(s["minp"]))

        if hasattr(self, "fa_var") and "flash_attention" in s:
            self.fa_var.set(bool(s["flash_attention"]))

        if hasattr(self, "jinja_var") and "jinja" in s:
            self.jinja_var.set(bool(s["jinja"]))

        opts = s.get("optimizations", {})
        for k in self.opt_vars:
            if k in opts:
                opt_item = opts[k]
                if isinstance(opt_item, dict):
                    self.opt_vars[k].set(bool(opt_item.get("enabled", False)))
                    if "value" in opt_item:
                        self.opt_str_vars[k].set(str(opt_item["value"]))
                    elif "val" in opt_item:
                        self.opt_str_vars[k].set(str(opt_item["val"]))
                else:
                    self.opt_vars[k].set(bool(opt_item))
            self._toggle_opt_widget(k)

    def _parse_and_apply_script_args(self, content: str) -> bool:
        """Fallback parser to extract llama-server command arguments from script text."""
        found_any = False

        # Model: -m <path> or -m, "<path>"
        m_match = re.search(r'(?:-m|--model)\s+["\']?([^"\'\r\n\t,]+)["\']?|["\'](?:-m|--model)["\']\s*,\s*["\']([^"\']+)["\']', content)
        if m_match:
            model_path = m_match.group(1) or m_match.group(2)
            if model_path:
                self.model_entry.delete(0, "end")
                self.model_entry.insert(0, os.path.normpath(model_path.strip()))
                self._add_recent_model(os.path.normpath(model_path.strip()))
                found_any = True

        # Exe: $llamaExe = "..." or "path/llama-server.exe"
        exe_match = re.search(r'\$llamaExe\s*=\s*["\']([^"\']+)["\']|["\']([^"\']*llama-server(?:\.exe)?)[ "\']', content, re.IGNORECASE)
        if exe_match:
            exe_path = exe_match.group(1) or exe_match.group(2)
            if exe_path and os.path.exists(exe_path):
                self.exe_entry.delete(0, "end")
                self.exe_entry.insert(0, os.path.normpath(exe_path.strip()))

        # Vision mmproj: --mmproj <path>
        mm_match = re.search(r'--mmproj\s+["\']?([^"\'\r\n\t,]+)["\']?|["\']--mmproj["\']\s*,\s*["\']([^"\']+)["\']', content)
        if mm_match:
            mm_path = mm_match.group(1) or mm_match.group(2)
            if mm_path:
                self.vision_var.set(True)
                self._toggle_vision()
                self.mmproj_entry.delete(0, "end")
                self.mmproj_entry.insert(0, os.path.normpath(mm_path.strip()))
                found_any = True

        # NGL: -ngl <num>
        ngl_match = re.search(r'(?:-ngl|--n-gpu-layers)\s+["\']?(\d+)["\']?|["\'](?:-ngl|--n-gpu-layers)["\']\s*,\s*["\'](\d+)["\']', content)
        if ngl_match:
            val = int(ngl_match.group(1) or ngl_match.group(2))
            self.ngl_slider.set(val)
            self._on_ngl_change(val)
            found_any = True

        # Context: -c <num>
        ctx_match = re.search(r'(?:-c|--ctx-size)\s+["\']?(\d+)["\']?|["\'](?:-c|--ctx-size)["\']\s*,\s*["\'](\d+)["\']', content)
        if ctx_match:
            tokens = int(ctx_match.group(1) or ctx_match.group(2))
            idx = min(range(len(CTX_STEPS)), key=lambda i: abs(CTX_STEPS[i] - tokens))
            self.ctx_slider.set(idx)
            self._on_ctx_change(idx)
            found_any = True

        # Batch: -b <num>
        b_match = re.search(r'(?:-b|--batch-size)\s+["\']?(\d+)["\']?|["\'](?:-b|--batch-size)["\']\s*,\s*["\'](\d+)["\']', content)
        if b_match:
            bs = int(b_match.group(1) or b_match.group(2))
            idx = min(range(len(BATCH_STEPS)), key=lambda i: abs(BATCH_STEPS[i] - bs))
            self.batch_slider.set(idx)
            self._on_batch_change(idx)
            found_any = True

        # Micro-batch: -ub <num>
        ub_match = re.search(r'(?:-ub|--ubatch-size)\s+["\']?(\d+)["\']?|["\'](?:-ub|--ubatch-size)["\']\s*,\s*["\'](\d+)["\']', content)
        if ub_match:
            ubs = int(ub_match.group(1) or ub_match.group(2))
            idx = min(range(len(UBATCH_STEPS)), key=lambda i: abs(UBATCH_STEPS[i] - ubs))
            self.ubatch_slider.set(idx)
            self._on_ubatch_change(idx)
            found_any = True

        # Threads: -t <num>
        t_match = re.search(r'(?:-t|--threads)\s+["\']?(\d+)["\']?|["\'](?:-t|--threads)["\']\s*,\s*["\'](\d+)["\']', content)
        if t_match:
            self.threads_entry.delete(0, "end")
            self.threads_entry.insert(0, t_match.group(1) or t_match.group(2))
            found_any = True

        # Port: --port <num>
        p_match = re.search(r'--port\s+["\']?(\d+)["\']?|["\']--port["\']\s*,\s*["\'](\d+)["\']', content)
        if p_match:
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, p_match.group(1) or p_match.group(2))
            found_any = True

        # Temp: --temp <val>
        tmp_match = re.search(r'--temp\s+["\']?([\d\.]+)["\']?|["\']--temp["\']\s*,\s*["\']([\d\.]+)["\']', content)
        if tmp_match:
            self.temp_entry.delete(0, "end")
            self.temp_entry.insert(0, tmp_match.group(1) or tmp_match.group(2))
            found_any = True

        # Top-P: --top-p <val>
        topp_match = re.search(r'--top-p\s+["\']?([\d\.]+)["\']?|["\']--top-p["\']\s*,\s*["\']([\d\.]+)["\']', content)
        if topp_match:
            self.topp_entry.delete(0, "end")
            self.topp_entry.insert(0, topp_match.group(1) or topp_match.group(2))
            found_any = True

        # Min-P: --min-p <val>
        minp_match = re.search(r'--min-p\s+["\']?([\d\.]+)["\']?|["\']--min-p["\']\s*,\s*["\']([\d\.]+)["\']', content)
        if minp_match:
            self.minp_entry.delete(0, "end")
            self.minp_entry.insert(0, minp_match.group(1) or minp_match.group(2))
            found_any = True

        # CTK: -ctk <val>
        ctk_match = re.search(r'-ctk\s+["\']?(\w+)["\']?|["\']-ctk["\']\s*,\s*["\'](\w+)["\']', content)
        if ctk_match:
            val = ctk_match.group(1) or ctk_match.group(2)
            if hasattr(self, "ctk_dropdown") and val in KV_CACHE_TYPES:
                self.ctk_dropdown.set(val)
                found_any = True

        # CTV: -ctv <val>
        ctv_match = re.search(r'-ctv\s+["\']?(\w+)["\']?|["\']-ctv["\']\s*,\s*["\'](\w+)["\']', content)
        if ctv_match:
            val = ctv_match.group(1) or ctv_match.group(2)
            if hasattr(self, "ctv_dropdown") and val in KV_CACHE_TYPES:
                self.ctv_dropdown.set(val)
                found_any = True

        # Flash attention: -fa
        if "-fa" in content:
            self.fa_var.set(True)
            found_any = True

        # Jinja: --jinja
        if "--jinja" in content:
            self.jinja_var.set(True)
            found_any = True

        # Optimizations
        opts_mapping = {
            "mlock": r'--load-mode\s+["\']?(\w+)["\']?|["\']--load-mode["\']\s*,\s*["\'](\w+)["\']',
            "tb": r'-tb\s+["\']?(\d+)["\']?|["\']-tb["\']\s*,\s*["\'](\d+)["\']',
            "fit_target": r'--fit-target\s+["\']?(\d+)["\']?|["\']--fit-target["\']\s*,\s*["\'](\d+)["\']',
            "cache_reuse": r'--cache-reuse\s+["\']?(\d+)["\']?|["\']--cache-reuse["\']\s*,\s*["\'](\d+)["\']',
            "parallel": r'-np\s+["\']?(\d+)["\']?|["\']-np["\']\s*,\s*["\'](\d+)["\']',
            "cache_ram": r'--cache-ram\s+["\']?(\d+)["\']?|["\']--cache-ram["\']\s*,\s*["\'](\d+)["\']',
            "cpu_moe": r'--n-cpu-moe\s+["\']?(\d+)["\']?|["\']--n-cpu-moe["\']\s*,\s*["\'](\d+)["\']',
        }

        for opt_key, pat in opts_mapping.items():
            if opt_key in self.opt_vars:
                m = re.search(pat, content)
                if m:
                    val = m.group(1) or m.group(2)
                    self.opt_vars[opt_key].set(True)
                    if val:
                        self.opt_str_vars[opt_key].set(val)
                    self._toggle_opt_widget(opt_key)
                    found_any = True

        return found_any

    def toggle_server(self):
        """Toggle server between running and stopped."""
        if self.is_server_running():
            self.stop_server()
        else:
            self.start_server()

    def launch(self):
        """Backwards-compatible alias for start_server."""
        self.start_server()

    def is_server_running(self):
        """Return True if the llama-server child process is currently alive."""
        return self.server_proc is not None and self.server_proc.poll() is None

    def start_server(self):
        """Launch the llama-server engine with real-time logging and optional watchdog monitoring."""
        cmd = self._build_command_args()
        if not cmd:
            return

        self.manual_stop = False
        self._add_recent_model(os.path.normpath(self.model_entry.get().strip().strip('"').strip("'")))

        env = os.environ.copy()
        env["GGML_VK_DISABLE_PINNED"] = "1"

        port = self.port_entry.get().strip()
        self._log_system(f"🚀 Launching llama-server on port {port}...")
        self._log_system(f"Command: {subprocess.list2cmdline(cmd)}")

        try:
            if self.external_console_var.get():
                full_cmd = f'cmd.exe /k "{subprocess.list2cmdline(cmd)}"'
                self.server_proc = subprocess.Popen(
                    full_cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    env=env,
                )
                self._log_system("[SYSTEM] Process running in dedicated external console window.")
            else:
                no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                self.server_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=no_window,
                    env=env,
                )

                def reader(proc, log_q):
                    try:
                        for line in iter(proc.stdout.readline, ''):
                            if not line:
                                break
                            log_q.put(line)
                    except Exception:
                        pass
                    finally:
                        try:
                            proc.stdout.close()
                        except Exception:
                            pass

                threading.Thread(target=reader, args=(self.server_proc, self.log_queue), daemon=True).start()
                self._log_system("[SYSTEM] Live stdout/stderr pipe attached. Streaming output to embedded console.")
        except Exception as e:
            self._flash_badge(f"⚠ FAILED TO LAUNCH: {e}", is_alert=True)
            self._log_system(f"⚠ Failed to launch: {e}")
            return

        # Update button to Stop Model Server state (Crimson danger state)
        self.start_btn.configure(
            text="🛑  Stop Model Server",
            fg_color="#7f1d1d",
            hover_color="#991b1b",
            border_color="#dc2626",
            text_color="#ffffff",
        )
        if hasattr(self, "open_webui_btn"):
            self.open_webui_btn.configure(
                state="normal",
                fg_color=THEME["secondary_btn_bg"],
                hover_color=THEME["secondary_btn_hover"],
                border_color=THEME["secondary_btn_border"],
                text_color=THEME["secondary_btn_text"],
            )
        self._flash_badge("● SERVER RUNNING")
        self.after(500, self._poll_server_status)

    def stop_server(self):
        """Cleanly terminate running llama-server process and console window."""
        self.manual_stop = True
        self.crash_count = 0
        if self.server_proc is not None:
            self._log_system("🛑 Stopping llama-server process...")
            try:
                no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                subprocess.run(
                    f"taskkill /F /T /PID {self.server_proc.pid}",
                    shell=True,
                    creationflags=no_window,
                )
            except Exception:
                pass
            try:
                self.server_proc.kill()
            except Exception:
                pass
            self.server_proc = None

        self._reset_server_btn_ui()
        self._flash_badge("● SERVER STOPPED")
        self._log_system("[SYSTEM] Server stopped successfully.")

    def restart_server(self):
        """Stop current server if running, wait briefly, and start again."""
        self._log_system("[SERVER] Restart initiated...")
        if self.is_server_running():
            self.stop_server()
            self.after(800, self.start_server)
        else:
            self.start_server()

    def _reset_server_btn_ui(self):
        """Reset launch button styling back to off-white start state."""
        self.start_btn.configure(
            text="🚀  Start Model Server",
            fg_color=THEME["primary_btn_bg"],
            hover_color=THEME["primary_btn_hover"],
            border_color=THEME["primary_btn_border"],
            text_color=THEME["primary_btn_text"],
        )
        if hasattr(self, "open_webui_btn"):
            self.open_webui_btn.configure(
                state="disabled",
                fg_color="#18181b",
                hover_color="#27272a",
                border_color="#3f3f46",
                text_color=THEME["text_muted"],
            )

    def _poll_server_status(self):
        """Check if server process is still alive and trigger watchdog auto-restart if crashed."""
        if self.server_proc is not None:
            exit_code = self.server_proc.poll()
            if exit_code is not None:
                self.server_proc = None
                self._reset_server_btn_ui()
                self._flash_badge("● SERVER OFFLINE")

                if not self.manual_stop:
                    self._log_system(f"⚠ [CRASH WATCHDOG] Engine terminated unexpectedly with exit code: {exit_code}")
                    self._flash_badge(f"⚠ CRASH DETECTED (Exit {exit_code})", is_alert=True)
                    if self.auto_restart_var.get():
                        now = time.time()
                        if now - self.last_crash_time < 30:
                            self.crash_count += 1
                        else:
                            self.crash_count = 1
                        self.last_crash_time = now

                        if self.crash_count > 5:
                            self._log_system("[WATCHDOG] 🛑 Auto-restart halted: 5 rapid crash events detected within 30 seconds.")
                            self._flash_badge("⚠ AUTO-RESTART HALTED", is_alert=True)
                        else:
                            self._log_system(f"[WATCHDOG] 🔄 Auto-restarting server in 2 seconds... (Attempt {self.crash_count}/5)")
                            self._flash_badge(f"● RESTARTING IN 2s ({self.crash_count}/5)...")
                            self.after(2000, self._do_auto_restart)
            else:
                self.after(500, self._poll_server_status)

    def _do_auto_restart(self):
        """Execute automatic server restart from watchdog timer."""
        if not self.manual_stop and not self.is_server_running():
            self._log_system("[WATCHDOG] 🚀 Triggering auto-restart now...")
            self.start_server()

    def _init_tray(self):
        """Initialize Windows notification tray icon and context menu."""
        if not HAS_PYSTRAY:
            return
        try:
            ico_file = resource_path(os.path.join("assets", "llauncher.ico"))
            if os.path.exists(ico_file):
                tray_img = Image.open(ico_file)
            else:
                logo_file = resource_path(os.path.join("assets", "Logo.png"))
                if os.path.exists(logo_file):
                    tray_img = Image.open(logo_file).resize((64, 64), Image.Resampling.LANCZOS)
                else:
                    tray_img = Image.new("RGBA", (64, 64), (16, 16, 20, 255))

            menu = pystray.Menu(
                pystray.MenuItem("Show LLauncher", lambda: self.after(0, self.show_window), default=True),
                pystray.MenuItem("Hide to Tray", lambda: self.after(0, self.hide_to_tray)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Start Model Server", lambda: self.after(0, self.start_server), visible=lambda item: not self.is_server_running()),
                pystray.MenuItem("Stop Model Server", lambda: self.after(0, self.stop_server), visible=lambda item: self.is_server_running()),
                pystray.MenuItem("Restart Model Server", lambda: self.after(0, self.restart_server)),
                pystray.MenuItem("View Logs", lambda: self.after(0, self.open_log_console)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Export Settings (.ps1)", lambda: self.after(0, self.export_script)),
                pystray.MenuItem("Import Settings (.ps1)", lambda: self.after(0, self.import_settings)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", lambda: self.after(0, self._exit_app)),
            )
            self.tray_icon = pystray.Icon("LLauncher", tray_img, "LLauncher - llama.cpp", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception:
            self.tray_icon = None

    def show_window(self):
        """Restore window from system tray and bring to front."""
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide_to_tray(self):
        """Minimize launcher to the notification area."""
        self.withdraw()
        self._flash_badge("● MINIMIZED TO TRAY")

    def _exit_app(self):
        """Full exit routine stopping background server and destroying tray icon."""
        self.manual_stop = True
        if self.is_server_running():
            try:
                no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                subprocess.run(
                    f"taskkill /F /T /PID {self.server_proc.pid}",
                    shell=True,
                    creationflags=no_window,
                )
            except Exception:
                pass
            try:
                self.server_proc.kill()
            except Exception:
                pass
            self.server_proc = None

        if hasattr(self, "tray_icon") and self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None

        self.destroy()

    def _on_close(self):
        """Clean up background server or minimize to tray on window close."""
        if self.minimize_to_tray_var.get() and HAS_PYSTRAY:
            self.hide_to_tray()
        else:
            self._exit_app()


if __name__ == "__main__":
    app = LlamaLauncher()
    app.mainloop()