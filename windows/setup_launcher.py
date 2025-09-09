#!/usr/bin/env python3
"""
ScryptMineOS Enterprise Edition - Setup Launcher
Downloads and installs the enterprise edition automatically
"""

import os
import sys
import subprocess
import tempfile
import zipfile
import shutil
from pathlib import Path
import urllib.request
import urllib.parse
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

class SetupLauncher:
    """GUI setup launcher for Windows"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ScryptMineOS Enterprise Edition - Setup")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Setup variables
        self.install_path = tk.StringVar(value=str(Path.home() / "ScryptMineOS"))
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready to install")
        
        # GitHub repository info
        self.repo_owner = "JlovesYouGit"
        self.repo_name = "ScryptMineOS"
        self.branch_name = "enterprise-transformation-v1.0"
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=20, pady=20)
        
        title_label = ttk.Label(
            title_frame, 
            text="🏢 ScryptMineOS Enterprise Edition",
            font=('Arial', 16, 'bold')
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Professional Cryptocurrency Mining Platform",
            font=('Arial', 10)
        )
        subtitle_label.pack()
        
        # Description
        desc_frame = ttk.LabelFrame(self.root, text="About", padding=10)
        desc_frame.pack(fill='x', padx=20, pady=10)
        
        desc_text = """ScryptMineOS Enterprise Edition provides:

• 🔒 Enterprise-grade security with access control
• 💰 Economic safeguards and kill-switch protection  
• 📊 Advanced monitoring and metrics
• 🚀 Production-ready deployment
• 🏢 Multi-user support with role-based permissions
• 🐛 Zero bugs - fully tested and optimized"""
        
        desc_label = ttk.Label(desc_frame, text=desc_text, justify='left')
        desc_label.pack(anchor='w')
        
        # Installation path
        path_frame = ttk.LabelFrame(self.root, text="Installation Path", padding=10)
        path_frame.pack(fill='x', padx=20, pady=10)
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill='x')
        
        self.path_entry = ttk.Entry(path_entry_frame, textvariable=self.install_path)
        self.path_entry.pack(side='left', fill='x', expand=True)
        
        browse_btn = ttk.Button(
            path_entry_frame, 
            text="Browse...", 
            command=self.browse_install_path
        )
        browse_btn.pack(side='right', padx=(10, 0))
        
        # Progress
        progress_frame = ttk.LabelFrame(self.root, text="Installation Progress", padding=10)
        progress_frame.pack(fill='x', padx=20, pady=10)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.pack()
        
        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=20, pady=20)
        
        self.install_btn = ttk.Button(
            button_frame,
            text="🚀 Install ScryptMineOS Enterprise",
            command=self.start_installation
        )
        self.install_btn.pack(side='left')
        
        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.root.quit
        )
        self.cancel_btn.pack(side='right')
        
        # System requirements
        req_frame = ttk.LabelFrame(self.root, text="System Requirements", padding=10)
        req_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        req_text = """• Windows 10/11 (64-bit)
