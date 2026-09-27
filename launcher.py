import os
import sys
import re
import time
import json
import queue
import shutil
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
import struct

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

# Path to persistent configurations
PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")
RECENT_MODELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recent_models.json")
APP_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")

# Curated community-verified sampling presets
SAMPLER_PRESETS = {
    "Default / Balanced": {"temp": "0.7", "topp": "0.95", "minp": "0.05"},
    "Precise / Code": {"temp": "0.1", "topp": "0.90", "minp": "0.02"},
    "Creative / Story": {"temp": "0.9", "topp": "0.98", "minp": "0.05"},
    "Deterministic": {"temp": "0.0", "topp": "1.00", "minp": "0.00"},
}

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
            "ctx_shift": {"enabled": False, "val": "on"},
            "defrag_thold": {"enabled": False, "val": "0.1"},
        },
    },
    {
        "name": "Balanced",
        "ngl": 99,
        "ctx": 65536,
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
            "ctx_shift": {"enabled": False, "val": "on"},
            "defrag_thold": {"enabled": False, "val": "0.1"},
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
            "ctx_shift": {"enabled": True, "val": "on"},
            "defrag_thold": {"enabled": True, "val": "0.1"},
        },
    },
]


class ToolTip:
    """Lightweight sleek dark tooltip for CustomTkinter widgets."""

    def __init__(self, widget, text: str, delay_ms: int = 400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.tip_window = None
        self._after_id = None

        targets = []
        if hasattr(widget, "_buttons_dict") and widget._buttons_dict:
            targets.extend(widget._buttons_dict.values())
        else:
            targets.append(widget)

        for t in targets:
            try:
                t.bind("<Enter>", self._on_enter, add="+")
                t.bind("<Leave>", self._on_leave, add="+")
                t.bind("<ButtonPress>", self._on_leave, add="+")
            except Exception:
                try:
                    if hasattr(t, "_canvas"):
                        t._canvas.bind("<Enter>", self._on_enter, add="+")
                        t._canvas.bind("<Leave>", self._on_leave, add="+")
                        t._canvas.bind("<ButtonPress>", self._on_leave, add="+")
                except Exception:
                    pass

    def _on_enter(self, event=None):
        self._cancel_timer()
        self._after_id = self.widget.after(self.delay_ms, self._show_tip)

    def _on_leave(self, event=None):
        self._cancel_timer()
        self._hide_tip()

    def _cancel_timer(self):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show_tip(self):
        if self.tip_window or not self.text:
            return

        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

            self.tip_window = tw = ctk.CTkToplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.attributes("-topmost", True)
            try:
                tw.attributes("-alpha", 0.96)
            except Exception:
                pass
            tw.wm_geometry(f"+{x}+{y}")

            frame = ctk.CTkFrame(
                tw,
                fg_color="#18181b",
                border_width=1,
                border_color="#3f3f46",
                corner_radius=6,
            )
            frame.pack(fill="both", expand=True)

            label = ctk.CTkLabel(
                frame,
                text=self.text,
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#f4f4f5",
                padx=8,
                pady=4,
                justify="left",
            )
            label.pack()
        except Exception:
            self._hide_tip()

    def _hide_tip(self):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


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
        ).pack(fill="x", pady=(0, 6))

        if hasattr(self.master, "tunnel_manager") and self.master.tunnel_manager and self.master.tunnel_manager.is_running():
            tunnel_url = self.master.tunnel_manager.public_url
            t_banner = ctk.CTkFrame(container, fg_color=THEME["card_bg"], corner_radius=8, border_width=1, border_color="#3f3f46")
            t_banner.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                t_banner,
                text=f"🌐 Public HTTPS Endpoint: {tunnel_url}/v1",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#4ade80",
            ).pack(side="left", padx=12, pady=6)
            ctk.CTkButton(
                t_banner,
                text="📋 Copy Public API",
                width=130,
                height=26,
                fg_color=THEME["secondary_btn_bg"],
                hover_color=THEME["secondary_btn_hover"],
                border_width=1,
                border_color=THEME["secondary_btn_border"],
                text_color=THEME["secondary_btn_text"],
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                corner_radius=6,
                command=lambda u=f"{tunnel_url}/v1": self._copy_to_clipboard(u, "Public Tunnel Endpoint"),
            ).pack(side="right", padx=8, pady=4)

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


