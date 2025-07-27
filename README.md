# GPU Monitor Flask Application

A lightweight Flask web application for monitoring NVIDIA GPU utilization and processes on Unraid servers. This application provides real-time GPU metrics through a web interface and REST API endpoints.

## Features

- **Real-time GPU monitoring** - Updates every second
- **Multi-GPU support** - Monitors all available NVIDIA GPUs
- **Process tracking** - Shows which processes are using GPU resources
- **REST API** - Multiple endpoints for programmatic access
- **CORS enabled** - Can be accessed from web frontends
- **Background monitoring** - Continuous data collection via background thread

## GPU Metrics Collected

- GPU index and name
- Temperature
- GPU utilization percentage
- Memory utilization percentage
- Memory used/total
- Power draw

## Process Information

- Process ID (PID)
- Process name (with Python script names for Python processes)
- GPU being used
- Memory consumption

## API Endpoints

### Main Endpoints
- `GET /` - Web interface (requires templates/index.html)
- `GET /api/gpu-data` - Get all GPU data and processes

### REST API v1
- `GET /api/v1/gpu` - Get all GPU data including processes
- `GET /api/v1/gpu/<gpu_index>` - Get data for specific GPU by index
- `GET /api/v1/processes` - Get all GPU processes
- `GET /api/v1/health` - Health check endpoint

## Requirements

- NVIDIA drivers installed on host
- `nvidia-smi` command available
- Python 3.x
- Flask
- Flask-CORS

## Installation for Unraid Docker

### Docker Template Settings
- **Repository:** `python:3.9-slim` (or similar Python base image)
- **Network Type:** `bridge`
- **Port:** `5000:5000`
- **Volume:** Map your app directory to `/app`

### Post Arguments
```bash
bash -c "ls -la /app && pip install --upgrade pip --quiet && pip install --quiet flask flask-cors gunicorn && export FLASK_ENV=production && python /app/app.py"
```

### Required Host Access
- Mount `/usr/bin/nvidia-smi` or ensure NVIDIA tools are available in container
- Access to `/proc` filesystem for process information

## Usage

1. Deploy the Docker container on your Unraid server
2. Access the web interface at `http://your-server-ip:5000`
3. Use API endpoints for integration with other monitoring tools

## Example API Response

```json
{
  "timestamp": 1690472443.123,
  "gpus": [
    {
      "index": "0",
      "name": "NVIDIA GeForce RTX 4090",
      "temperature": "45",
      "gpu_utilization": "25",
      "memory_utilization": "15.2",
      "memory_used": "2048",
      "memory_total": "24576",
      "power_draw": "180"
    }
  ],
  "processes": [
    {
      "pid": "1234",
      "process_name": "python train.py",
      "gpu_name": "NVIDIA GeForce RTX 4090",
      "used_memory": "1024 MB"
    }
  ]
}
```

## Notes

- Designed specifically for Unraid environments
- Uses background threading for continuous monitoring
- Handles multiple process detection methods for reliability
- Automatically calculates memory utilization percentages
- Includes error handling for missing NVIDIA tools

## Development Mode

To run in development mode, change the last line in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```