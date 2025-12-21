import customtkinter as ctk
import calendar
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry

try:
    from task_manager import task_manager
except ImportError:
    import sys
    sys.path.insert(0, '..')
    from task_manager import task_manager

class CalendarPopup(ctk.CTkFrame):
    def __init__(self, parent, on_select_callback, fg_color="white", text_color="black"):
        super().__init__(parent, fg_color=fg_color, corner_radius=15, border_width=1, border_color="#E0E0E0")
        self.on_select = on_select_callback
        self.fg_color = fg_color
        self.text_color = text_color
        
        self.current_date = datetime.now()
        self.year = self.current_date.year
        self.month = self.current_date.month
        self.selected_date = None

        self.setup_ui()
        self.update_calendar()

    def setup_ui(self):
        # Header (Month Year + Nav buttons)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)

        self.btn_prev = ctk.CTkButton(header, text="<", width=30, height=30, 
                                      fg_color="transparent", text_color=self.text_color, hover_color="#E0E0E0",
                                      command=lambda: self.change_month(-1))
        self.btn_prev.pack(side="left")

        self.lbl_month = ctk.CTkLabel(header, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.text_color)
        self.lbl_month.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(header, text=">", width=30, height=30, 
                                      fg_color="transparent", text_color=self.text_color, hover_color="#E0E0E0",
                                      command=lambda: self.change_month(1))
        self.btn_next.pack(side="right")

        # Days Grid
        self.days_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.days_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Weekday headers
        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i, day in enumerate(weekdays):
            lbl = ctk.CTkLabel(self.days_frame, text=day, font=ctk.CTkFont(size=12, weight="bold"), text_color="gray", width=30)
            lbl.grid(row=0, column=i, pady=5)

    def change_month(self, step):
        self.month += step
        if self.month > 12:
            self.month = 1
            self.year += 1
        elif self.month < 1:
            self.month = 12
            self.year -= 1
        self.update_calendar()

    def update_calendar(self):
        # Update Header
        month_name = calendar.month_name[self.month]
        self.lbl_month.configure(text=f"{month_name} {self.year}")

        # Clear existing day buttons (skipping the header row)
        for widget in self.days_frame.winfo_children():
            if int(widget.grid_info()["row"]) > 0:
                widget.destroy()

        # Generate days
        cal = calendar.monthcalendar(self.year, self.month)
        today = datetime.now()

        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    continue

                # Check if this day is today
                is_today = (day == today.day and self.month == today.month and self.year == today.year)
                
                # Determine colors
                btn_fg = "transparent"
                btn_text = self.text_color
                btn_hover = "#E0E0E0"

                if is_today:
                    btn_fg = "#2196F3" # Blue highlight for today
                    btn_text = "white"
                    btn_hover = "#1976D2"

                btn = ctk.CTkButton(self.days_frame, text=str(day), width=30, height=30,
                                    fg_color=btn_fg, text_color=btn_text, hover_color=btn_hover,
                                    corner_radius=15, font=ctk.CTkFont(size=12),
                                    command=lambda d=day: self.select_day(d))
                btn.grid(row=r+1, column=c, padx=2, pady=2)

    def select_day(self, day):
        # Format date string YYYY-MM-DD
        date_str = f"{self.year}-{self.month:02d}-{day:02d}"
        self.on_select(date_str)

