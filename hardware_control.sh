#!/bin/bash
"""
Hardware Control Script for GPU-ASIC Hybrid Layer
Run as root to apply ASIC-like hardware configurations

This script implements the "TAKE CONTROL OF THE HARDWARE" requirements:
1. Disable OS power management  
2. Lock PCIe settings
3. Set custom D-Bus policies
4. Configure for appliance-like operation
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 GPU-ASIC Hybrid Hardware Control${NC}"
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run as root${NC}"
    echo "Usage: sudo ./hardware_control.sh"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This will modify system power management${NC}"
echo "This script will configure your system for ASIC-like behavior"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 1
fi

echo -e "${BLUE}1. Disabling OS Power Management${NC}"
echo "------------------------------------------------"

# Disable sleep/hibernate targets
echo "Disabling sleep and hibernate..."
systemctl mask sleep.target hibernate.target hybrid-sleep.target suspend.target

# Set CPU governor to performance
echo "Setting CPU governor to performance..."
if [ -d "/sys/devices/system/cpu/cpu0/cpufreq" ]; then
    echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
    echo -e "${GREEN}✅ CPU governor set to performance${NC}"
else
    echo -e "${YELLOW}⚠️  CPU frequency scaling not available${NC}"
fi

# Disable audio power save (reduces interference)
echo "Disabling audio power save..."
if [ -f "/sys/module/snd_hda_intel/parameters/power_save" ]; then
    echo 0 > /sys/module/snd_hda_intel/parameters/power_save
    echo -e "${GREEN}✅ Audio power save disabled${NC}"
else
    echo -e "${YELLOW}⚠️  Audio power save not available${NC}"
fi

echo -e "${BLUE}2. Configuring PCIe Settings${NC}"
echo "------------------------------------------------"

# Find GPU PCIe bus
GPU_BUS=$(lspci | grep -i vga | head -1 | cut -d' ' -f1)
if [ -n "$GPU_BUS" ]; then
    echo "Found GPU at PCIe bus: $GPU_BUS"
    
    # Try to lock PCIe to Gen 3 and disable ASPM
    echo "Configuring PCIe settings..."
    
    # Note: These commands may fail on some systems - that's expected
    setpci -s $GPU_BUS CAP_EXP+0x10.w=0x42 2>/dev/null || echo -e "${YELLOW}⚠️  PCIe link control not accessible${NC}"
    
    # Disable ASPM (Active State Power Management)
    if [ -f "/sys/module/pcie_aspm/parameters/policy" ]; then
        echo performance > /sys/module/pcie_aspm/parameters/policy
        echo -e "${GREEN}✅ PCIe ASPM set to performance${NC}"
    else
        echo -e "${YELLOW}⚠️  PCIe ASPM control not available${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No GPU found on PCIe bus${NC}"
fi

echo -e "${BLUE}3. Creating D-Bus Policy${NC}"
echo "------------------------------------------------"

# Create custom D-Bus policy to restrict access to GPU settings
DBUS_POLICY="/etc/dbus-1/system.d/gpu-asic-hybrid.conf"

cat > "$DBUS_POLICY" << 'EOF'
<!DOCTYPE busconfig PUBLIC
 "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <!-- Restrict access to thermal and GPU control services -->
  <policy user="root">
    <allow send_destination="org.freedesktop.thermald"/>
    <allow send_destination="com.nvidia.settings"/>
  </policy>
  
  <policy at_console="true">
    <!-- Allow console users limited access -->
    <allow send_destination="org.freedesktop.thermald"
           send_interface="org.freedesktop.thermald.Query"/>
  </policy>
  
  <policy context="default">
    <!-- Deny everyone else -->
    <deny send_destination="org.freedesktop.thermald"/>
    <deny send_destination="com.nvidia.settings"/>
  </policy>
</busconfig>
EOF

echo -e "${GREEN}✅ D-Bus policy created: $DBUS_POLICY${NC}"

echo -e "${BLUE}4. Configuring System for Appliance Mode${NC}"
echo "------------------------------------------------"

# Set up watchdog if available
if [ -c "/dev/watchdog" ]; then
    echo "Configuring hardware watchdog..."
    
    # Create watchdog service
    cat > /etc/systemd/system/gpu-miner-watchdog.service << 'EOF'
[Unit]
Description=GPU Miner Watchdog
After=multi-user.target

[Service]
Type=simple
ExecStart=/bin/bash -c 'while true; do echo 1 > /dev/watchdog; sleep 5; done'
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
EOF

    systemctl enable gpu-miner-watchdog.service
    echo -e "${GREEN}✅ Watchdog service configured${NC}"
else
    echo -e "${YELLOW}⚠️  Hardware watchdog not available${NC}"
fi

# Configure for appliance-like boot
echo "Configuring boot settings..."

# Disable unnecessary services (optional)
SERVICES_TO_DISABLE="bluetooth.service cups.service avahi-daemon.service"
for service in $SERVICES_TO_DISABLE; do
    if systemctl is-enabled $service &>/dev/null; then
        systemctl disable $service
        echo "Disabled $service"
    fi
done

echo -e "${BLUE}5. GPU Vendor Detection and Configuration${NC}"
echo "------------------------------------------------"

# Detect GPU vendor and provide configuration guidance
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✅ NVIDIA GPU detected${NC}"
    echo "For NVIDIA GPU control, install nvidia-ml-py:"
    echo "  pip install nvidia-ml-py"
    
    # Show current GPU status
    echo "Current GPU status:"
    nvidia-smi --query-gpu=name,power.draw,temperature.gpu,clocks.gr,clocks.mem --format=csv,noheader,nounits
    
elif command -v rocm-smi &> /dev/null; then
    echo -e "${GREEN}✅ AMD GPU detected${NC}"
    echo "AMD ROCm utilities available for GPU control"
    
    # Show current GPU status
    echo "Current GPU status:"
    rocm-smi --showproductname --showpower --showtemp --showclocks
    
else
    echo -e "${YELLOW}⚠️  No GPU control utilities detected${NC}"
    echo "Install appropriate GPU drivers and utilities:"
    echo "  NVIDIA: nvidia-driver nvidia-utils"
    echo "  AMD: rocm-smi amdgpu-pro"
fi

echo -e "${BLUE}6. Creating Miner Auto-Start Service${NC}"
echo "------------------------------------------------"

# Create systemd service for auto-starting the miner
MINER_SERVICE="/etc/systemd/system/gpu-asic-miner.service"

cat > "$MINER_SERVICE" << 'EOF'
[Unit]
Description=GPU-ASIC Hybrid Miner
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=miner
Group=miner
WorkingDirectory=/opt/gpu-asic-miner
ExecStart=/usr/bin/python3 runner.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/gpu-asic-miner

# Resource limits for mining
LimitNOFILE=65536
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Miner service created: $MINER_SERVICE${NC}"
echo "To enable auto-start: systemctl enable gpu-asic-miner.service"

echo -e "${BLUE}7. Final Configuration Summary${NC}"
echo "=================================================="

echo -e "${GREEN}✅ Hardware Control Configuration Complete${NC}"
echo ""
echo "Applied configurations:"
echo "  • OS power management disabled"
echo "  • CPU governor set to performance"
echo "  • PCIe settings optimized"
echo "  • D-Bus policies restricted"
echo "  • Watchdog service configured"
echo "  • Auto-start service created"
echo ""
echo -e "${YELLOW}⚠️  REBOOT REQUIRED${NC}"
echo "Some changes require a system reboot to take effect"
echo ""
echo "Next steps:"
echo "1. Reboot the system"
echo "2. Run the GPU-ASIC hybrid miner"
echo "3. Test external API compatibility"
echo ""
echo "Test API endpoint after reboot:"
echo "  curl http://localhost:8080/cgi-bin/get_miner_status.cgi"
echo ""
echo -e "${BLUE}🎯 Your system is now configured for ASIC-like operation!${NC}"