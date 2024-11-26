import tkinter as tk
from tkinter import ttk, messagebox
import git
import os
from datetime import datetime
import re
from tkcalendar import DateEntry
import queue
import json

class GitEvent:
    def __init__(self):
        self.title = ""
        self.date = ""
        self.description = ""
        self.created_branch = ""
        self.merged_branches = []
        self.created_tag = ""
        self.notes = ""

class GitEventManager:
    def __init__(self):
        print("Initializing GUI...")
        self.root = tk.Tk()
        print("GUI initialized successfully")
        
        # 设置窗口标题
        self.root.title("Git Event Manager")
        print("Window title set successfully")
        
        # 初始化 Git 仓库
        self.repo = git.Repo(os.getcwd())
        print("Git repository initialized successfully")
        
        # 初始化操作计数
        self.operation_count = 0
        
        # 初始化变量
        self.base_type = tk.StringVar(value="branch")
        self.branch_prefix = tk.StringVar()
        self.branch_custom_suffix = tk.StringVar()
        self.branch_date_suffix = tk.StringVar(value=datetime.now().strftime('%Y.%m.%d'))
        self.final_branch_name = tk.StringVar()
        
        self.tag_prefix = tk.StringVar()
        self.tag_custom_suffix = tk.StringVar()
        self.tag_date_suffix = tk.StringVar(value=datetime.now().strftime('%Y.%m.%d'))
        self.final_tag_name = tk.StringVar()
        
        self.event_title = tk.StringVar()
        self.event_description = tk.StringVar()
        self.event_notes = tk.StringVar()
        
        self.merge_vars = {'branch': {}, 'tag': {}}
        self.events = []
        
        # 创建日志和状态文本框
        self.create_log_widgets()
        
        print("Starting UI setup...")
        self.setup_ui()
        print("UI setup completed")

    def create_log_widgets(self):
        """创建日志和状态文本框"""
        # 创建临时窗口来持有日志组件
        temp_window = ttk.Frame(self.root)
        
        # 创建日志文本框
        self.log_text = tk.Text(temp_window, height=6, wrap=tk.WORD)
        self.log_text.configure(state='disabled')
        
        # 创建状态文本框
        self.status_text = tk.Text(temp_window, height=3, wrap=tk.WORD)
        self.status_text.configure(state='disabled')

    def update_current_branch_labels(self):
        """更新所有显示当前分支的标签"""
        try:
            current = self.repo.active_branch.name
            branch_text = f"{current}"
            
            if hasattr(self, 'current_branch_label'):
                self.current_branch_label.config(text=branch_text)
            
            if hasattr(self, 'tag_branch_label'):
                self.tag_branch_label.config(text=branch_text)
            
        except Exception as e:
            print(f"Error updating branch labels: {str(e)}")

    def refresh_branch_name(self):
        """手动刷新分支名称"""
        try:
            remote = self.repo.remote()
            self.log_operation("Fetching remote branches...")
            remote.fetch()
            self.update_branch_name(force_check=True)
            self.update_current_branch_labels()
            self.log_operation("Refreshed branch name")
            self.update_status("Branch name refreshed successfully")
        except Exception as e:
            error_msg = str(e)
            self.log_operation(f"Error refreshing branch name: {error_msg}")
            self.update_status("Failed to refresh branch name", success=False)

    def refresh_merge_items(self):
        """手动刷新合并项目列表"""
        try:
            remote = self.repo.remote()
            self.log_operation("Fetching remote branches and tags...")
            remote.fetch()
            self.repo.git.fetch('--tags')
            
            self.update_current_branch_labels()
            
            # 清空现有的复选框
            for widget in self.merge_inner_frame.winfo_children():
                widget.destroy()
            
            # 获取当前分支
            current = self.repo.active_branch.name
            
            # 获取所有本地分支
            local_branches = [branch.name for branch in self.repo.heads if branch.name != current]
            
            # 获取所程分支
            remote_branches = []
            for ref in remote.refs:
                if ref.name == f"{remote.name}/HEAD":
                    continue
                branch_name = ref.name.split('/', 1)[1]
                if branch_name not in local_branches and branch_name != current:
                    remote_branches.append(branch_name)
            
            # 合并本地和远程分支列表
            all_branches = sorted(set(local_branches + remote_branches))
            
            # 获取所有标签
            tags = [tag.name for tag in self.repo.tags]
            
            # 重新创建复选框
            row = 0
            if all_branches:
                ttk.Label(self.merge_inner_frame, text="Branches:").grid(
                    row=row, column=0, sticky='w', padx=5, pady=2)
                row += 1
                for branch in all_branches:
                    self.merge_vars['branch'][branch] = tk.BooleanVar()
                    display_name = f"{branch} (remote)" if branch in remote_branches else branch
                    ttk.Checkbutton(self.merge_inner_frame, text=display_name, 
                                  variable=self.merge_vars['branch'][branch]).grid(
                        row=row, column=0, sticky='w', padx=20, pady=2)
                    row += 1
            
            if tags:
                ttk.Label(self.merge_inner_frame, text="Tags:").grid(
                    row=row, column=0, sticky='w', padx=5, pady=2)
                row += 1
                for tag in sorted(tags):
                    self.merge_vars['tag'][tag] = tk.BooleanVar()
                    ttk.Checkbutton(self.merge_inner_frame, text=tag, 
                                  variable=self.merge_vars['tag'][tag]).grid(
                        row=row, column=0, sticky='w', padx=20, pady=2)
                    row += 1
            
            # 更新画布滚动区域
            self.merge_inner_frame.update_idletasks()
            self.merge_canvas.configure(scrollregion=self.merge_canvas.bbox('all'))
            
            self.log_operation("Refreshed merge items list")
            self.update_status("Merge items list refreshed successfully")
            
        except Exception as e:
            error_msg = str(e)
            self.log_operation(f"Error refreshing merge items: {error_msg}")
            self.update_status(f"Failed to refresh merge items: {error_msg}", success=False)
    def refresh_tag_name(self):
        """手动刷新签名称"""
        try:
            self.log_operation("Fetching remote tags...")
            self.repo.git.fetch('--tags')
            self.update_tag_name(force_check=True)
            self.update_current_branch_labels()
            self.log_operation("Refreshed tag name")
            self.update_status("Tag name refreshed successfully")
        except Exception as e:
            error_msg = str(e)
            self.log_operation(f"Error refreshing tag name: {error_msg}")
            self.update_status("Failed to refresh tag name", success=False)

    def update_branch_name(self, event=None, force_check=False):
        """更新最终分支名称"""
        try:
            prefix = self.branch_prefix.get()
            custom = self.branch_custom_suffix.get()
            date = self.branch_date_suffix.get()
            
            # 构建基础分支名称
            if prefix == 'custom':
                if not custom:
                    self.final_branch_name.set('')
                    return
                base_name = custom
            else:
                base_name = f"{prefix}_{date}"
                if custom:
                    base_name = f"{base_name}_{custom}"
            
            # 如果是强制检查，重新获取信息
            if force_check:
                self.repo.remote().fetch()
            
            # 获取所有分支（包括远程分支）
            all_branches = [branch.name for branch in self.repo.heads]
            remote_branches = [ref.name.split('/')[-1] for ref in self.repo.remote().refs 
                             if not ref.name.endswith('/HEAD')]
            existing_branches = list(set(all_branches + remote_branches))
            
            # 如果名称已存在，添加数字后缀
            if base_name in existing_branches:
                # 查找所有相似的分支名
                pattern = re.compile(f"^{re.escape(base_name)}(\\.\\d+)?$")
                similar_branches = [b for b in existing_branches if pattern.match(b)]
                
                if similar_branches:
                    # 找出最大的编号
                    max_number = 0
                    for branch in similar_branches:
                        if branch == base_name:
                            max_number = max(max_number, 0)
                        else:
                            try:
                                suffix = branch.split('.')[-1]
                                if suffix.isdigit():
                                    max_number = max(max_number, int(suffix))
                            except (IndexError, ValueError):
                                continue
                    
                    # 使用下一个编号
                    final_name = f"{base_name}.{max_number + 1}"
                else:
                    final_name = f"{base_name}.1"
            else:
                final_name = base_name
            
            self.final_branch_name.set(final_name)
            
        except Exception as e:
            print(f"Error updating branch name: {str(e)}")
            self.final_branch_name.set('')

    def update_tag_name(self, event=None, force_check=False):
        """更新最终标签名称"""
        try:
            prefix = self.tag_prefix.get()
            custom = self.tag_custom_suffix.get()
            date = self.tag_date_suffix.get()
            
            # 构建基础标签名称
            if prefix == 'custom':
                if not custom:
                    self.final_tag_name.set('')
                    return
                base_name = custom
            else:
                base_name = f"{prefix}_{date}"
                if custom:
                    base_name = f"{base_name}_{custom}"
            
            # 如果是强制检查，重新获取远程信息
            if force_check:
                self.repo.git.fetch('--tags')
            
            # 获取所有标签
            existing_tags = [tag.name for tag in self.repo.tags]
            
            # 如果名称已存在，添加数字后缀
            if base_name in existing_tags:
                # 查找所有相似的标签名
                pattern = re.compile(f"^{re.escape(base_name)}(\\.\\d+)?$")
                similar_tags = [t for t in existing_tags if pattern.match(t)]
                
                if similar_tags:
                    # 找出最大的编号
                    max_number = 0
                    for tag in similar_tags:
                        if tag == base_name:
                            max_number = max(max_number, 0)
                        else:
                            try:
                                suffix = tag.split('.')[-1]
                                if suffix.isdigit():
                                    max_number = max(max_number, int(suffix))
                            except (IndexError, ValueError):
                                continue
                    
                    # 使用下一个编号
                    final_name = f"{base_name}.{max_number + 1}"
                else:
                    final_name = f"{base_name}.1"
            else:
                final_name = base_name
            
            self.final_tag_name.set(final_name)
            
        except Exception as e:
            print(f"Error updating tag name: {str(e)}")
            self.final_tag_name.set('')

    def log_operation(self, message, details=""):
        """记录操作日志"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"[{timestamp}] {message}\n"
            if details:
                log_message += f"Details:\n{details}\n"
            
            # 启用文本框编辑
            self.log_text.configure(state='normal')
            
            # 插入日志消息
            self.log_text.insert(tk.END, log_message)
            
            # 滚动到底部
            self.log_text.see(tk.END)
            
            # 禁用文本框编辑
            self.log_text.configure(state='disabled')
            
        except Exception as e:
            print(f"Error logging operation: {str(e)}")

    def update_status(self, message, success=True):
        """更新状态栏"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            status_message = f"[{timestamp}] {'✓' if success else '✗'} Step {self.operation_count + 1}\n"
            status_message += f"{message}\n"
            status_message += "-" * 30 + "\n"
            
            # 启用文本框编辑
            self.status_text.configure(state='normal')
            
            # 插入状态消息
            self.status_text.insert(tk.END, status_message)
            
            # 滚动到底部
            self.status_text.see(tk.END)
            
            # 禁用文本框编辑
            self.status_text.configure(state='disabled')
            
            # 增加操作计数
            self.operation_count += 1
            
        except Exception as e:
            print(f"Error updating status: {str(e)}")
    def setup_ui(self):
        """设置用户界面"""
        # 1. 设置主窗口
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        
        # 2. 创建左右分割的主局
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # 3. 创建左侧面板（带滚动条）
        left_panel = self.create_left_panel(main_paned)
        
        # 4. 创建右侧面板（日志和状态）
        right_panel = self.create_right_panel(main_paned)
        
        # 5. 将左右面板添加到主分割窗口
        main_paned.add(left_panel)
        main_paned.add(right_panel)
        
        # 6. 设置分割位置（左侧70%，右侧30%）
        self.root.update()
        main_paned.sashpos(0, int(self.root.winfo_width() * 0.7))

    def create_left_panel(self, parent):
        """创建左侧面板"""
        # 1. 创建左侧容器
        left_container = ttk.Frame(parent)
        
        # 2. 创建画布和滚动条
        canvas = tk.Canvas(left_container)
        scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
        
        # 3. 创建滚动框架
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # 4. 在画布上创建窗口
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 5. 创建事件信息区域
        self.create_event_info_section(scrollable_frame)
        
        # 6. 创建Git操作区域
        self.create_git_operations_section(scrollable_frame)
        
        # 7. 创建工具栏
        self.create_toolbar(scrollable_frame)
        
        # 8. 布局画布和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 9. 绑定鼠标滚轮
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        return left_container

    def create_right_panel(self, parent):
        """创建右侧面板"""
        right_frame = ttk.Frame(parent)
        
        # 1. 创建状态区域
        status_frame = ttk.LabelFrame(right_frame, text="Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_text.master = status_frame
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        status_scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        # 2. 创建日志区域
        log_frame = ttk.LabelFrame(right_frame, text="Operation Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text.master = log_frame
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        return right_frame

    def create_event_info_section(self, parent):
        """创建事件信息区域"""
        frame = ttk.LabelFrame(parent, text="Event Information")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 事件标题
        ttk.Label(frame, text="Event Title:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.event_title).grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # 事件描述
        ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.event_description).grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # 事件备注
        ttk.Label(frame, text="Notes:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.event_notes).grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        frame.grid_columnconfigure(1, weight=1)

    def create_git_operations_section(self, parent):
        """创建Git操作区域"""
        frame = ttk.LabelFrame(parent, text="Git Operations")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 1. Branch Creation
        self.create_branch_section(frame)
        
        # 2. Merge Configuration
        self.create_merge_section(frame)
        
        # 3. Tag Creation
        self.create_tag_section(frame)

    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        save_event_btn = ttk.Button(toolbar, text="Save Event", command=self.save_current_event)
        save_event_btn.pack(side=tk.RIGHT, padx=5)
        
        history_btn = ttk.Button(toolbar, text="View History", command=self.show_event_history)
        history_btn.pack(side=tk.RIGHT, padx=5)

    def update_base_items(self):
        """更新基础项目列表"""
        try:
            # 获取远程仓库信息
            remote = self.repo.remote()
            remote.fetch()  # 获取最新的远程信息
            
            base_type = self.base_type.get()
            current = self.repo.active_branch.name
            
            if base_type == "branch":
                # 获取所有本地分支
                local_branches = [branch.name for branch in self.repo.heads if branch.name != current]
                
                # 获取所有远程分支
                remote_branches = []
                for ref in remote.refs:
                    if ref.name == f"{remote.name}/HEAD":
                        continue
                    branch_name = ref.name.split('/', 1)[1]
                    if branch_name not in local_branches and branch_name != current:
                        remote_branches.append(f"{branch_name} (remote)")
                
                # 合并本地和远程分支列表
                items = sorted(set(local_branches + remote_branches))
                
            else:  # tag
                # 获取所有标签
                items = sorted([tag.name for tag in self.repo.tags])
            
            # 更新下拉列表
            self.base_items_combo['values'] = items
            if items:
                self.base_items_combo.set(items[0])
                self.branch_prefix.set(items[0].split(' (remote)')[0])  # 移除可能的 (remote) 后缀
            else:
                self.base_items_combo.set('')
                self.branch_prefix.set('')
            
            self.log_operation(f"Updated base items list with {len(items)} items")
            self.update_branch_name()  # 更新最终分支名称
            
        except Exception as e:
            error_msg = str(e)
            self.log_operation(f"Error updating base items: {error_msg}")
            self.update_status(f"Failed to update base items: {error_msg}", success=False)

    def create_branch(self):
        """创建新分支"""
        try:
            # 获取新分支名称
            new_branch_name = self.final_branch_name.get()
            if not new_branch_name:
                messagebox.showerror("Error", "Branch name cannot be empty")
                return
            
            # 获取基础项目
            base_item = self.base_items_combo.get()
            if not base_item:
                messagebox.showerror("Error", "Please select a base item")
                return
            
            # 获取基础类型
            base_type = self.base_type.get()
            
            # 记录操作
            self.log_operation(f"Creating new branch: {new_branch_name}", 
                             f"Base {base_type}: {base_item}")
            
            # 切换到基础项目
            if base_type == "branch":
                self.repo.git.checkout(base_item)
            else:
                self.repo.git.checkout(base_item)
            
            # 创建新分支
            self.repo.git.checkout('-b', new_branch_name)
            
            # 更新状态
            self.update_status(f"Created new branch: {new_branch_name}")
            
            # 更新基础项目列表
            self.update_base_items()
            
            # 更新当前分支显示
            self.update_current_branch_labels()
            
            # 显示成功消息
            messagebox.showinfo("Success", f"Branch '{new_branch_name}' created successfully")
            
        except Exception as e:
            error_msg = str(e)
            self.log_operation(f"Error creating branch: {error_msg}")
            self.update_status(f"Failed to create branch: {error_msg}", success=False)
            messagebox.showerror("Error", f"Failed to create branch: {error_msg}")

    def merge_branches(self):
        """合并选中的分支和标签"""
        try:
            # 获取选中的分支和标签
            selected_branches = [branch for branch, var in self.merge_vars['branch'].items() 
                               if var.get()]
            selected_tags = [tag for tag, var in self.merge_vars['tag'].items() 
                           if var.get()]
            
            if not selected_branches and not selected_tags:
                messagebox.showwarning("Warning", "Please select at least one branch or tag")
                return
            
            # 记录操作
            self.log_operation("Starting merge operation", 
                             f"Selected branches: {selected_branches}\n"
                             f"Selected tags: {selected_tags}")
            
            # 合并分支
            for branch in selected_branches:
                try:
                    self.log_operation(f"Merging branch: {branch}")
                    self.repo.git.merge(branch, '--no-ff')
                    self.update_status(f"Merged branch: {branch}")
                except Exception as e:
                    error_msg = str(e)
                    self.log_operation(f"Error merging branch {branch}: {error_msg}")
                    self.update_status(f"Failed to merge branch {branch}", success=False)
                    if messagebox.askyesno("Error", 
                                         f"Failed to merge branch {branch}. Continue with remaining items?"):
                        self.repo.git.merge('--abort')
                        continue
                    else:
                        self.repo.git.merge('--abort')
                        return
            
            # 合并标签
            for tag in selected_tags:
                try:
                    self.log_operation(f"Merging tag: {tag}")
                    self.repo.git.merge(tag, '--no-ff')
                    self.update_status(f"Merged tag: {tag}")
                except Exception as e:
                    error_msg = str(e)
                    self.log_operation(f"Error merging tag {tag}: {error_msg}")
                    self.update_status(f"Failed to merge tag {tag}", success=False)
                    if messagebox.askyesno("Error", 
                                         f"Failed to merge tag {tag}. Continue with remaining items?"):
                        self.repo.git.merge('--abort')
                        continue
                    else:
                        self.repo.git.merge('--abort')
                        return
            
            # 刷新合并项目列表
            self.refresh_merge_items()
            
            # 显示成功消息
            messagebox.showinfo("Success", "Merge operation completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            self.log_operation(f"Error during merge operation: {error_msg}")
            self.update_status("Merge operation failed", success=False)
            messagebox.showerror("Error", f"Merge operation failed: {error_msg}")

    def create_tag(self):
        """创建新标签"""
        try:
            # 获取新标签名称
            new_tag_name = self.final_tag_name.get()
            if not new_tag_name:
                messagebox.showerror("Error", "Tag name cannot be empty")
                return
            
            # 记录操作
            self.log_operation(f"Creating new tag: {new_tag_name}")
            
            # 创建新标签
            self.repo.create_tag(new_tag_name)
            
            # 推送标签到程
            self.repo.remote().push(new_tag_name)
            
            # 更新状态
            self.update_status(f"Created new tag: {new_tag_name}")
            
            # 刷新合并项目列表
            self.refresh_merge_items()
            
            # 显示成功消息
            messagebox.showinfo("Success", f"Tag '{new_tag_name}' created successfully")
            
        except Exception as e:
            error_msg = str(e)
            self.log_operation(f"Error creating tag: {error_msg}")
            self.update_status(f"Failed to create tag: {error_msg}", success=False)
            messagebox.showerror("Error", f"Failed to create tag: {error_msg}")

    def run(self):
        """运行应用程序"""
        self.root.mainloop()

    def save_current_event(self):
        """保存当前事件"""
        if not self.event_title.get():
            messagebox.showwarning("Warning", "Please enter an event title")
            return
        
        event = GitEvent()
        event.title = self.event_title.get()
        event.date = datetime.now().strftime('%Y年%m月%d日')
        event.description = self.event_description.get()
        event.created_branch = self.final_branch_name.get()
        event.merged_branches = [branch for branch, var in self.merge_vars['branch'].items() 
                               if var.get()]
        event.created_tag = self.final_tag_name.get()
        event.notes = self.event_notes.get()
        
        self.events.append(event)
        self.save_events_to_file()
        
        # 显示成功消息
        messagebox.showinfo("Success", "Event saved successfully")
        
        # 清空输入框
        self.event_title.set("")
        self.event_description.set("")
        self.event_notes.set("")
        
    def save_events_to_file(self):
        """将事件保存到文件"""
        events_data = []
        for event in self.events:
            event_dict = {
                'title': event.title,
                'date': event.date,
                'description': event.description,
                'created_branch': event.created_branch,
                'merged_branches': event.merged_branches,
                'created_tag': event.created_tag,
                'notes': event.notes
            }
            events_data.append(event_dict)
            
        with open('git_events.json', 'w', encoding='utf-8') as f:
            json.dump(events_data, f, ensure_ascii=False, indent=2)
            
    def load_events_from_file(self):
        """从文件加载事件"""
        try:
            with open('git_events.json', 'r', encoding='utf-8') as f:
                events_data = json.load(f)
                
            self.events = []
            for event_dict in events_data:
                event = GitEvent()
                event.title = event_dict['title']
                event.date = event_dict['date']
                event.description = event_dict['description']
                event.created_branch = event_dict['created_branch']
                event.merged_branches = event_dict['merged_branches']
                event.created_tag = event_dict['created_tag']
                event.notes = event_dict['notes']
                self.events.append(event)
        except FileNotFoundError:
            pass
            
    def show_event_history(self):
        """显示事件历史"""
        history_window = tk.Toplevel(self.root)
        history_window.title("Event History")
        
        # 创建树形视图
        tree = ttk.Treeview(history_window, columns=('Date', 'Branch', 'Tag', 'Description'), show='headings')
        tree.heading('Date', text='Date')
        tree.heading('Branch', text='Created Branch')
        tree.heading('Tag', text='Created Tag')
        tree.heading('Description', text='Description')
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 填充数据
        for event in self.events:
            tree.insert('', 'end', values=(
                event.date,
                event.created_branch,
                event.created_tag,
                event.description
            ))
            
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        history_btn = ttk.Button(toolbar, text="View History", command=self.show_event_history)
        history_btn.pack(side=tk.RIGHT, padx=5)

    def on_base_item_selected(self, event):
        """当选择基础项目时的处理"""
        selected_item = self.base_items_combo.get()
        if selected_item:
            # 移除可能的 (remote) 后缀
            base_name = selected_item.split(' (remote)')[0]
            self.branch_prefix.set(base_name)
            self.update_branch_name()
            self.log_operation(f"Selected base item: {selected_item}")

    def create_branch_section(self, parent):
        """创建分支操作区域"""
        branch_frame = ttk.LabelFrame(parent, text="1. Create New Branch")
        branch_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 基础分支/标签选择
        base_type_frame = ttk.Frame(branch_frame)
        base_type_frame.grid(row=0, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
        ttk.Label(base_type_frame, text="Base Type:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(base_type_frame, text="Branch", variable=self.base_type, 
                       value="branch", command=self.update_base_items).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(base_type_frame, text="Tag", variable=self.base_type, 
                       value="tag", command=self.update_base_items).pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_branch_btn = ttk.Button(base_type_frame, text="↻", width=3, 
                                      command=lambda: [self.refresh_branch_name(), self.update_base_items()])
        refresh_branch_btn.pack(side=tk.RIGHT, padx=5)
        
        # 基础项目选择
        ttk.Label(branch_frame, text="Base Item:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.base_items_combo = ttk.Combobox(branch_frame, state='readonly')
        self.base_items_combo.grid(row=1, column=1, columnspan=3, sticky='ew', padx=5, pady=5)
        self.base_items_combo.bind('<<ComboboxSelected>>', self.on_base_item_selected)
        
        # 分支前缀
        ttk.Label(branch_frame, text="Branch Prefix:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(branch_frame, textvariable=self.branch_prefix).grid(
            row=2, column=1, columnspan=3, sticky='ew', padx=5, pady=5)
        
        # 自定义后缀
        ttk.Label(branch_frame, text="Custom Suffix:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(branch_frame, textvariable=self.branch_custom_suffix).grid(
            row=3, column=1, columnspan=3, sticky='ew', padx=5, pady=5)
        
        # 日期选择
        ttk.Label(branch_frame, text="Date:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(branch_frame, textvariable=self.branch_date_suffix).grid(
            row=4, column=1, columnspan=3, sticky='ew', padx=5, pady=5)
        
        # 最终分支名称
        ttk.Label(branch_frame, text="Final Name:").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(branch_frame, textvariable=self.final_branch_name, 
                 state='readonly').grid(row=5, column=1, columnspan=3, sticky='ew', padx=5, pady=5)
        
        # 创建分支按钮
        ttk.Button(branch_frame, text="Create Branch", 
                   command=self.create_branch).grid(row=6, column=0, 
                   columnspan=4, sticky='ew', padx=5, pady=5)
        
        # 配置网格列权重
        branch_frame.grid_columnconfigure(1, weight=1)

    def create_merge_section(self, parent):
        """创建合并操作区域"""
        merge_frame = ttk.LabelFrame(parent, text="2. Merge Branches/Tags")
        merge_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 当前分支信息
        current_branch_frame = ttk.Frame(merge_frame)
        current_branch_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(current_branch_frame, text="Current Branch:").pack(side=tk.LEFT, padx=(0,5))
        self.current_branch_label = ttk.Label(current_branch_frame, text="", 
                                            font=('TkDefaultFont', 9, 'bold'), 
                                            foreground='blue')
        self.current_branch_label.pack(side=tk.LEFT)
        
        # 刷新按钮
        refresh_merge_btn = ttk.Button(current_branch_frame, text="↻", width=3, 
                                     command=self.refresh_merge_items)
        refresh_merge_btn.pack(side=tk.RIGHT)
        
        # 创建可滚动的合并项目列表
        merge_scroll_frame = ttk.Frame(merge_frame)
        merge_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.merge_canvas = tk.Canvas(merge_scroll_frame, height=150)
        merge_scrollbar = ttk.Scrollbar(merge_scroll_frame, orient="vertical", 
                                      command=self.merge_canvas.yview)
        
        self.merge_inner_frame = ttk.Frame(self.merge_canvas)
        self.merge_inner_frame.bind(
            '<Configure>', 
            lambda e: self.merge_canvas.configure(scrollregion=self.merge_canvas.bbox("all"))
        )
        
        self.merge_canvas.create_window((0, 0), window=self.merge_inner_frame, anchor='nw')
        self.merge_canvas.configure(yscrollcommand=merge_scrollbar.set)
        
        self.merge_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        merge_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 合并按钮
        ttk.Button(merge_frame, text="Merge Selected", 
                   command=self.merge_branches).pack(fill=tk.X, padx=5, pady=5)

    def create_tag_section(self, parent):
        """创建标签操作区域"""
        tag_frame = ttk.LabelFrame(parent, text="3. Create Tag")
        tag_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 当前分支信息
        current_branch_frame = ttk.Frame(tag_frame)
        current_branch_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(current_branch_frame, text="Current Branch:").pack(side=tk.LEFT, padx=(0,5))
        self.tag_branch_label = ttk.Label(current_branch_frame, text="", 
                                        font=('TkDefaultFont', 9, 'bold'), 
                                        foreground='blue')
        self.tag_branch_label.pack(side=tk.LEFT)
        
        # 刷新按钮
        refresh_tag_btn = ttk.Button(current_branch_frame, text="↻", width=3, 
                                     command=self.refresh_tag_name)
        refresh_tag_btn.pack(side=tk.RIGHT)
        
        # 标签前缀
        ttk.Label(tag_frame, text="Tag Prefix:").pack(anchor='w', padx=5, pady=2)
        ttk.Entry(tag_frame, textvariable=self.tag_prefix).pack(fill=tk.X, padx=5, pady=2)
        
        # 自定义后缀
        ttk.Label(tag_frame, text="Custom Suffix:").pack(anchor='w', padx=5, pady=2)
        ttk.Entry(tag_frame, textvariable=self.tag_custom_suffix).pack(fill=tk.X, padx=5, pady=2)
        
        # 日期选择
        ttk.Label(tag_frame, text="Date:").pack(anchor='w', padx=5, pady=2)
        ttk.Entry(tag_frame, textvariable=self.tag_date_suffix).pack(fill=tk.X, padx=5, pady=2)
        
        # 最终标签名称
        ttk.Label(tag_frame, text="Final Name:").pack(anchor='w', padx=5, pady=2)
        ttk.Entry(tag_frame, textvariable=self.final_tag_name, 
                 state='readonly').pack(fill=tk.X, padx=5, pady=2)
        
        # 创建标签按钮
        ttk.Button(tag_frame, text="Create Tag", 
                   command=self.create_tag).pack(fill=tk.X, padx=5, pady=5)

if __name__ == "__main__":
    app = GitEventManager()
    app.run()            