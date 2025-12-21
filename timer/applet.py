import json
import os
from pathlib import Path
import customtkinter as ctk
import tkinter.messagebox
import random

class PomodoroApplet:
    def __init__(self, parent, on_tick_callback=None):
        self.parent = parent
        self.root = self.parent.winfo_toplevel()
        self.on_tick_callback = on_tick_callback
        
        # --- Theme Configuration ---
        self.THEME = {
            "timer_bg": random.choice(["#B83232", "#26C2A8", "#FFC7C7"]),
            "timer_card": random.choice(["#E29E85", "#997676", "#F7D2A8"]),
            "timer_text": "#8B2323",
            "settings_bg": "#3E3245",
            "settings_card": "#493E60",
            "settings_accent": "#D1C4E9",
            "settings_text": "white"
        }

        # Timer Logic
        self.timer_mode = "pomodoro" 
        self.is_running = False
        self.remaining_time = 25 * 60
        self.timer_id = None
        self.mini_window = None # <--- New: Track the mini window
        
        self.durations = {
            "pomodoro": 25 * 60,
            "short_break": 5 * 60,
            "long_break": 15 * 60
        }
        
        # Load settings
        self.load_config()
        self.remaining_time = self.durations[self.timer_mode]
        
        # Settings Logic
        self.current_view = "timer"
        self.temp_durations = {}
        self.settings_mode = "pomodoro"
        
        self.setup_ui()
        self._setup_hooks()

    def setup_ui(self):
        # 1. Main Background Frame (The Overlay)
        self.frame = ctk.CTkFrame(self.root, fg_color=self.THEME["timer_bg"], corner_radius=0)
        
        # 2. Navigation Pill
        self.header_container = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.header_container.pack(anchor="nw", padx=30, pady=30)

        self.nav_pill = ctk.CTkFrame(self.header_container, fg_color="#E0E0E0", corner_radius=20, height=40)
        self.nav_pill.pack(side="left")

        # Back Button
        self.back_btn = ctk.CTkButton(
            self.nav_pill, text="◄", width=50, height=35,
            fg_color="transparent", text_color="black", hover_color="#D0D0D0",
            corner_radius=20, font=ctk.CTkFont(size=18),
            command=self.handle_back_click
        )
        self.back_btn.pack(side="left", padx=(2, 0), pady=2)

        ctk.CTkFrame(self.nav_pill, width=1, height=20, fg_color="gray").pack(side="left", pady=5)

        # Settings Button
        self.settings_btn = ctk.CTkButton(
            self.nav_pill, text="⚙", width=50, height=35,
            fg_color="transparent", text_color="black", hover_color="#D0D0D0",
            corner_radius=20, font=ctk.CTkFont(size=18),
            command=self.show_settings_view
        )
        self.settings_btn.pack(side="left", padx=(0, 2), pady=2)

        # 3. Center Card
        self.center_card = ctk.CTkFrame(
            self.frame, 
            fg_color=self.THEME["timer_card"], 
            corner_radius=30, 
            width=600, height=400
        )
        self.center_card.place(relx=0.5, rely=0.5, anchor="center")
        self.center_card.pack_propagate(False)

        self.show_timer_view()

    # =========================================================
    #                    LIFECYCLE HOOKS
    # =========================================================
    def _setup_hooks(self):
        # Bind to the PARENT container (the one inside main.py)
        self.parent.bind("<Map>", self.on_show)
        self.parent.bind("<Unmap>", self.on_hide)
        
        # *** BUG FIX: ***
        # If the parent is ALREADY visible (Race condition), show immediately!
        if self.parent.winfo_ismapped():
            self.on_show(None)

    def on_show(self, event):
        # 1. Show the full screen applet overlay
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # 2. If a Mini Window exists, destroy it because we are back!
        if self.mini_window:
            self.mini_window.destroy()
            self.mini_window = None

    def on_hide(self, event):
        # 1. Hide the full screen overlay
        self.frame.place_forget()
        
        # 2. If the timer is running, detach to Mini Window
        if self.is_running and self.remaining_time > 0 and self.mini_window is None:
            self.open_mini_window()

    def open_mini_window(self):
        """Creates the small floating window"""
        self.mini_window = ctk.CTkToplevel()
        self.mini_window.title("Timer")
        self.mini_window.geometry("250x120")
        self.mini_window.attributes("-topmost", True) # Keep on top
        
        # Apply the current theme color
        bg_color = self.THEME["timer_bg"]
        self.mini_window.configure(fg_color=bg_color)
        
        # Add Time Label
        self.mini_label = ctk.CTkLabel(
            self.mini_window, 
            text=self.format_time(self.remaining_time),
            font=("Arial", 40, "bold"),
            text_color="white"
        )
        self.mini_label.pack(expand=True)
        
        # Add Stop Button
        ctk.CTkButton(
            self.mini_window, text="STOP", width=80, height=30,
            fg_color="white", text_color="red", hover_color="#EEE",
            command=self.stop_timer
        ).pack(pady=10)

        # Handle X button
        self.mini_window.protocol("WM_DELETE_WINDOW", self.stop_timer)

    # =========================================================
    #                     VIEW LOGIC
    # =========================================================

    def handle_back_click(self):
        if self.current_view == "settings":
            self.show_timer_view()
        else:
            self.go_to_home()

    def go_to_home(self):
        if hasattr(self.root, "show_documents_home"): 
            self.root.show_documents_home()
        else: 
            self.frame.place_forget()

    def show_timer_view(self):
        self.current_view = "timer"
        self.frame.configure(fg_color=self.THEME["timer_bg"])
        self.center_card.configure(fg_color=self.THEME["timer_card"])
        
        for widget in self.center_card.winfo_children():
            widget.destroy()

        # Mode Tabs
        self.mode_frame = ctk.CTkFrame(self.center_card, fg_color="transparent")
        self.mode_frame.pack(pady=(40, 20))

        self.btn_pomodoro = self.create_mode_button("Pomodoro", "pomodoro")
        self.btn_short = self.create_mode_button("Short Break", "short_break")
        self.btn_long = self.create_mode_button("Long Break", "long_break")
        self.update_mode_buttons()

        # Timer Numbers
        self.timer_label = ctk.CTkLabel(
            self.center_card,
            text=self.format_time(self.remaining_time),
            font=ctk.CTkFont(family="Calibri", size=100, weight="bold"),
            text_color="white"
        )
        self.timer_label.pack(pady=10)

        # Start Button
        self.start_btn = ctk.CTkButton(
            self.center_card,
            text="STOP" if self.is_running else "START",
            font=ctk.CTkFont(family="Calibri", size=24, weight="bold"),
            fg_color="white", text_color=self.THEME["timer_text"],
            hover_color="#F0F0F0", width=220, height=65, corner_radius=32,
            command=self.toggle_timer
        )
        self.start_btn.pack(pady=30)

    def show_settings_view(self):
        self.current_view = "settings"
        self.frame.configure(fg_color=self.THEME["settings_bg"])
        self.center_card.configure(fg_color=self.THEME["settings_card"])
        
        for widget in self.center_card.winfo_children():
            widget.destroy()

        self.temp_durations = self.durations.copy()
        self.settings_mode = "pomodoro"

        # Settings Header
        header_bg = ctk.CTkFrame(self.center_card, fg_color="#6A5B85", corner_radius=10, height=40)
        header_bg.pack(pady=(30, 15), padx=100, fill="x")
        ctk.CTkLabel(header_bg, text="SET UP", font=ctk.CTkFont(size=18, weight="bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        # Settings Tabs
        tab_frame = ctk.CTkFrame(self.center_card, fg_color="transparent")
        tab_frame.pack(pady=10)
        self.set_btn_pomo = self.create_settings_tab(tab_frame, "Timer", "pomodoro")
        self.set_btn_short = self.create_settings_tab(tab_frame, "Short", "short_break")
        self.set_btn_long = self.create_settings_tab(tab_frame, "Long", "long_break")
        self.set_btn_pomo.pack(side="left", padx=5)
        self.set_btn_short.pack(side="left", padx=5)
        self.set_btn_long.pack(side="left", padx=5)

        # Input
        input_container = ctk.CTkFrame(self.center_card, fg_color="white", corner_radius=20, height=60, width=300)
        input_container.pack(pady=20)
        input_container.pack_propagate(False)
        ctk.CTkLabel(input_container, text="🕒", font=ctk.CTkFont(size=24), text_color="black").pack(side="left", padx=(20, 10))
        self.time_entry = ctk.CTkEntry(input_container, font=ctk.CTkFont(size=30, weight="bold"), text_color="black", fg_color="transparent", border_width=0, justify="center")
        self.time_entry.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Footer
        footer = ctk.CTkFrame(self.center_card, fg_color="transparent")
        footer.pack(side="bottom", pady=30, padx=30, anchor="e")
        ctk.CTkButton(footer, text="Save", width=80, fg_color="#C0C0C0", hover_color="#A0A0A0", text_color="black", command=self.save_settings).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="Cancel", width=80, fg_color="#808080", hover_color="#606060", text_color="white", command=self.show_timer_view).pack(side="left", padx=5)
        self.select_settings_tab("pomodoro")

    # =========================================================
    #                     CORE LOGIC
    # =========================================================

    def tick(self):
        # 1. Stop if needed
        if not self.is_running or self.remaining_time <= 0:
            if self.is_running: self.stop_timer()
            return

        # 2. Decrement
        self.remaining_time -= 1

        # 3. Update MAIN View (Only if visible)
        if self.current_view == "timer" and hasattr(self, 'timer_label'):
            try: self.timer_label.configure(text=self.format_time(self.remaining_time))
            except: pass

        # 4. Update MINI Window (Only if active)
        if self.mini_window and hasattr(self, 'mini_label'):
            try: self.mini_label.configure(text=self.format_time(self.remaining_time))
            except: pass

        # 5. Update Taskbar Widget (Callback)
        if self.on_tick_callback:
            self.on_tick_callback(self.format_time(self.remaining_time), True)

        # 6. Loop
        self.timer_id = self.parent.after(1000, self.tick)

    def start_timer(self):
        self.is_running = True
        self.start_btn.configure(text="STOP")
        if self.on_tick_callback:
            self.on_tick_callback(self.format_time(self.remaining_time), True)
        self.tick()

    def stop_timer(self):
        self.is_running = False
        
        # Reset Button (Safely)
        try: 
            if hasattr(self, 'start_btn'): self.start_btn.configure(text="START")
        except: pass

        # Cancel Loop
        if self.timer_id:
            try: self.parent.after_cancel(self.timer_id)
            except: pass
            self.timer_id = None
            
        # Update Taskbar Widget
        if self.on_tick_callback:
            self.on_tick_callback(self.format_time(self.remaining_time), False)
            
        # Close Mini Window
        if self.mini_window:
            self.mini_window.destroy()
            self.mini_window = None

    def toggle_timer(self):
        if self.is_running: self.stop_timer()
        else: self.start_timer()

    # --- Helpers ---
    def create_mode_button(self, text, mode_key):
        return ctk.CTkButton(self.mode_frame, text=text, font=ctk.CTkFont(size=15), fg_color="transparent", text_color="#333333", hover_color=self.THEME["timer_text"], corner_radius=20, width=100, height=35, command=lambda: self.set_mode(mode_key))
    
    def set_mode(self, mode):
        if self.is_running: self.stop_timer()
        self.timer_mode = mode
        self.remaining_time = self.durations[mode]
        self.timer_label.configure(text=self.format_time(self.remaining_time))
        self.update_mode_buttons()

    def update_mode_buttons(self):
        for btn in [self.btn_pomodoro, self.btn_short, self.btn_long]:
            btn.pack(side="left", padx=10)
            btn.configure(fg_color="transparent", text_color="#5A3A3A")
        
        active_btn = None
        if self.timer_mode == "pomodoro": active_btn = self.btn_pomodoro
        elif self.timer_mode == "short_break": active_btn = self.btn_short
        elif self.timer_mode == "long_break": active_btn = self.btn_long
        
        if active_btn: active_btn.configure(fg_color=self.THEME["timer_text"], text_color="white")

    def create_settings_tab(self, parent, text, mode):
        return ctk.CTkButton(parent, text=text, width=80, height=30, fg_color="transparent", text_color="white", font=ctk.CTkFont(size=12, weight="bold"), command=lambda: self.select_settings_tab(mode))

    def select_settings_tab(self, mode):
        try:
            val = int(self.time_entry.get())
            self.temp_durations[self.settings_mode] = val * 60
        except ValueError: pass

        self.settings_mode = mode
        active_col = self.THEME["settings_accent"]
        self.set_btn_pomo.configure(fg_color=active_col if mode=="pomodoro" else "transparent", text_color="black" if mode=="pomodoro" else "white")
        self.set_btn_short.configure(fg_color=active_col if mode=="short_break" else "transparent", text_color="black" if mode=="short_break" else "white")
        self.set_btn_long.configure(fg_color=active_col if mode=="long_break" else "transparent", text_color="black" if mode=="long_break" else "white")

        mins = self.temp_durations[mode] // 60
        self.time_entry.delete(0, "end")
        self.time_entry.insert(0, str(mins))

    def save_settings(self):
        try:
            val = int(self.time_entry.get())
            self.temp_durations[self.settings_mode] = val * 60
        except ValueError:
            tkinter.messagebox.showerror("Error", "Please enter a valid number.")
            return

        for key, seconds in self.temp_durations.items():
            if seconds <= 0:
                tkinter.messagebox.showwarning("Invalid Time", f"{key} cannot be 0 minute")
                return 

        if self.temp_durations.get("short_break", 0) > self.temp_durations.get("long_break", 0):
             tkinter.messagebox.showwarning("Invalid Time", "Short break cannot be longer than long break")
             return

        self.durations = self.temp_durations
        self.remaining_time = self.durations[self.timer_mode]
        self.save_config()
        self.stop_timer()
        self.show_timer_view()

    @staticmethod
    def format_time(seconds):
        return f"{seconds//60:02d}:{seconds%60:02d}"

    def get_config_file(self):
        app_name = "sapient"
        if os.name == "nt": data_dir = Path(os.getenv("LOCALAPPDATA")) / app_name
        else: data_dir = Path.home() / f".{app_name}"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "timer_config.json"

    def load_config(self):
        config_file = self.get_config_file()
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    self.durations.update(json.load(f))
            except: pass

    def save_config(self):
        try:
            with open(self.get_config_file(), "w") as f:
                json.dump(self.durations, f)
        except: pass