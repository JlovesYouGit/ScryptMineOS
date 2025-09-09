#!/usr/bin/env python3
"""
ScryptMineOS Enterprise Edition - Windows Launcher
Simple launcher for the enterprise mining system
"""

import os
import sys
import asyncio
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from pathlib import Path
import subprocess

class EnterpriseLauncher:
    """GUI launcher for ScryptMineOS Enterprise"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ScryptMineOS Enterprise Edition")
        self.root.geometry("800x600")
        
        # Variables
        self.mining_process = None
        self.is_mining = False
        
        self.setup_ui()
        self.check_configuration()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=20, pady=20)
        
        title_label = ttk.Label(
            title_frame,
            text="🏢 ScryptMineOS Enterprise Edition",
            font=('Arial', 18, 'bold')
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Professional Cryptocurrency Mining Platform",
            font=('Arial', 12)
        )
        subtitle_label.pack()
        
        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="System Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Ready to start mining")
        self.status_label.pack()
        
        # Configuration frame
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill='x', padx=20, pady=10)
        
        # Wallet addresses
        wallet_frame = ttk.Frame(config_frame)
        wallet_frame.pack(fill='x', pady=5)
        
        ttk.Label(wallet_frame, text="LTC Address:").pack(side='left')
        self.ltc_var = tk.StringVar()
        self.ltc_entry = ttk.Entry(wallet_frame, textvariable=self.ltc_var, width=50)
        self.ltc_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)
        
        wallet_frame2 = ttk.Frame(config_frame)
        wallet_frame2.pack(fill='x', pady=5)
        
        ttk.Label(wallet_frame2, text="DOGE Address:").pack(side='left')
        self.doge_var = tk.StringVar()
        self.doge_entry = ttk.Entry(wallet_frame2, textvariable=self.doge_var, width=50)
        self.doge_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)
        
        # Worker name
        worker_frame = ttk.Frame(config_frame)
        worker_frame.pack(fill='x', pady=5)
        
        ttk.Label(worker_frame, text="Worker Name:").pack(side='left')
        self.worker_var = tk.StringVar(value="windows-miner")
        self.worker_entry = ttk.Entry(worker_frame, textvariable=self.worker_var, width=20)
        self.worker_entry.pack(side='left', padx=(10, 0))
        
        # Save config button
        save_btn = ttk.Button(config_frame, text="Save Configuration", command=self.save_config)
        save_btn.pack(pady=10)
        
        # Control buttons
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=20, pady=20)
        
        self.start_btn = ttk.Button(
            control_frame,
            text="🚀 Start Mining",
            command=self.start_mining
        )
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = ttk.Button(
            control_frame,
            text="⏹️ Stop Mining",
            command=self.stop_mining,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=(0, 10))
        
        self.config_btn = ttk.Button(
            control_frame,
            text="⚙️ Open Config",
            command=self.open_config_file
        )
        self.config_btn.pack(side='left', padx=(0, 10))
        
        self.monitor_btn = ttk.Button(
            control_frame,
            text="📊 Open Monitoring",
            command=self.open_monitoring
        )
        self.monitor_btn.pack(side='left')
        
        # Log output
        log_frame = ttk.LabelFrame(self.root, text="Mining Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Clear log button
        clear_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_btn.pack(pady=(10, 0))
    
    def check_configuration(self):
        """Check if configuration exists and load it"""
        env_file = Path('.env')
        
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                
                # Parse basic configuration
                for line in content.split('\n'):
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'LTC_ADDRESS':
                            self.ltc_var.set(value)
                        elif key == 'DOGE_ADDRESS':
                            self.doge_var.set(value)
                        elif key == 'WORKER_NAME':
                            self.worker_var.set(value)
                
                self.log("✅ Configuration loaded from .env file")
                
            except Exception as e:
                self.log(f"⚠️ Error loading configuration: {e}")
        else:
            self.log("⚠️ No .env file found. Please configure your wallet addresses.")
    
    def save_config(self):
        """Save configuration to .env file"""
        try:
            env_content = f"""# ScryptMineOS Enterprise Edition - Windows Configuration
# Edit these values with your actual wallet addresses

# ===========================================
# USER WALLET ADDRESSES (REQUIRED)
# ===========================================
LTC_ADDRESS={self.ltc_var.get()}
DOGE_ADDRESS={self.doge_var.get()}
WORKER_NAME={self.worker_var.get()}

