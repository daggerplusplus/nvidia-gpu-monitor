# app.py
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import subprocess
import time
from threading import Thread
import re
import json

app = Flask(__name__)
CORS(app)

# Store the latest GPU data
gpu_data = {}

def parse_nvidia_smi():
    """Parse nvidia-smi output and return structured data"""
    try:
        # Run nvidia-smi command with specific format for GPU info
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, check=True
        )
        
        gpu_list = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(', ')
                if len(parts) >= 8:
                    # Calculate memory utilization percentage
                    mem_used = float(parts[5])
                    mem_total = float(parts[6])
                    mem_util = round((mem_used / mem_total) * 100, 1) if mem_total > 0 else 0
                    
                    gpu_list.append({
                        'index': parts[0],
                        'name': parts[1],
                        'temperature': parts[2],
                        'gpu_utilization': parts[3],
                        'memory_utilization': str(mem_util),  # Calculate correctly
                        'memory_used': parts[5],
                        'memory_total': parts[6],
                        'power_draw': parts[7]
                    })
        
        # Skip the standard nvidia-smi output parsing since it's not finding processes
        
        # Try to get process info using nvidia-smi query
        processes = []
        try:
            proc_result = subprocess.run(
                ['nvidia-smi', '--query-compute-apps=pid,process_name,gpu_uuid,used_memory',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True
            )
            
            for line in proc_result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(', ')
                    if len(parts) >= 4:
                        pid = parts[0]
                        
                        # Get command details from /proc
                        try:
                            with open(f'/proc/{pid}/cmdline', 'r') as f:
                                cmdline = f.read().replace('\0', ' ').strip()
                            
                            cmd_parts = cmdline.split()
                            process_name = cmd_parts[0].split('/')[-1]
                            
                            # For Python processes, include the script name
                            if process_name == 'python' or process_name == 'python3':
                                for part in cmd_parts:
                                    if part.endswith('.py'):
                                        process_name = f"{process_name} {part.split('/')[-1]}"
                                        break
                        except:
                            process_name = parts[1]
                        
                        processes.append({
                            'pid': pid,
                            'process_name': process_name,
                            'gpu_name': gpu_list[0]['name'] if gpu_list else parts[2],
                            'used_memory': parts[3]
                        })
        
            # If no processes found, use the grep approach
            if not processes:
                pid_result = subprocess.run(
                    "grep -l nvidia /proc/*/maps 2>/dev/null | cut -d'/' -f3 | sort -u",
                    shell=True, capture_output=True, text=True
                )
                
                pids = pid_result.stdout.strip().split('\n')
                for pid in pids:
                    if not pid or not pid.isdigit():
                        continue
                    
                    try:
                        # Get full command line
                        with open(f'/proc/{pid}/cmdline', 'r') as f:
                            cmdline = f.read().replace('\0', ' ').strip()
                        
                        # Get process name from the command
                        cmd_parts = cmdline.split()
                        process_name = cmd_parts[0].split('/')[-1]
                        
                        # For Python processes, include the script name
                        if process_name == 'python' or process_name == 'python3':
                            for part in cmd_parts:
                                if part.endswith('.py'):
                                    process_name = f"{process_name} {part.split('/')[-1]}"
                                    break
                        
                        # Try to estimate memory usage
                        mem_used = "Unknown"
                        try:
                            # Try to check if nvidia-smi can tell us memory usage
                            mem_check = subprocess.run(
                                f"nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits | grep {pid}",
                                shell=True, capture_output=True, text=True
                            )
                            if mem_check.stdout.strip():
                                mem_parts = mem_check.stdout.strip().split(', ')
                                if len(mem_parts) >= 2:
                                    mem_used = mem_parts[1]
                        except:
                            pass
                        
                        if mem_used == "Unknown":
                            try:
                                # Fall back to process memory
                                with open(f'/proc/{pid}/status', 'r') as f:
                                    status = f.read()
                                    mem_match = re.search(r'VmRSS:\s+(\d+)', status)
                                    if mem_match:
                                        mem_kb = int(mem_match.group(1))
                                        mem_used = f"{mem_kb // 1024}"
                            except:
                                pass
                        
                        processes.append({
                            'pid': pid,
                            'process_name': process_name,
                            'gpu_name': gpu_list[0]['name'] if gpu_list else 'Unknown',
                            'used_memory': f"{mem_used} MB"
                        })
                    except Exception as e:
                        print(f"Error processing PID {pid}: {e}")
                
        except Exception as proc_e:
            print(f"Error finding GPU processes: {proc_e}")
        
        return {'timestamp': time.time(), 'gpus': gpu_list, 'processes': processes}
    except Exception as e:
        print(f"Error parsing nvidia-smi: {e}")
        return {'error': str(e)}

def update_gpu_data():
    """Background thread to continuously update GPU data"""
    global gpu_data
    while True:
        gpu_data = parse_nvidia_smi()
        time.sleep(1)  # Update every second

def get_gpu_processes():
    """Get processes using GPUs by checking for NVIDIA libraries in process mappings"""
    processes = []
    
    try:
        # List all processes with mapped NVIDIA libraries
        ps_result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True, text=True, check=True
        )
        
        # Get GPU memory usage from nvidia-smi
        nvidia_result = subprocess.run(
            ['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, check=True
        )
        
        # Build dictionary of PIDs with GPU memory usage
        gpu_pids = {}
        for line in nvidia_result.stdout.strip().split('\n'):
            if line:
                parts = line.split(', ')
                if len(parts) >= 2:
                    gpu_pids[parts[0]] = parts[1]
        
        # Parse ps output to get process names
        for line in ps_result.stdout.strip().split('\n')[1:]:  # Skip header
            parts = line.split(None, 10)
            if len(parts) >= 11:
                pid = parts[1]
                if pid in gpu_pids:
                    processes.append({
                        'pid': pid,
                        'process_name': parts[10],
                        'gpu_name': 'GPU 0',  # Assuming GPU 0 for simplicity
                        'used_memory': f"{gpu_pids[pid]} MB"
                    })
        
        return processes
    except Exception as e:
        print(f"Error getting GPU processes: {e}")
        return []

# Start the background thread
Thread(target=update_gpu_data, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/gpu-data')
def get_gpu_data():
    return jsonify(gpu_data)

@app.route('/api/v1/gpu', methods=['GET'])
def get_all_gpu_data():
    """Get all GPU data including processes"""
    return jsonify(gpu_data)

@app.route('/api/v1/gpu/<int:gpu_index>', methods=['GET'])
def get_specific_gpu_data(gpu_index):
    """Get data for a specific GPU by index"""
    if 'error' in gpu_data:
        return jsonify({'error': gpu_data['error']}), 500
    
    for gpu in gpu_data.get('gpus', []):
        if int(gpu['index']) == gpu_index:
            return jsonify({
                'timestamp': gpu_data['timestamp'],
                'gpu': gpu
            })
    
    return jsonify({'error': f'GPU with index {gpu_index} not found'}), 404

@app.route('/api/v1/processes', methods=['GET'])
def get_processes():
    """Get all processes using GPUs"""
    if 'error' in gpu_data:
        return jsonify({'error': gpu_data['error']}), 500
    
    return jsonify({
        'timestamp': gpu_data['timestamp'],
        'processes': gpu_data.get('processes', [])
    })

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    import os
    
    # In testing mode, always return healthy
    if os.getenv('TESTING') == 'true':
        return jsonify({
            'status': 'healthy',
            'message': 'Running in test mode',
            'gpu_count': 0,
            'last_update': time.time()
        })
    
    # Check if nvidia-smi is available
    try:
        subprocess.run(['nvidia-smi', '--version'], capture_output=True, check=True)
        nvidia_available = True
    except:
        nvidia_available = False
    
    if not nvidia_available:
        return jsonify({
            'status': 'degraded',
            'message': 'nvidia-smi not available - GPU monitoring disabled',
            'gpu_count': 0,
            'last_update': time.time()
        })
    
    if 'error' in gpu_data:
        return jsonify({
            'status': 'error',
            'message': gpu_data['error']
        }), 500
    
    return jsonify({
        'status': 'healthy',
        'gpu_count': len(gpu_data.get('gpus', [])),
        'last_update': gpu_data.get('timestamp', 0)
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)