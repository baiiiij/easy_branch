import tkinter as tk
from tkinter import ttk, messagebox
import git
from datetime import datetime
import json
import os
import sys

class GitEventManager:
    def __init__(self):
        print("Initializing GUI...")
        try:
            self.root = tk.Tk()
            print("GUI initialized successfully")
            
        except Exception as e:
            print(f"GUI initialization failed: {str(e)}")
            sys.exit(1)
        
        self.root.title("Git Event Manager")
        print("Window title set successfully")
        
        try:
            self.repo = git.Repo(os.getcwd())
            print("Git repository initialized successfully")
        except git.exc.InvalidGitRepositoryError:
            print("Git repository initialization failed - not a valid Git repository")
            messagebox.showerror("Error", "Current directory is not a Git repository!\nPlease run this program in a Git repository directory.")
            self.root.destroy()
            sys.exit(1)
            
        self.current_operations = []
        
        print("Starting UI setup...")
        self.setup_ui()
        print("UI setup completed")
        self.events = self.load_events()
        print("Events loaded successfully")

    def setup_ui(self):
        # Event information frame
        event_frame = ttk.LabelFrame(self.root, text="Event Information")
        event_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(event_frame, text="Event Title:").grid(row=0, column=0, padx=5, pady=5)
        self.event_title = ttk.Entry(event_frame)
        self.event_title.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(event_frame, text="Event Description:").grid(row=1, column=0, padx=5, pady=5)
        self.event_desc = tk.Text(event_frame, height=3)
        self.event_desc.grid(row=1, column=1, padx=5, pady=5)

        # Git operation frame
        git_frame = ttk.LabelFrame(self.root, text="Git Operations")
        git_frame.pack(padx=10, pady=5, fill="x")

        # Branch selection
        ttk.Label(git_frame, text="Select Base Branch:").grid(row=0, column=0, padx=5, pady=5)
        self.branch_var = tk.StringVar()
        self.branch_combo = ttk.Combobox(git_frame, textvariable=self.branch_var)
        self.branch_combo['values'] = self.get_branches()
        self.branch_combo.grid(row=0, column=1, padx=5, pady=5)

        # New branch creation
        ttk.Label(git_frame, text="New Branch Name:").grid(row=1, column=0, padx=5, pady=5)
        self.new_branch = ttk.Entry(git_frame)
        self.new_branch.grid(row=1, column=1, padx=5, pady=5)

        # Branch to merge selection
        ttk.Label(git_frame, text="Select Branches to Merge:").grid(row=2, column=0, padx=5, pady=5)
        self.merge_listbox = tk.Listbox(git_frame, selectmode=tk.MULTIPLE, height=4)
        self.merge_listbox.grid(row=2, column=1, padx=5, pady=5)
        for branch in self.get_branches():
            self.merge_listbox.insert(tk.END, branch)

        # Operation buttons
        button_frame = ttk.Frame(git_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Create Branch", command=self.create_branch).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Merge Branches", command=self.merge_branches).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Create Tag", command=self.create_tag).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Push", command=self.push_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Event", command=self.save_event).pack(side=tk.LEFT, padx=5)

    def get_branches(self):
        return [ref.name for ref in self.repo.refs]

    def create_branch(self):
        try:
            new_branch_name = self.new_branch.get()
            base_branch = self.branch_var.get()
            if new_branch_name and base_branch:
                base = self.repo.refs[base_branch]
                new_branch = self.repo.create_head(new_branch_name, base)
                new_branch.checkout()
                messagebox.showinfo("Success", f"Branch created and switched to: {new_branch_name}")
                self.log_operation(f"Created branch: {new_branch_name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def merge_branches(self):
        try:
            selected_indices = self.merge_listbox.curselection()
            for idx in selected_indices:
                branch_name = self.merge_listbox.get(idx)
                self.repo.git.merge(branch_name)
                self.log_operation(f"Merged branch: {branch_name}")
            messagebox.showinfo("Success", "Branch merge completed")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_tag(self):
        try:
            tag_name = f"tag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.repo.create_tag(tag_name)
            self.log_operation(f"Created Tag: {tag_name}")
            messagebox.showinfo("Success", f"Tag created: {tag_name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def push_changes(self):
        try:
            self.repo.git.push('origin', '--all')
            self.repo.git.push('origin', '--tags')
            self.log_operation("Pushed all changes to remote")
            messagebox.showinfo("Success", "All changes pushed to remote")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_events(self):
        try:
            with open('git_events.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_event(self):
        event = {
            'title': self.event_title.get(),
            'description': self.event_desc.get("1.0", tk.END).strip(),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'operations': self.current_operations
        }
        self.events.append(event)
        with open('git_events.json', 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Success", "Event saved")

    def log_operation(self, operation):
        if not hasattr(self, 'current_operations'):
            self.current_operations = []
        self.current_operations.append({
            'operation': operation,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    def run(self):
        print("Starting main loop...")
        self.root.mainloop()
        print("Main loop ended")  # If you see this message, the program exited normally 

if __name__ == "__main__":
    app = GitEventManager()
    app.run() 