class TodoApplet:
    def __init__(self, parent):
        self.parent = parent
        self.name = "To-Do List"
        
        # Get theme colors from appearance mode
        self.update_theme_colors()
        
        # Track editing state
        self.is_editing = False
        self.editing_task_id = None
        
        # Create main container with theme background
        self.main_frame = ctk.CTkFrame(parent, fg_color=self.colors['bg'])
        self.main_frame.pack(fill="both", expand=True)
        
        # Create layout: main content with two columns
        self.create_main_content()
        
        self.update_task_display()
    
    def update_theme_colors(self):
        """Update colors based on current theme"""
        is_dark = ctk.get_appearance_mode() == "Dark"
        
        if is_dark:
            self.colors = {
                'bg': '#493E60',
                'card_bg': '#4A3B5C',
                'task_bg': '#B8B3C1',
                'add_btn_bg': '#B8B3C1',
                'text_dark': '#000000',
                'description_text': '#C0BFBF',
            }
        else:
            self.colors = {
                'bg': '#FAE5D5', 
                'card_bg': '#C0BFBF',
                'task_bg': '#FFFFFF', 
                'add_btn_bg': '#E0E0E0', 
                'text_dark': '#2D1B4E',
                'description_text': '#D9D9D9',
            }
    
    def create_main_content(self):
        """Create main content area"""
        # Content area with two columns
        self.content_area = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left column - Task list
        self.left_column = ctk.CTkFrame(self.content_area, fg_color=self.colors['card_bg'], corner_radius=25)
        self.left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Tasks scrollable area
        self.tasks_container = ctk.CTkScrollableFrame(
            self.left_column,
            fg_color="transparent"
        )
        self.tasks_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Right column - placeholder for edit panel (created on demand)
        self.right_column = None
    
    def show_add_panel(self):
        """Show the add/edit panel on the right"""
        self.is_editing = True
        
        # Create right column if it doesn't exist
        if self.right_column is None or not self.right_column.winfo_exists():
            self.right_column = ctk.CTkFrame(self.content_area, fg_color=self.colors['card_bg'], corner_radius=25, width=350)
            self.right_column.pack(side="right", fill="y", padx=(10, 0))
            self.right_column.pack_propagate(False)
            self.create_task_input_panel(self.right_column)
        
        # Clear inputs
        self.clear_input()
        if hasattr(self, 'delete_btn'):
            self.delete_btn.pack_forget() 
            
        self.editing_task_id = None # Reset ID for new task
    
    def hide_add_panel(self):
        """Hide the add/edit panel"""
        self.is_editing = False
        self.editing_task_id = None
        
        if self.right_column and self.right_column.winfo_exists():
            self.right_column.destroy()
            self.right_column = None
    
    def create_task_input_panel(self, parent):
        """Create task input/edit panel"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        # Close button (Moved to Top Right)
        close_btn = ctk.CTkButton(
            header_frame,
            text="✕",
            command=self.cancel_edit,
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=self.colors['add_btn_bg'],
            text_color=self.colors['text_dark'],
            font=ctk.CTkFont(size=18, weight="bold"),
            corner_radius=15
        )
        close_btn.pack(side="right")
        # ------------------------------------------

        # Title entry field
        self.title_input = ctk.CTkEntry(
            parent,
            fg_color=self.colors['card_bg'],
            text_color=self.colors['text_dark'],
            placeholder_text="Title",
            placeholder_text_color=self.colors['text_dark'],
            font=ctk.CTkFont(size=20,weight="bold"),
            border_width=0,
            corner_radius=15,
            height=45
        )
        self.title_input.pack(fill="x", padx=20)
        
        # Description label
        desc_label = ctk.CTkLabel(
            parent,
            text="Description",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text_dark']
        )
        desc_label.pack(pady=(5, 10), padx=20, anchor="w")
        
        # Description box
        self.task_input = ctk.CTkTextbox(
            parent,
            fg_color=self.colors['description_text'],
            text_color=self.colors['text_dark'],
            font=ctk.CTkFont(size=13),
            border_width=0,
            corner_radius=15,
            height=150
        )
        self.task_input.pack(fill="x", padx=20, pady=(0, 20))
        
        # Bottom controls
        controls_frame = ctk.CTkFrame(parent, fg_color=self.colors['task_bg'], corner_radius=20, height=60)
        controls_frame.pack(fill="x", padx=20, pady=(0, 20), side="bottom")
        controls_frame.pack_propagate(False) # Enforce height
        
        # Priority dropdown
        self.priority_var = ctk.StringVar(value="normal")
        self.priority_btn = ctk.CTkButton(
            controls_frame,
            text="Priority",
            command=self.toggle_priority_menu,
            width=100,
            height=35,
            fg_color="white",
            hover_color="#E0E0E0",
            text_color=self.colors['text_dark'],
            font=ctk.CTkFont(size=11),
            corner_radius=17
        )
        self.priority_btn.pack(side="left", padx=10, pady=12)
        
        # Date button
        self.selected_date = None
        self.date_btn = ctk.CTkButton(
            controls_frame,
            text="Date",
            command=self.toggle_date_menu,
            width=80,
            height=35,
            fg_color="white",
            hover_color="#E0E0E0",
            text_color=self.colors['text_dark'],
            font=ctk.CTkFont(size=11),
            corner_radius=17
        )
        self.date_btn.pack(side="left", padx=5, pady=12)
        
        # Save button
        self.save_btn = ctk.CTkButton(
            controls_frame,
            text="Save",
            command=self.save_task,
            width=70,
            height=35,
            fg_color="white",
            hover_color="#E0E0E0",
            text_color=self.colors['text_dark'],
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=17
        )
        self.save_btn.pack(side="left", padx=5, pady=12)

        # Delete Button (Created but hidden initially)
        self.delete_btn = ctk.CTkButton(
            controls_frame,
            text="🗑", # Trash icon
            command=self.delete_current_task,
            width=40,
            height=35,
            fg_color="#FFEBEE", # Light red background
            hover_color="#FFCDD2",
            text_color="#D32F2F", # Red text
            font=ctk.CTkFont(size=14),
            corner_radius=17
        )
        
        # Dropdown menus placeholders
        self.priority_dropdown = None
        self.date_dropdown = None

    def toggle_priority_menu(self):
        """Toggle priority dropdown menu"""
        # Close date menu if open
        if self.date_dropdown and self.date_dropdown.winfo_exists():
            self.date_dropdown.destroy()
            self.date_dropdown = None
        
        # Toggle priority menu
        if self.priority_dropdown and self.priority_dropdown.winfo_exists():
            self.priority_dropdown.destroy()
            self.priority_dropdown = None
            return
        
        # Create priority dropdown
        self.priority_dropdown = ctk.CTkFrame(
            self.right_column,
            fg_color="white",
            corner_radius=10,
            border_width=1,
            border_color="#E0E0E0",
            width=120,
            height=100
        )
        
        # Position below the priority button
        self.priority_dropdown.place(x=30, y=520)
        
        priorities = [("Low", "low"), ("Normal", "normal"), ("High", "high")]
        for text, value in priorities:
            btn = ctk.CTkButton(
                self.priority_dropdown,
                text=text,
                command=lambda v=value, t=text: self.select_priority(v, t),
                height=30,
                fg_color="transparent",
                hover_color="#E3F2FD",
                text_color=self.colors['text_dark'],
                font=ctk.CTkFont(size=11),
                anchor="w"
            )
            btn.pack(fill="x", padx=5, pady=2)
    
    def select_priority(self, priority, display_text):
        """Select priority and close dropdown"""
        self.priority_var.set(priority)
        self.priority_btn.configure(text=f"{display_text}▼")
        
        if self.priority_dropdown:
            self.priority_dropdown.destroy()
            self.priority_dropdown = None
    
    def toggle_date_menu(self):
        """Toggle custom calendar popup"""
        # Close priority menu if open
        if self.priority_dropdown and self.priority_dropdown.winfo_exists():
            self.priority_dropdown.destroy()
            self.priority_dropdown = None
        
        # Close calendar if already open
        if self.date_dropdown and self.date_dropdown.winfo_exists():
            self.date_dropdown.destroy()
            self.date_dropdown = None
            return

        # Determine colors based on current theme (Dark vs Light)
        is_dark = ctk.get_appearance_mode() == "Dark"
        cal_bg = "#2B2042" if is_dark else "white"  # Use a dark purple for dark mode
        cal_text = "white" if is_dark else "black"

        # Create the Calendar Popup
        self.date_dropdown = CalendarPopup(
            self.right_column, 
            on_select_callback=self.on_date_selected,
            fg_color=cal_bg,
            text_color=cal_text
        )
        
        # Position it smartly
        # Note: You might need to adjust y=520 depending on your layout height
        self.date_dropdown.place(x=-20, y=320) 

    def on_date_selected(self, date_str):
        """Callback when a date is clicked on the calendar"""
        self.select_date(date_str, date_str) # Pass date_str as both value and display text
        
        # Close calendar
        if self.date_dropdown:
            self.date_dropdown.destroy()
            self.date_dropdown = None
        
    def on_date_selected(self, date_str):
        """Callback when a date is clicked on the calendar"""
        self.select_date(date_str, date_str) # Pass date_str as both value and display text
        # Close calendar
        if self.date_dropdown:
            self.date_dropdown.destroy()
            self.date_dropdown = None
    
    def select_date(self, date_str, display_text):
        """Handle date selection"""
        self.selected_date = date_str
        if date_str:
            try:
                # Calendar returns YYYY-MM-DD, parse it for display
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                display = dt.strftime("%d/%m") # Show as DD/MM on the button
            except:
                display = display_text
            self.date_btn.configure(text=f"{display}▼")
        else:
            self.date_btn.configure(text="Date▼")
    
    def save_task(self):
        """Save the current task"""
        # 1. Get Inputs
        title = ""
        if hasattr(self, 'title_input'):
            title = self.title_input.get().strip()
            
        description = self.task_input.get("1.0", "end-1c").strip()
        
        if not title:
            tk.messagebox.showwarning("Missing Title", "The task title cannot be blank.")
            # Focus the title entry so they can type immediately
            self.title_input.focus()
            return # STOP here, do not save
            
        # Check if a specific date was chosen (stored in self.selected_date)
        if not self.selected_date:
            tk.messagebox.showwarning("Missing Date", "You must choose a due date.")
            return # STOP here, do not save

        # If we passed both checks, proceed to save
        deadline = self.selected_date
        priority = self.priority_var.get()
        
        if self.editing_task_id:
            # Edit existing task
            task_manager.edit_task(
                self.editing_task_id,
                text=title,
                description=description,
                deadline=deadline,
                priority=priority
            )
        else:
            # Add new task
            task_manager.add_task(
                text=title, 
                description=description,
                deadline=deadline, 
                priority=priority
            )
        
        # Close panel and refresh
        self.hide_add_panel()
        self.update_task_display()
    
    def cancel_edit(self):
        """Cancel editing and close panel"""
        self.hide_add_panel()
    
    def clear_input(self):
        """Clear input fields"""
        if hasattr(self, 'title_input'):
            self.title_input.delete(0, "end")
        if hasattr(self, 'task_input'):
            self.task_input.delete("1.0", "end")
        self.selected_date = None
        if hasattr(self, 'date_btn'):
            self.date_btn.configure(text="Date▼")
        self.priority_var.set("normal")
        if hasattr(self, 'priority_btn'):
            self.priority_btn.configure(text="Priority▼")
    
    def update_task_display(self):
        """Update the task list display"""
        # Clear existing tasks
        for widget in self.tasks_container.winfo_children():
            widget.destroy()
        
        tasks = task_manager.tasks
        
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
        
        # Add "+" button at the end
        self.create_add_button()
    
    def create_add_button(self):
        """Create the add new task button"""
        add_card = ctk.CTkFrame(
            self.tasks_container,
            fg_color=self.colors['add_btn_bg'],
            corner_radius=20,
            height=80
        )
        add_card.pack(fill="x", pady=8, padx=5)
        add_card.pack_propagate(False)
        
        add_btn = ctk.CTkButton(
            add_card,
            text="+",
            command=self.show_add_panel,
            fg_color="transparent",
            hover_color="#D0C8D8",
            text_color=self.colors['text_dark'],
            font=ctk.CTkFont(size=36, weight="bold")
        )
        add_btn.pack(expand=True)
    
    def create_task_card(self, task, today):
        """Create a task card widget"""
        is_done = task.get("done", False)
        priority = task.get("priority", "normal")
        
        # Task card frame
        card = ctk.CTkFrame(
            self.tasks_container,
            fg_color=self.colors['task_bg'],
            corner_radius=20,
            height=80
        )
        card.pack(fill="x", pady=8, padx=5)
        card.pack_propagate(False)
        
        # Checkbox (Kept separate so clicking it doesn't open edit)
        checkbox_text = ctk.StringVar(value="off")
        checkbox = ctk.CTkCheckBox(
            card,
            text="",
            variable=checkbox_text,
            onvalue="on",
            offvalue="off",
            width=40,
            height=40,
            hover_color="#D0C8D8",
            text_color=self.colors['text_dark'],
        )
        checkbox.pack(side="left", padx=15, pady=20)
        
        # Clickable Info Container
        # We wrap the text info in a frame that detects clicks
        info_frame = ctk.CTkButton(
            card, 
            fg_color="transparent", 
            hover_color=self.colors['add_btn_bg'], # Subtle hover effect
            text="", 
            command=lambda t=task: self.load_task_details(t)
        )
        info_frame.pack(side="left", fill="both", expand=True, pady=5, padx=5)
        info_frame.destroy() # Remove the button attempt
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=10)
        
        # Bind click to open details
        info_frame.bind("<Button-1>", lambda e, t=task: self.load_task_details(t))
        
        # Task text
        task_label = ctk.CTkLabel(
            info_frame,
            text=task["text"][:40] + "..." if len(task["text"]) > 40 else task["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.colors['text_dark'],
            anchor="w"
        )
        task_label.pack(anchor="w", pady=(0, 5))
        
        # Bind label too so clicking text works
        task_label.bind("<Button-1>", lambda e, t=task: self.load_task_details(t))
        
        # Details Row
        details_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        details_frame.pack(anchor="w")
        
        # Bind details frame
        details_frame.bind("<Button-1>", lambda e, t=task: self.load_task_details(t))

        # Date label
        if task.get("deadline") and task.get("deadline") != today:
            deadline = task["deadline"]
            try:
                dt = datetime.strptime(deadline, "%Y-%m-%d")
                date_display = dt.strftime("%d/%m")
            except:
                date_display = deadline
            
            date_label = ctk.CTkLabel(
                details_frame,
                text=f"📅 {date_display}",
                font=ctk.CTkFont(size=11),
                text_color=self.colors['text_dark']
            )
            date_label.pack(side="left", padx=(0, 15))
            date_label.bind("<Button-1>", lambda e, t=task: self.load_task_details(t))

        # Priority badge
        if priority != "normal":
            prio_colors = {"high": "#FF5252", "low": "#4CAF50"}
            p_color = prio_colors.get(priority, "gray")
            
            priority_label = ctk.CTkLabel(
                details_frame,
                text=f"• {priority.capitalize()}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=p_color
            )
            priority_label.pack(side="left")
            priority_label.bind("<Button-1>", lambda e, t=task: self.load_task_details(t))

        # Note: Old delete button is removed.
    
    def load_task_details(self,task):
        """Load a task into the right panel for editing"""
        self.show_add_panel() # Ensure panel is visible
        
        self.is_editing = True
        self.editing_task_id = task["id"]
        
        # 1. Load Title
        self.title_input.delete(0, "end")
        self.title_input.insert(0, task["text"])
        
        # 2. Load Description (If your task_manager supports it, otherwise leave blank)
        self.task_input.delete("1.0", "end")
        if "description" in task:
            self.task_input.insert("1.0", task["description"])
            
        # 3. Load Date
        deadline = task.get("deadline")
        self.selected_date = deadline
        if deadline:
            try:
                dt = datetime.strptime(deadline, "%Y-%m-%d")
                display = dt.strftime("%d/%m")
            except:
                display = "Date"
            self.date_btn.configure(text=f"{display}▼")
        else:
            self.date_btn.configure(text="Date▼")

        # 4. Load Priority
        priority = task.get("priority", "normal")
        self.priority_var.set(priority)
        self.priority_btn.configure(text=f"{priority.capitalize()}▼")
        
        if hasattr(self, 'delete_btn'):
            self.delete_btn.pack(side="left", padx=5, pady=12)
    
    def toggle_task(self, task_id):
        """Toggle task completion"""
        task_manager.toggle_task(task_id)
        self.update_task_display()
    
    def delete_task(self, task_id):
        """Delete a task"""
        task_manager.delete_task(task_id)
        self.update_task_display()
    def delete_current_task(self):
        """Delete the task currently being edited"""
        if self.editing_task_id:
            task_manager.delete_task(self.editing_task_id)
            self.hide_add_panel()
            self.update_task_display()
    