#!/usr/bin/env python3
"""
Production deployment script for the Scrypt DOGE mining system.
Automates deployment, configuration, and service setup.
"""

import os
import sys
import subprocess
import argparse
import yaml
import json
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("deployment")


class ProductionDeployer:
    """Handles production deployment of the mining system"""
    
    def __init__(self, config_file="config/production.yaml"):
        self.config_file = config_file
        self.install_dir = Path("/opt/scrypt-doge-miner")
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load deployment configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                # Create default configuration
                self.config = self.get_default_config()
                self.save_config()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        """Get default deployment configuration"""
        return {
            "deployment": {
                "install_dir": "/opt/scrypt-doge-miner",
                "user": "miner",
                "group": "miner"
            },
            "mining": {
                "pools": [
                    {
                        "url": "stratum+tcp://doge.zsolo.bid:8057",
                        "username": "YOUR_WALLET_ADDRESS",
                        "password": "x",
                        "algorithm": "scrypt",
                        "priority": 1
                    }
                ],
                "hardware": {
                    "type": "asic",
                    "temperature_limit": 80
                },
                "economic": {
                    "enabled": True,
                    "max_power_cost": 0.12,
                    "min_profitability": 0.01,
                    "shutdown_on_unprofitable": True
                }
            },
            "monitoring": {
                "enabled": True,
                "metrics_port": 8080,
                "health_check_port": 8081
            },
            "security": {
                "enable_encryption": True,
                "rate_limiting_enabled": True
            }
        }
    
    def save_config(self):
        """Save current configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def check_prerequisites(self):
        """Check system prerequisites"""
        logger.info("Checking system prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8 or higher is required")
        
        # Check if running as root (for system installation)
        if os.geteuid() != 0:
            logger.warning("Not running as root. Some operations may fail.")
        
        # Check required system packages
        required_packages = ["python3-pip", "python3-venv"]
        missing_packages = []
        
        for package in required_packages:
            try:
                subprocess.run(["dpkg", "-l", package], 
                              capture_output=True, check=True)
            except subprocess.CalledProcessError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.warning(f"Missing system packages: {missing_packages}")
            logger.info("Consider installing with: apt-get install " + " ".join(missing_packages))
        
        logger.info("Prerequisites check completed")
    
    def create_installation_directory(self):
        """Create installation directory"""
        logger.info(f"Creating installation directory: {self.install_dir}")
        
        try:
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Set ownership (if running as root)
            if os.geteuid() == 0:
                import pwd
                import grp
                
                user = self.config["deployment"].get("user", "miner")
                group = self.config["deployment"].get("group", "miner")
                
                try:
                    uid = pwd.getpwnam(user).pw_uid
                    gid = grp.getgrnam(group).gr_gid
                    os.chown(self.install_dir, uid, gid)
                except KeyError:
                    logger.warning(f"User {user} or group {group} not found")
            
            logger.info("Installation directory created successfully")
        except Exception as e:
            logger.error(f"Failed to create installation directory: {e}")
            raise
    
    def copy_application_files(self):
        """Copy application files to installation directory"""
        logger.info("Copying application files...")
        
        # Get current directory (assuming script is in the project root)
        current_dir = Path(__file__).parent.parent
        
        # Files and directories to copy
        items_to_copy = [
            "main.py",
            "core",
            "network",
            "security",
            "hardware",
            "monitoring",
            "optimization",
            "utils",
            "config",
            "requirements.txt"
        ]
        
        for item in items_to_copy:
            src = current_dir / item
            dst = self.install_dir / item
            
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
                logger.debug(f"Copied {src} to {dst}")
            else:
                logger.warning(f"Source item not found: {src}")
        
        logger.info("Application files copied successfully")
    
    def create_virtual_environment(self):
        """Create Python virtual environment"""
        logger.info("Creating Python virtual environment...")
        
        venv_path = self.install_dir / "venv"
        
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], 
                          check=True, capture_output=True)
            logger.info("Virtual environment created successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e}")
            raise
    
    def install_dependencies(self):
        """Install Python dependencies"""
        logger.info("Installing Python dependencies...")
        
        venv_pip = self.install_dir / "venv" / "bin" / "pip"
        requirements_file = self.install_dir / "requirements.txt"
        
        try:
            # Upgrade pip first
            subprocess.run([str(venv_pip), "install", "--upgrade", "pip"], 
                          check=True, capture_output=True)
            
            # Install dependencies
            if requirements_file.exists():
                subprocess.run([str(venv_pip), "install", "-r", str(requirements_file)], 
                              check=True, capture_output=True)
                logger.info("Dependencies installed successfully")
            else:
                logger.warning("requirements.txt not found, skipping dependency installation")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            raise
    
    def create_log_directories(self):
        """Create log directories"""
        logger.info("Creating log directories...")
        
        log_dir = self.install_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Set appropriate permissions
        os.chmod(log_dir, 0o755)
        
        logger.info("Log directories created successfully")
    
    def create_systemd_service(self):
        """Create systemd service file"""
        logger.info("Creating systemd service...")
        
        service_content = f"""[Unit]
Description=Scrypt DOGE Miner
After=network.target