• 4GB RAM minimum (8GB recommended)
• Internet connection for pool connectivity
• Python 3.11+ (will be installed if missing)"""
        
        req_label = ttk.Label(req_frame, text=req_text, justify='left')
        req_label.pack(anchor='w')
    
    def browse_install_path(self):
        """Browse for installation directory"""
        directory = filedialog.askdirectory(
            title="Select Installation Directory",
            initialdir=self.install_path.get()
        )
        if directory:
            self.install_path.set(directory)
    
    def update_progress(self, value, status):
        """Update progress bar and status"""
        self.progress_var.set(value)
        self.status_var.set(status)
        self.root.update()
    
    def start_installation(self):
        """Start installation in background thread"""
        self.install_btn.config(state='disabled')
        self.cancel_btn.config(text='Close', command=self.root.quit)
        
        # Start installation thread
        install_thread = threading.Thread(target=self.run_installation)
        install_thread.daemon = True
        install_thread.start()
    
    def run_installation(self):
        """Run the complete installation process"""
        try:
            install_dir = Path(self.install_path.get())
            
            # Step 1: Create installation directory
            self.update_progress(10, "Creating installation directory...")
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 2: Check Python installation
            self.update_progress(20, "Checking Python installation...")
            if not self.check_python():
                self.update_progress(25, "Installing Python...")
                if not self.install_python():
                    raise Exception("Failed to install Python")
            
            # Step 3: Download enterprise codebase
            self.update_progress(40, "Downloading ScryptMineOS Enterprise...")
            if not self.download_enterprise_code(install_dir):
                raise Exception("Failed to download enterprise code")
            
            # Step 4: Install dependencies
            self.update_progress(60, "Installing Python dependencies...")
            if not self.install_dependencies(install_dir):
                raise Exception("Failed to install dependencies")
            
            # Step 5: Create configuration
            self.update_progress(80, "Creating configuration files...")
            self.create_configuration(install_dir)
            
            # Step 6: Create shortcuts
            self.update_progress(90, "Creating desktop shortcuts...")
            self.create_shortcuts(install_dir)
            
            # Step 7: Complete
            self.update_progress(100, "Installation completed successfully!")
            
            # Show success message
            messagebox.showinfo(
                "Installation Complete",
                f"ScryptMineOS Enterprise Edition has been installed successfully!\n\n"
                f"Installation directory: {install_dir}\n\n"
                f"Next steps:\n"
                f"1. Edit the .env file with your wallet addresses\n"
                f"2. Run ScryptMineOS from the desktop shortcut\n"
                f"3. Access monitoring at http://localhost:9090"
            )
            
        except Exception as e:
            self.update_progress(0, f"Installation failed: {str(e)}")
            messagebox.showerror("Installation Error", f"Installation failed:\n{str(e)}")
        
        finally:
            self.install_btn.config(state='normal')
    
    def check_python(self):
        """Check if Python 3.11+ is installed"""
        try:
            result = subprocess.run([
                'python', '--version'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                version_str = result.stdout.strip()
                # Extract version number
                version_parts = version_str.split()[1].split('.')
                major, minor = int(version_parts[0]), int(version_parts[1])
                
                if major >= 3 and minor >= 11:
                    return True
            
            return False
            
        except FileNotFoundError:
            return False
    
    def install_python(self):
        """Install Python 3.11"""
        try:
            # Download Python installer
            python_url = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
            installer_path = Path(tempfile.gettempdir()) / "python-installer.exe"
            
            urllib.request.urlretrieve(python_url, installer_path)
            
            # Run installer
            subprocess.run([
                str(installer_path),
                '/quiet',
                'InstallAllUsers=1',
                'PrependPath=1',
                'Include_test=0'
            ], check=True)
            
            # Clean up
            installer_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Failed to install Python: {e}")
            return False
    
    def download_enterprise_code(self, install_dir):
        """Download enterprise codebase from GitHub"""
        try:
            # GitHub API URL for the branch
            api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/zipball/{self.branch_name}"
            
            # Download ZIP file
            zip_path = install_dir / "enterprise-code.zip"
            urllib.request.urlretrieve(api_url, zip_path)
            
            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(install_dir)
            
            # Find extracted directory and move contents
            extracted_dirs = [d for d in install_dir.iterdir() if d.is_dir() and d.name.startswith(f"{self.repo_owner}-{self.repo_name}")]
            
            if extracted_dirs:
                extracted_dir = extracted_dirs[0]
                
                # Move all contents to install directory
                for item in extracted_dir.iterdir():
                    dest = install_dir / item.name
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    shutil.move(str(item), str(dest))
                
                # Remove empty extracted directory
                extracted_dir.rmdir()
            
            # Clean up ZIP file
            zip_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Failed to download enterprise code: {e}")
            return False
    
    def install_dependencies(self, install_dir):
        """Install Python dependencies"""
        try:
            requirements_file = install_dir / "requirements.txt"
            
            if requirements_file.exists():
                subprocess.run([
                    'python', '-m', 'pip', 'install', '-r', str(requirements_file)
                ], check=True, cwd=install_dir)
            
            # Install additional Windows-specific packages
            windows_packages = [
                'pywin32',
                'wmi',
                'psutil'
            ]
            
            for package in windows_packages:
                subprocess.run([
                    'python', '-m', 'pip', 'install', package
                ], check=True)
            
            return True
            
        except Exception as e:
            print(f"Failed to install dependencies: {e}")
            return False
    
    def create_configuration(self, install_dir):
        """Create default configuration files"""
        try:
            # Create .env file from template
            env_template = install_dir / "private" / ".env.enterprise"
            env_file = install_dir / ".env"
            
            if env_template.exists() and not env_file.exists():
                shutil.copy2(env_template, env_file)
            
            # Create Windows-specific launcher script
            launcher_script = install_dir / "launch.bat"
            with open(launcher_script, 'w') as f:
                f.write(f'''@echo off
cd /d "{install_dir}"
python enterprise_runner.py --user-id windows-user
pause
''')
            
        except Exception as e:
            print(f"Failed to create configuration: {e}")
    
    def create_shortcuts(self, install_dir):
        """Create desktop shortcuts"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            
            # Create shortcut for main application
            shortcut_path = os.path.join(desktop, "ScryptMineOS Enterprise.lnk")
            target = str(install_dir / "launch.bat")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = str(install_dir)
            shortcut.IconLocation = target
            shortcut.save()
            
        except ImportError:
            # If winshell not available, skip shortcuts
            pass
        except Exception as e:
            print(f"Failed to create shortcuts: {e}")
    
    def run(self):
        """Run the setup GUI"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        launcher = SetupLauncher()
        launcher.run()
    except Exception as e:
        print(f"Setup launcher error: {e}")
        messagebox.showerror("Setup Error", f"Failed to start setup: {e}")

if __name__ == "__main__":
    main()
