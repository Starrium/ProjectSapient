import tkinter
import tkinter.messagebox
import customtkinter as ctk

try:
    from todo_list.applet import TodoApplet
except ImportError:
    print("Todo applet not found. Skipping.")
    TodoApplet = None

try:
    from pomodoro.applet import PomodoroApplet
except ImportError:
    print("Pomodoro applet not found. Skipping.")
    PomodoroApplet = None

try:
    from notepad.applet import NotepadApplet
except ImportError:
    print("Notepad applet not found. Skipping.")
    NotepadApplet = None

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Dictionary to track open module windows
        self.open_windows = {
            'notepad': None,
            'timer': None,
            'todo': None
        }

        # configure window
        self.title("CustomTkinter complex_example.py")
        self.geometry(f"{1100}x{580}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=10)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Purse", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.notepad_button = ctk.CTkButton(self.sidebar_frame, text="Documents", command=self.open_notepad)
        self.notepad_button.grid(row=1, column=0, padx=20, pady=10)
        self.timer_button = ctk.CTkButton(self.sidebar_frame, text="Pomodoro Timer", command=self.open_timer)
        self.timer_button.grid(row=2, column=0, padx=20, pady=10)
        self.to_do_list_button = ctk.CTkButton(self.sidebar_frame, text="To-do List", command=self.open_to_do)
        self.to_do_list_button.grid(row=3, column=0, padx=20, pady=10)
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # create main content area
        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, rowspan=3, columnspan=2, padx=20, pady=20, sticky="nsew")

        # Configure main content grid
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)

        # Create calendar preview frame (far right)
        self.calendar_frame = ctk.CTkFrame(self, width=250, corner_radius=10)
        self.calendar_frame.grid(row=0, column=3, rowspan=3, padx=(0, 20), pady=20, sticky="nsew")
        self.calendar_frame.grid_propagate(False)

        # Calendar frame title
        self.calendar_title = ctk.CTkLabel(
            self.calendar_frame,
            text="Upcoming Events",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.calendar_title.pack(padx=20, pady=(20, 10))

        # Calendar content placeholder
        self.calendar_content = ctk.CTkTextbox(self.calendar_frame, wrap="word")
        self.calendar_content.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        self.calendar_content.insert("1.0", "No upcoming events.\n\nClick 'Calendar' to add events!")
        self.calendar_content.configure(state="disabled")

    def check_window_exists(self, window_key):
        """
        Check if a window is already open and bring it to focus if it exists.
        Returns True if window exists, False otherwise.
        """
        window = self.open_windows.get(window_key)
        if window is not None and window.winfo_exists():
            # Window exists, bring it to front
            window.lift()
            window.focus()
            return True
        return False

    def on_window_close(self, window_key, window):
        """
        Callback function when a window is closed.
        Clears the reference from the dictionary.
        """
        self.open_windows[window_key] = None
        window.destroy()

    def open_input_dialog_event(self):
        dialog = ctk.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def sidebar_button_event(self):
        print("sidebar_button click")

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)

    def open_notepad(self):
        print("open_document click")

        # Check if window already exists
        if self.check_window_exists('notepad'):
            print("Notepad window already open!")
            return

        # Create new window
        applet_window = ctk.CTkToplevel(self)
        applet_window.title("Documents")
        applet_window.geometry(f"{1100}x{580}")

        # Store reference
        self.open_windows['notepad'] = applet_window

        # Set close protocol
        applet_window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close('notepad', applet_window))

        # Uncomment when ready to use
        # if NotepadApplet:
        #     applet = NotepadApplet()
        #     applet.run(applet_window)

    def open_timer(self):
        print("open_timer click")

        # Check if window already exists
        if self.check_window_exists('timer'):
            print("Timer window already open!")
            return

        # Create new window
        applet_window = ctk.CTkToplevel(self)
        applet_window.title("Timer")
        applet_window.geometry(f"{1100}x{580}")

        # Store reference
        self.open_windows['timer'] = applet_window

        # Set close protocol
        applet_window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close('timer', applet_window))

        # Uncomment when ready to use
        # if PomodoroApplet:
        #     applet = PomodoroApplet()
        #     applet.run(applet_window)

    def open_to_do(self):
        print("open_to_do click")

        # Check if window already exists
        if self.check_window_exists('todo'):
            print("To-do window already open!")
            return

        # Create new window
        applet_window = ctk.CTkToplevel(self)
        applet_window.title("To-do List")
        applet_window.geometry(f"{1100}x{580}")

        # Store reference
        self.open_windows['todo'] = applet_window

        # Set close protocol
        applet_window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close('todo', applet_window))

        # Uncomment when ready to use
        # if TodoApplet:
        #     applet = TodoApplet()
        #     applet.run(applet_window)


if __name__ == "__main__":
    app = App()
    app.mainloop()