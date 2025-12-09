import tkinter
import tkinter.messagebox
import customtkinter as ctk
from datetime import datetime
import calendar
import json
import os
from pathlib import Path

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
            "text_color": "black"
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
            "text_color": "white"
        }
        self.theme_colors = self.LIGHT_THEME if ctk.get_appearance_mode() == "Light" else self.DARK_THEME

        # Track current active applet
        self.current_applet = None
        self.current_view = "documents"
        
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
        self.grid_rowconfigure(0, weight=0)     # Header
        self.grid_rowconfigure(1, weight=1)     # Content

        # Create header bar
        self.header_frame = ctk.CTkFrame(self, height=50, fg_color="#2196F3", corner_radius=0)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="sew")
        self.header_frame.grid_propagate(False)

        # App title in header
        self.header_title = ctk.CTkButton(
            self.header_frame,
            text="SAPIENT",
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color="transparent",
            hover_color=self.theme_colors["header_bg"],
            text_color="white",
            command=self.show_documents_home
        )
        self.header_title.pack(side="left", padx=30)

        # Theme toggle button
        self.theme_toggle = ctk.CTkButton(
            self.header_frame,
            text="☀️🌙",
            width=50,
            height=35,
            fg_color="#FDD835",
            hover_color="#F9A825",
            command=self.toggle_theme
        )
        self.theme_toggle.pack(side="right", padx=10)
        # App usage card in header
        self.usage_card = ctk.CTkFrame(self.header_frame,
                                      fg_color="#F3DEDE",
                                         corner_radius=15,
                                        height=25)
        self.usage_card.pack(side="right", padx=20)
        self.usage_card.pack_propagate(False)
        # Calculate current usage
        session_seconds = (datetime.now() - self.start_time).total_seconds()
        total_seconds = self.total_usage_seconds + session_seconds
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        self.usage_hours_label = ctk.CTkLabel(
            self.usage_card,
            text=f"Use Time: {hours}h {minutes}m",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.theme_colors["text_color"]
        )
        self.usage_hours_label.pack()

        # Create left sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#F5F5F5")
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        # Sidebar buttons
        button_config = {
            "width": 180,
            "height": 45,
            "corner_radius": 10,
            "font": ctk.CTkFont(size=14),
            "anchor": "w",
            "text_color": "black"
        }

        self.documents_button = ctk.CTkButton(
            self.sidebar_frame,
            text="📄  Document Manager",
            fg_color="#0088FF",
            command=self.open_notepad,
            **button_config
        )
        self.documents_button.pack(padx=20, pady=(30, 10))

        self.pomodoro_button = ctk.CTkButton(
            self.sidebar_frame,
            text="🕐  Focus Timer",
            fg_color="#4CABFF",
            command=self.open_timer,
            **button_config
        )
        self.pomodoro_button.pack(padx=20, pady=10)

        self.todo_button = ctk.CTkButton(
            self.sidebar_frame,
            text="📋  To do list",
            fg_color="#8AC9FF",
            command=self.open_to_do,
            **button_config
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
            command=self.open_settings
        )
        self.settings_button.pack(side="bottom", pady=30)

        # Create main content area
        self.main_content_frame = ctk.CTkFrame(self, fg_color="#FAF3E0", corner_radius=0)
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
        """Load total usage time from file"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    return data.get('total_seconds', 0)
            except:
                return 0
        return 0

    def save_usage_data(self):
        """Save total usage time to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump({'total_seconds': self.total_usage_seconds}, f)
        except Exception as e:
            print(f"Error saving usage data: {e}")

    def start_usage_tracking(self):
        """Start tracking app usage time"""
        self.update_usage_time()

    def update_usage_time(self):
        """Update usage counter every second"""
        # Calculate session time
        session_seconds = (datetime.now() - self.start_time).total_seconds()
        total_seconds = self.total_usage_seconds + session_seconds
        
        # Convert to hours and minutes
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        # Update display if usage card exists
        if hasattr(self, 'usage_hours_label'):
            self.usage_hours_label.configure(text=f"Use time: {hours}h {minutes}m")
        
        # Save every 60 seconds
        if int(session_seconds) % 60 == 0 and int(session_seconds) > 0:
            self.total_usage_seconds = int(total_seconds)
            self.save_usage_data()
        
        # Schedule next update
        self.usage_timer = self.after(1000, self.update_usage_time)

    def on_closing(self):
        """Handle window closing - save usage data"""
        # Save final usage time
        session_seconds = (datetime.now() - self.start_time).total_seconds()
        self.total_usage_seconds = int(self.total_usage_seconds + session_seconds)
        self.save_usage_data()
        
        # Cancel timer
        if self.usage_timer:
            self.after_cancel(self.usage_timer)
        
        # Close window
        self.destroy()

    def open_settings(self):
        """Open settings dialog"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        
        label = ctk.CTkLabel(
            settings_window,
            text="Settings",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        label.pack(pady=20)

    def clear_main_content(self):
        """Clear all widgets from main content frame"""
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()

    def show_documents_home(self):
        """Show the documents home screen with calendar and tasks"""
        self.current_view = "documents"
        self.clear_main_content()

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
            border_width= 1
        )
        search_entry.pack(side="left", fill="x", expand=True)

        search_button = ctk.CTkButton(
            search_frame,
            text="🔍",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color="#E0E0E0"
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
        calendar_card = ctk.CTkFrame(left_panel,
                                      fg_color=self.theme_colors["calendar_bg"],
                                         corner_radius=15)
        calendar_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.create_calendar(calendar_card)

        # Task preview card under calendar
        task_card = ctk.CTkFrame(left_panel,
                                  fg_color=self.theme_colors["task_card_bg_1"],
                                    corner_radius=15)
        task_card.grid(row=1, column=0, sticky="nsew")

        task_date = ctk.CTkLabel(
            task_card,
            text="date here when we implement closest date logic",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.theme_colors["text_color"]
        )
        task_date.pack(anchor="w", padx=20, pady=(20, 10))

        tasks = ["this is a task", "this is also a task",]
        for task in tasks:
            task_label = ctk.CTkLabel(
                task_card,
                text=f"• {task}",
                font=ctk.CTkFont(size=12),
                anchor="w",
                text_color=self.theme_colors["text_color"]
            )
            task_label.pack(anchor="w", padx=20, pady=2)

        # Right side - Recent files
        right_panel = ctk.CTkFrame(content_grid,
                                    fg_color="transparent",)
        right_panel.grid(row=0, column=2, sticky="nsew", padx=(20, 0))
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=0)
        right_panel.grid_columnconfigure(0, weight=5)

        # Recent files card (main area)
        files_card = ctk.CTkFrame(right_panel,
                                   fg_color="transparent",
                                     corner_radius=15)
        files_card.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        files_title = ctk.CTkLabel(
            files_card,
            text="Recent files",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.theme_colors["recent_files_fg"],
            corner_radius=8,
            width=120,
            height=30
        )
        files_title.pack(padx=100,pady=20)
    
    def change_month(self, step):
        self.cal_month += step

        if self.cal_month > 12:
            self.cal_month = 1
            self.cal_year += 1
        elif self.cal_month < 1:
            self.cal_month = 12
            self.cal_year -= 1

        if hasattr(self, 'calendar_container'): # Refresh calendar display
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
            text_color="black"
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
            command=lambda: self.change_month(-1)
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
            command=lambda: self.change_month(1)
        )
        next_btn.pack(side="left", padx=2)

        # Calendar grid
        cal_grid = ctk.CTkFrame(parent, fg_color="transparent")
        cal_grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        for i in range(7):
            cal_grid.grid_columnconfigure(i, weight=1)
        for i in range(1,7):
            cal_grid.grid_rowconfigure(i, weight=1)

        # Day headers
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for i, day in enumerate(days):
            day_label = ctk.CTkLabel(
                cal_grid,
                text=day,
                font=ctk.CTkFont(size=10),
                text_color="gray",
                width=40
            )
            day_label.grid(row=0, column=i, padx=2, pady=5)

        # Calendar days
        cal_obj = calendar.monthcalendar(self.cal_year, self.cal_month)
        real_now = datetime.now()
        for week_num, week in enumerate(cal_obj):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                
                is_today = (day == real_now.day and
                            self.cal_month == real_now.month and
                            self.cal_year == real_now.year)
                
                # Use theme colors for today/range highlight
                today_bg = "#2196F3" if ctk.get_appearance_mode() == "Light" else self.theme_colors["document_button_fg"] # Use a theme color for today
                range_bg = "#E3F2FD" if ctk.get_appearance_mode() == "Light" else self.theme_colors["task_card_bg_2"]
                
                fg_color = today_bg if is_today else "transparent"
                text_color = "white" if is_today else "black"
                
                day_btn = ctk.CTkButton(
                    cal_grid,
                    text=str(day),
                    #width=40, # temporarily disable fixed size for better scaling
                    #height=35,
                    fg_color=fg_color,
                    hover_color=range_bg, # Use range color for hover
                    text_color=text_color,
                    corner_radius=8,
                    font=ctk.CTkFont(size=12)
                )
                day_btn.grid(row=week_num + 1, column=day_num, padx=2, pady=2)
            day_btn.grid(row=week_num + 1, column=day_num, padx=2, pady=2,sticky="nsew")
    def set_theme_colors(self,colors):
        self.theme_colors = colors

        # Update Header Color
        self.header_frame.configure(fg_color=colors["header_bg"])
        self.sidebar_frame.configure(
            fg_color=colors["sidebar_bg"],)
        self.main_content_frame.configure(fg_color=colors["main_bg"])
        self.usage_card.configure(fg_color=colors["usage_card_bg"])
        self.usage_hours_label.configure(text_color=colors["text_color"])

        self.documents_button.configure(fg_color=colors["document_button_fg"],
                                        text_color=colors["text_color"])
        self.pomodoro_button.configure(fg_color=colors["pomodoro_button_fg"],
                                        text_color=colors["text_color"])
        self.todo_button.configure(fg_color=colors["todo_button_fg"],
                                        text_color=colors["text_color"])

        if ctk.get_appearance_mode() == "Light":
            self.theme_toggle.configure(fg_color="#FDD835", hover_color="#F9A825")
        else:
            self.theme_toggle.configure(fg_color="#424242", hover_color="#616161")
        if self.current_view == "documents":
            self.show_documents_home()

    def toggle_theme(self):
        """Toggle between light and dark mode"""
        current = ctk.get_appearance_mode()
        if current == "Light":
            ctk.set_appearance_mode("Dark")
            self.set_theme_colors(self.DARK_THEME)
        else:
            ctk.set_appearance_mode("Light")
            self.set_theme_colors(self.LIGHT_THEME)

    def open_notepad(self):
        """Load notepad applet into main content area"""
        print("Opening Documents...")
        self.current_view = "documents"
        self.clear_main_content()

        if NotepadApplet:
            self.current_applet = NotepadApplet(self.main_content_frame)
        else:
            placeholder = ctk.CTkLabel(
                self.main_content_frame,
                text="document? nah wait for it lol",
                font=ctk.CTkFont(size=24)
            )
            placeholder.pack(expand=True)

    def open_timer(self):
        """Load pomodoro applet into main content area"""
        print("Opening Pomodoro Timer...")
        self.current_view = "pomodoro"
        self.clear_main_content()

        if PomodoroApplet:
            self.current_applet = PomodoroApplet(self.main_content_frame)
        else:
            placeholder = ctk.CTkLabel(
                self.main_content_frame,
                text="just wait, we have like 4 weeks for this lmfao",
                font=ctk.CTkFont(size=24)
            )
            placeholder.pack(expand=True)

    def open_to_do(self):
        """Load todo applet into main content area"""
        print("Opening To-Do List...")
        self.current_view = "todo"
        self.clear_main_content()

        if TodoApplet:
            self.current_applet = TodoApplet(self.main_content_frame)
        else:
            placeholder = ctk.CTkLabel(
                self.main_content_frame,
                text="✓ To-Do List\n\nComing Soon...",
                font=ctk.CTkFont(size=24)
            )
            placeholder.pack(expand=True)
    def get_app_data_path(self):
        app_name = "sapient"
        
        if os.name == 'nt': # Windows
            data_dir = Path(os.getenv('LOCALAPPDATA')) / app_name
        elif os.name == 'posix': # macOS/Linux
            if sys.platform == 'darwin': # macOS
                data_dir = Path.home() / 'Library' / 'Application Support' / app_name
            else: # Linux
                data_dir = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / '.config')) / app_name
        else: # Fallback
            data_dir = Path.home() / f".{app_name.lower()}"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        return data_dir


if __name__ == "__main__":
    app = App()
    app.mainloop()