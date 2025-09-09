#!/usr/bin/env python3
"""
ScryptMineOS Enterprise Edition - Windows Setup Script
Creates executable package for easy Windows deployment
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
import requests
import json

class WindowsSetup:
    """Windows executable setup and packaging"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.windows_dir = self.project_root / "windows"
        
        # Ensure directories exist
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        self.windows_dir.mkdir(exist_ok=True)
    
    def check_dependencies(self):
        """Check if required tools are installed"""
        print("🔍 Checking Windows build dependencies...")
        
        required_tools = {
            'python': 'Python 3.11+',
            'pip': 'Python package manager',
            'git': 'Git version control'
        }
        
        missing_tools = []
        
        for tool, description in required_tools.items():
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✅ {tool}: {description}")
                else:
                    missing_tools.append((tool, description))
            except FileNotFoundError:
                missing_tools.append((tool, description))
        
        if missing_tools:
            print("\n❌ Missing required tools:")
            for tool, description in missing_tools:
                print(f"  - {tool}: {description}")
            return False
        
        print("✅ All dependencies available")
        return True
    
    def install_build_tools(self):
        """Install Python build tools"""
        print("📦 Installing build tools...")
        
        build_packages = [
            'pyinstaller',
            'cx_Freeze',
            'auto-py-to-exe',
            'requests',
            'zipfile36'
        ]
        
        try:
            for package in build_packages:
                print(f"  Installing {package}...")
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ])
            
            print("✅ Build tools installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install build tools: {e}")
            return False
    
    def create_setup_exe_spec(self):
        """Create PyInstaller spec for setup.exe"""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['setup_launcher.py'],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=[
        ('requirements.txt', '.'),
        ('README.md', '.'),
        ('ENTERPRISE_README.md', '.'),
        ('private/.env.enterprise', 'private'),
    ],
    hiddenimports=[
        'requests',
        'zipfile',
        'subprocess',
        'pathlib',
        'json',
        'urllib.request',
        'urllib.parse',
        'shutil',
        'tempfile'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ScryptMineOS-Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='windows/icon.ico'
)
'''
        
        spec_file = self.windows_dir / "setup.spec"
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        print(f"✅ Created setup spec: {spec_file}")
        return spec_file
    
    def create_launcher_exe_spec(self):
        """Create PyInstaller spec for launcher.exe"""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['enterprise_launcher.py'],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=[
        ('enterprise_runner.py', '.'),
        ('enterprise/security/*.py', 'enterprise/security'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'asyncio',
        'logging',
        'argparse',
        'pathlib',
        'os',
        'sys',
        'json',
        'datetime',
        'cryptography.fernet',
        'prometheus_client',
        'aiohttp',
        'numpy',
        'requests'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ScryptMineOS-Enterprise',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='windows/icon.ico'
)
'''
        
        spec_file = self.windows_dir / "launcher.spec"
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        print(f"✅ Created launcher spec: {spec_file}")
        return spec_file
    
    def build_executables(self):
        """Build Windows executables"""
        print("🔨 Building Windows executables...")
        
        # Create spec files
        setup_spec = self.create_setup_exe_spec()
        launcher_spec = self.create_launcher_exe_spec()
        
        # Build setup.exe
        print("  Building setup.exe...")
        try:
            subprocess.check_call([
                'pyinstaller', '--clean', str(setup_spec)
            ], cwd=self.project_root)
            print("  ✅ setup.exe built successfully")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to build setup.exe: {e}")
            return False
        
        # Build launcher.exe
        print("  Building launcher.exe...")
        try:
            subprocess.check_call([
                'pyinstaller', '--clean', str(launcher_spec)
            ], cwd=self.project_root)
            print("  ✅ launcher.exe built successfully")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to build launcher.exe: {e}")
            return False
        
        return True
    
    def create_release_package(self):
        """Create release package with executables"""
        print("📦 Creating release package...")
        
        release_dir = self.dist_dir / "ScryptMineOS-Enterprise-Windows"
        release_dir.mkdir(exist_ok=True)
        
        # Copy executables
        setup_exe = self.dist_dir / "ScryptMineOS-Setup.exe"
        launcher_exe = self.dist_dir / "ScryptMineOS-Enterprise.exe"
        
        if setup_exe.exists():
            shutil.copy2(setup_exe, release_dir / "Setup.exe")
            print("  ✅ Copied Setup.exe")
        
        if launcher_exe.exists():
            shutil.copy2(launcher_exe, release_dir / "ScryptMineOS.exe")
            print("  ✅ Copied ScryptMineOS.exe")
        
        # Copy documentation
        docs_to_copy = [
            'README.md',
            'ENTERPRISE_README.md',
            'LICENSE'
        ]
        
        for doc in docs_to_copy:
            doc_path = self.project_root / doc
            if doc_path.exists():
                shutil.copy2(doc_path, release_dir / doc)
                print(f"  ✅ Copied {doc}")
        
        # Create Windows-specific README
        windows_readme = release_dir / "WINDOWS_SETUP.md"
        with open(windows_readme, 'w') as f:
            f.write(self.get_windows_readme_content())
        print("  ✅ Created Windows setup guide")
        
        # Create ZIP package
        zip_path = self.dist_dir / "ScryptMineOS-Enterprise-Windows.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in release_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(release_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Created release package: {zip_path}")
        return zip_path
    
    def get_windows_readme_content(self):
        """Get Windows-specific README content"""
        return '''# ScryptMineOS Enterprise Edition - Windows Setup

## 🚀 Quick Start

### 1. Run Setup
Double-click `Setup.exe` to install ScryptMineOS Enterprise Edition.

The setup will:
- Download the latest enterprise codebase
- Install Python dependencies
- Configure the environment
- Create desktop shortcuts

### 2. Launch Application
After setup completes, double-click `ScryptMineOS.exe` to start mining.

## 📋 System Requirements

- **Windows 10/11** (64-bit)
- **4GB RAM** minimum (8GB recommended)
- **Internet connection** for pool connectivity
- **GPU** with OpenCL support (optional but recommended)

## 🔧 Configuration

### First Run
1. The application will create a `.env` file
2. Edit this file with your wallet addresses:
   ```
   LTC_ADDRESS=your_litecoin_address_here
   DOGE_ADDRESS=your_dogecoin_address_here
   ```
3. Save and restart the application

### Advanced Configuration
- Edit `.env` file for custom pool settings
- Modify power and performance limits
- Configure monitoring ports

## 🌐 Monitoring

Access the web interface at:
- **Main Dashboard**: http://localhost:8080
- **Metrics**: http://localhost:9090/metrics
- **Health Check**: http://localhost:8081/health

## 🆘 Troubleshooting

### Common Issues

**Application won't start:**
- Run as Administrator
- Check Windows Defender/Antivirus settings
- Verify internet connection

**Mining not working:**
- Check wallet addresses in `.env` file
- Verify pool connectivity
- Check firewall settings

**Performance issues:**
- Close unnecessary applications
- Check GPU drivers are updated
- Monitor system temperature

### Support
- Check the logs in the application directory
- Review ENTERPRISE_README.md for detailed documentation
- Ensure your system meets minimum requirements

## 🔒 Security

- Keep your wallet addresses private
- Only download from official sources
- Regular system updates recommended
- Monitor mining activity regularly

---

**ScryptMineOS Enterprise Edition**  
Professional Cryptocurrency Mining Platform
'''
    
    def run_setup(self):
        """Run complete Windows setup process"""
        print("🏢 ScryptMineOS Enterprise Edition - Windows Setup")
        print("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Please install missing dependencies and try again")
            return False
        
        # Install build tools
        if not self.install_build_tools():
            print("❌ Failed to install build tools")
            return False
        
        # Build executables
        if not self.build_executables():
            print("❌ Failed to build executables")
            return False
        
        # Create release package
        package_path = self.create_release_package()
        if not package_path:
            print("❌ Failed to create release package")
            return False
        
        print("\n" + "=" * 60)
        print("✅ Windows setup completed successfully!")
        print(f"📦 Release package: {package_path}")
        print("🚀 Ready for distribution!")
        print("=" * 60)
        
        return True

def main():
    """Main setup entry point"""
    setup = WindowsSetup()
    success = setup.run_setup()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        return 0
    else:
        print("\n❌ Setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