[Service]
Type=simple
User={self.config["deployment"].get("user", "miner")}
Group={self.config["deployment"].get("group", "miner")}
WorkingDirectory={self.install_dir}
ExecStart={self.install_dir}/venv/bin/python main.py --mode production
Restart=always
RestartSec=10
Environment=PYTHONPATH={self.install_dir}

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/scrypt-doge-miner.service")
        
        try:
            # Write service file (requires root)
            if os.geteuid() == 0:
                with open(service_file, 'w') as f:
                    f.write(service_content)
                
                # Reload systemd
                subprocess.run(["systemctl", "daemon-reload"], 
                              check=True, capture_output=True)
                
                # Enable service
                subprocess.run(["systemctl", "enable", "scrypt-doge-miner.service"], 
                              check=True, capture_output=True)
                
                logger.info("Systemd service created and enabled successfully")
            else:
                # Create local service file for user reference
                local_service_file = self.install_dir / "scrypt-doge-miner.service"
                with open(local_service_file, 'w') as f:
                    f.write(service_content)
                logger.info(f"Systemd service file created at {local_service_file}")
                logger.warning("Run as root to install system-wide service")
        
        except Exception as e:
            logger.error(f"Failed to create systemd service: {e}")
    
    def create_configuration_files(self):
        """Create configuration files"""
        logger.info("Creating configuration files...")
        
        config_dir = self.install_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Create production configuration
        production_config = {
            "environment": "production",
            "mining": {
                "algorithm": "scrypt",
                "threads": "auto",
                "intensity": "auto"
            },
            "pools": self.config["mining"]["pools"],
            "hardware": self.config["mining"]["hardware"],
            "economic": self.config["mining"]["economic"],
            "security": self.config["security"],
            "monitoring": self.config["monitoring"],
            "logging": {
                "level": "INFO",
                "file_path": f"{self.install_dir}/logs/mining.log",
                "max_file_size": 10485760,
                "backup_count": 5
            }
        }
        
        production_config_file = config_dir / "production.yaml"
        with open(production_config_file, 'w') as f:
            yaml.dump(production_config, f, default_flow_style=False)
        
        logger.info("Configuration files created successfully")
    
    def set_permissions(self):
        """Set appropriate file permissions"""
        logger.info("Setting file permissions...")
        
        try:
            # Set ownership (if running as root)
            if os.geteuid() == 0:
                import pwd
                import grp
                
                user = self.config["deployment"].get("user", "miner")
                group = self.config["deployment"].get("group", "miner")
                
                try:
                    uid = pwd.getpwnam(user).pw_uid
                    gid = grp.getgrnam(group).gr_gid
                    
                    # Recursively change ownership
                    for root, dirs, files in os.walk(self.install_dir):
                        os.chown(root, uid, gid)
                        for dir_name in dirs:
                            os.chown(os.path.join(root, dir_name), uid, gid)
                        for file_name in files:
                            os.chown(os.path.join(root, file_name), uid, gid)
                    
                    logger.info("File permissions set successfully")
                except KeyError:
                    logger.warning(f"User {user} or group {group} not found")
            else:
                # Set read/write permissions for current user
                for root, dirs, files in os.walk(self.install_dir):
                    os.chmod(root, 0o755)
                    for dir_name in dirs:
                        os.chmod(os.path.join(root, dir_name), 0o755)
                    for file_name in files:
                        os.chmod(os.path.join(root, file_name), 0o644)
                
                logger.info("Basic file permissions set successfully")
        
        except Exception as e:
            logger.error(f"Failed to set permissions: {e}")
    
    def create_monitoring_config(self):
        """Create monitoring configuration files"""
        logger.info("Creating monitoring configuration...")
        
        # Create Prometheus configuration
        prometheus_config = """
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'scrypt-doge-miner'
    static_configs:
      - targets: ['localhost:8080']
"""
        
        prometheus_dir = self.install_dir / "monitoring" / "prometheus"
        prometheus_dir.mkdir(parents=True, exist_ok=True)
        
        prometheus_file = prometheus_dir / "prometheus.yml"
        with open(prometheus_file, 'w') as f:
            f.write(prometheus_config)
        
        logger.info("Monitoring configuration created successfully")
    
    def deploy(self):
        """Execute full deployment process"""
        logger.info("Starting production deployment...")
        
        try:
            self.check_prerequisites()
            self.create_installation_directory()
            self.copy_application_files()
            self.create_virtual_environment()
            self.install_dependencies()
            self.create_log_directories()
            self.create_configuration_files()
            self.create_monitoring_config()
            self.set_permissions()
            self.create_systemd_service()
            
            logger.info("Production deployment completed successfully!")
            logger.info(f"Installation directory: {self.install_dir}")
            logger.info("To start the service, run: sudo systemctl start scrypt-doge-miner")
            logger.info("To enable auto-start on boot: sudo systemctl enable scrypt-doge-miner")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Deploy Scrypt DOGE Miner")
    parser.add_argument("--config", default="config/deployment.yaml",
                       help="Deployment configuration file")
    parser.add_argument("--install-dir", 
                       help="Installation directory (overrides config)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Perform dry run without making changes")
    
    args = parser.parse_args()
    
    try:
        deployer = ProductionDeployer(args.config)
        
        if args.install_dir:
            deployer.install_dir = Path(args.install_dir)
            deployer.config["deployment"]["install_dir"] = args.install_dir
        
        if args.dry_run:
            logger.info("Performing dry run (no changes will be made)")
            # In a real implementation, this would simulate the deployment
            logger.info("Dry run completed")
        else:
            deployer.deploy()
    
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()