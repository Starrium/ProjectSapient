import customtkinter as ctk
from datetime import datetime, timedelta
from tkcalendar import DateEntry

try:
    from task_manager import task_manager
except ImportError:
    import sys
    sys.path.insert(0, '..')
    from task_manager import task_manager


class TodoApplet:
    def __init__(self, parent):
        self.parent = parent
        self.name = "To-Do List"
        
        # Create main container
        self.main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title = ctk.CTkLabel(
            self.main_frame,
            text="✓ My Tasks",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title.pack(pady=(0, 20))
        
        # Stats frame
        stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 15))
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.stats_label.pack()
        
        # Input frame for new tasks - modern white card style
        input_frame = ctk.CTkFrame(self.main_frame, fg_color="#FFFFFF", corner_radius=12)
        input_frame.pack(fill="x", pady=10, padx=5)
        
        # Task text input
        self.task_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Add new task...",
            height=45,
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(size=14)
        )
        self.task_input.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        self.task_input.bind("<Return>", lambda e: self.add_task())
        
        # Date picker button - modern pill style
        self.selected_date = None
        self.date_btn = ctk.CTkButton(
            input_frame,
            text="📅 Today",
            command=self.show_date_picker,
            width=110,
            height=38,
            fg_color="#E3F2FD",
            hover_color="#BBDEFB",
            text_color="#1565C0",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=19
        )
        self.date_btn.pack(side="left", padx=(0, 8), pady=10)
        
        # Priority selector - cleaner styling
        self.priority_var = ctk.StringVar(value="normal")
        self.priority_menu = ctk.CTkOptionMenu(
            input_frame,
            values=["🔵 low", "⚪ normal", "🔴 high"],
            variable=self.priority_var,
            width=120,
            height=38,
            fg_color="#F5F5F5",
            button_color="#E0E0E0",
            button_hover_color="#BDBDBD",
            text_color="#424242",
            font=ctk.CTkFont(size=12),
            corner_radius=19,
            dropdown_fg_color="#FFFFFF",
            dropdown_hover_color="#E3F2FD"
        )
        self.priority_menu.set("⚪ normal")
        self.priority_menu.pack(side="left", padx=(0, 8), pady=10)
        
        # Add button - vibrant green
        self.add_button = ctk.CTkButton(
            input_frame,
            text="＋",
            command=self.add_task,
            width=45,
            height=38,
            fg_color="#4CAF50",
            hover_color="#43A047",
            font=ctk.CTkFont(size=20, weight="bold"),
            corner_radius=19
        )
        self.add_button.pack(side="left", padx=(0, 10), pady=10)
        
        # Search bar
        search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(10, 5))
        
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search tasks...",
            textvariable=self.search_var,
            height=35,
            width=250,
            corner_radius=17,
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#E0E0E0"
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_var.trace_add("write", lambda *args: self.update_task_display())
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        filter_frame.pack(side="left", fill="x", expand=True)
        
        self.filter_var = ctk.StringVar(value="all")
        filters = [("All", "all"), ("Active", "active"), ("Completed", "done"), ("Today", "today")]
        
        for text, value in filters:
            btn = ctk.CTkButton(
                filter_frame,
                text=text,
                command=lambda v=value: self.set_filter(v),
                width=70,
                height=30,
                fg_color="#E0E0E0" if value != "all" else "#2196F3",
                hover_color="#BDBDBD",
                text_color="black" if value != "all" else "white",
                corner_radius=15
            )
            btn.pack(side="left", padx=3)
            setattr(self, f"filter_btn_{value}", btn)
        
        # Clear Completed button
        self.clear_btn = ctk.CTkButton(
            search_frame,
            text="🧹 Clear Done",
            command=self.clear_completed,
            width=100,
            height=30,
            fg_color="#FFEBEE",
            hover_color="#FFCDD2",
            text_color="#C62828",
            corner_radius=15
        )
        self.clear_btn.pack(side="right", padx=5)
        
        # Tasks container with scroll
        self.tasks_container = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="transparent"
        )
        self.tasks_container.pack(fill="both", expand=True, pady=10)
        
        # Date picker popup (hidden initially)
        self.date_popup = None
        
        self.update_task_display()
        self.update_stats()
    
    def show_date_picker(self):
        """Show date picker popup"""
        if self.date_popup and self.date_popup.winfo_exists():
            self.date_popup.destroy()
            return
        
        self.date_popup = ctk.CTkToplevel(self.parent)
        self.date_popup.title("Select Date")
        self.date_popup.geometry("250x280")
        self.date_popup.transient(self.parent)
        
        # Quick date buttons
        quick_frame = ctk.CTkFrame(self.date_popup, fg_color="transparent")
        quick_frame.pack(fill="x", padx=10, pady=10)
        
        today = datetime.now()
        quick_dates = [
            ("Today", today.strftime("%Y-%m-%d")),
            ("Tomorrow", (today + timedelta(days=1)).strftime("%Y-%m-%d")),
            ("Next Week", (today + timedelta(days=7)).strftime("%Y-%m-%d")),
        ]
        
        for text, date in quick_dates:
            btn = ctk.CTkButton(
                quick_frame,
                text=text,
                command=lambda d=date, t=text: self.select_date(d, t),
                height=30,
                fg_color="#E3F2FD",
                hover_color="#BBDEFB",
                text_color="#1976D2"
            )
            btn.pack(fill="x", pady=2)
        
        # Calendar widget
        try:
            cal = DateEntry(
                self.date_popup,
                width=20,
                background='#2196F3',
                foreground='white',
                borderwidth=2,
                date_pattern='yyyy-mm-dd'
            )
            cal.pack(pady=10)
            
            def on_date_select(event=None):
                date = cal.get_date()
                date_str = date.strftime("%Y-%m-%d")
                display = date.strftime("%b %d")
                self.select_date(date_str, display)
            
            cal.bind("<<DateEntrySelected>>", on_date_select)
        except Exception as e:
            # Fallback if tkcalendar not installed
            label = ctk.CTkLabel(
                self.date_popup,
                text="Install tkcalendar for date picker:\npip install tkcalendar",
                text_color="gray"
            )
            label.pack(pady=10)
        
        # No date button
        no_date_btn = ctk.CTkButton(
            self.date_popup,
            text="No deadline",
            command=lambda: self.select_date(None, "No date"),
            fg_color="#FFEBEE",
            hover_color="#FFCDD2",
            text_color="#C62828"
        )
        no_date_btn.pack(pady=10)
    
    def select_date(self, date_str, display_text):
        """Handle date selection"""
        self.selected_date = date_str
        if date_str:
            self.date_btn.configure(text=f"📅 {display_text}")
        else:
            self.date_btn.configure(text="📅 No date")
        
        if self.date_popup:
            self.date_popup.destroy()
    
    def add_task(self):
        """Add a new task"""
        task_text = self.task_input.get().strip()
        if task_text:
            deadline = self.selected_date or datetime.now().strftime("%Y-%m-%d")
            # Extract priority from the emoji format
            priority_raw = self.priority_var.get()
            if "low" in priority_raw:
                priority = "low"
            elif "high" in priority_raw:
                priority = "high"
            else:
                priority = "normal"
            
            task_manager.add_task(task_text, deadline, priority)
            
            # Reset inputs
            self.task_input.delete(0, "end")
            self.selected_date = None
            self.date_btn.configure(text="📅 Today")
            self.priority_menu.set("⚪ normal")
            
            self.update_task_display()
            self.update_stats()
    
    def set_filter(self, filter_type):
        """Set task filter"""
        self.filter_var.set(filter_type)
        
        # Update button colors
        for f in ["all", "active", "done", "today"]:
            btn = getattr(self, f"filter_btn_{f}", None)
            if btn:
                if f == filter_type:
                    btn.configure(fg_color="#2196F3", text_color="white")
                else:
                    btn.configure(fg_color="#E0E0E0", text_color="black")
        
        self.update_task_display()
    
    def update_stats(self):
        """Update task statistics"""
        all_tasks = task_manager.tasks
        pending = len([t for t in all_tasks if not t.get("done")])
        done = len([t for t in all_tasks if t.get("done")])
        overdue = len(task_manager.get_overdue_tasks())
        
        stats_text = f"📊 {len(all_tasks)} total | ✓ {done} done | ⏳ {pending} pending"
        if overdue > 0:
            stats_text += f" | 🔴 {overdue} overdue"
        
        self.stats_label.configure(text=stats_text)
    
    def update_task_display(self):
        """Update the task list display"""
        # Clear existing tasks
        for widget in self.tasks_container.winfo_children():
            widget.destroy()
        
        # Get all tasks
        tasks = task_manager.tasks
        
        # Apply search filter
        search_query = self.search_var.get().strip().lower()
        if search_query:
            tasks = [t for t in tasks if search_query in t.get("text", "").lower()]
        
        # Apply status filter
        filter_type = self.filter_var.get()
        if filter_type == "active":
            tasks = [t for t in tasks if not t.get("done")]
        elif filter_type == "done":
            tasks = [t for t in tasks if t.get("done")]
        elif filter_type == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            tasks = [t for t in tasks if t.get("deadline") == today]
        
        if not tasks:
            empty_label = ctk.CTkLabel(
                self.tasks_container,
                text="No tasks found. Add your first task above!",
                text_color="gray",
                font=ctk.CTkFont(size=14)
            )
            empty_label.pack(pady=50)
            return
        
        # Sort by deadline and priority
        priority_order = {"high": 0, "normal": 1, "low": 2}
        tasks_sorted = sorted(
            tasks,
            key=lambda x: (
                x.get("done", False),
                x.get("deadline") or "9999-99-99",
                priority_order.get(x.get("priority", "normal"), 1)
            )
        )
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        for task in tasks_sorted:
            self.create_task_card(task, today)
    
    def create_task_card(self, task, today):
        """Create a task card widget"""
        is_done = task.get("done", False)
        is_overdue = task.get("deadline") and task["deadline"] < today and not is_done
        priority = task.get("priority", "normal")
        
        # Card colors based on state and theme
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        if is_done:
            bg_color = "#2E4534" if is_dark else "#E8F5E9"
            border_color = "#4CAF50" if is_dark else "#81C784"
        elif is_overdue:
            bg_color = "#4A2020" if is_dark else "#FFEBEE"
            border_color = "#EF5350" if is_dark else "#E57373"
        elif priority == "high":
            bg_color = "#4A3520" if is_dark else "#FFF3E0"
            border_color = "#FF9800" if is_dark else "#FFB74D"
        else:
            bg_color = "#2D2D2D" if is_dark else "#FFFFFF"
            border_color = "#555555" if is_dark else "#E0E0E0"
        
        # Task card frame
        card = ctk.CTkFrame(
            self.tasks_container,
            fg_color=bg_color,
            corner_radius=8,
            border_width=1,
            border_color=border_color
        )
        card.pack(fill="x", pady=4, padx=2)
        
        # Checkbox
        checkbox_text = "☑" if is_done else "☐"
        checkbox = ctk.CTkButton(
            card,
            text=checkbox_text,
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#E0E0E0",
            text_color="#4CAF50" if is_done else "gray",
            font=ctk.CTkFont(size=18),
            command=lambda t=task: self.toggle_task(t["id"])
        )
        checkbox.pack(side="left", padx=5)
        
        # Task text
        text_style = ctk.CTkFont(size=14)
        if is_done:
            text_color = "gray"
        else:
            text_color = "#E0E0E0" if is_dark else "black"
        
        task_label = ctk.CTkLabel(
            card,
            text=task["text"],
            font=text_style,
            text_color=text_color,
            anchor="w"
        )
        task_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # Deadline badge
        if task.get("deadline"):
            deadline = task["deadline"]
            if deadline == today:
                deadline_text = "Today"
                deadline_color = "#2196F3"
            elif deadline == (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"):
                deadline_text = "Tomorrow"
                deadline_color = "#FF9800"
            elif is_overdue:
                deadline_text = f"Overdue"
                deadline_color = "#F44336"
            else:
                try:
                    dt = datetime.strptime(deadline, "%Y-%m-%d")
                    deadline_text = dt.strftime("%b %d")
                except:
                    deadline_text = deadline
                deadline_color = "#9E9E9E"
            
            deadline_label = ctk.CTkLabel(
                card,
                text=deadline_text,
                font=ctk.CTkFont(size=11),
                text_color=deadline_color
            )
            deadline_label.pack(side="left", padx=5)
        
        # Priority indicator
        if priority == "high" and not is_done:
            priority_label = ctk.CTkLabel(
                card,
                text="🔥",
                font=ctk.CTkFont(size=12)
            )
            priority_label.pack(side="left", padx=2)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            card,
            text="🗑",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#FFCDD2",
            text_color="#E57373",
            command=lambda t=task: self.delete_task(t["id"])
        )
        delete_btn.pack(side="right", padx=5, pady=5)
        
        # Edit button
        edit_btn = ctk.CTkButton(
            card,
            text="✏️",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#E3F2FD",
            text_color="#1976D2",
            command=lambda t=task: self.show_edit_popup(t)
        )
        edit_btn.pack(side="right", padx=2, pady=5)
    
    def toggle_task(self, task_id):
        """Toggle task completion"""
        task_manager.toggle_task(task_id)
        self.update_task_display()
        self.update_stats()
    
    def delete_task(self, task_id):
        """Delete a task"""
        task_manager.delete_task(task_id)
        self.update_task_display()
        self.update_stats()
    
    def clear_completed(self):
        """Clear all completed tasks"""
        removed = task_manager.clear_completed()
        if removed > 0:
            self.update_task_display()
            self.update_stats()
    
    def show_edit_popup(self, task):
        """Show popup to edit a task"""
        popup = ctk.CTkToplevel(self.parent)
        popup.title("Edit Task")
        popup.geometry("420x350")
        popup.resizable(False, False)
        
        # Wait for window to be ready before adding widgets
        popup.after(100, lambda: self._create_edit_widgets(popup, task))
    
    def _create_edit_widgets(self, popup, task):
        """Create edit popup widgets after window is ready"""
        # Make sure popup still exists
        if not popup.winfo_exists():
            return
            
        popup.grab_set()
        popup.focus_force()
        
        # Task text
        text_label = ctk.CTkLabel(popup, text="Task:", font=ctk.CTkFont(size=14, weight="bold"))
        text_label.pack(pady=(20, 5), padx=20, anchor="w")
        
        text_entry = ctk.CTkEntry(popup, height=40, width=380)
        text_entry.insert(0, task.get("text", ""))
        text_entry.pack(padx=20, pady=5)
        text_entry.focus()
        
        # Deadline
        deadline_label = ctk.CTkLabel(popup, text="Deadline:", font=ctk.CTkFont(size=14, weight="bold"))
        deadline_label.pack(pady=(15, 5), padx=20, anchor="w")
        
        deadline_entry = ctk.CTkEntry(popup, height=40, width=380, placeholder_text="YYYY-MM-DD")
        if task.get("deadline"):
            deadline_entry.insert(0, task.get("deadline"))
        deadline_entry.pack(padx=20, pady=5)
        
        # Priority
        priority_label = ctk.CTkLabel(popup, text="Priority:", font=ctk.CTkFont(size=14, weight="bold"))
        priority_label.pack(pady=(15, 5), padx=20, anchor="w")
        
        priority_var = ctk.StringVar(value=task.get("priority", "normal"))
        priority_menu = ctk.CTkOptionMenu(
            popup,
            values=["low", "normal", "high"],
            variable=priority_var,
            width=380,
            height=35
        )
        priority_menu.pack(padx=20, pady=5)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save_changes():
            new_text = text_entry.get().strip()
            new_deadline = deadline_entry.get().strip() or None
            new_priority = priority_var.get()
            
            if new_text:
                task_manager.edit_task(
                    task["id"],
                    text=new_text,
                    deadline=new_deadline,
                    priority=new_priority
                )
                self.update_task_display()
                self.update_stats()
            popup.destroy()
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            command=save_changes,
            fg_color="#4CAF50",
            hover_color="#43A047",
            width=120,
            height=40
        )
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=popup.destroy,
            fg_color="#9E9E9E",
            hover_color="#757575",
            width=120,
            height=40
        )
        cancel_btn.pack(side="left", padx=10)