# ===========================================
# POOL CONFIGURATION (DEFAULT)
# ===========================================
LTC_POOL_HOST=ltc.f2pool.com
LTC_POOL_PORT=8888
DOGE_POOL_HOST=doge.zsolo.bid
DOGE_POOL_PORT=8057

# ===========================================
# WINDOWS MINING SETTINGS
# ===========================================
TARGET_HASHRATE=5000.0
POWER_LIMIT=200.0
MAX_POWER_COST=0.15
MIN_PROFITABILITY=0.01

# ===========================================
# MONITORING (WINDOWS)
# ===========================================
API_PORT=8080
METRICS_PORT=9090
HEALTH_CHECK_PORT=8081
METRICS_ENABLED=true

# ===========================================
# ENVIRONMENT
# ===========================================
ENVIRONMENT=windows
DEBUG=false
LOG_LEVEL=INFO
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            self.log("✅ Configuration saved to .env file")
            messagebox.showinfo("Configuration Saved", "Configuration has been saved successfully!")
            
        except Exception as e:
            self.log(f"❌ Error saving configuration: {e}")
            messagebox.showerror("Save Error", f"Failed to save configuration:\n{e}")
    
    def start_mining(self):
        """Start the mining process"""
        if self.is_mining:
            return
        
        # Validate configuration
        if not self.ltc_var.get() or not self.doge_var.get():
            messagebox.showerror(
                "Configuration Error",
                "Please configure your LTC and DOGE wallet addresses before starting mining."
            )
            return
        
        # Save configuration first
        self.save_config()
        
        try:
            self.log("🚀 Starting ScryptMineOS Enterprise Edition...")
            
            # Start mining process
            self.mining_process = subprocess.Popen([
                sys.executable, 'enterprise_runner.py',
                '--user-id', 'windows-user'
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
               universal_newlines=True, bufsize=1)
            
            self.is_mining = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text="Mining in progress...")
            
            # Start log monitoring thread
            log_thread = threading.Thread(target=self.monitor_mining_log)
            log_thread.daemon = True
            log_thread.start()
            
        except Exception as e:
            self.log(f"❌ Error starting mining: {e}")
            messagebox.showerror("Mining Error", f"Failed to start mining:\n{e}")
    
    def stop_mining(self):
        """Stop the mining process"""
        if not self.is_mining:
            return
        
        try:
            self.log("⏹️ Stopping mining...")
            
            if self.mining_process:
                self.mining_process.terminate()
                self.mining_process.wait(timeout=10)
            
            self.is_mining = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.status_label.config(text="Mining stopped")
            
            self.log("✅ Mining stopped successfully")
            
        except Exception as e:
            self.log(f"❌ Error stopping mining: {e}")
    
    def monitor_mining_log(self):
        """Monitor mining process output"""
        try:
            while self.is_mining and self.mining_process:
                output = self.mining_process.stdout.readline()
                if output:
                    self.log(output.strip())
                elif self.mining_process.poll() is not None:
                    break
            
            # Process ended
            if self.is_mining:
                self.log("⚠️ Mining process ended unexpectedly")
                self.root.after(0, self.stop_mining)
                
        except Exception as e:
            self.log(f"❌ Error monitoring mining log: {e}")
    
    def open_config_file(self):
        """Open configuration file in default editor"""
        try:
            env_file = Path('.env')
            if env_file.exists():
                os.startfile(str(env_file))
            else:
                messagebox.showwarning("File Not Found", "Configuration file .env not found. Please save configuration first.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open configuration file:\n{e}")
    
    def open_monitoring(self):
        """Open monitoring dashboard in browser"""
        try:
            import webbrowser
            webbrowser.open("http://localhost:9090/metrics")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open monitoring dashboard:\n{e}")
    
    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_mining:
            if messagebox.askokcancel("Quit", "Mining is in progress. Do you want to stop mining and quit?"):
                self.stop_mining()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Run the launcher"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        launcher = EnterpriseLauncher()
        launcher.run()
    except Exception as e:
        print(f"Launcher error: {e}")
        messagebox.showerror("Launcher Error", f"Failed to start launcher: {e}")

if __name__ == "__main__":
    main()
