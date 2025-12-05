import tkinter
import tkinter.messagebox
import customtkinter as ctk

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

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Track current active applet
        self.current_applet = None
        self.current_view = "home"

        # configure window
        self.title("Sapient")
        self.geometry(f"{1280}x{720}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=10)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Sapient",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Home button (to return to main view)
        self.home_button = ctk.CTkButton(
            self.sidebar_frame,
            text="🏠 Home",
            command=self.show_home
        )
        self.home_button.grid(row=1, column=0, padx=20, pady=10)

        self.notepad_button = ctk.CTkButton(
            self.sidebar_frame,
            text="📄 Documents",
            command=self.open_notepad
        )
        self.notepad_button.grid(row=2, column=0, padx=20, pady=10)

        self.timer_button = ctk.CTkButton(
            self.sidebar_frame,
            text="⏱️ Pomodoro",
            command=self.open_timer
        )
        self.timer_button.grid(row=3, column=0, padx=20, pady=10)

        self.to_do_list_button = ctk.CTkButton(
            self.sidebar_frame,
            text="✓ To-do List",
            command=self.open_to_do
        )
        self.to_do_list_button.grid(row=4, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Appearance Mode:",
            anchor="w"
        )
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))

        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))

        self.scaling_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="UI Scaling:",
            anchor="w"
        )
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))

        self.scaling_optionemenu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event
        )
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # create main content area
        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_frame.grid(
            row=0, column=1, rowspan=3, columnspan=2,
            padx=20, pady=20, sticky="nsew"
        )

        # Configure main content grid
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)

        # Create calendar preview frame (far right)
        self.calendar_frame = ctk.CTkFrame(self, width=250, corner_radius=10)
        self.calendar_frame.grid(
            row=0, column=3, rowspan=3,
            padx=(0, 20), pady=20, sticky="nsew"
        )
        self.calendar_frame.grid_propagate(False)

        # Calendar frame title
        self.calendar_title = ctk.CTkLabel(
            self.calendar_frame,
            text="Quick Stats",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.calendar_title.pack(padx=20, pady=(20, 10))

        # Calendar content placeholder
        self.calendar_content = ctk.CTkTextbox(self.calendar_frame, wrap="word")
        self.calendar_content.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        self.update_calendar_content()

        # Show home view by default
        self.show_home()

    def clear_main_content(self):
        """Clear all widgets from main content frame"""
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()

    def update_calendar_content(self):
        """Update the sidebar stats/calendar"""
        self.calendar_content.configure(state="normal")
        self.calendar_content.delete("1.0", "end")

        content = f"Current View: {self.current_view.title()}\n\n"
        content += "📊 Today's Progress:\n"
        content += "• Pomodoros: 0\n"
        content += "• Tasks Done: 0\n"
        content += "• Study Time: 0h\n\n"
        content += "💡 Tip: Start with\nyour most important\ntask first!"

        self.calendar_content.insert("1.0", content)
        self.calendar_content.configure(state="disabled")

    def show_home(self):
        """Show the home/welcome screen"""
        self.current_view = "home"
        self.clear_main_content()
        self.update_calendar_content()

        # Create welcome content
        welcome_frame = ctk.CTkFrame(self.main_content_frame)
        welcome_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            welcome_frame,
            text="Lorem Ipsum",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(40, 10))

        # Feature cards frame
        cards_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=40)

        # Configure grid for cards
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Card 1: Documents
        self.create_feature_card(
            cards_frame,
            "📄 Documents",
            "Read PDFs and take\nlinked notes",
            0, 0,
            self.open_notepad
        )

        # Card 2: Pomodoro
        self.create_feature_card(
            cards_frame,
            "⏱️ Pomodoro Timer",
            "Focus with work-rest\ncycles",
            0, 1,
            self.open_timer
        )

        # Card 3: To-Do
        self.create_feature_card(
            cards_frame,
            "✓ To-Do List",
            "Track tasks and\nprogress",
            0, 2,
            self.open_to_do
        )

    def create_feature_card(self, parent, title, description, row, col, command):
        """Helper to create feature cards"""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        card_title = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        card_title.pack(pady=(20, 10))

        card_desc = ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=12)
        )
        card_desc.pack(pady=(0, 20))

        card_button = ctk.CTkButton(
            card,
            text="Open",
            command=command,
            width=100
        )
        card_button.pack(pady=(0, 20))

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)

    def open_notepad(self):
        """Load notepad applet into main content area"""
        print("Opening Documents...")
        self.current_view = "documents"
        self.clear_main_content()
        self.update_calendar_content()

        if NotepadApplet:
            self.current_applet = NotepadApplet(self.main_content_frame)
        else:
            # Placeholder when applet not ready
            placeholder = ctk.CTkLabel(
                self.main_content_frame,
                text="📄 Documents Module\n\nComing Soon...",
                font=ctk.CTkFont(size=24)
            )
            placeholder.pack(expand=True)

    def open_timer(self):
        """Load pomodoro applet into main content area"""
        print("Opening Pomodoro Timer...")
        self.current_view = "pomodoro"
        self.clear_main_content()
        self.update_calendar_content()

        if PomodoroApplet:
            self.current_applet = PomodoroApplet(self.main_content_frame)
        else:
            # Placeholder when applet not ready
            placeholder = ctk.CTkLabel(
                self.main_content_frame,
                text="⏱️ Pomodoro Timer\n\nComing Soon...",
                font=ctk.CTkFont(size=24)
            )
            placeholder.pack(expand=True)

    def open_to_do(self):
        """Load todo applet into main content area"""
        print("Opening To-Do List...")
        self.current_view = "todo"
        self.clear_main_content()
        self.update_calendar_content()

        if TodoApplet:
            self.current_applet = TodoApplet(self.main_content_frame)
        else:
            # Placeholder when applet not ready
            placeholder = ctk.CTkLabel(
                self.main_content_frame,
                text="✓ To-Do List\n\nComing Soon...",
                font=ctk.CTkFont(size=24)
            )
            placeholder.pack(expand=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()