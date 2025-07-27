#!/usr/bin/env python3
import subprocess
import json

print("=== GPU Diagnostics ===")

# Test 1: Basic nvidia-smi
print("\n1. Basic nvidia-smi output:")
try:
    result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
    print(result.stdout)
except Exception as e:
    print(f"Error: {e}")

# Test 2: Process listing with nvidia-smi
print("\n2. Process listing with nvidia-smi:")
try:
    result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name,gpu_name,used_memory', 
                            '--format=csv,noheader,nounits'], 
                            capture_output=True, text=True)
    print(result.stdout or "No output returned")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Check host processes
print("\n3. Host processes check:")
try:
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    print(result.stdout[:1000] + "..." if len(result.stdout) > 1000 else result.stdout)
except Exception as e:
    print(f"Error: {e}")

# Test 4: Search for NVIDIA in process maps
print("\n4. Looking for NVIDIA in process maps:")
try:
    result = subprocess.run("grep -l nvidia /proc/*/maps 2>/dev/null | cut -d'/' -f3 | sort -u", 
                            shell=True, capture_output=True, text=True)
    pids = result.stdout.strip().split('\n')
    print(f"Found {len(pids)} processes with NVIDIA libraries:")
    for pid in pids[:10]:  # Show first 10
        try:
            cmd = subprocess.run(['ps', '-p', pid, '-o', 'pid,cmd', '--no-headers'], 
                                capture_output=True, text=True)
            print(cmd.stdout.strip())
        except:
            print(f"PID {pid} - Unable to get details")
except Exception as e:
    print(f"Error: {e}")

print("\n=== End of Diagnostics ===")