import calendar
import json
import os
import sys
import tkinter
import tkinter.messagebox
from datetime import datetime, timedelta
from pathlib import Path

import customtkinter as ctk

try:
    from task_manager import task_manager
except ImportError:
    task_manager = None

try:
    from to_do_list.applet import TodoApplet
except ImportError:
    print("Todo applet not found. Skipping.")
    TodoApplet = None

try:
    from timer.applet import PomodoroApplet
except ImportError:
    print("Pomodoro applet not found. Skipping.")
    PomodoroApplet = None

try:
    from notepad.applet import NotepadApplet
except ImportError:
    print("Notepad applet not found. Skipping.")
    NotepadApplet = None

ctk.set_appearance_mode("Default")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Configure light and dark themes
        self.LIGHT_THEME = {
            "header_bg": "#2391F0",
            "sidebar_bg": "#F5F5F5",
            "main_bg": "#FAE5D5",
            "document_button_fg": "#0088FF",
            "pomodoro_button_fg": "#4CABFF",
            "todo_button_fg": "#8AC9FF",
            "calendar_bg": "#FFFFFF",
            "search_bar_bg": "#DFF0FF",
            "usage_card_bg": "#F3DEDE",
            "task_card_bg_1": "#B3E5FC",
            "task_card_bg_2": "#8BC9FF",
            "task_card_bg_3": "#42A7FF",
            "recent_files_fg": "#B3E5FC",
            "text_color": "black",
        }
        self.DARK_THEME = {
            "header_bg": "#210F37",
            "sidebar_bg": "#112233",
            "main_bg": "#493E60",
            "document_button_fg": "#470A70",
            "pomodoro_button_fg": "#5D3677",
            "todo_button_fg": "#665075",
            "calendar_bg": "#FFFFFF",
            "search_bar_bg": "#E7EBEA",
            "usage_card_bg": "#4F1C51",
            "task_card_bg_1": "#570190",
            "task_card_bg_2": "#621F8E",
            "task_card_bg_3": "#5F4571",
            "recent_files_fg": "#585293",
            "text_color": "white",
        }
        self.theme_colors = (
            self.LIGHT_THEME
            if ctk.get_appearance_mode() == "Light"
            else self.DARK_THEME
        )

        # Track current active applet
        self.current_applet = None
        self.current_view = "documents"
        
        # View caching for performance - store created view frames
        self.cached_views = {}
        self.cached_applets = {}

        # Usage tracking
        app_data_dir = self.get_app_data_path()
        self.usage_file = app_data_dir / "app_usage.json"
        self.start_time = datetime.now()
        self.total_usage_seconds = self.load_usage_data()
        self.usage_timer = None
        self.start_usage_tracking()

        # Calendar state
        self.cal_view_date = datetime.now()
        self.cal_year = self.cal_view_date.year
        self.cal_month = self.cal_view_date.month

        # configure window
        self.title("Sapient")
        self.geometry(f"{1400}x{800}")

        # Configure main grid
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Main content
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Content

        # Create header bar
        self.header_frame = ctk.CTkFrame(
            self, height=50, fg_color="#2196F3", corner_radius=0
        )
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="sew")
        self.header_frame.grid_propagate(False)

        # App title in header (clickable home button)
        self.header_title = ctk.CTkButton(
            self.header_frame,
            text="🏠  SAPIENT",
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="transparent",
            hover_color="#1976D2",
            text_color="white",
            corner_radius=8,
            cursor="hand2",
            command=self.show_documents_home,
        )
        self.header_title.pack(side="left", padx=30)

        # Add tooltip-like label hint
        self.home_hint = ctk.CTkLabel(
            self.header_frame,
            text="← Click to go Home",
            font=ctk.CTkFont(size=11),
            text_color="#B3E5FC",
        )
        self.home_hint.pack(side="left", padx=(0, 20))

        # Theme toggle button with clear styling
        current_mode = ctk.get_appearance_mode()
        toggle_text = "🌙 Dark" if current_mode == "Light" else "☀️ Light"
        toggle_fg = "#37474F" if current_mode == "Light" else "#FFD54F"
        toggle_text_color = "white" if current_mode == "Light" else "#212121"

        self.theme_toggle = ctk.CTkButton(
            self.header_frame,
            text=toggle_text,
            width=90,
            height=35,
            fg_color=toggle_fg,
            hover_color="#546E7A" if current_mode == "Light" else "#FFC107",
            text_color=toggle_text_color,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=17,
            command=self.toggle_theme,
        )
        self.theme_toggle.pack(side="right", padx=10, pady=8)
        
        # App usage card in header - same height as toggle button for alignment
        self.usage_card = ctk.CTkFrame(
            self.header_frame, fg_color="#F3DEDE", corner_radius=17, height=35
        )
        self.usage_card.pack(side="right", padx=10, pady=8)
        self.usage_card.pack_propagate(False)
        
        # Calculate current usage
        session_seconds = (datetime.now() - self.start_time).total_seconds()
        total_seconds = self.total_usage_seconds + session_seconds
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        self.usage_hours_label = ctk.CTkLabel(
            self.usage_card,
            text=f"Use time: {hours}h {minutes}m",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.theme_colors["text_color"],
        )
        self.usage_hours_label.pack(padx=15, pady=5)

        # Create left sidebar
        self.sidebar_frame = ctk.CTkFrame(
            self, width=220, corner_radius=0, fg_color="#F5F5F5"
        )
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        # Sidebar buttons
        button_config = {
            "width": 180,
            "height": 45,
            "corner_radius": 10,
            "font": ctk.CTkFont(size=14),
            "anchor": "w",
            "text_color": "black",
        }

        self.documents_button = ctk.CTkButton(
            self.sidebar_frame,
            text="📄  Document Manager",
            fg_color="#0088FF",
            command=self.open_notepad,
            **button_config,
        )
        self.documents_button.pack(padx=20, pady=(30, 10))

        self.pomodoro_button = ctk.CTkButton(
            self.sidebar_frame,
            text="🕐  Focus Timer",
            fg_color="#4CABFF",
            command=self.open_timer,
            **button_config,
        )
        self.pomodoro_button.pack(padx=20, pady=10)

        self.todo_button = ctk.CTkButton(
            self.sidebar_frame,
            text="📋  To do list",
            fg_color="#8AC9FF",
            command=self.open_to_do,
            **button_config,
        )
        self.todo_button.pack(padx=20, pady=10)

        # Settings button at bottom
        self.settings_button = ctk.CTkButton(
            self.sidebar_frame,
            text="⚙️",
            width=50,
            height=50,
            corner_radius=25,
            fg_color="transparent",
            hover_color="#E0E0E0",
            text_color="gray",
            font=ctk.CTkFont(size=20),
            command=self.open_settings,
        )
        self.settings_button.pack(side="bottom", pady=30)

        # Create main content area
        self.main_content_frame = ctk.CTkFrame(
            self, fg_color="#FAF3E0", corner_radius=0
        )
        self.main_content_frame.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)

        # Configure main content grid
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)

        # Show documents view by default
        self.show_documents_home()

        # Bind cleanup on close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.set_theme_colors(self.theme_colors)

    def load_usage_data(self):
        """Load total usage time from file, reset if it's a new day"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.usage_file.exists():
            try:
                with open(self.usage_file, "r") as f:
                    data = json.load(f)
                    saved_date = data.get("date", "")
                    # Reset if it's a new day
                    if saved_date != today:
                        return 0
                    return data.get("total_seconds", 0)
            except:
                return 0
        return 0

    def save_usage_data(self,current_total=None):
        """Save total usage time to file with current date"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            value_to_save = current_total if current_total is not None else self.total_usage_seconds
            
            with open(self.usage_file, "w") as f:
                json.dump({"total_seconds": int(value_to_save), "date": today}, f)
        except Exception as e:
            print(f"Error saving usage data: {e}")

    def start_usage_tracking(self):
        """Start tracking app usage time"""
        self.update_usage_time()

    def update_usage_time(self):
        """Update usage counter every second"""
        # Calculate session time
        session_seconds = (datetime.now() - self.start_time).total_seconds()
        real_time_total = self.total_usage_seconds + session_seconds

        # Convert to hours and minutes
        hours = int(real_time_total // 3600)
        minutes = int((real_time_total % 3600) // 60)

        # Update display if usage card exists
        if hasattr(self, "usage_hours_label"):
            self.usage_hours_label.configure(text=f"Use time: {hours}h {minutes}m")

        # Save every 60 seconds
        if int(session_seconds) % 60 == 0 and int(session_seconds) > 0:
            self.save_usage_data(current_total=real_time_total)

        # Schedule next update
        self.usage_timer = self.after(1000, self.update_usage_time)

    def on_closing(self):
        """Handle window closing - save usage data"""
        # Calculate final total
        session_seconds = (datetime.now() - self.start_time).total_seconds()
        final_total = self.total_usage_seconds + session_seconds
        
        # Save the final calculated sum
        self.save_usage_data(current_total=final_total)

        # Cancel timer
        if self.usage_timer:
            self.after_cancel(self.usage_timer)

        # Close window
        self.destroy()

    def open_settings(self):
        """Open settings in main content area"""
        self.current_view = "settings"
        self.clear_main_content()

        # Settings container
        settings_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Settings title
        title_label = ctk.CTkLabel(
            settings_frame,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.theme_colors["text_color"],
        )
        title_label.pack(pady=(20, 30))

        # Theme section
        theme_section = ctk.CTkFrame(
            settings_frame, fg_color=self.theme_colors["calendar_bg"], corner_radius=15
        )
        theme_section.pack(fill="x", pady=10)

        theme_label = ctk.CTkLabel(
            theme_section,
            text="Appearance",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="black",
        )
        theme_label.pack(anchor="w", padx=20, pady=(15, 10))

        theme_desc = ctk.CTkLabel(
            theme_section,
            text="Toggle between light and dark mode",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        theme_desc.pack(anchor="w", padx=20)

        theme_btn = ctk.CTkButton(
            theme_section,
            text="Toggle Theme ☀️🌙",
            command=self.toggle_theme,
            fg_color="#2196F3",
            hover_color="#1976D2",
            width=150,
        )
        theme_btn.pack(anchor="w", padx=20, pady=(10, 15))

        # About section
        about_section = ctk.CTkFrame(
            settings_frame, fg_color=self.theme_colors["calendar_bg"], corner_radius=15
        )
        about_section.pack(fill="x", pady=10)

        about_label = ctk.CTkLabel(
            about_section,
            text="About",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="black",
        )
        about_label.pack(anchor="w", padx=20, pady=(15, 10))

        version_label = ctk.CTkLabel(
            about_section,
            text="Sapient v1.0.0",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        version_label.pack(anchor="w", padx=20, pady=(0, 15))

    def clear_main_content(self):
        """Clear all widgets from main content frame"""
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()
        self.cached_views.clear()
        self.cached_applets.clear()
    
    def hide_all_views(self):
        """Hide all cached views and destroy any non-cached widgets"""
        # First hide all cached views
        cached_frames = set(self.cached_views.values())
        for frame in cached_frames:
            if frame and frame.winfo_exists():
                frame.pack_forget()
        
        # Destroy any widgets that are not in cache (like placeholders)
        for widget in self.main_content_frame.winfo_children():
            if widget not in cached_frames:
                widget.destroy()

    def show_documents_home(self):
        """Show the documents home screen with calendar and tasks"""
        self.current_view = "documents"
        self.hide_all_views()
        
        # Check if home view is cached
        if "home" in self.cached_views and self.cached_views["home"].winfo_exists():
            self.cached_views["home"].pack(fill="both", expand=True, padx=30, pady=20)
            return

        # Create container for content
        content_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Search bar at top
        search_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 20))

        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="search",
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=self.theme_colors["search_bar_bg"],
            border_width=1,
        )
        search_entry.pack(side="left", fill="x", expand=True)

        search_button = ctk.CTkButton(
            search_frame,
            text="🔍",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color="#E0E0E0",
        )
        search_button.pack(side="right", padx=(10, 0))

        # Main content area with calendar and tasks
        content_grid = ctk.CTkFrame(content_frame, fg_color="transparent")
        content_grid.pack(fill="both", expand=True)
        content_grid.grid_columnconfigure(0, weight=3)  # Calendar column narrower
        content_grid.grid_columnconfigure(1, weight=3)  # Right side wider
        content_grid.grid_rowconfigure(0, weight=1)

        # Left side - Calendar and Task card stacked
        left_panel = ctk.CTkFrame(content_grid, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_rowconfigure(0, weight=10)
        left_panel.grid_rowconfigure(1, weight=5)
        left_panel.grid_columnconfigure(0, weight=10)

        # Calendar (thinner)
        calendar_card = ctk.CTkFrame(
            left_panel, fg_color=self.theme_colors["calendar_bg"], corner_radius=15
        )
        calendar_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.create_calendar(calendar_card)

        # Task preview card under calendar
        task_card = ctk.CTkFrame(
            left_panel, fg_color=self.theme_colors["task_card_bg_1"], corner_radius=15
        )
        task_card.grid(row=1, column=0, sticky="nsew")

        # Get real upcoming tasks
        if task_manager:
            upcoming = task_manager.get_upcoming_tasks(limit=5)
            today_tasks = task_manager.get_today_tasks()
            overdue = task_manager.get_overdue_tasks()

            # Header with task count
            pending_count = len(task_manager.get_all_pending_tasks())
            header_text = f"📋 Upcoming Tasks ({pending_count})"

            task_header = ctk.CTkLabel(
                task_card,
                text=header_text,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=self.theme_colors["text_color"],
            )
            task_header.pack(anchor="w", padx=20, pady=(15, 5))

            # Show overdue warning if any
            if overdue:
                overdue_label = ctk.CTkLabel(
                    task_card,
                    text=f"🔴 {len(overdue)} overdue task(s)!",
                    font=ctk.CTkFont(size=11),
                    text_color="#F44336",
                )
                overdue_label.pack(anchor="w", padx=20, pady=(0, 5))

            # Show today's tasks first
            if today_tasks:
                today_label = ctk.CTkLabel(
                    task_card,
                    text="Today:",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.theme_colors["text_color"],
                )
                today_label.pack(anchor="w", padx=20, pady=(5, 2))

                for task in today_tasks[:3]:
                    if not task.get("done"):
                        task_label = ctk.CTkLabel(
                            task_card,
                            text=f"  • {task['text'][:30]}{'...' if len(task['text']) > 30 else ''}",
                            font=ctk.CTkFont(size=11),
                            anchor="w",
                            text_color=self.theme_colors["text_color"],
                        )
                        task_label.pack(anchor="w", padx=20, pady=1)

            # Show upcoming tasks
            future_tasks = [
                t
                for t in upcoming
                if t.get("deadline") != datetime.now().strftime("%Y-%m-%d")
            ]
            if future_tasks:
                upcoming_label = ctk.CTkLabel(
                    task_card,
                    text="Coming up:",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=self.theme_colors["text_color"],
                )
                upcoming_label.pack(anchor="w", padx=20, pady=(8, 2))

                for task in future_tasks[:3]:
                    deadline = task.get("deadline", "")
                    try:
                        dt = datetime.strptime(deadline, "%Y-%m-%d")
                        date_str = dt.strftime("%b %d")
                    except:
                        date_str = deadline

                    task_label = ctk.CTkLabel(
                        task_card,
                        text=f"  • [{date_str}] {task['text'][:25]}{'...' if len(task['text']) > 25 else ''}",
                        font=ctk.CTkFont(size=11),
                        anchor="w",
                        text_color=self.theme_colors["text_color"],
                    )
                    task_label.pack(anchor="w", padx=20, pady=1)

            if not upcoming and not today_tasks and not overdue:
                empty_label = ctk.CTkLabel(
                    task_card,
                    text="No upcoming tasks!\nAdd tasks in To-Do List.",
                    font=ctk.CTkFont(size=12),
                    text_color="gray",
                )
                empty_label.pack(pady=20)
        else:
            task_date = ctk.CTkLabel(
                task_card,
                text="Task Manager not available",
                font=ctk.CTkFont(size=14),
                text_color=self.theme_colors["text_color"],
            )
            task_date.pack(anchor="w", padx=20, pady=20)

        # Right side - Recent files
        right_panel = ctk.CTkFrame(
            content_grid,
            fg_color="transparent",
        )
        right_panel.grid(row=0, column=2, sticky="nsew", padx=(20, 0))
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=0)
        right_panel.grid_columnconfigure(0, weight=5)

        # Recent files card (main area)
        files_card = ctk.CTkFrame(right_panel, fg_color="transparent", corner_radius=15)
        files_card.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        files_title = ctk.CTkLabel(
            files_card,
            text="Recent files",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.theme_colors["recent_files_fg"],
            corner_radius=8,
            width=120,
            height=30,
        )
        files_title.pack(padx=100, pady=20)
        
        # Cache this view
        self.cached_views["home"] = content_frame

    def change_month(self, step):
        self.cal_month += step

        if self.cal_month > 12:
            self.cal_month = 1
            self.cal_year += 1
        elif self.cal_month < 1:
            self.cal_month = 12
            self.cal_year -= 1

        if hasattr(self, "calendar_container"):  # Refresh calendar display
            self.create_calendar(self.calendar_container)

    def create_calendar(self, parent):
        """Create a calendar widget"""
        # Clear previous calendar if exists
        self.calendar_container = parent
        for widget in parent.winfo_children():
            widget.destroy()

        # Calendar header
        cal_header = ctk.CTkFrame(parent, fg_color="transparent")
        cal_header.pack(fill="x", padx=20, pady=(20, 10))

        # State variables
        view_date = datetime(self.cal_year, self.cal_month, 1)
        month_label = ctk.CTkLabel(
            cal_header,
            text=f"{view_date.strftime('%B %Y')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="black",
        )
        month_label.pack(side="left")
        nav_frame = ctk.CTkFrame(cal_header, fg_color="transparent")
        nav_frame.pack(side="right")

        prev_btn = ctk.CTkButton(
            nav_frame,
            text="<",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#E0E0E0",
            text_color="gray",
            command=lambda: self.change_month(-1),
        )
        prev_btn.pack(side="left", padx=2)

        next_btn = ctk.CTkButton(
            nav_frame,
            text=">",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#E0E0E0",
            text_color="gray",
            command=lambda: self.change_month(1),
        )
        next_btn.pack(side="left", padx=2)

        # Calendar grid
        cal_grid = ctk.CTkFrame(parent, fg_color="transparent")
        cal_grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for i in range(7):
            cal_grid.grid_columnconfigure(i, weight=1)
        for i in range(1, 7):
            cal_grid.grid_rowconfigure(i, weight=1)

        # Day headers
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for i, day in enumerate(days):
            day_label = ctk.CTkLabel(
                cal_grid,
                text=day,
                font=ctk.CTkFont(size=10),
                text_color="gray",
                width=40,
            )
            day_label.grid(row=0, column=i, padx=2, pady=5)

        # Calendar days
        cal_obj = calendar.monthcalendar(self.cal_year, self.cal_month)
        real_now = datetime.now()

        # Get dates with tasks
        dates_with_tasks = set()
        if task_manager:
            dates_with_tasks = task_manager.get_dates_with_tasks()

        for week_num, week in enumerate(cal_obj):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue

                date_str = f"{self.cal_year}-{self.cal_month:02d}-{day:02d}"
                has_tasks = date_str in dates_with_tasks

                is_today = (
                    day == real_now.day
                    and self.cal_month == real_now.month
                    and self.cal_year == real_now.year
                )

                # Use theme colors for today/range highlight
                today_bg = (
                    "#2196F3"
                    if ctk.get_appearance_mode() == "Light"
                    else self.theme_colors["document_button_fg"]
                )
                range_bg = (
                    "#E3F2FD"
                    if ctk.get_appearance_mode() == "Light"
                    else self.theme_colors["task_card_bg_2"]
                )
                task_bg = "#FFF3E0"  # Light orange for days with tasks

                if is_today:
                    fg_color = today_bg
                    text_color = "white"
                elif has_tasks:
                    fg_color = task_bg
                    text_color = "#E65100"  # Dark orange
                else:
                    fg_color = "transparent"
                    text_color = "black"

                # Create button frame to hold day and indicator
                day_frame = ctk.CTkFrame(cal_grid, fg_color="transparent")
                day_frame.grid(
                    row=week_num + 1, column=day_num, padx=2, pady=2, sticky="nsew"
                )
                day_frame.grid_rowconfigure(0, weight=1)
                day_frame.grid_columnconfigure(0, weight=1)

                day_btn = ctk.CTkButton(
                    day_frame,
                    text=str(day),
                    fg_color=fg_color,
                    hover_color=range_bg,
                    text_color=text_color,
                    corner_radius=8,
                    font=ctk.CTkFont(size=12),
                    command=lambda d=date_str: self.show_day_tasks(d),
                )
                day_btn.grid(row=0, column=0, sticky="nsew")

                # Add task indicator dot
                if has_tasks and not is_today:
                    dot = ctk.CTkLabel(
                        day_frame,
                        text="•",
                        font=ctk.CTkFont(size=14),
                        text_color="#FF5722",
                    )
                    dot.place(relx=0.8, rely=0.1)

    def show_day_tasks(self, date_str):
        """Show tasks for a specific date in a popup"""
        if not task_manager:
            return

        tasks = task_manager.get_tasks_by_date(date_str)

        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title(f"Tasks for {date_str}")
        popup.geometry("350x400")
        popup.transient(self)

        # Center the popup
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 175
        y = self.winfo_y() + (self.winfo_height() // 2) - 200
        popup.geometry(f"+{x}+{y}")

        # Header
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            header_text = dt.strftime("%A, %B %d, %Y")
        except:
            header_text = date_str

        header = ctk.CTkLabel(
            popup, text=header_text, font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=(20, 10))

        # Tasks count
        pending = [t for t in tasks if not t.get("done")]
        done = [t for t in tasks if t.get("done")]

        count_label = ctk.CTkLabel(
            popup,
            text=f"📋 {len(pending)} pending | ✓ {len(done)} done",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        count_label.pack(pady=(0, 15))

        # Tasks list
        if tasks:
            tasks_frame = ctk.CTkScrollableFrame(popup, fg_color="transparent")
            tasks_frame.pack(fill="both", expand=True, padx=20, pady=10)

            for task in tasks:
                is_done = task.get("done", False)

                task_frame = ctk.CTkFrame(
                    tasks_frame,
                    fg_color="#E8F5E9" if is_done else "#FFFFFF",
                    corner_radius=8,
                )
                task_frame.pack(fill="x", pady=3)

                checkbox = "☑" if is_done else "☐"
                priority = task.get("priority", "normal")
                priority_icon = "🔥" if priority == "high" else ""

                task_label = ctk.CTkLabel(
                    task_frame,
                    text=f"{checkbox} {task['text']} {priority_icon}",
                    font=ctk.CTkFont(size=12),
                    text_color="gray" if is_done else "black",
                    anchor="w",
                )
                task_label.pack(fill="x", padx=10, pady=8)
        else:
            empty_label = ctk.CTkLabel(
                popup,
                text="No tasks for this date.\n\nGo to To-Do List to add tasks!",
                font=ctk.CTkFont(size=13),
                text_color="gray",
            )
            empty_label.pack(expand=True)

        # Close button
        close_btn = ctk.CTkButton(popup, text="Close", command=popup.destroy, width=100)
        close_btn.pack(pady=15)

    def set_theme_colors(self, colors):
        self.theme_colors = colors

        # Update Header Color
        self.header_frame.configure(fg_color=colors["header_bg"])
        self.sidebar_frame.configure(
            fg_color=colors["sidebar_bg"],
        )
        self.main_content_frame.configure(fg_color=colors["main_bg"])
        self.usage_card.configure(fg_color=colors["usage_card_bg"])
        self.usage_hours_label.configure(text_color=colors["text_color"])

        self.documents_button.configure(
            fg_color=colors["document_button_fg"], text_color=colors["text_color"]
        )
        self.pomodoro_button.configure(
            fg_color=colors["pomodoro_button_fg"], text_color=colors["text_color"]
        )
        self.todo_button.configure(
            fg_color=colors["todo_button_fg"], text_color=colors["text_color"]
        )

        # Update home hint color based on theme
        if hasattr(self, "home_hint"):
            hint_color = (
                "#B3E5FC" if ctk.get_appearance_mode() == "Light" else "#90CAF9"
            )
            self.home_hint.configure(text_color=hint_color)

        # Invalidate cache and rebuild current view on theme change
        # (colors need to be updated)
        for view_name, frame in list(self.cached_views.items()):
            if frame and frame.winfo_exists():
                frame.destroy()
        self.cached_views.clear()
        self.cached_applets.clear()
        
        # Rebuild current view with new colors
        if self.current_view == "todo":
            self.open_to_do()
        elif self.current_view == "documents":
            self.show_documents_home()

    def toggle_theme(self):
        """Toggle between light and dark mode"""
        current = ctk.get_appearance_mode()
        if current == "Light":
            ctk.set_appearance_mode("Dark")
            self.set_theme_colors(self.DARK_THEME)
            # Update toggle button for dark mode
            self.theme_toggle.configure(
                text="☀️ Light",
                fg_color="#FFD54F",
                hover_color="#FFC107",
                text_color="#212121",
            )
        else:
            ctk.set_appearance_mode("Light")
            self.set_theme_colors(self.LIGHT_THEME)
            # Update toggle button for light mode
            self.theme_toggle.configure(
                text="🌙 Dark",
                fg_color="#37474F",
                hover_color="#546E7A",
                text_color="white",
            )

    def open_notepad(self):
        """Load notepad applet into main content area with caching"""
        self.current_view = "notepad"
        self.hide_all_views()
        
        # Check if we have a cached view
        if "notepad" in self.cached_views and self.cached_views["notepad"].winfo_exists():
            self.cached_views["notepad"].pack(fill="both", expand=True)
            self.current_applet = self.cached_applets.get("notepad")
            return
        
        # Create new view
        container = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True)
        self.cached_views["notepad"] = container
        
        if NotepadApplet:
            self.current_applet = NotepadApplet(container)
            self.cached_applets["notepad"] = self.current_applet
        else:
            placeholder = ctk.CTkLabel(
                container,
                text="📄 Document Manager\n\nComing Soon...",
                font=ctk.CTkFont(size=24),
            )
            placeholder.pack(expand=True)

    def open_timer(self):
        """Load pomodoro applet into main content area with caching"""
        self.current_view = "pomodoro"
        self.hide_all_views()
        
        # Check if we have a cached view
        if "pomodoro" in self.cached_views and self.cached_views["pomodoro"].winfo_exists():
            self.cached_views["pomodoro"].pack(fill="both", expand=True)
            self.current_applet = self.cached_applets.get("pomodoro")
            return
        
        # Create new view
        container = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True)
        self.cached_views["pomodoro"] = container
        
        if PomodoroApplet:
            self.current_applet = PomodoroApplet(container)
            self.cached_applets["pomodoro"] = self.current_applet
        else:
            placeholder = ctk.CTkLabel(
                container,
                text="⏱️ Focus Timer\n\nComing Soon...",
                font=ctk.CTkFont(size=24),
            )
            placeholder.pack(expand=True)

    def open_to_do(self):
        """Load todo applet into main content area with caching"""
        self.current_view = "todo"
        self.hide_all_views()
        
        # Check if we have a cached view
        if "todo" in self.cached_views and self.cached_views["todo"].winfo_exists():
            self.cached_views["todo"].pack(fill="both", expand=True)
            self.current_applet = self.cached_applets.get("todo")
            return
        
        # Create new view
        container = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True)
        self.cached_views["todo"] = container
        
        if TodoApplet:
            self.current_applet = TodoApplet(container)
            self.cached_applets["todo"] = self.current_applet
        else:
            placeholder = ctk.CTkLabel(
                container,
                text="✓ To-Do List\n\nComing Soon...",
                font=ctk.CTkFont(size=24),
            )
            placeholder.pack(expand=True)

    def get_app_data_path(self):
        app_name = "sapient"

        if os.name == "nt":  # Windows
            data_dir = Path(os.getenv("LOCALAPPDATA")) / app_name
        elif os.name == "posix":  # macOS/Linux
            if sys.platform == "darwin":  # macOS
                data_dir = Path.home() / "Library" / "Application Support" / app_name
            else:  # Linux
                data_dir = (
                    Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
                    / app_name
                )
        else:  # Fallback
            data_dir = Path.home() / f".{app_name.lower()}"
        data_dir.mkdir(parents=True, exist_ok=True)

        return data_dir


if __name__ == "__main__":
    app = App()
    app.mainloop()
