import customtkinter as ctk


class TodoApplet:
    def __init__(self, parent):
        self.parent = parent
        self.name = "To-Do List"
        self.tasks = []
        
        # Create main container
        self.main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)
        
        # Title
        self.title = ctk.CTkLabel(
            self.main_frame,
            text="✓ My Tasks",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title.pack(pady=(0, 20))
        
        # Input frame for new tasks
        input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=10)
        
        self.task_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="lorem ipsum dolor sit amet",
            height=40
        )
        self.task_input.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.task_input.bind("<Return>", lambda e: self.add_task())
        
        self.add_button = ctk.CTkButton(
            input_frame,
            text="Add",
            command=self.add_task,
            width=80
        )
        self.add_button.pack(side="left")
        
        # Tasks list frame with scrollbar
        list_frame = ctk.CTkFrame(self.main_frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tasks_listbox = ctk.CTkTextbox(list_frame, wrap="word")
        self.tasks_listbox.pack(fill="both", expand=True)
        self.tasks_listbox.configure(state="disabled")
        
        self.update_task_display()
    
    def add_task(self):
        """Add a new task to the list"""
        task_text = self.task_input.get().strip()
        if task_text:
            self.tasks.append({"text": task_text, "done": False})
            self.task_input.delete(0, "end")
            self.update_task_display()
    
    def update_task_display(self):
        """Update the task list display"""
        self.tasks_listbox.configure(state="normal")
        self.tasks_listbox.delete("1.0", "end")
        
        if not self.tasks:
            self.tasks_listbox.insert("1.0", "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.")
        else:
            for i, task in enumerate(self.tasks, 1):
                checkbox = "☑" if task["done"] else "☐"
                self.tasks_listbox.insert("end", f"{checkbox} {task['text']}\n")
        
        self.tasks_listbox.configure(state="disabled")
