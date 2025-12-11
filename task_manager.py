"""
Task Manager - Shared module for managing tasks with deadlines
Used by both To-Do List applet and Home page calendar
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_app_data_path():
    """Get the app data directory path"""
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


class TaskManager:
    """Manages tasks with persistence"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.tasks_file = get_app_data_path() / "tasks.json"
        self.tasks = self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from file"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_tasks(self):
        """Save tasks to file"""
        try:
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
    def add_task(self, text, description="", deadline=None, priority="normal"):
        """Add a new task
        
        Args:
            text: Task description
            deadline: Optional deadline date string (YYYY-MM-DD)
            priority: Task priority (low, normal, high)
        """
        task = {
            "id": len(self.tasks) + 1,
            "text": text,
            "description": description,
            "done": False,
            "deadline": deadline,
            "priority": priority,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.tasks.append(task)
        self.save_tasks()
        return task
    
    def toggle_task(self, task_id):
        """Toggle task completion status"""
        for task in self.tasks:
            if task["id"] == task_id:
                task["done"] = not task["done"]
                self.save_tasks()
                return True
        return False
    
    def delete_task(self, task_id):
        """Delete a task by ID"""
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save_tasks()
    
    def get_tasks_by_date(self, date_str):
        """Get all tasks for a specific date (YYYY-MM-DD)"""
        return [t for t in self.tasks if t.get("deadline") == date_str]
    
    def get_dates_with_tasks(self):
        """Get a set of dates that have tasks"""
        dates = set()
        for task in self.tasks:
            if task.get("deadline") and not task.get("done"):
                dates.add(task["deadline"])
        return dates
    
    def get_upcoming_tasks(self, limit=5):
        """Get upcoming tasks sorted by deadline"""
        today = datetime.now().strftime("%Y-%m-%d")
        upcoming = [
            t for t in self.tasks 
            if t.get("deadline") and t["deadline"] >= today and not t.get("done")
        ]
        upcoming.sort(key=lambda x: x["deadline"])
        return upcoming[:limit]
    
    def get_today_tasks(self):
        """Get tasks due today"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_tasks_by_date(today)
    
    def get_overdue_tasks(self):
        """Get overdue tasks"""
        today = datetime.now().strftime("%Y-%m-%d")
        return [
            t for t in self.tasks 
            if t.get("deadline") and t["deadline"] < today and not t.get("done")
        ]
    
    def get_all_pending_tasks(self):
        """Get all pending (not done) tasks"""
        return [t for t in self.tasks if not t.get("done")]
    
    def edit_task(self, task_id, text=None, description=None, deadline=None, priority=None):
        """Edit an existing task including description"""
        for task in self.tasks:
            if task["id"] == task_id:
                if text is not None:
                    task["text"] = text
                if description is not None:
                    task["description"] = description
                if deadline is not None:
                    task["deadline"] = deadline
                if priority is not None:
                    task["priority"] = priority
                self.save_tasks()
                return True
        return False
    
    def clear_completed(self):
        """Remove all completed tasks
        
        Returns:
            Number of tasks removed
        """
        original_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if not t.get("done")]
        removed_count = original_count - len(self.tasks)
        if removed_count > 0:
            self.save_tasks()
        return removed_count
    
    def search_tasks(self, query):
        """Search tasks by text
        
        Args:
            query: Search query string
        
        Returns:
            List of tasks matching the query
        """
        query = query.lower().strip()
        if not query:
            return self.tasks
        return [
            t for t in self.tasks 
            if query in t.get("text", "").lower() or query in t.get("description", "").lower()
        ]


# Global instance
task_manager = TaskManager()
