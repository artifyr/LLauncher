import os
import sys
import re
import json
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog

try:
    import pywinstyles
    HAS_PYWINSTYLES = True
except ImportError:
    HAS_PYWINSTYLES = False


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# Appearance & Theme Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Design Tokens (Aero Glass & Deep Space Obsidian with Dark Red Accents)
THEME = {
    "bg": "#060203",
    "card_bg": "transparent",
    "card_border": "#280d12",
    "dropdown_bg": "#140608",
    "input_bg": "#0a0304",
    "input_border": "#220b0f",
    "input_focus": "#990000",
    "modal_bg": "#100507",
    "text_primary": "#cbd5e1",
    "text_secondary": "#64748b",
    "text_muted": "#475569",
    "accent_blue": "#8b0000",      # Pure dark red
    "accent_red": "#8b0000",       # Pure dark red
    "accent_maroon": "#8b0000",    # Alias
    "accent_hover": "#5c0000",     # Deep dark red hover
    "accent_glow": "#990000",      # Pure dark red highlight
    "cyan_badge": "#dc2626",       # Pure dark red badges & headers (zero pink)
    "secondary_btn_bg": "#120608",
    "secondary_btn_hover": "#1e0a0d",
    "secondary_btn_border": "#2e0f14",
    "badge_bg": "#150507",
    "badge_border": "#360a0f",
}

# Pre-defined step ladders
CTX_STEPS = [2048, 4096, 8192, 16384, 24576, 32768, 49152, 65536, 98304, 131072]
BATCH_STEPS = [128, 256, 512, 1024, 2048, 4096]
UBATCH_STEPS = [128, 256, 512, 1024, 2048]
KV_CACHE_TYPES = ["q8_0", "q4_0", "q4_1", "f16"]

# Path to persistent profiles configuration
PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")

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
        },
    },
]


class RenameProfileDialog(ctk.CTkInputDialog):
    """Custom themed rename dialog matching the Obsidian & Dark Red Aero aesthetic."""

    def __init__(self, curr_name: str, master=None):
        self._initial_name = curr_name
        self._parent = master
        super().__init__(
            title="Rename Profile",
            text=f"Enter custom name for '{curr_name}':",
            fg_color=THEME["modal_bg"],
            text_color=THEME["text_primary"],
            button_fg_color=THEME["accent_red"],
            button_hover_color=THEME["accent_hover"],
            button_text_color="#ffffff",
            entry_fg_color=THEME["input_bg"],
            entry_border_color=THEME["input_border"],
            entry_text_color=THEME["text_primary"],
        )

        # Set taskbar & window icon
        ico_file = resource_path(os.path.join("assets", "llauncher.ico"))
        if not os.path.exists(ico_file):
            ico_file = resource_path("llauncher.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        # Apply dark/aero styling if pywinstyles is available
        if HAS_PYWINSTYLES:
            try:
                pywinstyles.apply_style(self, style="aero")
            except Exception:
                pass

        # Center on parent window if available
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
                fg_color=THEME["accent_red"],
                hover_color=THEME["accent_hover"],
                text_color="#ffffff",
                corner_radius=6,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            )

        if hasattr(self, "_cancel_button"):
            self._cancel_button.configure(
                fg_color=THEME["secondary_btn_bg"],
                hover_color=THEME["secondary_btn_hover"],
                border_width=1,
                border_color=THEME["secondary_btn_border"],
                text_color=THEME["text_primary"],
                corner_radius=6,
                font=ctk.CTkFont(family="Segoe UI", size=12),
            )


class LlamaLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # Off-screen construction eliminates launch stutter and flicker
        self.title("LLauncher - llama.cpp Server Launcher")
        self.geometry("1184x565")
        self.minsize(1120, 530)
        self.resizable(True, True)
        self.configure(fg_color="black")

        # Window Icon
        ico_file = resource_path(os.path.join("assets", "llauncher.ico"))
        if not os.path.exists(ico_file):
            ico_file = resource_path("llauncher.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        # Default paths
        self.llama_exe = r"E:\LLAMACPP\llama.cpp\build\bin\Release\llama-server.exe"

        # Typography (Scaled up for maximum clarity & legibility)
        self.font_title = ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Segoe UI", size=12)
        self.font_section = ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        self.font_label = ctk.CTkFont(family="Segoe UI", size=12)
        self.font_badge = ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        self.font_btn = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        self.font_sm = ctk.CTkFont(family="Segoe UI", size=11)

        # Device mapping {display_label: device_arg}
        self.device_map = {
            "Vulkan0: AMD Radeon RX 9070 XT": "Vulkan0",
            "Vulkan1: AMD Radeon(TM) Graphics": "Vulkan1",
            "none: CPU Only": "none",
        }

        # Profile state
        self.profiles = []
        self.active_profile_idx = 0
        self._load_profiles()

        # Performance-optimized flat container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=16, pady=10)

        # 1. Header with Profile Selector & Status Badge
        self._build_header()

        # 2. Binary & Model Paths (Full-width row)
        self._build_paths_card()

        # 3. Horizontal 3-Column Grid (Direct grid without redundant intermediate wrappers)
        cols_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        cols_container.pack(fill="both", expand=True, pady=(0, 8))
        cols_container.columnconfigure(0, weight=1)
        cols_container.columnconfigure(1, weight=1)
        cols_container.columnconfigure(2, weight=1)
        cols_container.rowconfigure(0, weight=1)

        # Col 1: Hardware & Compute
        self._build_hardware_column(cols_container)

        # Col 2: Batching, Sampling & Toggles
        self._build_batch_sampling_column(cols_container)

        # Col 3: Optional 9070 XT & 32GB RAM Optimizations
        self._build_optimizations_column(cols_container)

        # 4. Launch Action Button (Full width bottom)
        self._build_launch_action()

        # Apply initial active profile
        self._apply_profile(self.profiles[self.active_profile_idx])

        # Apply Windows Aero glass styling via pywinstyles & reveal window
        if HAS_PYWINSTYLES:
            try:
                pywinstyles.apply_style(self, style="aero")
            except Exception:
                self.configure(fg_color=THEME["bg"])

        self.deiconify()

        # Detect devices asynchronously in background without freezing UI
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
            text_color=THEME["cyan_badge"],
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
            fg_color=THEME["secondary_btn_bg"],
            selected_color=THEME["accent_maroon"],
            selected_hover_color=THEME["accent_hover"],
            unselected_color=THEME["secondary_btn_bg"],
            unselected_hover_color=THEME["secondary_btn_hover"],
            text_color=THEME["text_primary"],
            border_width=1,
            corner_radius=6,
            command=self._on_profile_selected,
            height=28,
        )
        self.profile_seg.set(self.profiles[self.active_profile_idx]["name"])
        self.profile_seg.pack(side="left", padx=(0, 6))

        self.save_prof_btn = ctk.CTkButton(
            prof_box,
            text="💾 Save",
            width=62,
            height=28,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["text_primary"],
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
            text_color=THEME["text_primary"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._rename_current_profile,
        )
        self.rename_prof_btn.pack(side="left")

    def _flash_badge(self, text, is_alert=False):
        """Temporarily show confirmation feedback on the engine status pill."""
        color = THEME["accent_glow"] if not is_alert else "#f87171"
        self.badge_label.configure(text=text, text_color=color)
        self.after(2200, lambda: self.badge_label.configure(text="● ENGINE READY", text_color=THEME["cyan_badge"]))

    def _on_profile_selected(self, selected_name):
        """Switch active profile without altering chosen model path."""
        for idx, p in enumerate(self.profiles):
            if p["name"] == selected_name:
                self.active_profile_idx = idx
                self._apply_profile(p)
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
            text_color=THEME["text_primary"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.browse_exe,
        )
        self.browse_exe_btn.grid(row=0, column=2, sticky="e", padx=(0, 12), pady=(8, 4))

        # Row 1: Model GGUF
        ctk.CTkLabel(
            card,
            text="Model GGUF",
            font=self.font_label,
            text_color=THEME["text_secondary"],
            width=115,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(12, 4), pady=(0, 8))

        self.model_entry = ctk.CTkEntry(
            card,
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
        self.model_entry.grid(row=1, column=1, sticky="ew", padx=(4, 8), pady=(0, 8))

        self.browse_btn = ctk.CTkButton(
            card,
            text="Browse",
            width=85,
            height=30,
            fg_color=THEME["secondary_btn_bg"],
            hover_color=THEME["secondary_btn_hover"],
            border_width=1,
            border_color=THEME["secondary_btn_border"],
            text_color=THEME["text_primary"],
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.browse_model,
        )
        self.browse_btn.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=(0, 8))

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
        """Column 1: Hardware & Compute Parameters (Optimized single-pass grid)"""
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

        # Title
        ctk.CTkLabel(
            card,
            text="HARDWARE & ACCELERATION",
            font=self.font_section,
            text_color=THEME["cyan_badge"],
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 6))

        # Device
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
            button_color=THEME["secondary_btn_bg"],
            button_hover_color=THEME["secondary_btn_hover"],
            text_color=THEME["text_primary"],
            dropdown_fg_color=THEME["dropdown_bg"],
            dropdown_text_color=THEME["text_primary"],
            dropdown_hover_color=THEME["secondary_btn_hover"],
            corner_radius=6,
            height=28,
            font=self.font_sm,
        )
        self.device_dropdown.set(self._get_default_device_display())
        self.device_dropdown.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=(0, 6))

        # GPU Layers (-ngl) Slider
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
            button_color=THEME["accent_blue"],
            button_hover_color=THEME["accent_glow"],
            progress_color=THEME["accent_blue"],
            fg_color=THEME["input_bg"],
            height=16,
            command=self._on_ngl_change,
        )
        self.ngl_slider.set(99)
        self.ngl_slider.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=(0, 6))

        self.ngl_badge = ctk.CTkLabel(
            card,
            text="99 (All)",
            font=self.font_badge,
            text_color=THEME["cyan_badge"],
            width=55,
            anchor="e",
        )
        self.ngl_badge.grid(row=2, column=2, sticky="e", padx=(0, 12), pady=(0, 6))

        # Context Length (-c) Slider
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
            button_color=THEME["accent_blue"],
            button_hover_color=THEME["accent_glow"],
            progress_color=THEME["accent_blue"],
            fg_color=THEME["input_bg"],
            height=16,
            command=self._on_ctx_change,
        )
        self.ctx_slider.set(len(CTX_STEPS) - 1)
        self.ctx_slider.grid(row=3, column=1, sticky="ew", padx=(0, 6), pady=(0, 8))

        self.ctx_badge = ctk.CTkLabel(
            card,
            text="131K",
            font=self.font_badge,
            text_color=THEME["cyan_badge"],
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
            text_color=THEME["text_primary"],
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
        """Column 2: Batching, KV Types, Sampling & Core Toggles (Flattened grid)"""
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

        # Title
        ctk.CTkLabel(
            card,
            text="BATCHING & GENERATION",
            font=self.font_section,
            text_color=THEME["cyan_badge"],
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 6))

        # Batch Size Slider
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
            button_color=THEME["accent_blue"],
            button_hover_color=THEME["accent_glow"],
            progress_color=THEME["accent_blue"],
            fg_color=THEME["input_bg"],
            height=16,
            command=self._on_batch_change,
        )
        self.batch_slider.set(BATCH_STEPS.index(1024))
        self.batch_slider.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=(0, 5))

        self.batch_badge = ctk.CTkLabel(
            card,
            text="1024",
            font=self.font_badge,
            text_color=THEME["cyan_badge"],
            width=48,
            anchor="e",
        )
        self.batch_badge.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=(0, 5))

        # Micro Batch Slider
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
            button_color=THEME["accent_blue"],
            button_hover_color=THEME["accent_glow"],
            progress_color=THEME["accent_blue"],
            fg_color=THEME["input_bg"],
            height=16,
            command=self._on_ubatch_change,
        )
        self.ubatch_slider.set(UBATCH_STEPS.index(256))
        self.ubatch_slider.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=(0, 6))

        self.ubatch_badge = ctk.CTkLabel(
            card,
            text="256",
            font=self.font_badge,
            text_color=THEME["cyan_badge"],
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
            button_color=THEME["secondary_btn_bg"],
            button_hover_color=THEME["secondary_btn_hover"],
            text_color=THEME["text_primary"],
            dropdown_fg_color=THEME["dropdown_bg"],
            dropdown_text_color=THEME["text_primary"],
            dropdown_hover_color=THEME["secondary_btn_hover"],
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
            button_color=THEME["secondary_btn_bg"],
            button_hover_color=THEME["secondary_btn_hover"],
            text_color=THEME["text_primary"],
            dropdown_fg_color=THEME["dropdown_bg"],
            dropdown_text_color=THEME["text_primary"],
            dropdown_hover_color=THEME["secondary_btn_hover"],
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
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_hover"],
            border_color=THEME["secondary_btn_border"],
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
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_hover"],
            border_color=THEME["secondary_btn_border"],
            border_width=2,
            corner_radius=4,
            height=22,
        ).pack(side="left")

    def _on_batch_change(self, val):
        self.batch_badge.configure(text=str(BATCH_STEPS[int(round(val))]))

    def _on_ubatch_change(self, val):
        self.ubatch_badge.configure(text=str(UBATCH_STEPS[int(round(val))]))

    def _build_optimizations_column(self, parent):
        """Column 3: RX 9070 XT & 32GB RAM Optional Optimizations (Flattened grid)"""
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

        # Header Title and Hint
        ctk.CTkLabel(
            card,
            text="9070 XT & 32GB PROFILE",
            font=self.font_section,
            text_color=THEME["cyan_badge"],
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
                fg_color=THEME["accent_blue"],
                hover_color=THEME["accent_hover"],
                border_color=THEME["secondary_btn_border"],
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
                    button_color=THEME["secondary_btn_bg"],
                    button_hover_color=THEME["secondary_btn_hover"],
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
        self.start_btn = ctk.CTkButton(
            self.main_container,
            text="🚀  Start Model Server",
            height=42,
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_hover"],
            border_width=1,
            border_color=THEME["accent_glow"],
            font=self.font_btn,
            text_color=THEME["text_primary"],
            corner_radius=8,
            command=self.launch,
        )
        self.start_btn.pack(fill="x", padx=2, pady=(2, 0))

    def browse_exe(self):
        f = filedialog.askopenfilename(
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")],
            title="Select llama-server.exe"
        )
        if f:
            self.exe_entry.delete(0, "end")
            self.exe_entry.insert(0, f)
            self._refresh_devices()

    def browse_model(self):
        f = filedialog.askopenfilename(filetypes=[("GGUF Files", "*.gguf")])
        if f:
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, f)

    def launch(self):
        exe = self.exe_entry.get().strip()
        model = self.model_entry.get().strip()
        if not model:
            return

        # Resolve selected device argument (e.g. "Vulkan0")
        selected_device_display = self.device_dropdown.get()
        device_id = self.device_map.get(selected_device_display, "Vulkan0")

        # Resolve sliders
        gpu_layers = str(int(round(self.ngl_slider.get())))
        ctx_tokens = str(CTX_STEPS[int(round(self.ctx_slider.get()))])
        batch_size = str(BATCH_STEPS[int(round(self.batch_slider.get()))])
        micro_batch = str(UBATCH_STEPS[int(round(self.ubatch_slider.get()))])

        cmd = [
            exe,
            "-m", model,
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
        ]

        if self.fa_var.get():
            cmd.extend(["-fa", "on"])
        if self.jinja_var.get():
            cmd.append("--jinja")

        # Apply checked optional optimizations
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

        # Launch in a new cmd window with Vulkan memory fix
        env_cmd = "set GGML_VK_DISABLE_PINNED=1 && " + subprocess.list2cmdline(cmd)
        subprocess.Popen(f'start cmd /k "{env_cmd}"', shell=True)


if __name__ == "__main__":
    app = LlamaLauncher()
    app.mainloop()