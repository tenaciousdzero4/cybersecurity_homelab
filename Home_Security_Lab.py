#!/usr/bin/env python3
"""
Virtual Cybersecurity Lab Builder
Automates the creation and configuration of a cybersecurity homelab using VirtualBox
"""

import subprocess
import sys
import os
import time
import platform
import requests
from pathlib import Path


class VirtualBoxLabBuilder:
    """Build and manage a virtual cybersecurity lab"""
    
    def __init__(self):
        self.vbox_path = self.find_vboxmanage()
        self.lab_name = "CyberSecLab"
        self.vms = {}
        
    def find_vboxmanage(self):
        """Find VBoxManage executable path"""
        try:
            result = subprocess.run(['VBoxManage', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return 'VBoxManage'
        except FileNotFoundError:
            pass
        
        # Try common paths on Windows
        common_paths = [
            r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
            r"C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe"
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        print("Error: VBoxManage not found. Please install VirtualBox.")
        sys.exit(1)
    
    def run_command(self, cmd):
        """Execute a command and return output"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def create_vm(self, vm_name, os_type, memory_mb=2048, cpus=2):
        """Create a new virtual machine"""
        print(f"Creating VM: {vm_name}...")
        
        cmd = f'"{self.vbox_path}" createvm --name "{vm_name}" --ostype "{os_type}" --register'
        success, stdout, stderr = self.run_command(cmd)
        
        if not success:
            print(f"Error creating VM: {stderr}")
            return False
        
        # Configure VM resources
        self.run_command(f'"{self.vbox_path}" modifyvm "{vm_name}" --memory {memory_mb} --cpus {cpus}')
        self.run_command(f'"{self.vbox_path}" modifyvm "{vm_name}" --nic1 nat')
        self.run_command(f'"{self.vbox_path}" modifyvm "{vm_name}" --nic2 intnet --intnet2 labnet')
        
        self.vms[vm_name] = {
            'os_type': os_type,
            'memory': memory_mb,
            'cpus': cpus,
            'state': 'stopped'
        }
        
        print(f"✓ VM '{vm_name}' created successfully")
        return True
    
    def create_disk(self, vm_name, size_mb=40960):
        """Create a virtual disk for VM"""
        print(f"Creating disk for {vm_name}...")
        
        disk_path = f"{vm_name}_disk.vdi"
        cmd = f'"{self.vbox_path}" createmedium disk --filename "{disk_path}" --size {size_mb}'
        success, _, stderr = self.run_command(cmd)
        
        if not success:
            print(f"Error creating disk: {stderr}")
            return False
        
        # Attach disk to VM
        cmd = f'"{self.vbox_path}" storagectl "{vm_name}" --name "SATA" --add sata'
        self.run_command(cmd)
        
        cmd = f'"{self.vbox_path}" storageattach "{vm_name}" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "{disk_path}"'
        success, _, stderr = self.run_command(cmd)
        
        if not success:
            print(f"Error attaching disk: {stderr}")
            return False
        
        print(f"✓ Disk created and attached to {vm_name}")
        return True
    
    def start_vm(self, vm_name):
        """Start a virtual machine"""
        print(f"Starting VM: {vm_name}...")
        
        cmd = f'"{self.vbox_path}" startvm "{vm_name}" --type headless'
        success, _, stderr = self.run_command(cmd)
        
        if success:
            self.vms[vm_name]['state'] = 'running'
            print(f"✓ VM '{vm_name}' started")
            time.sleep(2)
        else:
            print(f"Error starting VM: {stderr}")
        
        return success
    
    def stop_vm(self, vm_name):
        """Stop a virtual machine"""
        print(f"Stopping VM: {vm_name}...")
        
        cmd = f'"{self.vbox_path}" controlvm "{vm_name}" poweroff'
        success, _, stderr = self.run_command(cmd)
        
        if success:
            self.vms[vm_name]['state'] = 'stopped'
            print(f"✓ VM '{vm_name}' stopped")
        else:
            print(f"Error stopping VM: {stderr}")
        
        return success
    
    def list_vms(self):
        """List all VMs in the lab"""
        print("\n=== Cybersecurity Lab VMs ===")
        if not self.vms:
            print("No VMs created yet")
            return
        
        for vm_name, details in self.vms.items():
            print(f"{vm_name}:")
            print(f"  OS: {details['os_type']}")
            print(f"  Memory: {details['memory']}MB")
            print(f"  CPUs: {details['cpus']}")
            print(f"  State: {details['state']}")
    
    def delete_vm(self, vm_name):
        """Delete a virtual machine"""
        print(f"Deleting VM: {vm_name}...")
        
        # Stop VM if running
        if self.vms.get(vm_name, {}).get('state') == 'running':
            self.stop_vm(vm_name)
        
        cmd = f'"{self.vbox_path}" unregistervm "{vm_name}" --delete'
        success, _, stderr = self.run_command(cmd)
        
        if success:
            del self.vms[vm_name]
            print(f"✓ VM '{vm_name}' deleted")
        else:
            print(f"Error deleting VM: {stderr}")
        
        return success
    
    def build_lab(self):
        """Build a complete cybersecurity lab"""
        print("=== Building Virtual Cybersecurity Lab ===\n")
        
        # Create attacker VM
        self.create_vm("AttackerVM", "Linux_64", memory_mb=2048, cpus=2)
        self.create_disk("AttackerVM", size_mb=40960)
        
        # Create target VM
        self.create_vm("TargetVM", "Linux_64", memory_mb=2048, cpus=2)
        self.create_disk("TargetVM", size_mb=40960)
        
        # Create monitoring VM
        self.create_vm("MonitorVM", "Linux_64", memory_mb=1024, cpus=1)
        self.create_disk("MonitorVM", size_mb=20480)
        
        print("\n=== Lab Creation Complete ===")
        self.list_vms()
    
    def start_lab(self):
        """Start all VMs in the lab"""
        print("\n=== Starting Lab ===")
        for vm_name in self.vms.keys():
            self.start_vm(vm_name)
    
    def stop_lab(self):
        """Stop all VMs in the lab"""
        print("\n=== Stopping Lab ===")
        for vm_name in self.vms.keys():
            self.stop_vm(vm_name)


def main():
    """Main entry point"""
    print("Virtual Cybersecurity Lab Builder")
    print("=" * 40)
    
    try:
        lab = VirtualBoxLabBuilder()
        
        # Build the lab
        lab.build_lab()
        
        # Optional: Start the lab
        response = input("\nStart lab now? (y/n): ").lower()
        if response == 'y':
            lab.start_lab()
            print("\nLab is running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping lab...")
                lab.stop_lab()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