class ProfileHelperDialog(ctk.CTkToplevel):
    """Flyout dialog allowing users to enter system hardware specs and generate/copy an AI optimization prompt."""

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Profile Helper - Generate AI Prompt")
        self.geometry("640x660")
        self.minsize(580, 560)
        self.transient(master)

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
                d_w, d_h = 640, 660
                pos_x = max(0, m_x + (m_w - d_w) // 2)
                pos_y = max(0, m_y + (m_h - d_h) // 2)
                self.geometry(f"{d_w}x{d_h}+{pos_x}+{pos_y}")
            except Exception:
                pass

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # Header Title & Description
        top_frame = ctk.CTkFrame(container, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_frame,
            text="AI Profile Prompt Generator",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            container,
            text="Enter your system specifications below. Click 'Copy Prompt' to generate an optimized prompt and paste it directly into Grok, ChatGPT, Claude, or any AI to get a ready-to-import profile script.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_secondary"],
            wraplength=590,
            justify="left",
        ).pack(fill="x", pady=(0, 12))

        # Specs Card Frame
        specs_card = ctk.CTkFrame(
            container,
            fg_color=THEME["card_bg"],
            corner_radius=8,
            border_width=1,
            border_color=THEME["card_border"],
        )
        specs_card.pack(fill="x", pady=(0, 12), padx=2)
        specs_card.columnconfigure(1, weight=1)

        fields = [
            ("gpu_1", "GPU_1", "e.g. RTX 4070 Ti Super 16GB, RX 7800 XT 16GB"),
            ("gpu_2", "GPU_2 (optional)", "e.g. RTX 3060 12GB (or leave blank)"),
            ("gpu_3", "GPU_3 (optional)", "Secondary card (or leave blank)"),
            ("gpu_4", "GPU_4 (optional)", "Secondary card (or leave blank)"),
            ("cpu", "CPU", "e.g. AMD Ryzen 7 7800X3D (8C/16T), Intel i7-14700K"),
            ("ram", "RAM", "e.g. 32GB DDR5 6000MHz, 64GB DDR4"),
            ("model", "Target Model (optional)", "e.g. Qwen 2.5 32B Q4_K_M, Mixtral 8x7B"),
        ]

        self.spec_entries = {}

        for row_idx, (key, label_text, placeholder) in enumerate(fields):
            lbl = ctk.CTkLabel(
                specs_card,
                text=label_text,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=THEME["text_primary"] if "optional" not in label_text else THEME["text_secondary"],
                anchor="w",
                width=140,
            )
            lbl.grid(row=row_idx, column=0, padx=(14, 8), pady=5, sticky="w")

            ent = ctk.CTkEntry(
                specs_card,
                placeholder_text=placeholder,
                placeholder_text_color=THEME["text_muted"],
                fg_color=THEME["input_bg"],
                border_color=THEME["input_border"],
                border_width=1,
                text_color=THEME["text_primary"],
                corner_radius=6,
                height=28,
                font=ctk.CTkFont(family="Segoe UI", size=11),
            )
            ent.grid(row=row_idx, column=1, padx=(0, 14), pady=5, sticky="ew")
            self.spec_entries[key] = ent

        # Prompt Preview Label & Textbox
        preview_header = ctk.CTkFrame(container, fg_color="transparent")
        preview_header.pack(fill="x", pady=(2, 4))

        ctk.CTkLabel(
            preview_header,
            text="Prompt Preview",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")

        self.prompt_box = ctk.CTkTextbox(
            container,
            height=130,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_secondary"],
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=6,
            wrap="word",
        )
        self.prompt_box.pack(fill="both", expand=True, pady=(0, 12))

        # Bottom Button Row
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x")

        self.copy_btn = ctk.CTkButton(
            btn_row,
            text="📋  Copy Prompt to Clipboard",
            height=36,
            fg_color=THEME["primary_btn_bg"],
            hover_color=THEME["primary_btn_hover"],
            border_width=1,
            border_color=THEME["primary_btn_border"],
            text_color=THEME["primary_btn_text"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=6,
            command=self._copy_prompt,
        )
        self.copy_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        close_btn = ctk.CTkButton(
            btn_row,
            text="Close",
            height=36,
            width=90,
            fg_color="#27272a",
            hover_color="#3f3f46",
            border_width=1,
            border_color="#3f3f46",
            text_color="#e4e4e7",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=6,
            command=self.destroy,
        )
        close_btn.pack(side="right")

        # Initial prompt rendering & live binding
        for ent in self.spec_entries.values():
            ent.bind("<KeyRelease>", lambda e: self._refresh_prompt())

        self._refresh_prompt()

    def _generate_prompt_text(self) -> str:
        gpu_1 = self.spec_entries["gpu_1"].get().strip() or "Not specified (Primary GPU)"
        gpu_2 = self.spec_entries["gpu_2"].get().strip()
        gpu_3 = self.spec_entries["gpu_3"].get().strip()
        gpu_4 = self.spec_entries["gpu_4"].get().strip()
        cpu = self.spec_entries["cpu"].get().strip() or "Standard Multi-core CPU"
        ram = self.spec_entries["ram"].get().strip() or "Standard System RAM"
        model = self.spec_entries["model"].get().strip() or "Any LLM (General & MoE architectures)"

        gpu_lines = [f"- Primary GPU (GPU_1): {gpu_1}"]
        if gpu_2:
            gpu_lines.append(f"- Secondary GPU (GPU_2): {gpu_2}")
        if gpu_3:
            gpu_lines.append(f"- Secondary GPU (GPU_3): {gpu_3}")
        if gpu_4:
            gpu_lines.append(f"- Secondary GPU (GPU_4): {gpu_4}")
        gpu_spec_str = "\n".join(gpu_lines)

        prompt = f"""You are an expert system optimization engineer and high-performance LLM deployment specialist using llama.cpp / llama-server.

TASK:
Generate a specialized, finetuned, and hardware-optimized profile script for LLauncher (a modern Windows GUI launcher for llama-server).
Based on the provided hardware specifications (VRAM, RAM, CPU), calculate the memory budget and determine the best-fit suggested models and recommended quantization tiers (both for full GPU offload and hybrid CPU/RAM offload if applicable), and populate them in the top header comment.

TARGET SYSTEM SPECIFICATIONS:
{gpu_spec_str}
- CPU: {cpu}
- System RAM: {ram}
- Target Model / Quant: {model}

STRICT LLAUNCHER COMPATIBILITY RULES & CONSTRAINTS:
1. The script MUST be written as a valid Windows PowerShell script (`.ps1`).
2. It MUST contain the executable `$serverArgs` array followed by the exact LLauncher embedded JSON configuration block within `# <LLAUNCHER_SETTINGS_JSON>` tags so LLauncher can parse and import it cleanly.
3. In the top comment block, you MUST evaluate the hardware specs and provide specific, tailored "Suggested Models" with recommended quantizations (e.g., "7B-14B Dense Q4_K_M/Q8_0 (Full VRAM offload), Mixtral 8x7B / Qwen 2.5 32B MoE Q4_K_M (Hybrid VRAM + RAM)").
4. Allowed values for LLauncher parameters:
   - ctx_tokens: Must pick from [2048, 4096, 8192, 16384, 24576, 32768, 49152, 65536, 98304, 131072]
   - ctx_index: Corresponding 0-based index of ctx_tokens (0=2048, 1=4096, 2=8192, 3=16384, 4=24576, 5=32768, 6=49152, 7=65536, 8=98304, 9=131072)
   - batch_size: Pick from [128, 256, 512, 1024, 2048, 4096]
   - batch_index: 0-based index (0=128, 1=256, 2=512, 3=1024, 4=2048, 5=4096)
   - ubatch_size: Pick from [128, 256, 512, 1024, 2048]
   - ubatch_index: 0-based index (0=128, 1=256, 2=512, 3=1024, 4=2048)
   - ctk and ctv (KV cache quantization): Must be one of ["q8_0", "q4_0", "q4_1", "f16"]
   - device: Standard Vulkan or CUDA device identifier (e.g. "Vulkan0" or "CUDA0")
   - cpu_moe: For dense models, MUST be "enabled": false. For MoE models (Mixtral, DeepSeek MoE, Qwen MoE), set "enabled": true with a reasonable expert layer offload number like "16" or "8".
   - mlock: Use "enabled": true only if system RAM exceeds total model size to lock pages in memory.
   - fit_target: Margin in MiB to leave free on the GPU (e.g. 256, 512, 768, 1024, 1536).
   - cache_reuse: Number of tokens to reuse in KV cache (typically 128 or 256).
   - cache_ram: Host RAM cache in MiB (e.g. 8192 or 16384).
   - ctx_shift: Enable continuous context sliding when context limit is reached ("enabled": true/false).
   - defrag_thold: KV cache memory defragmentation threshold ("enabled": true/false, "value": "0.1").

OUTPUT FORMAT:
Output ONLY the raw PowerShell script formatted exactly like the template below. Do not wrap in conversational text but, wrap it in a codeblock.

```powershell
# =====================================================================
# LLauncher Profile: [Descriptive Profile Name]
# Target Hardware: [Hardware details, e.g. GPU, CPU, System RAM]
# Suggested Models: [Best-fit models with recommended quants, e.g. 7B-14B Dense (Full VRAM offload), 8x7B / Qwen-32B / DeepSeek MoE (Hybrid VRAM + DDR5)]
# Strategy: [1-sentence explanation of chosen flags and optimization rationale]
# =====================================================================

$env:GGML_VK_DISABLE_PINNED = '1'

$llamaExe = "llama-server.exe"

$serverArgs = @(
    "--device", "Vulkan0",
    "-ngl", "<ngl_value>",
    "-c", "<ctx_value>",
    "-t", "<threads_value>",
    "-b", "<batch_value>",
    "-ub", "<ubatch_value>",
    "-ctk", "<ctk_value>",
    "-ctv", "<ctv_value>",
    "--host", "127.0.0.1",
    "--port", "8082",
    "--temp", "<temp_value>",
    "--top-p", "<topp_value>",
    "--min-p", "<minp_value>",
    "-fa", "on",
    "--jinja",
    # Add optional flags based on optimizations:
    # "--load-mode", "mlock",
    # "-tb", "<prompt_threads>",
    # "--fit-target", "<mib_margin>",
    # "--cache-reuse", "<tokens>",
    # "--cache-ram", "<mib_ram>",
    # "--n-cpu-moe", "<expert_layers>",
    # "--ctx-shift",
    # "--defrag-thold", "0.1"
)

Write-Host "Launching llama-server with [Profile Name]..." -ForegroundColor Cyan
& $llamaExe @serverArgs

# =====================================================================
# LLauncher Embedded Settings (For importing back into LLauncher)
# <LLAUNCHER_SETTINGS_JSON>
# {{
#   "version": "1.4.0",
#   "profile_name": "[Profile Name]",
#   "device": "Vulkan0",
#   "ngl": <ngl_int>,
#   "ctx_index": <ctx_idx_int>,
#   "ctx_tokens": <ctx_int>,
#   "batch_index": <batch_idx_int>,
#   "batch_size": <batch_int>,
#   "ubatch_index": <ubatch_idx_int>,
#   "ubatch_size": <ubatch_int>,
#   "threads": "<threads_str>",
#   "port": "8082",
#   "ctk": "<ctk_str>",
#   "ctv": "<ctv_str>",
#   "temp": "<temp_str>",
#   "topp": "<topp_str>",
#   "minp": "<minp_str>",
#   "flash_attention": true,
#   "jinja": true,
#   "optimizations": {{
#     "mlock": {{
#       "enabled": <true_or_false>,
#       "value": "mlock"
#     }},
#     "tb": {{
#       "enabled": <true_or_false>,
#       "value": "<prompt_threads>"
#     }},
#     "fit_target": {{
#       "enabled": <true_or_false>,
#       "value": "<mib_margin>"
#     }},
#     "cache_reuse": {{
#       "enabled": <true_or_false>,
#       "value": "<tokens>"
#     }},
#     "parallel": {{
#       "enabled": false,
#       "value": "1"
#     }},
#     "cache_ram": {{
#       "enabled": <true_or_false>,
#       "value": "<mib_ram>"
#     }},
#     "cpu_moe": {{
#       "enabled": <true_or_false>,
#       "value": "<moe_layers>"
#     }},
#     "ctx_shift": {{
#       "enabled": <true_or_false>,
#       "value": "on"
#     }},
#     "defrag_thold": {{
#       "enabled": <true_or_false>,
#       "value": "0.1"
#     }}
#   }}
# }}
# </LLAUNCHER_SETTINGS_JSON>
# =====================================================================
```
"""
        return prompt

    def _refresh_prompt(self):
        text = self._generate_prompt_text()
        self.prompt_box.configure(state="normal")
        self.prompt_box.delete("1.0", "end")
        self.prompt_box.insert("1.0", text)
        self.prompt_box.configure(state="disabled")

    def _copy_prompt(self):
        prompt_text = self._generate_prompt_text()
        try:
            self.clipboard_clear()
            self.clipboard_append(prompt_text)
            self.update()
            self.copy_btn.configure(text="✓  Prompt Copied to Clipboard!")
            self.after(2000, lambda: self.copy_btn.configure(text="📋  Copy Prompt to Clipboard"))
        except Exception:
            pass


class TunnelManager:
    """Manages background tunnel processes (Ngrok / Cloudflare Quick Tunnel) to expose llama-server securely."""

    def __init__(self, app=None):
        self.app = app
        self.proc = None
        self.provider = "ngrok"  # "ngrok" or "cloudflare"
        self.public_url = ""
        self.status = "stopped"  # "stopped", "starting", "running", "error"
        self.error_message = ""
        self.log_lines = []
        self.on_update_callbacks = []

    def register_callback(self, cb):
        if cb not in self.on_update_callbacks:
            self.on_update_callbacks.append(cb)

    def unregister_callback(self, cb):
        if cb in self.on_update_callbacks:
            self.on_update_callbacks.remove(cb)

    def _notify(self):
        for cb in list(self.on_update_callbacks):
            try:
                cb(self)
            except Exception:
                pass

    @staticmethod
    def find_ngrok(custom_path: str = "") -> str:
        if custom_path and os.path.isfile(custom_path):
            return custom_path
        which = shutil.which("ngrok") or shutil.which("ngrok.exe")
        if which:
            return which
        candidates = [
            r"D:\ngrok\ngrok.exe",
            os.path.expanduser(r"~\scoop\shims\ngrok.exe"),
            r"C:\Program Files\ngrok\ngrok.exe",
            r"C:\ngrok\ngrok.exe",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return ""

    @staticmethod
    def find_cloudflared(custom_path: str = "") -> str:
        if custom_path and os.path.isfile(custom_path):
            return custom_path
        which = shutil.which("cloudflared") or shutil.which("cloudflared.exe")
        if which:
            return which
        candidates = [
            r"C:\Program Files\cloudflared\cloudflared.exe",
            os.path.expanduser(r"~\scoop\shims\cloudflared.exe"),
            r"C:\cloudflared\cloudflared.exe",
            r"D:\cloudflared\cloudflared.exe",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return ""

    def start_tunnel(self, provider: str, port: int, custom_bin: str = "", auth_token: str = ""):
        self.stop_tunnel()
        self.provider = provider
        self.status = "starting"
        self.public_url = ""
        self.error_message = ""
        self.log_lines = []
        self._notify()

        def worker():
            no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            if provider == "ngrok":
                bin_path = self.find_ngrok(custom_bin)
                if not bin_path:
                    self.status = "error"
                    self.error_message = "ngrok.exe not found on system. Install ngrok or browse for ngrok.exe."
                    self.log_lines.append(f"[ERROR] {self.error_message}")
                    self._notify()
                    return

                if auth_token and auth_token.strip():
                    try:
                        subprocess.run(
                            [bin_path, "config", "add-authtoken", auth_token.strip()],
                            capture_output=True,
                            text=True,
                            creationflags=no_window,
                            timeout=5,
                        )
                        self.log_lines.append("[INFO] Ngrok authtoken configured successfully.")
                    except Exception as e:
                        self.log_lines.append(f"[WARN] Failed configuring authtoken: {e}")

                cmd = [bin_path, "http", str(port)]
                self.log_lines.append(f"[EXEC] {subprocess.list2cmdline(cmd)}")
                try:
                    self.proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        creationflags=no_window,
                    )
                except Exception as e:
                    self.status = "error"
                    self.error_message = f"Failed to start ngrok: {e}"
                    self.log_lines.append(f"[ERROR] {self.error_message}")
                    self._notify()
                    return

                def read_ngrok(p):
                    try:
                        for line in iter(p.stdout.readline, ''):
                            if not line:
                                break
                            clean = line.strip()
                            self.log_lines.append(clean)
                            if "ERR_NGROK" in clean or ("error" in clean.lower() and not self.error_message):
                                self.error_message = clean
                    except Exception:
                        pass

                threading.Thread(target=read_ngrok, args=(self.proc,), daemon=True).start()

                # Poll ngrok local web inspection API on 127.0.0.1:4040/api/tunnels
                for _ in range(25):
                    if self.proc is None or self.proc.poll() is not None:
                        break
                    time.sleep(0.4)
                    try:
                        req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels", headers={"User-Agent": "LLauncher"})
                        with urllib.request.urlopen(req, timeout=1.2) as resp:
                            data = json.loads(resp.read().decode("utf-8"))
                            tunnels = data.get("tunnels", [])
                            for t in tunnels:
                                p_url = t.get("public_url", "")
                                if p_url.startswith("https://"):
                                    self.public_url = p_url
                                    self.status = "running"
                                    self.log_lines.append(f"[SUCCESS] Public HTTPS Tunnel Live: {p_url}")
                                    self._notify()
                                    return
                                elif p_url and not self.public_url:
                                    self.public_url = p_url
                            if self.public_url:
                                self.status = "running"
                                self.log_lines.append(f"[SUCCESS] Public Tunnel Live: {self.public_url}")
                                self._notify()
                                return
                    except Exception:
                        pass

                if self.status != "running":
                    self.status = "error"
                    if not self.error_message:
                        if self.proc and self.proc.poll() is not None:
                            self.error_message = f"ngrok terminated with exit code {self.proc.poll()}."
                        else:
                            self.error_message = "Timed out waiting for ngrok tunnel URL."
                    self.log_lines.append(f"[ERROR] {self.error_message}")
                    self._notify()

            elif provider == "cloudflare":
                bin_path = self.find_cloudflared(custom_bin)
                if not bin_path:
                    self.status = "error"
                    self.error_message = "cloudflared.exe not found. Install via 'winget install --id Cloudflare.cloudflared' or browse for binary."
                    self.log_lines.append(f"[ERROR] {self.error_message}")
                    self._notify()
                    return

                cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]
                self.log_lines.append(f"[EXEC] {subprocess.list2cmdline(cmd)}")
                try:
                    self.proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        creationflags=no_window,
                    )
                except Exception as e:
                    self.status = "error"
                    self.error_message = f"Failed to start cloudflared: {e}"
                    self.log_lines.append(f"[ERROR] {self.error_message}")
                    self._notify()
                    return

                cf_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

                def read_cf(p):
                    try:
                        for line in iter(p.stdout.readline, ''):
                            if not line:
                                break
                            clean = line.strip()
                            self.log_lines.append(clean)
                            m = cf_pattern.search(clean)
                            if m and not self.public_url:
                                self.public_url = m.group(0)
                                self.status = "running"
                                self.log_lines.append(f"[SUCCESS] Cloudflare Quick Tunnel Live: {self.public_url}")
                                self._notify()
                    except Exception:
                        pass
                    if self.status != "running":
                        self.status = "error"
                        if not self.error_message:
                            self.error_message = "cloudflared closed before generating tunnel URL."
                        self.log_lines.append(f"[ERROR] {self.error_message}")
                        self._notify()

                threading.Thread(target=read_cf, args=(self.proc,), daemon=True).start()

        threading.Thread(target=worker, daemon=True).start()

    def stop_tunnel(self):
        if self.proc is not None:
            pid = self.proc.pid
            try:
                no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, creationflags=no_window)
            except Exception:
                pass
            try:
                self.proc.kill()
            except Exception:
                pass
            self.proc = None
        self.status = "stopped"
        self.public_url = ""
        self._notify()

    def is_running(self) -> bool:
        return self.status == "running" and self.proc is not None and self.proc.poll() is None


class TunnelDialog(ctk.CTkToplevel):
    """Flyout dialog to manage instant secure public tunneling (Ngrok / Cloudflare Tunnel)."""

    def __init__(self, master=None):
        super().__init__(master)
        self.app = master
        self.tunnel_manager = getattr(master, "tunnel_manager", None)
        self.title("Instant Secure Public Tunnel - LLauncher")
        self.geometry("660x650")
        self.minsize(600, 580)
        self.transient(master)

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
                d_w, d_h = 660, 650
                pos_x = max(0, m_x + (m_w - d_w) // 2)
                pos_y = max(0, m_y + (m_h - d_h) // 2)
                self.geometry(f"{d_w}x{d_h}+{pos_x}+{pos_y}")
            except Exception:
                pass

        self._build_ui()
        if self.tunnel_manager:
            self.tunnel_manager.register_callback(self._on_manager_update)
            self._render_state(self.tunnel_manager)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self.tunnel_manager:
            self.tunnel_manager.unregister_callback(self._on_manager_update)
        if hasattr(self.app, "tunnel_dialog"):
            self.app.tunnel_dialog = None
        self.destroy()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=14)

        # Header Row
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🌐  Instant Secure Tunnel",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=THEME["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Expose local llama-server via HTTPS for remote access, mobile apps & web APIs.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=THEME["text_muted"],
        ).pack(anchor="w")

        status_frame = ctk.CTkFrame(
            header,
            fg_color=THEME["badge_bg"],
            corner_radius=14,
            border_width=1,
            border_color=THEME["badge_border"],
        )
        status_frame.pack(side="right")
        self.status_pill = ctk.CTkLabel(
            status_frame,
            text="● OFFLINE",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#71717a",
            padx=10,
            pady=3,
        )
        self.status_pill.pack()

        # Configuration Card
        cfg_card = ctk.CTkFrame(
            container,
            fg_color=THEME["card_bg"],
            corner_radius=8,
            border_width=1,
            border_color=THEME["card_border"],
        )
        cfg_card.pack(fill="x", pady=(0, 10))
        cfg_card.columnconfigure(1, weight=1)

        # Row 0: Provider Selector
        ctk.CTkLabel(
            cfg_card,
            text="Provider",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_secondary"],
            anchor="w",
            width=110,
        ).grid(row=0, column=0, padx=(14, 8), pady=(12, 6), sticky="w")

        self.provider_seg = ctk.CTkSegmentedButton(
            cfg_card,
            values=["Ngrok", "Cloudflare Tunnel"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#18181b",
            selected_color=THEME["primary_btn_bg"],
            selected_hover_color=THEME["primary_btn_hover"],
            unselected_color="#18181b",
            unselected_hover_color="#27272a",
            text_color=THEME["text_primary"],
            border_width=1,
            corner_radius=6,
            command=self._on_provider_changed,
            height=28,
        )
        current_provider = self.tunnel_manager.provider if self.tunnel_manager else "ngrok"
        self.provider_seg.set("Ngrok" if current_provider == "ngrok" else "Cloudflare Tunnel")
        self.provider_seg.grid(row=0, column=1, columnspan=2, padx=(0, 14), pady=(12, 6), sticky="ew")
        self._update_provider_seg_colors()
        self.after(20, self._update_provider_seg_colors)

        # Row 1: Target Port
        ctk.CTkLabel(
            cfg_card,
            text="Local Port",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_secondary"],
            anchor="w",
            width=110,
        ).grid(row=1, column=0, padx=(14, 8), pady=5, sticky="w")

        port_val = "8082"
        if hasattr(self.app, "port_entry"):
            port_val = self.app.port_entry.get().strip() or "8082"

        self.port_entry = ctk.CTkEntry(
            cfg_card,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            width=90,
        )
        self.port_entry.insert(0, port_val)
        self.port_entry.grid(row=1, column=1, padx=(0, 14), pady=5, sticky="w")

        # Row 2: Executable Binary Path + Browse
        ctk.CTkLabel(
            cfg_card,
            text="Binary Path",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_secondary"],
            anchor="w",
            width=110,
        ).grid(row=2, column=0, padx=(14, 8), pady=5, sticky="w")

        bin_frame = ctk.CTkFrame(cfg_card, fg_color="transparent")
        bin_frame.grid(row=2, column=1, columnspan=2, padx=(0, 14), pady=5, sticky="ew")
        bin_frame.columnconfigure(0, weight=1)

        self.bin_entry = ctk.CTkEntry(
            bin_frame,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self.bin_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.browse_btn = ctk.CTkButton(
            bin_frame,
            text="Browse",
            width=70,
            height=28,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=6,
            command=self._browse_binary,
        )
        self.browse_btn.grid(row=0, column=1)

        # Row 3: Detection / Helper Info
        self.detection_lbl = ctk.CTkLabel(
            cfg_card,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=THEME["text_muted"],
            anchor="w",
        )
        self.detection_lbl.grid(row=3, column=1, columnspan=2, padx=(0, 14), pady=(0, 6), sticky="w")

        # Row 4: Auth Token (for Ngrok)
        self.token_label = ctk.CTkLabel(
            cfg_card,
            text="Auth Token",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_secondary"],
            anchor="w",
            width=110,
        )
        self.token_label.grid(row=4, column=0, padx=(14, 8), pady=(0, 12), sticky="w")

        self.token_entry = ctk.CTkEntry(
            cfg_card,
            placeholder_text="Optional (leave blank if already configured)",
            placeholder_text_color=THEME["text_muted"],
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self.token_entry.grid(row=4, column=1, columnspan=2, padx=(0, 14), pady=(0, 12), sticky="ew")

        # Action Button Row (Start/Stop Tunnel)
        action_bar = ctk.CTkFrame(container, fg_color="transparent")
        action_bar.pack(fill="x", pady=(0, 10))

        self.action_btn = ctk.CTkButton(
            action_bar,
            text="🚀  Start Secure Tunnel",
            height=36,
            fg_color=THEME["primary_btn_bg"],
            hover_color=THEME["primary_btn_hover"],
            border_width=1,
            border_color=THEME["primary_btn_border"],
            text_color=THEME["primary_btn_text"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=8,
            command=self._toggle_tunnel,
        )
        self.action_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.helper_action_btn = ctk.CTkButton(
            action_bar,
            text="Install / Guide",
            height=36,
            width=110,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=8,
            command=self._on_helper_action,
        )
        self.helper_action_btn.pack(side="right")

        # Live Public Connection Card
        self.url_card = ctk.CTkFrame(
            container,
            fg_color=THEME["card_bg"],
            corner_radius=8,
            border_width=1,
            border_color=THEME["card_border"],
        )
        self.url_card.pack(fill="x", pady=(0, 10))
        self.url_card.columnconfigure(1, weight=1)

        # Public Web URL
        ctk.CTkLabel(
            self.url_card,
            text="Public URL",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_secondary"],
            width=110,
            anchor="w",
        ).grid(row=0, column=0, padx=(14, 8), pady=(12, 4), sticky="w")

        self.url_entry = ctk.CTkEntry(
            self.url_card,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=6,
            height=28,
        )
        self.url_entry.grid(row=0, column=1, padx=(0, 6), pady=(12, 4), sticky="ew")

        url_btn_frame = ctk.CTkFrame(self.url_card, fg_color="transparent")
        url_btn_frame.grid(row=0, column=2, padx=(0, 14), pady=(12, 4))

        self.copy_url_btn = ctk.CTkButton(
            url_btn_frame,
            text="📋 Copy",
            width=65,
            height=28,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=6,
            command=self._copy_public_url,
        )
        self.copy_url_btn.pack(side="left", padx=(0, 4))

        self.open_url_btn = ctk.CTkButton(
            url_btn_frame,
            text="🌐 Open",
            width=65,
            height=28,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=6,
            command=self._open_public_url,
        )
        self.open_url_btn.pack(side="left")

        # OpenAI Base URL
        ctk.CTkLabel(
            self.url_card,
            text="OpenAI API Base",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_secondary"],
            width=110,
            anchor="w",
        ).grid(row=1, column=0, padx=(14, 8), pady=(4, 12), sticky="w")

        self.api_url_entry = ctk.CTkEntry(
            self.url_card,
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=6,
            height=28,
        )
        self.api_url_entry.grid(row=1, column=1, padx=(0, 6), pady=(4, 12), sticky="ew")

        self.copy_api_btn = ctk.CTkButton(
            self.url_card,
            text="📋 Copy API",
            width=134,
            height=28,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=6,
            command=self._copy_api_url,
        )
        self.copy_api_btn.grid(row=1, column=2, padx=(0, 14), pady=(4, 12))

        # Diagnostics & Output Log Card
        diag_header = ctk.CTkFrame(container, fg_color="transparent")
        diag_header.pack(fill="x", pady=(2, 4))

        ctk.CTkLabel(
            diag_header,
            text="Tunnel Diagnostics & Output",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(side="left")

        ctk.CTkButton(
            diag_header,
            text="Clear Log",
            width=65,
            height=20,
            fg_color="transparent",
            hover_color="#27272a",
            text_color=THEME["text_muted"],
            font=ctk.CTkFont(family="Segoe UI", size=10),
            command=self._clear_diag,
        ).pack(side="right")

        self.diag_box = ctk.CTkTextbox(
            container,
            height=110,
            fg_color="#0e0e11",
            border_color="#222226",
            border_width=1,
            text_color="#e4e4e7",
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=6,
            wrap="none",
        )
        self.diag_box.pack(fill="both", expand=True, pady=(0, 8))

        self._refresh_detection()

    def _update_provider_seg_colors(self, selected_choice=None):
        """Ensure active provider tab has dark readable text and inactive has white bold text."""
        if not hasattr(self, "provider_seg"):
            return
        current = selected_choice or self.provider_seg.get()
        if hasattr(self.provider_seg, "_buttons_dict"):
            for name, btn in self.provider_seg._buttons_dict.items():
                btn.configure(font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"))
                if name == current:
                    btn.configure(text_color=THEME["primary_btn_text"])
                else:
                    btn.configure(text_color="#ffffff")

    def _on_provider_changed(self, choice: str):
        self._update_provider_seg_colors(choice)
        self.after(10, lambda: self._update_provider_seg_colors(choice))
        self._refresh_detection()

    def _refresh_detection(self):
        provider = "ngrok" if "ngrok" in self.provider_seg.get().lower() else "cloudflare"
        if provider == "ngrok":
            self.token_label.grid()
            self.token_entry.grid()
            found = TunnelManager.find_ngrok(self.bin_entry.get().strip())
            if found:
                self.bin_entry.delete(0, "end")
                self.bin_entry.insert(0, found)
                self.detection_lbl.configure(text=f"✓ Detected: {found}", text_color="#4ade80")
            else:
                self.detection_lbl.configure(text="⚠ ngrok.exe not found on PATH or default locations.", text_color="#facc15")
            self.helper_action_btn.configure(text="ngrok.com")
        else:
            self.token_label.grid_remove()
            self.token_entry.grid_remove()
            found = TunnelManager.find_cloudflared(self.bin_entry.get().strip())
            if found:
                self.bin_entry.delete(0, "end")
                self.bin_entry.insert(0, found)
                self.detection_lbl.configure(text=f"✓ Detected: {found}", text_color="#4ade80")
            else:
                self.detection_lbl.configure(text="⚠ cloudflared.exe not found. Install via winget or scoop.", text_color="#facc15")
            self.helper_action_btn.configure(text="Copy winget")

    def _browse_binary(self):
        f = filedialog.askopenfilename(
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")],
            title="Select Tunnel Binary Executable"
        )
        if f:
            self.bin_entry.delete(0, "end")
            self.bin_entry.insert(0, os.path.normpath(f))
            self._refresh_detection()

    def _on_helper_action(self):
        provider = "ngrok" if "ngrok" in self.provider_seg.get().lower() else "cloudflare"
        if provider == "ngrok":
            webbrowser.open("https://dashboard.ngrok.com/signup")
        else:
            cmd_str = "winget install --id Cloudflare.cloudflared"
            try:
                self.clipboard_clear()
                self.clipboard_append(cmd_str)
                self.update()
                self.helper_action_btn.configure(text="✓ Copied!")
                self.after(1800, lambda: self.helper_action_btn.configure(text="Copy winget"))
            except Exception:
                pass

    def _toggle_tunnel(self):
        if not self.tunnel_manager:
            return
        if self.tunnel_manager.is_running() or self.tunnel_manager.status == "starting":
            self.tunnel_manager.stop_tunnel()
        else:
            provider = "ngrok" if "ngrok" in self.provider_seg.get().lower() else "cloudflare"
            try:
                port = int(self.port_entry.get().strip())
            except ValueError:
                port = 8082
            custom_bin = self.bin_entry.get().strip()
            token = self.token_entry.get().strip()
            self.tunnel_manager.start_tunnel(provider, port, custom_bin, token)

    def _on_manager_update(self, tm):
        self.after(0, lambda: self._render_state(tm))

    def _render_state(self, tm):
        # Update logs
        self.diag_box.configure(state="normal")
        self.diag_box.delete("1.0", "end")
        if tm.log_lines:
            self.diag_box.insert("end", "\n".join(tm.log_lines[-40:]) + "\n")
            self.diag_box.see("end")
        self.diag_box.configure(state="disabled")

        if tm.status == "running":
            self.status_pill.configure(text="● TUNNEL ONLINE", text_color="#4ade80")
            self.action_btn.configure(
                text="🛑  Stop Secure Tunnel",
                fg_color="#7f1d1d",
                hover_color="#991b1b",
                border_color="#dc2626",
                text_color="#ffffff",
                state="normal"
            )
            self.url_card.configure(fg_color=THEME["card_bg"], border_color="#3f3f46")
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, tm.public_url)
            self.url_entry.configure(text_color="#4ade80")
            self.api_url_entry.delete(0, "end")
            self.api_url_entry.insert(0, f"{tm.public_url}/v1")
            self.api_url_entry.configure(text_color="#4ade80")
            self.copy_url_btn.configure(state="normal")
            self.open_url_btn.configure(state="normal")
            self.copy_api_btn.configure(state="normal")
        elif tm.status == "starting":
            self.status_pill.configure(text="● CONNECTING...", text_color="#facc15")
            self.action_btn.configure(
                text="⏳  Establishing Tunnel...",
                fg_color="#27272a",
                hover_color="#27272a",
                border_color="#3f3f46",
                text_color="#a1a1aa",
                state="disabled"
            )
            self.url_card.configure(fg_color=THEME["card_bg"], border_color=THEME["card_border"])
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, "Waiting for public URL...")
            self.url_entry.configure(text_color=THEME["text_muted"])
            self.api_url_entry.delete(0, "end")
            self.api_url_entry.insert(0, "Waiting for endpoint...")
            self.api_url_entry.configure(text_color=THEME["text_muted"])
            self.copy_url_btn.configure(state="disabled")
            self.open_url_btn.configure(state="disabled")
            self.copy_api_btn.configure(state="disabled")
        elif tm.status == "error":
            self.status_pill.configure(text="● ERROR", text_color="#f87171")
            self.action_btn.configure(
                text="🚀  Retry Start Tunnel",
                fg_color=THEME["primary_btn_bg"],
                hover_color=THEME["primary_btn_hover"],
                border_color=THEME["primary_btn_border"],
                text_color=THEME["primary_btn_text"],
                state="normal"
            )
            self.url_card.configure(fg_color=THEME["card_bg"], border_color=THEME["card_border"])
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, tm.error_message or "Tunnel failed to start")
            self.url_entry.configure(text_color="#f87171")
            self.api_url_entry.delete(0, "end")
            self.api_url_entry.insert(0, "")
            self.copy_url_btn.configure(state="disabled")
            self.open_url_btn.configure(state="disabled")
            self.copy_api_btn.configure(state="disabled")
        else:
            self.status_pill.configure(text="● OFFLINE", text_color="#71717a")
            self.action_btn.configure(
                text="🚀  Start Secure Tunnel",
                fg_color=THEME["primary_btn_bg"],
                hover_color=THEME["primary_btn_hover"],
                border_color=THEME["primary_btn_border"],
                text_color=THEME["primary_btn_text"],
                state="normal"
            )
            self.url_card.configure(fg_color=THEME["card_bg"], border_color=THEME["card_border"])
            self.url_entry.delete(0, "end")
            self.url_entry.configure(text_color=THEME["text_primary"])
            self.api_url_entry.delete(0, "end")
            self.api_url_entry.configure(text_color=THEME["text_primary"])
            self.copy_url_btn.configure(state="normal")
            self.open_url_btn.configure(state="normal")
            self.copy_api_btn.configure(state="normal")

    def _copy_public_url(self):
        url = self.url_entry.get().strip()
        if url and url.startswith("http"):
            try:
                self.clipboard_clear()
                self.clipboard_append(url)
                self.update()
                self.copy_url_btn.configure(text="✓ Copied!")
                self.after(1500, lambda: self.copy_url_btn.configure(text="📋 Copy"))
            except Exception:
                pass

    def _open_public_url(self):
        url = self.url_entry.get().strip()
        if url and url.startswith("http"):
            webbrowser.open(url)

    def _copy_api_url(self):
        url = self.api_url_entry.get().strip()
        if url and url.startswith("http"):
            try:
                self.clipboard_clear()
                self.clipboard_append(url)
                self.update()
                self.copy_api_btn.configure(text="✓ API Copied!")
                self.after(1500, lambda: self.copy_api_btn.configure(text="📋 Copy API"))
            except Exception:
                pass

    def _clear_diag(self):
        self.diag_box.configure(state="normal")
        self.diag_box.delete("1.0", "end")
        self.diag_box.configure(state="disabled")
        if self.tunnel_manager:
            self.tunnel_manager.log_lines.clear()


class LlamaLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # Off-screen construction eliminates launch stutter and flicker
        self.title("LLauncher - llama.cpp Server Launcher")
        self.geometry("1184x640")
        self.minsize(1120, 580)
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
        self.device_vram_map = {
            "Vulkan0: AMD Radeon RX 9070 XT": 16.0,
            "Vulkan1: AMD Radeon(TM) Graphics": 16.0,
            "none: CPU Only": 32.0,
        }
        self.gguf_metadata_cache = {}

        self.profiles = []
        self.active_profile_idx = 0
        self._load_profiles()

        self.recent_models = []
        self._load_recent_models()

        # Configurable Model Library & App Config
        self.app_config = {}
        self.models_dir = ""
        self.scanned_models_map = {}
        self._scan_thread = None
        self._load_app_config()

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

        # Live Inference Telemetry State (Phase 2)
        self._metrics_stop_event = threading.Event()
        self._metrics_thread = None
        self._last_metrics_sample = None

        # Public Secure Tunneling State
        self.tunnel_manager = TunnelManager(self)
        self.tunnel_dialog = None
        self.tunnel_manager.register_callback(self._on_main_tunnel_update)

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
        self._trigger_models_scan()
        self._update_memory_estimation()
        self._apply_tooltips()

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

    def _load_app_config(self):
        """Load persistent application configurations including models_dir."""
        self.app_config = {}
        if os.path.exists(APP_CONFIG_FILE):
            try:
                with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.app_config = data
            except Exception:
                pass
        self.models_dir = self.app_config.get("models_dir", "")
        if not self.models_dir:
            # Fallback to existing recent model directory or user's models folder if exists
            if self.recent_models and os.path.isfile(self.recent_models[0]):
                self.models_dir = os.path.dirname(self.recent_models[0])
            else:
                default_models = os.path.join(os.path.expanduser("~"), "models")
                if os.path.isdir(default_models):
                    self.models_dir = default_models

    def _persist_app_config(self):
        """Persist application configurations to app_config.json."""
        try:
            self.app_config["models_dir"] = self.models_dir
            with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.app_config, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format byte size into human readable string (GB or MB)."""
        gb = size_bytes / (1024 ** 3)
        if gb >= 1.0:
            return f"{gb:.2f} GB"
        mb = size_bytes / (1024 ** 2)
        return f"{mb:.1f} MB"

    @classmethod
    def _get_total_model_file_size(cls, filepath: str) -> int:
        """Sum total bytes across all parts if model is multi-part, or return file size."""
        if not filepath or not os.path.isfile(filepath):
            return 0
        clean = os.path.normpath(filepath)
        parent = os.path.dirname(clean)
        fname = os.path.basename(clean)

        p1 = re.compile(r"^(.*?)[-_.]+(\d{4,5})[-_.]+(?:of[-_.]+(\d{4,5}))\.gguf$", re.IGNORECASE)
        p2 = re.compile(r"^(.*?)[-_.]+(\d{4,5})\.gguf$", re.IGNORECASE)
        p3 = re.compile(r"^(.*?)[-_.]+part[-_.]*(\d{1,5})\.gguf$", re.IGNORECASE)

        base = None
        for pat in (p1, p2, p3):
            m = pat.match(fname)
            if m:
                base = m.group(1).rstrip("-_. ")
                break

        if not base or not os.path.isdir(parent):
            try:
                return os.path.getsize(clean)
            except Exception:
                return 0

        total = 0
        matched = 0
        try:
            for f in os.listdir(parent):
                if not f.lower().endswith(".gguf") or "mmproj" in f.lower():
                    continue
                for pat in (p1, p2, p3):
                    m = pat.match(f)
                    if m and m.group(1).rstrip("-_. ") == base:
                        try:
                            total += os.path.getsize(os.path.join(parent, f))
                            matched += 1
                        except Exception:
                            pass
                        break
        except Exception:
            pass

        return total if matched > 0 else (os.path.getsize(clean) if os.path.isfile(clean) else 0)

    @classmethod
    def parse_gguf_summary(cls, filepath: str) -> dict:
        """
        Fast in-memory GGUF binary inspector.
        Extracts layer count, embedding dimension, attention heads, context limit, and total model bytes.
        Fast-skips large tensor and tokenizer arrays in <5ms without external dependencies.
        """
        if not filepath or not os.path.isfile(filepath):
            return {}

        total_bytes = cls._get_total_model_file_size(filepath)

        try:
            with open(filepath, "rb") as f:
                magic = f.read(4)
                if magic != b"GGUF":
                    return {"file_bytes": total_bytes, "layers": 32, "heads": 32, "kv_heads": 8, "embd": 4096, "ctx_train": 4096}

                version = struct.unpack("<I", f.read(4))[0]
                count_fmt = "<Q" if version >= 2 else "<I"
                count_size = 8 if version >= 2 else 4

                tensor_count = struct.unpack(count_fmt, f.read(count_size))[0]
                kv_count = struct.unpack(count_fmt, f.read(count_size))[0]

                meta = {}
                max_kvs = min(kv_count, 1200)
                for _ in range(max_kvs):
                    klen = struct.unpack(count_fmt, f.read(count_size))[0]
                    if klen > 256 or klen <= 0:
                        break
                    key = f.read(klen).decode("utf-8", errors="replace")
                    vtype = struct.unpack("<I", f.read(4))[0]

                    if vtype == 8:  # STRING
                        vlen = struct.unpack(count_fmt, f.read(count_size))[0]
                        val = f.read(vlen).decode("utf-8", errors="replace")
                    elif vtype in (4, 5):  # UINT32, INT32
                        val = struct.unpack("<I", f.read(4))[0]
                    elif vtype in (10, 11):  # UINT64, INT64
                        val = struct.unpack("<Q", f.read(8))[0]
                    elif vtype == 6:  # FLOAT32
                        val = struct.unpack("<f", f.read(4))[0]
                    elif vtype == 7:  # BOOL
                        val = struct.unpack("<?", f.read(1))[0]
                    elif vtype in (0, 1):  # UINT8, INT8
                        val = struct.unpack("<B", f.read(1))[0]
                    elif vtype in (2, 3):  # UINT16, INT16
                        val = struct.unpack("<H", f.read(2))[0]
                    elif vtype == 12:  # FLOAT64
                        val = struct.unpack("<d", f.read(8))[0]
                    elif vtype == 9:  # ARRAY
                        elem_type = struct.unpack("<I", f.read(4))[0]
                        arr_len = struct.unpack(count_fmt, f.read(count_size))[0]
                        if elem_type in (0, 1, 7):
                            f.seek(arr_len, 1)
                        elif elem_type in (2, 3):
                            f.seek(arr_len * 2, 1)
                        elif elem_type in (4, 5, 6):
                            f.seek(arr_len * 4, 1)
                        elif elem_type in (10, 11, 12):
                            f.seek(arr_len * 8, 1)
                        elif elem_type == 8:
                            for _a in range(arr_len):
                                slen = struct.unpack(count_fmt, f.read(count_size))[0]
                                f.seek(slen, 1)
                        val = f"[array {arr_len}]"
                    else:
                        break
                    meta[key] = val

                arch = meta.get("general.architecture", "llama")
                layers = meta.get(f"{arch}.block_count")
                if layers is None:
                    for k, v in meta.items():
                        if k.endswith(".block_count") and isinstance(v, (int, float)):
                            layers = int(v)
                            break
                if layers is None:
                    layers = 32

                ctx_train = meta.get(f"{arch}.context_length")
                if ctx_train is None:
                    for k, v in meta.items():
                        if k.endswith(".context_length") and isinstance(v, (int, float)):
                            ctx_train = int(v)
                            break
                if ctx_train is None:
                    ctx_train = 4096

                embd = meta.get(f"{arch}.embedding_length")
                if embd is None:
                    for k, v in meta.items():
                        if k.endswith(".embedding_length") and isinstance(v, (int, float)):
                            embd = int(v)
                            break
                if embd is None:
                    embd = 4096

                heads = meta.get(f"{arch}.attention.head_count")
                if heads is None:
                    for k, v in meta.items():
                        if k.endswith(".attention.head_count") and isinstance(v, (int, float)):
                            heads = int(v)
                            break
                if heads is None:
                    heads = 32

                kv_heads = meta.get(f"{arch}.attention.head_count_kv")
                if kv_heads is None:
                    for k, v in meta.items():
                        if k.endswith(".attention.head_count_kv") and isinstance(v, (int, float)):
                            kv_heads = int(v)
                            break
                if kv_heads is None:
                    kv_heads = heads

                return {
                    "arch": arch,
                    "layers": int(layers),
                    "ctx_train": int(ctx_train),
                    "embd": int(embd),
                    "heads": int(heads),
                    "kv_heads": int(kv_heads),
                    "file_bytes": total_bytes,
                }
        except Exception:
            return {
                "arch": "unknown",
                "layers": 32,
                "ctx_train": 4096,
                "embd": 4096,
                "heads": 32,
                "kv_heads": 8,
                "file_bytes": total_bytes,
            }

    def estimate_vram_and_ram(self) -> dict:
        """
        Calculate projected GPU VRAM and CPU RAM footprints based on active model,
        device, ngl, context, and KV cache quantizations.
        """
        model_path = self.model_entry.get().strip() if hasattr(self, "model_entry") else ""
        if not model_path or not os.path.isfile(model_path):
            return {
                "valid_model": False,
                "vram_gb": 0.0,
                "total_vram_gb": 16.0,
                "headroom_gb": 16.0,
                "ram_gb": 0.0,
                "weights_vram_gb": 0.0,
                "kv_vram_gb": 0.0,
                "status": "NO MODEL",
                "status_color": THEME["text_muted"],
                "ratio": 0.0,
            }

        if model_path not in self.gguf_metadata_cache:
            self.gguf_metadata_cache[model_path] = self.parse_gguf_summary(model_path)
        meta = self.gguf_metadata_cache[model_path]

        total_layers = max(int(meta.get("layers", 32)), 1)
        total_file_bytes = int(meta.get("file_bytes", os.path.getsize(model_path) if os.path.isfile(model_path) else 0))
        heads = max(int(meta.get("heads", 32)), 1)
        kv_heads = max(int(meta.get("kv_heads", 8)), 1)
        embd = max(int(meta.get("embd", 4096)), 1)
        head_dim = max(embd // heads, 64)

        ngl = int(round(self.ngl_slider.get())) if hasattr(self, "ngl_slider") else 99
        ctx_idx = int(round(self.ctx_slider.get())) if hasattr(self, "ctx_slider") else len(CTX_STEPS) - 1
        ctx_tokens = CTX_STEPS[min(ctx_idx, len(CTX_STEPS) - 1)]

        ctk_type = self.ctk_dropdown.get() if hasattr(self, "ctk_dropdown") else "q8_0"
        ctv_type = self.ctv_dropdown.get() if hasattr(self, "ctv_dropdown") else "q8_0"

        dev_disp = self.device_dropdown.get() if hasattr(self, "device_dropdown") else ""
        dev_id = self.device_map.get(dev_disp, "")
        is_cpu_only = (dev_id == "none" or "cpu" in dev_disp.lower() or dev_disp == "none: CPU Only")

        bytes_map = {
            "f32": 4.0, "f16": 2.0, "bf16": 2.0, "q8_0": 1.0,
            "q5_1": 0.6875, "q5_0": 0.625, "q4_1": 0.5625, "q4_0": 0.5, "iq4_nl": 0.5,
        }
        k_b = bytes_map.get(ctk_type, 1.0)
        v_b = bytes_map.get(ctv_type, 1.0)

        if is_cpu_only:
            offloaded_layers = 0
        elif ngl >= 99 or ngl >= total_layers:
            offloaded_layers = total_layers
        else:
            offloaded_layers = max(0, min(ngl, total_layers))

        cpu_layers = total_layers - offloaded_layers

        weights_vram_bytes = total_file_bytes * (offloaded_layers / total_layers)
        weights_ram_bytes = total_file_bytes * (cpu_layers / total_layers)

        kv_per_token_per_layer = kv_heads * head_dim * (k_b + v_b)
        kv_vram_bytes = offloaded_layers * ctx_tokens * kv_per_token_per_layer
        kv_ram_bytes = cpu_layers * ctx_tokens * kv_per_token_per_layer

        if offloaded_layers > 0:
            overhead_vram_bytes = (600 * 1024 * 1024) + (ctx_tokens * 4096)
        else:
            overhead_vram_bytes = 0

        overhead_ram_bytes = 450 * 1024 * 1024

        vram_bytes = weights_vram_bytes + kv_vram_bytes + overhead_vram_bytes
        ram_bytes = weights_ram_bytes + kv_ram_bytes + overhead_ram_bytes

        vram_gb = vram_bytes / (1024 ** 3)
        ram_gb = ram_bytes / (1024 ** 3)

        device_total_vram = self.device_vram_map.get(dev_disp, 16.0)
        if is_cpu_only:
            device_total_vram = 32.0
            headroom_gb = 32.0 - ram_gb
            status = "CPU MODE"
            status_color = "#38bdf8"
            ratio = min(ram_gb / 32.0, 1.0)
        else:
            headroom_gb = device_total_vram - vram_gb
            ratio = min(vram_gb / max(device_total_vram, 0.1), 1.0)
            if vram_gb > device_total_vram:
                status = "OVERFLOW"
                status_color = "#ef4444"
            elif headroom_gb < 1.0:
                status = "TIGHT"
                status_color = "#f59e0b"
            else:
                status = "SAFE"
                status_color = "#10b981"

        return {
            "valid_model": True,
            "vram_gb": vram_gb,
            "total_vram_gb": device_total_vram,
            "headroom_gb": headroom_gb,
            "ram_gb": ram_gb,
            "weights_vram_gb": weights_vram_bytes / (1024 ** 3),
            "kv_vram_gb": kv_vram_bytes / (1024 ** 3),
            "status": status,
            "status_color": status_color,
            "ratio": min(max(ratio, 0.0), 1.0),
            "is_cpu_only": is_cpu_only,
            "total_layers": total_layers,
        }

    def _update_memory_estimation(self):
        """Update VRAM and RAM projection widgets in Column 1."""
        if not hasattr(self, "vram_est_label") or not hasattr(self, "vram_bar"):
            return

        est = self.estimate_vram_and_ram()
        if not est.get("valid_model", False):
            self.vram_est_label.configure(text="0.0 / -- GB", text_color=THEME["text_muted"])
            self.vram_status_badge.configure(text="IDLE", text_color=THEME["text_muted"])
            self.vram_bar.set(0.0)
            self.vram_bar.configure(progress_color=THEME["slider_progress"])
            self.vram_detail_label.configure(text="Select or browse a .gguf model to preview VRAM")
            return

        if est.get("is_cpu_only", False):
            self.vram_est_label.configure(
                text=f"RAM: {est['ram_gb']:.1f} GB (CPU Only)",
                text_color=THEME["text_primary"],
            )
            self.vram_status_badge.configure(text="CPU", text_color="#38bdf8")
            self.vram_bar.set(est["ratio"])
            self.vram_bar.configure(progress_color="#38bdf8")
            self.vram_detail_label.configure(
                text=f"RAM: {est['ram_gb']:.1f}G | Weights: {est['weights_vram_gb']:.1f}G | KV: {est['kv_ram_gb']:.1f}G"
            )
        else:
            v_gb = est["vram_gb"]
            tot_gb = est["total_vram_gb"]
            headroom = est["headroom_gb"]
            color = est["status_color"]

            headroom_str = f"+{headroom:.1f} GB Free" if headroom >= 0 else f"{abs(headroom):.1f} GB OOM"
            self.vram_est_label.configure(
                text=f"{v_gb:.1f} / {tot_gb:.1f} GB ({headroom_str})",
                text_color=THEME["text_primary"],
            )
            self.vram_status_badge.configure(text=est["status"], text_color=color)
            self.vram_bar.set(est["ratio"])
            self.vram_bar.configure(progress_color=color)
            self.vram_detail_label.configure(
                text=f"Weights: {est['weights_vram_gb']:.1f}G | KV: {est['kv_vram_gb']:.1f}G | RAM: {est['ram_gb']:.1f}G"
            )

    def auto_fit_hardware(self):
        """
        Auto-Fit Engine:
        Calculates maximum viable GPU layers (-ngl) and largest context window (-c)
        to fit into available VRAM while preserving safe headroom.
        """
        model_path = self.model_entry.get().strip() if hasattr(self, "model_entry") else ""
        if not model_path or not os.path.isfile(model_path):
            self._flash_badge("● SELECT MODEL FIRST", is_alert=True)
            return

        dev_disp = self.device_dropdown.get() if hasattr(self, "device_dropdown") else ""
        dev_id = self.device_map.get(dev_disp, "")
        if dev_id == "none" or "cpu" in dev_disp.lower():
            self._flash_badge("● GPU NOT SELECTED", is_alert=True)
            return

        total_vram_gb = self.device_vram_map.get(dev_disp, 16.0)

        # Parse safety margin from extra flags if specified, else 1.0 GB
        safety_gb = 1.0
        extra_flags = self.extra_flags_entry.get() if hasattr(self, "extra_flags_entry") else ""
        margin_match = re.search(r"--fit-target\s+(\d+(?:\.\d+)?)", extra_flags)
        if margin_match:
            try:
                val = float(margin_match.group(1))
                safety_gb = val / 1024.0 if val > 32.0 else val
            except Exception:
                safety_gb = 1.0

        target_vram_gb = max(total_vram_gb - safety_gb, 1.0)

        if model_path not in self.gguf_metadata_cache:
            self.gguf_metadata_cache[model_path] = self.parse_gguf_summary(model_path)
        meta = self.gguf_metadata_cache[model_path]

        total_layers = max(int(meta.get("layers", 32)), 1)
        total_file_bytes = int(meta.get("file_bytes", os.path.getsize(model_path)))
        heads = max(int(meta.get("heads", 32)), 1)
        kv_heads = max(int(meta.get("kv_heads", 8)), 1)
        embd = max(int(meta.get("embd", 4096)), 1)
        head_dim = max(embd // heads, 64)

        ctk_type = self.ctk_dropdown.get() if hasattr(self, "ctk_dropdown") else "q8_0"
        ctv_type = self.ctv_dropdown.get() if hasattr(self, "ctv_dropdown") else "q8_0"

        bytes_map = {
            "f32": 4.0, "f16": 2.0, "bf16": 2.0, "q8_0": 1.0,
            "q5_1": 0.6875, "q5_0": 0.625, "q4_1": 0.5625, "q4_0": 0.5, "iq4_nl": 0.5,
        }
        k_b = bytes_map.get(ctk_type, 1.0)
        v_b = bytes_map.get(ctv_type, 1.0)
        kv_per_token_per_layer = kv_heads * head_dim * (k_b + v_b)

        def calc_vram(ngl_val, ctx_tokens):
            offload = total_layers if (ngl_val >= 99 or ngl_val >= total_layers) else max(0, ngl_val)
            w_bytes = total_file_bytes * (offload / total_layers)
            kv_bytes = offload * ctx_tokens * kv_per_token_per_layer
            over_bytes = (600 * 1024 * 1024) + (ctx_tokens * 4096) if offload > 0 else 0
            return (w_bytes + kv_bytes + over_bytes) / (1024 ** 3)

        best_ngl = 99
        best_ctx_idx = 0
        full_offload_possible = False

        for c_idx in range(len(CTX_STEPS) - 1, -1, -1):
            c_val = CTX_STEPS[c_idx]
            v = calc_vram(99, c_val)
            if v <= target_vram_gb:
                best_ngl = 99
                best_ctx_idx = c_idx
                full_offload_possible = True
                break

        if not full_offload_possible:
            best_ctx_idx = 0
            c_val = CTX_STEPS[best_ctx_idx]
            best_ngl = 0
            for test_ngl in range(total_layers, -1, -1):
                v = calc_vram(test_ngl, c_val)
                if v <= target_vram_gb:
                    best_ngl = test_ngl
                    break

        self.ngl_slider.set(best_ngl)
        self._on_ngl_change(best_ngl)
        self.ctx_slider.set(best_ctx_idx)
        self._on_ctx_change(best_ctx_idx)
        self._update_memory_estimation()

        ctx_disp = f"{CTX_STEPS[best_ctx_idx] // 1024}K"
        ngl_disp = "All" if best_ngl == 99 else str(best_ngl)
        self._flash_badge(f"● AUTO-FIT: {ngl_disp} L, {ctx_disp} CTX")

    @classmethod
    def scan_models_in_dir(cls, directory: str) -> dict:
        """
        Scan directory for .gguf files, grouping multi-part models (e.g. 00001-of-00004, 0001, part1).
        Excludes standalone mmproj-*.gguf files.
        Returns a dict mapping display_name -> first_part_filepath.
        """
        if not directory or not os.path.isdir(directory):
            return {}

        try:
            entries = os.listdir(directory)
        except Exception:
            return {}

        # Patterns for split/multipart models
        p1 = re.compile(r"^(.*?)[-_.]+(\d{4,5})[-_.]+(?:of[-_.]+(\d{4,5}))\.gguf$", re.IGNORECASE)
        p2 = re.compile(r"^(.*?)[-_.]+(\d{4,5})\.gguf$", re.IGNORECASE)
        p3 = re.compile(r"^(.*?)[-_.]+part[-_.]*(\d{1,5})\.gguf$", re.IGNORECASE)

        groups = {} # base_key -> list of (part_num, full_path, size)
        singles = [] # list of (full_path, filename, size)

        for filename in entries:
            lower = filename.lower()
            if not lower.endswith(".gguf") or "mmproj" in lower:
                continue

            full_path = os.path.normpath(os.path.join(directory, filename))
            if not os.path.isfile(full_path):
                continue

            try:
                size = os.path.getsize(full_path)
            except Exception:
                size = 0

            m1 = p1.match(filename)
            m2 = p2.match(filename)
            m3 = p3.match(filename)

            if m1:
                base = m1.group(1).rstrip("-_.")
                part = int(m1.group(2))
                groups.setdefault(base, []).append((part, full_path, size))
            elif m2:
                base = m2.group(1).rstrip("-_.")
                part = int(m2.group(2))
                groups.setdefault(base, []).append((part, full_path, size))
            elif m3:
                base = m3.group(1).rstrip("-_.")
                part = int(m3.group(2))
                groups.setdefault(base, []).append((part, full_path, size))
            else:
                singles.append((full_path, filename, size))

        result_map = {}

        # Process grouped multi-part models
        for base, parts in sorted(groups.items(), key=lambda x: x[0].lower()):
            if len(parts) > 1:
                parts.sort(key=lambda x: x[0])
                first_file = parts[0][1] # lowest part number, e.g. 00001 or 0001
                total_size = sum(x[2] for x in parts)
                size_str = cls._format_file_size(total_size)
                display_label = f"{base} ({size_str} - {len(parts)} parts)"
                result_map[display_label] = first_file
            else:
                # Only 1 part found; display as single
                p_info = parts[0]
                fname = os.path.basename(p_info[1])
                clean_name = fname[:-5] if fname.lower().endswith(".gguf") else fname
                size_str = cls._format_file_size(p_info[2])
                display_label = f"{clean_name} ({size_str})"
                result_map[display_label] = p_info[1]

        # Process standalone single models
        for full_path, fname, size in sorted(singles, key=lambda x: x[1].lower()):
            clean_name = fname[:-5] if fname.lower().endswith(".gguf") else fname
            size_str = cls._format_file_size(size)
            display_label = f"{clean_name} ({size_str})"
            result_map[display_label] = full_path

        return result_map

    def _trigger_models_scan(self, on_complete=None):
        """Asynchronously scan the configured models_dir and populate model_library_menu."""
        models_folder = self.models_dir.strip() if hasattr(self, "models_dir") else ""
        if hasattr(self, "models_dir_entry"):
            models_folder = self.models_dir_entry.get().strip()

        if not models_folder or not os.path.isdir(models_folder):
            self.scanned_models_map = {}
            if hasattr(self, "model_library_menu"):
                self.model_library_menu.configure(values=["No Models Found (Set Folder)"])
                self.model_library_menu.set("No Models Found (Set Folder)")
            if on_complete:
                on_complete(0)
            return

        def worker():
            res = self.scan_models_in_dir(models_folder)

            def apply_results():
                self.scanned_models_map = res
                if hasattr(self, "model_library_menu"):
                    if res:
                        options = ["Select Model from Folder..."] + list(res.keys())
                        self.model_library_menu.configure(values=options)
                        self.model_library_menu.set("Select Model from Folder...")
                    else:
                        self.model_library_menu.configure(values=["No Models in Folder"])
                        self.model_library_menu.set("No Models in Folder")
                if on_complete:
                    on_complete(len(res))

            self.after(0, apply_results)

        threading.Thread(target=worker, daemon=True).start()

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
            self._update_memory_estimation()

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

        self._update_memory_estimation()

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

        # Row 1: Models Folder (Configurable Directory)
        ctk.CTkLabel(
            card,
            text="Models Folder",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=115,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(12, 4), pady=(0, 5))

        self.models_dir_entry = ctk.CTkEntry(
            card,
            placeholder_text=r"Folder containing .gguf models (e.g. D:\Models)",
            placeholder_text_color=THEME["text_muted"],
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            border_width=1,
            text_color=THEME["text_primary"],
            corner_radius=6,
            height=30,
            font=self.font_sm,
        )
        if self.models_dir:
            self.models_dir_entry.insert(0, self.models_dir)
        self.models_dir_entry.grid(row=1, column=1, sticky="ew", padx=(4, 8), pady=(0, 5))

        folder_btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        folder_btn_frame.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=(0, 5))

        self.browse_dir_btn = ctk.CTkButton(
            folder_btn_frame,
            text="Browse",
            width=50,
            height=30,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.choose_models_folder,
        )
        self.browse_dir_btn.pack(side="left", padx=(0, 4))

        self.refresh_models_btn = ctk.CTkButton(
            folder_btn_frame,
            text="🔄",
            width=31,
            height=30,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=self.refresh_models_folder,
        )
        self.refresh_models_btn.pack(side="left")

        # Row 2: Model GGUF + Vision Checkbox
        model_lbl_frame = ctk.CTkFrame(card, fg_color="transparent")
        model_lbl_frame.grid(row=2, column=0, sticky="w", padx=(12, 4), pady=(0, 6))

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

        # Model input container: Entry + Library Dropdown + Recent Models Dropdown
        model_input_frame = ctk.CTkFrame(card, fg_color="transparent")
        model_input_frame.grid(row=2, column=1, sticky="ew", padx=(4, 8), pady=(0, 6))
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
        self.model_entry.bind("<KeyRelease>", lambda _: self._update_memory_estimation())
        self.model_entry.bind("<FocusOut>", lambda _: self._update_memory_estimation())

        self.model_library_menu = ctk.CTkOptionMenu(
            model_input_frame,
            values=["Scanning Folder..."],
            command=self._on_library_model_selected,
            fg_color=THEME["input_bg"],
            button_color="#27272a",
            button_hover_color="#3f3f46",
            text_color=THEME["text_secondary"],
            dropdown_fg_color=THEME["dropdown_bg"],
            dropdown_text_color=THEME["text_primary"],
            dropdown_hover_color="#27272a",
            corner_radius=6,
            height=30,
            width=150,
            font=self.font_sm,
        )
        self.model_library_menu.set("Model Library...")
        self.model_library_menu.grid(row=0, column=1, sticky="e", padx=(0, 4))

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
            width=125,
            font=self.font_sm,
        )
        self.recent_models_menu.set("Recent Models...")
        self.recent_models_menu.grid(row=0, column=2, sticky="e")

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
        self.browse_btn.grid(row=2, column=2, sticky="e", padx=(0, 12), pady=(0, 6))

        # Row 3: Vision mmproj (Conditionally displayed when Vision checkbox is checked)
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
                self.mmproj_label.grid(row=3, column=0, sticky="w", padx=(12, 4), pady=(0, 8))
                self.mmproj_entry.grid(row=3, column=1, sticky="ew", padx=(4, 8), pady=(0, 8))
                self.mmproj_browse_btn.grid(row=3, column=2, sticky="e", padx=(0, 12), pady=(0, 8))
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
            new_vram_map = {}
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
                        # Extract VRAM size if present, e.g. (16304 MiB, 15416 MiB free)
                        vram_gb = 16.0
                        vram_match = re.search(r"\((\d+)\s*MiB", desc)
                        if vram_match:
                            vram_gb = round(float(vram_match.group(1)) / 1024.0, 1)

                        clean_desc = re.sub(r"\s*\(\d+\s*MiB.*?\)", "", desc).strip()
                        disp_key = f"{dev_id}: {clean_desc}"
                        new_map[disp_key] = dev_id
                        new_vram_map[disp_key] = vram_gb
            except Exception:
                pass

            if new_map:
                if not any(v == "none" for v in new_map.values()):
                    new_map["none: CPU Only"] = "none"
                    new_vram_map["none: CPU Only"] = 32.0

                def apply_results():
                    self.device_map = new_map
                    self.device_vram_map = new_vram_map
                    if hasattr(self, "device_dropdown"):
                        options = list(self.device_map.keys())
                        curr = self.device_dropdown.get()
                        self.device_dropdown.configure(values=options)
                        if curr in self.device_map:
                            self.device_dropdown.set(curr)
                        else:
                            self.device_dropdown.set(self._get_default_device_display())
                    self._update_memory_estimation()
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
            command=self._on_device_change,
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

        # Row 5: Action Buttons (Detect GPUs & Auto-Fit)
        act_frame = ctk.CTkFrame(card, fg_color="transparent")
        act_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 6))
        act_frame.columnconfigure(0, weight=1)
        act_frame.columnconfigure(1, weight=1)

        self.detect_btn = ctk.CTkButton(
            act_frame,
            text="Detect GPUs",
            height=26,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["secondary_btn_text"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self._refresh_devices,
        )
        self.detect_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.auto_fit_btn = ctk.CTkButton(
            act_frame,
            text="⚡ Auto-Fit",
            height=26,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color="#38bdf8",
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.auto_fit_hardware,
        )
        self.auto_fit_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Row 6: Real-Time Projected VRAM & Memory Estimator Card
        self.vram_est_card = ctk.CTkFrame(
            card,
            fg_color="#18181b",
            border_width=1,
            border_color="#27272a",
            corner_radius=8,
        )
        self.vram_est_card.grid(row=6, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 8))

        top_est_frame = ctk.CTkFrame(self.vram_est_card, fg_color="transparent")
        top_est_frame.pack(fill="x", padx=8, pady=(5, 2))

        ctk.CTkLabel(
            top_est_frame,
            text="PROJECTED VRAM",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=THEME["text_muted"],
        ).pack(side="left")

        self.vram_status_badge = ctk.CTkLabel(
            top_est_frame,
            text="SAFE",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#10b981",
        )
        self.vram_status_badge.pack(side="right")

        self.vram_est_label = ctk.CTkLabel(
            self.vram_est_card,
            text="0.0 / 16.0 GB (+16.0 GB Free)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME["text_primary"],
            anchor="w",
        )
        self.vram_est_label.pack(fill="x", padx=8, pady=(0, 3))

        self.vram_bar = ctk.CTkProgressBar(
            self.vram_est_card,
            height=6,
            corner_radius=3,
            fg_color="#27272a",
            progress_color="#10b981",
        )
        self.vram_bar.set(0.0)
        self.vram_bar.pack(fill="x", padx=8, pady=(0, 4))

        self.vram_detail_label = ctk.CTkLabel(
            self.vram_est_card,
            text="Weights: 0.0G | KV: 0.0G | RAM: 0.0G",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=THEME["text_secondary"],
            anchor="w",
        )
        self.vram_detail_label.pack(fill="x", padx=8, pady=(0, 5))

    def _on_ngl_change(self, val):
        v = int(round(val))
        self.ngl_badge.configure(text="99 (All)" if v == 99 else ("0 (CPU)" if v == 0 else str(v)))
        self._update_memory_estimation()

    def _on_ctx_change(self, val):
        tokens = CTX_STEPS[int(round(val))]
        self.ctx_badge.configure(text=f"{tokens // 1024}K")
        self._update_memory_estimation()

    def _on_device_change(self, choice):
        self._update_memory_estimation()

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

        # Header with Title and Sampler Presets Dropdown
        hdr_frame = ctk.CTkFrame(card, fg_color="transparent")
        hdr_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=12, pady=(8, 6))
        hdr_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr_frame,
            text="BATCHING & GENERATION",
            font=self.font_section,
            text_color=THEME["text_primary"],
        ).pack(side="left")

        preset_options = ["Sampler Preset..."] + list(SAMPLER_PRESETS.keys())
        self.sampler_preset_menu = ctk.CTkOptionMenu(
            hdr_frame,
            values=preset_options,
            command=self._on_sampler_preset_selected,
            fg_color=THEME["input_bg"],
            button_color="#27272a",
            button_hover_color="#3f3f46",
            text_color=THEME["text_secondary"],
            dropdown_fg_color=THEME["dropdown_bg"],
            dropdown_text_color=THEME["text_primary"],
            dropdown_hover_color="#27272a",
            corner_radius=6,
            height=24,
            width=140,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
        )
        self.sampler_preset_menu.set("Sampler Preset...")
        self.sampler_preset_menu.pack(side="right")

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
            command=lambda _: self._update_memory_estimation(),
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
            command=lambda _: self._update_memory_estimation(),
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

        self.fa_chk = ctk.CTkCheckBox(
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
        )
        self.fa_chk.pack(side="left", padx=(0, 12))

        self.jinja_chk = ctk.CTkCheckBox(
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
        )
        self.jinja_chk.pack(side="left")

    def _on_batch_change(self, val):
        self.batch_badge.configure(text=str(BATCH_STEPS[int(round(val))]))

    def _on_ubatch_change(self, val):
        self.ubatch_badge.configure(text=str(UBATCH_STEPS[int(round(val))]))

    def _on_sampler_preset_selected(self, preset_name: str):
        """Apply community-verified sampling parameters and persist to active profile."""
        if preset_name not in SAMPLER_PRESETS:
            return

        cfg = SAMPLER_PRESETS[preset_name]
        self.temp_entry.delete(0, "end")
        self.temp_entry.insert(0, cfg["temp"])

        self.topp_entry.delete(0, "end")
        self.topp_entry.insert(0, cfg["topp"])

        self.minp_entry.delete(0, "end")
        self.minp_entry.insert(0, cfg["minp"])

        if hasattr(self, "profiles") and self.profiles and hasattr(self, "active_profile_idx"):
            p = self.profiles[self.active_profile_idx]
            p["temp"] = cfg["temp"]
            p["topp"] = cfg["topp"]
            p["minp"] = cfg["minp"]
            self._persist_profiles()

        self._flash_badge(f"● SAMPLER: {preset_name.upper()}")

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
        self.opt_chks = {}

        opts_config = [
            ("mlock", "Lock in RAM (--load-mode)", "dropdown", "mlock", ["mlock", "mmap+mlock"]),
            ("tb", "Prompt Threads (-tb)", "entry", "8", None),
            ("fit_target", "VRAM Margin (--fit-target MiB)", "entry", "1024", None),
            ("cache_reuse", "KV Cache Reuse (--cache-reuse)", "entry", "256", None),
            ("parallel", "Dedicated Slot (-np)", "entry", "1", None),
            ("cache_ram", "System RAM Cache (--cache-ram MiB)", "entry", "8192", None),
            ("cpu_moe", "CPU MoE Experts (--n-cpu-moe)", "entry", "16", None),
            ("ctx_shift", "Context Shift (--ctx-shift)", "none", "on", None),
            ("defrag_thold", "KV Defrag Thold (--defrag-thold)", "entry", "0.1", None),
        ]

        for idx, (key, label, w_type, default_val, options) in enumerate(opts_config, start=1):
            self.opt_vars[key] = ctk.BooleanVar(value=False)
            self.opt_str_vars[key] = ctk.StringVar(value=default_val if default_val else "")

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
            self.opt_chks[key] = chk

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
                widget.grid(row=idx, column=1, sticky="e", padx=(0, 12), pady=2)
                self.opt_widgets[key] = widget
            elif w_type == "entry":
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
            else:
                self.opt_widgets[key] = None

    def _toggle_opt_widget(self, key):
        widget = self.opt_widgets.get(key)
        if widget is None:
            return
        is_active = self.opt_vars[key].get()

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
        action_row.columnconfigure(0, weight=3)
        action_row.columnconfigure(1, weight=1)
        action_row.columnconfigure(2, weight=1)
        action_row.columnconfigure(3, weight=1)
        action_row.columnconfigure(4, weight=1)
        action_row.columnconfigure(5, weight=1)
        action_row.columnconfigure(6, weight=1)

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
        self.import_script_btn.grid(row=0, column=5, sticky="ew", padx=(0, 6))

        self.profile_helper_btn = ctk.CTkButton(
            action_row,
            text="✨  Profile Helper",
            height=42,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["secondary_btn_text"],
            corner_radius=8,
            command=self.open_profile_helper,
        )
        self.profile_helper_btn.grid(row=0, column=6, sticky="ew")

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

        # Live Inference Telemetry Strip (Phase 2)
        self.telemetry_strip = ctk.CTkFrame(
            self.drawer_bar,
            fg_color="#18181b",
            corner_radius=6,
            border_width=1,
            border_color="#27272a",
            height=28,
        )
        self.telemetry_strip.pack(side="left", padx=(4, 8), fill="x", expand=True)

        self.telemetry_label = ctk.CTkLabel(
            self.telemetry_strip,
            text="⚪ SERVER OFFLINE  |  Prompt: -- t/s  |  Gen: -- t/s  |  Tokens: --  |  Slots: Idle (0%)",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#ffffff",
            anchor="center",
        )
        self.telemetry_label.pack(fill="both", expand=True, padx=8, pady=3)

        # Public Tunnel quick button on the right
        self.tunnel_btn = ctk.CTkButton(
            self.drawer_bar,
            text="🌐  Public Tunnel",
            height=28,
            width=135,
            fg_color="#18181b",
            hover_color="#27272a",
            border_width=1,
            border_color="#3f3f46",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#e4e4e7",
            corner_radius=6,
            command=self.open_tunnel_dialog,
        )
        self.tunnel_btn.pack(side="right", padx=(0, 8))

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

        self.autoscroll_chk = ctk.CTkCheckBox(
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
        )
        self.autoscroll_chk.pack(side="left", padx=(0, 8))

        self.copy_logs_btn = ctk.CTkButton(
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
        )
        self.copy_logs_btn.pack(side="left", padx=(0, 6))

        self.clear_logs_btn = ctk.CTkButton(
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
        )
        self.clear_logs_btn.pack(side="left")

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

    def _apply_tooltips(self):
        """Attach concise, informative tooltips to all interactive elements across the launcher."""
        tips = {
            # Profiles & Top Header
            "profile_seg": "Switch hardware profile preset",
            "save_prof_btn": "Save current settings to selected profile",
            "rename_prof_btn": "Rename active profile preset",

            # Paths Card
            "exe_entry": "Path to llama-server.exe executable binary",
            "browse_exe_btn": "Browse filesystem for llama-server.exe",
            "models_dir_entry": "Folder containing .gguf models for auto-scanning",
            "browse_dir_btn": "Select folder containing GGUF model files",
            "refresh_models_btn": "Rescan models folder for new GGUF files",
            "model_entry": "Active GGUF model file path or split part 00001",
            "model_library_menu": "Quick-select model from configured folder",
            "recent_models_menu": "Recently loaded model files history",
            "browse_btn": "Browse filesystem for a .gguf model file",
            "vision_chk": "Enable vision multimodal projector (--mmproj)",
            "mmproj_entry": "Path to vision multimodal projector (.gguf)",
            "mmproj_browse_btn": "Browse filesystem for mmproj .gguf file",

            # Column 1: Hardware & Acceleration
            "device_dropdown": "Select compute backend device (Vulkan/CUDA/CPU)",
            "ngl_slider": "GPU layers offloaded (-ngl). 99 offloads all layers",
            "ctx_slider": "Context window limit in tokens (-c)",
            "port_entry": "HTTP server listening port (default: 8082)",
            "threads_entry": "CPU worker threads for generation (-t)",
            "detect_btn": "Query system GPUs via llama-server --list-devices",
            "auto_fit_btn": "Auto-tune layers (-ngl) & context (-c) to fit VRAM safely",
            "vram_est_card": "Pre-launch projected VRAM & RAM memory estimation",

            # Column 2: Batching & Generation
            "sampler_preset_menu": "Load curated sampling presets (Balanced, Code, Story, etc.)",
            "batch_slider": "Logical prompt processing batch size (-b)",
            "ubatch_slider": "Physical compute micro-batch size (-ub)",
            "ctk_dropdown": "Key (K) cache quantization type (-ctk)",
            "ctv_dropdown": "Value (V) cache quantization type (-ctv)",
            "temp_entry": "Generation randomness temperature (--temp)",
            "topp_entry": "Nucleus sampling probability threshold (--top-p)",
            "minp_entry": "Minimum token probability threshold (--min-p)",
            "fa_chk": "Flash Attention acceleration for lower VRAM & faster prompt processing (-fa)",
            "jinja_chk": "Enable Jinja template parser for chat formatting (--jinja)",

            # Column 3: Hardware Profile Optimizations
            "opt_mlock": "Lock model weights in physical RAM to prevent OS swapping (--load-mode)",
            "opt_tb": "Dedicated threads for prompt batch processing (-tb)",
            "opt_fit_target": "VRAM margin in MiB reserved for driver headroom (--fit-target)",
            "opt_cache_reuse": "KV cache chunk reuse threshold for faster repeated prompts (--cache-reuse)",
            "opt_parallel": "Parallel processing slots for multi-turn requests (-np)",
            "opt_cache_ram": "RAM allocated for context swap cache in MiB (--cache-ram)",
            "opt_cpu_moe": "Number of MoE expert layers offloaded to CPU (--n-cpu-moe)",
            "opt_ctx_shift": "Prevent OOM by shifting older context when full (--ctx-shift)",
            "opt_defrag_thold": "KV cache defragmentation threshold ratio (--defrag-thold)",

            # Action Row
            "start_btn": "Launch or stop the llama-server HTTP process",
            "open_webui_btn": "Open llama.cpp embedded Web UI in default browser",
            "client_configs_btn": "View connection snippets for OpenAI, Ollama, LangChain, etc.",
            "api_tester_btn": "Test model with live interactive API prompt tester",
            "export_script_btn": "Export configured parameters as standalone PowerShell script",
            "import_script_btn": "Import parameters from a previously exported PowerShell script",
            "profile_helper_btn": "Automated hardware benchmark & profile recommendation wizard",

            # Log Console & Bottom Drawer Toolbar
            "drawer_toggle_btn": "Expand or collapse embedded live log console",
            "auto_restart_chk": "Automatically restart server if process crashes unexpectedly",
            "external_console_chk": "Launch server in separate Windows Command Prompt console",
            "tray_close_chk": "Minimize application to system tray instead of closing",
            "telemetry_strip": "Real-time inference tokens/sec, throughput & slot metrics",
            "tunnel_btn": "Create instant public secure tunnel (Cloudflare / Ngrok)",
            "tray_btn": "Minimize window directly to Windows system tray",
            "log_filter_entry": "Filter console output by regex or keyword",
            "copy_logs_btn": "Copy all console log lines to clipboard",
            "clear_logs_btn": "Clear log console buffer",
        }

        # Header widgets
        if hasattr(self, "profile_seg"):
            ToolTip(self.profile_seg, tips["profile_seg"])
        if hasattr(self, "save_prof_btn"):
            ToolTip(self.save_prof_btn, tips["save_prof_btn"])
        if hasattr(self, "rename_prof_btn"):
            ToolTip(self.rename_prof_btn, tips["rename_prof_btn"])

        # Paths Card
        if hasattr(self, "exe_entry"):
            ToolTip(self.exe_entry, tips["exe_entry"])
        if hasattr(self, "browse_exe_btn"):
            ToolTip(self.browse_exe_btn, tips["browse_exe_btn"])
        if hasattr(self, "models_dir_entry"):
            ToolTip(self.models_dir_entry, tips["models_dir_entry"])
        if hasattr(self, "browse_dir_btn"):
            ToolTip(self.browse_dir_btn, tips["browse_dir_btn"])
        if hasattr(self, "refresh_models_btn"):
            ToolTip(self.refresh_models_btn, tips["refresh_models_btn"])
        if hasattr(self, "model_entry"):
            ToolTip(self.model_entry, tips["model_entry"])
        if hasattr(self, "model_library_menu"):
            ToolTip(self.model_library_menu, tips["model_library_menu"])
        if hasattr(self, "recent_models_menu"):
            ToolTip(self.recent_models_menu, tips["recent_models_menu"])
        if hasattr(self, "browse_btn"):
            ToolTip(self.browse_btn, tips["browse_btn"])
        if hasattr(self, "vision_chk"):
            ToolTip(self.vision_chk, tips["vision_chk"])
        if hasattr(self, "mmproj_entry"):
            ToolTip(self.mmproj_entry, tips["mmproj_entry"])
        if hasattr(self, "mmproj_browse_btn"):
            ToolTip(self.mmproj_browse_btn, tips["mmproj_browse_btn"])

        # Column 1
        if hasattr(self, "device_dropdown"):
            ToolTip(self.device_dropdown, tips["device_dropdown"])
        if hasattr(self, "ngl_slider"):
            ToolTip(self.ngl_slider, tips["ngl_slider"])
        if hasattr(self, "ctx_slider"):
            ToolTip(self.ctx_slider, tips["ctx_slider"])
        if hasattr(self, "port_entry"):
            ToolTip(self.port_entry, tips["port_entry"])
        if hasattr(self, "threads_entry"):
            ToolTip(self.threads_entry, tips["threads_entry"])
        if hasattr(self, "detect_btn"):
            ToolTip(self.detect_btn, tips["detect_btn"])
        if hasattr(self, "auto_fit_btn"):
            ToolTip(self.auto_fit_btn, tips["auto_fit_btn"])
        if hasattr(self, "vram_est_card"):
            ToolTip(self.vram_est_card, tips["vram_est_card"])

        # Column 2
        if hasattr(self, "sampler_preset_menu"):
            ToolTip(self.sampler_preset_menu, tips["sampler_preset_menu"])
        if hasattr(self, "batch_slider"):
            ToolTip(self.batch_slider, tips["batch_slider"])
        if hasattr(self, "ubatch_slider"):
            ToolTip(self.ubatch_slider, tips["ubatch_slider"])
        if hasattr(self, "ctk_dropdown"):
            ToolTip(self.ctk_dropdown, tips["ctk_dropdown"])
        if hasattr(self, "ctv_dropdown"):
            ToolTip(self.ctv_dropdown, tips["ctv_dropdown"])
        if hasattr(self, "temp_entry"):
            ToolTip(self.temp_entry, tips["temp_entry"])
        if hasattr(self, "topp_entry"):
            ToolTip(self.topp_entry, tips["topp_entry"])
        if hasattr(self, "minp_entry"):
            ToolTip(self.minp_entry, tips["minp_entry"])
        if hasattr(self, "fa_chk"):
            ToolTip(self.fa_chk, tips["fa_chk"])
        if hasattr(self, "jinja_chk"):
            ToolTip(self.jinja_chk, tips["jinja_chk"])

        # Column 3
        if hasattr(self, "opt_chks"):
            for k, chk in self.opt_chks.items():
                tip_key = f"opt_{k}"
                if tip_key in tips:
                    ToolTip(chk, tips[tip_key])
        if hasattr(self, "opt_widgets"):
            for k, w in self.opt_widgets.items():
                if w is not None:
                    tip_key = f"opt_{k}"
                    if tip_key in tips:
                        ToolTip(w, tips[tip_key])

        # Action Row
        if hasattr(self, "start_btn"):
            ToolTip(self.start_btn, tips["start_btn"])
        if hasattr(self, "open_webui_btn"):
            ToolTip(self.open_webui_btn, tips["open_webui_btn"])
        if hasattr(self, "client_configs_btn"):
            ToolTip(self.client_configs_btn, tips["client_configs_btn"])
        if hasattr(self, "api_tester_btn"):
            ToolTip(self.api_tester_btn, tips["api_tester_btn"])
        if hasattr(self, "export_script_btn"):
            ToolTip(self.export_script_btn, tips["export_script_btn"])
        if hasattr(self, "import_script_btn"):
            ToolTip(self.import_script_btn, tips["import_script_btn"])
        if hasattr(self, "profile_helper_btn"):
            ToolTip(self.profile_helper_btn, tips["profile_helper_btn"])

        # Drawer & Bottom Bar
        if hasattr(self, "drawer_toggle_btn"):
            ToolTip(self.drawer_toggle_btn, tips["drawer_toggle_btn"])
        if hasattr(self, "auto_restart_chk"):
            ToolTip(self.auto_restart_chk, tips["auto_restart_chk"])
        if hasattr(self, "external_console_chk"):
            ToolTip(self.external_console_chk, tips["external_console_chk"])
        if hasattr(self, "tray_close_chk"):
            ToolTip(self.tray_close_chk, tips["tray_close_chk"])
        if hasattr(self, "telemetry_strip"):
            ToolTip(self.telemetry_strip, tips["telemetry_strip"])
        if hasattr(self, "tunnel_btn"):
            ToolTip(self.tunnel_btn, tips["tunnel_btn"])
        if hasattr(self, "tray_btn"):
            ToolTip(self.tray_btn, tips["tray_btn"])
        if hasattr(self, "log_filter_entry"):
            ToolTip(self.log_filter_entry, tips["log_filter_entry"])
        if hasattr(self, "autoscroll_chk"):
            ToolTip(self.autoscroll_chk, "Automatically scroll to bottom on new log output")
        if hasattr(self, "copy_logs_btn"):
            ToolTip(self.copy_logs_btn, tips["copy_logs_btn"])
        if hasattr(self, "clear_logs_btn"):
            ToolTip(self.clear_logs_btn, tips["clear_logs_btn"])

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

    def open_profile_helper(self):
        """Open the Profile Helper dialog to generate AI optimization prompts from hardware specs."""
        ProfileHelperDialog(master=self)

    def browse_exe(self):
        f = filedialog.askopenfilename(
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")],
            title="Select llama-server.exe"
        )
        if f:
            self.exe_entry.delete(0, "end")
            self.exe_entry.insert(0, os.path.normpath(f))
            self._refresh_devices()

    def choose_models_folder(self):
        """Open directory chooser for Models Folder, persist config, and scan for models."""
        initial_dir = self.models_dir if (self.models_dir and os.path.isdir(self.models_dir)) else None
        d = filedialog.askdirectory(initialdir=initial_dir, title="Select Models Folder Containing .gguf Files")
        if d:
            norm_dir = os.path.normpath(d)
            self.models_dir = norm_dir
            if hasattr(self, "models_dir_entry"):
                self.models_dir_entry.delete(0, "end")
                self.models_dir_entry.insert(0, norm_dir)
            self._persist_app_config()
            self._flash_badge("● SCANNING MODELS FOLDER...")
            self.refresh_models_folder()

    def refresh_models_folder(self):
        """Refresh models list from the entered or selected models folder."""
        if hasattr(self, "models_dir_entry"):
            entered_dir = self.models_dir_entry.get().strip()
            if entered_dir and os.path.isdir(entered_dir):
                self.models_dir = os.path.normpath(entered_dir)
                self._persist_app_config()

        if hasattr(self, "refresh_models_btn"):
            self.refresh_models_btn.configure(state="disabled")

        def on_done(count):
            if hasattr(self, "refresh_models_btn"):
                self.refresh_models_btn.configure(state="normal")
            if count > 0:
                self._flash_badge(f"● LOADED {count} MODELS")
            else:
                self._flash_badge("⚠ NO MODELS IN FOLDER", is_alert=True)

        self._trigger_models_scan(on_complete=on_done)

    def _on_library_model_selected(self, choice: str):
        """Handle user selecting a model from the scanned folder library dropdown."""
        if choice in ("Model Library...", "Select Model from Folder...", "No Models in Folder", "No Models Found (Set Folder)", "Scanning Folder..."):
            return

        if choice in self.scanned_models_map:
            target_path = self.scanned_models_map[choice]
            if os.path.exists(target_path):
                self.model_entry.delete(0, "end")
                self.model_entry.insert(0, target_path)
                self._add_recent_model(target_path)
                self._auto_detect_vision_mmproj(target_path)
                self._flash_badge(f"● SELECTED: {os.path.basename(target_path)[:24]}")
                self._update_memory_estimation()

    def browse_model(self):
        f = filedialog.askopenfilename(filetypes=[("GGUF Files", "*.gguf")])
        if f:
            norm_path = os.path.normpath(f)
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, norm_path)
            self._add_recent_model(norm_path)
            self._auto_detect_vision_mmproj(norm_path)
            # If current models_dir is empty, automatically adopt parent directory of selected model
            if not self.models_dir:
                self.models_dir = os.path.dirname(norm_path)
                if hasattr(self, "models_dir_entry"):
                    self.models_dir_entry.delete(0, "end")
                    self.models_dir_entry.insert(0, self.models_dir)
                self._persist_app_config()
                self._trigger_models_scan()
            self._update_memory_estimation()

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
        if self.opt_vars.get("ctx_shift") and self.opt_vars["ctx_shift"].get():
            cmd.append("--ctx-shift")
        if self.opt_vars.get("defrag_thold") and self.opt_vars["defrag_thold"].get():
            val = self.opt_str_vars["defrag_thold"].get().strip() or "0.1"
            cmd.extend(["--defrag-thold", val])

        return cmd

    def _build_current_settings_dict(self) -> dict:
        """Serialize the current launcher GUI state to a JSON-compatible dictionary."""
        ctx_idx = int(round(self.ctx_slider.get()))
        batch_idx = int(round(self.batch_slider.get()))
        ubatch_idx = int(round(self.ubatch_slider.get()))

        return {
            "version": "1.4.0",
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

        # Context Shift: --ctx-shift
        if "--ctx-shift" in content:
            if "ctx_shift" in self.opt_vars:
                self.opt_vars["ctx_shift"].set(True)
                self._toggle_opt_widget("ctx_shift")
                found_any = True

        # Defrag Threshold: --defrag-thold <val>
        defrag_match = re.search(r'--defrag-thold\s+["\']?([\d\.-]+)["\']?|["\']--defrag-thold["\']\s*,\s*["\']([\d\.-]+)["\']', content)
        if defrag_match:
            if "defrag_thold" in self.opt_vars:
                val = defrag_match.group(1) or defrag_match.group(2)
                self.opt_vars["defrag_thold"].set(True)
                if val:
                    self.opt_str_vars["defrag_thold"].set(val)
                self._toggle_opt_widget("defrag_thold")
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
        self._start_metrics_poller()
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

        self._stop_metrics_poller()
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
                self._stop_metrics_poller()
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

    # =========================================================================
    # Phase 2: Live Inference Dashboard & Metrics Polling Engine
    # =========================================================================
    @staticmethod
    def parse_prometheus_metrics(raw_text: str) -> dict:
        """Parse Prometheus key-value telemetry text from llama-server /metrics endpoint."""
        data = {}
        for line in raw_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0]
                try:
                    val = float(parts[1])
                    data[key] = val
                except ValueError:
                    pass
        return data

    def _start_metrics_poller(self):
        """Spin up background daemon thread to query /metrics and /slots endpoints continuously."""
        self._stop_metrics_poller()
        self._metrics_stop_event.clear()
        self._last_metrics_sample = None

        port = self.port_entry.get().strip() if hasattr(self, "port_entry") else "8082"
        metrics_url = f"http://127.0.0.1:{port}/metrics"
        slots_url = f"http://127.0.0.1:{port}/slots"

        def poller():
            # Initial grace period while llama-server boots and binds HTTP port
            time.sleep(1.5)
            while not self._metrics_stop_event.is_set():
                metrics_data = None
                slots_data = None

                # 1. Fetch Prometheus /metrics
                try:
                    req = urllib.request.Request(metrics_url, headers={"User-Agent": "LLauncher-Telemetry"})
                    with urllib.request.urlopen(req, timeout=1.2) as resp:
                        if resp.status == 200:
                            content = resp.read().decode("utf-8", errors="replace")
                            metrics_data = self.parse_prometheus_metrics(content)
                except Exception:
                    pass

                # 2. Fetch JSON /slots
                try:
                    req_slots = urllib.request.Request(slots_url, headers={"User-Agent": "LLauncher-Telemetry"})
                    with urllib.request.urlopen(req_slots, timeout=1.2) as resp:
                        if resp.status == 200:
                            content = resp.read().decode("utf-8", errors="replace")
                            slots_data = json.loads(content)
                except Exception:
                    pass

                if self._metrics_stop_event.is_set():
                    break

                # 3. Compute telemetry metrics
                prompt_ts = None
                gen_ts = None
                total_tokens = None
                is_active = False

                if metrics_data:
                    # Preferred Prometheus gauge names from llama.cpp server
                    prompt_tokens = metrics_data.get("llamacpp:prompt_tokens_total") or metrics_data.get("prompt_tokens_total")
                    prompt_seconds = metrics_data.get("llamacpp:prompt_seconds_total") or metrics_data.get("prompt_seconds_total")
                    tokens_predicted = metrics_data.get("llamacpp:tokens_predicted_total") or metrics_data.get("tokens_predicted_total")
                    tokens_seconds = metrics_data.get("llamacpp:tokens_seconds_total") or metrics_data.get("tokens_seconds_total")

                    now = time.time()
                    if self._last_metrics_sample is not None and prompt_tokens is not None and tokens_predicted is not None:
                        last_t, last_p_toks, last_p_sec, last_g_toks, last_g_sec = self._last_metrics_sample
                        delta_p_toks = prompt_tokens - last_p_toks
                        delta_p_sec = (prompt_seconds - last_p_sec) if prompt_seconds is not None else (now - last_t)
                        delta_g_toks = tokens_predicted - last_g_toks
                        delta_g_sec = (tokens_seconds - last_g_sec) if tokens_seconds is not None else (now - last_t)

                        if delta_p_toks > 0 and delta_p_sec > 0.05:
                            prompt_ts = delta_p_toks / delta_p_sec
                        if delta_g_toks > 0 and delta_g_sec > 0.05:
                            gen_ts = delta_g_toks / delta_g_sec

                    # Fallback to cumulative average if instantaneous window is 0
                    if prompt_ts is None and prompt_tokens and prompt_seconds and prompt_seconds > 0:
                        prompt_ts = prompt_tokens / prompt_seconds
                    if gen_ts is None and tokens_predicted and tokens_seconds and tokens_seconds > 0:
                        gen_ts = tokens_predicted / tokens_seconds

                    if prompt_tokens is not None or tokens_predicted is not None:
                        total_tokens = int((prompt_tokens or 0) + (tokens_predicted or 0))

                    if prompt_tokens is not None and tokens_predicted is not None:
                        self._last_metrics_sample = (
                            now,
                            prompt_tokens,
                            prompt_seconds or 0.0,
                            tokens_predicted,
                            tokens_seconds or 0.0,
                        )

                # 4. Slot saturation & activity state
                slot_info = "Idle (0%)"
                if isinstance(slots_data, list) and len(slots_data) > 0:
                    total_slots = len(slots_data)
                    busy_slots = 0
                    total_ctx_used = 0
                    max_ctx_total = 0
                    for s in slots_data:
                        state = s.get("state", 0) # 0=idle, 1=processing
                        if state != 0:
                            busy_slots += 1
                            is_active = True
                        n_ctx = s.get("n_ctx", 0)
                        n_past = s.get("n_past", 0)
                        max_ctx_total += n_ctx
                        total_ctx_used += n_past

                    if max_ctx_total > 0:
                        sat_pct = int(round((total_ctx_used / max_ctx_total) * 100))
                    elif total_slots > 0:
                        sat_pct = int(round((busy_slots / total_slots) * 100))
                    else:
                        sat_pct = 0

                    if busy_slots > 0:
                        slot_info = f"Busy {busy_slots}/{total_slots} ({sat_pct}%)"
                    else:
                        slot_info = f"Idle ({sat_pct}%)"

                # 5. Dispatch telemetry UI update safely on main GUI thread
                self.after(
                    0,
                    self._update_telemetry_ui,
                    prompt_ts,
                    gen_ts,
                    total_tokens,
                    slot_info,
                    is_active,
                )

                time.sleep(1.2)

        self._metrics_thread = threading.Thread(target=poller, daemon=True)
        self._metrics_thread.start()

    def _stop_metrics_poller(self):
        """Halt background telemetry metrics polling thread and reset status bar."""
        self._metrics_stop_event.set()
        self._last_metrics_sample = None
        self._metrics_thread = None
        if hasattr(self, "telemetry_label"):
            self.telemetry_label.configure(
                text="⚪ SERVER OFFLINE  |  Prompt: -- t/s  |  Gen: -- t/s  |  Tokens: --  |  Slots: Idle (0%)",
                text_color="#ffffff",
            )

    def _update_telemetry_ui(self, prompt_ts, gen_ts, total_tokens, slot_info, is_active):
        """Update the live telemetry dashboard strip with colored metrics."""
        if not hasattr(self, "telemetry_label"):
            return

        if not self.is_server_running():
            self._stop_metrics_poller()
            return

        pts_str = f"{prompt_ts:.1f} t/s" if prompt_ts is not None else "-- t/s"
        gts_str = f"{gen_ts:.1f} t/s" if gen_ts is not None else "-- t/s"
        tok_str = f"{total_tokens:,}" if total_tokens is not None else "--"

        if is_active:
            status_dot = "⚡ GENERATING"
        else:
            status_dot = "🟢 ONLINE"

        display_text = f"{status_dot}  |  Prompt: {pts_str}  |  Gen: {gts_str}  |  Tokens: {tok_str}  |  Slots: {slot_info}"
        self.telemetry_label.configure(text=display_text, text_color="#ffffff")

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
                pystray.MenuItem("Secure Public Tunnel...", lambda: self.after(0, self.open_tunnel_dialog)),
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

    def open_tunnel_dialog(self):
        """Open or bring to front the Instant Secure Tunnel manager window."""
        if hasattr(self, "tunnel_dialog") and self.tunnel_dialog is not None and self.tunnel_dialog.winfo_exists():
            self.tunnel_dialog.lift()
            self.tunnel_dialog.focus_force()
        else:
            self.tunnel_dialog = TunnelDialog(self)

    def _on_main_tunnel_update(self, tm):
        """Callback to update main window toolbar button when tunnel status changes."""
        def apply_state():
            if not hasattr(self, "tunnel_btn"):
                return
            if tm.status == "running":
                self.tunnel_btn.configure(
                    text="🟢  Tunnel Active",
                    fg_color="#18181b",
                    hover_color="#27272a",
                    border_color="#4ade80",
                    text_color="#4ade80",
                )
                self._flash_badge("● SECURE TUNNEL ONLINE")
            elif tm.status == "starting":
                self.tunnel_btn.configure(
                    text="⏳  Tunnel Starting...",
                    fg_color="#18181b",
                    hover_color="#27272a",
                    border_color="#facc15",
                    text_color="#facc15",
                )
            else:
                self.tunnel_btn.configure(
                    text="🌐  Public Tunnel",
                    fg_color="#18181b",
                    hover_color="#27272a",
                    border_color="#3f3f46",
                    text_color="#e4e4e7",
                )
        self.after(0, apply_state)

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
        """Full exit routine stopping background server, tunnel, and destroying tray icon."""
        self.manual_stop = True
        if hasattr(self, "tunnel_manager") and self.tunnel_manager is not None:
            self.tunnel_manager.stop_tunnel()
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