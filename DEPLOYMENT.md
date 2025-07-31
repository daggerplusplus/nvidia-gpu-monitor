# Docker Deployment Guide

## Prerequisites

1. **Docker Hub Account**: Create an account at [Docker Hub](https://hub.docker.com)
2. **GitHub Secrets**: Configure the following secrets in your GitHub repository:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: Docker Hub access token (create at Docker Hub > Account Settings > Security)

## Automated Build & Deployment

The repository includes GitHub Actions workflow that automatically:
1. Builds the Docker image on every push to main branch
2. Publishes to Docker Hub with appropriate tags
3. Supports multi-architecture builds (amd64, arm64)

## Local Testing

### Build and Test Locally
```bash
# Build the image
docker build -t nvidia-gpu-monitor:local .

# Test run (without GPU access)
docker run --rm -p 5000:5000 nvidia-gpu-monitor:local

# Test with GPU access (Linux with NVIDIA Docker runtime)
docker run --rm -p 5000:5000 --gpus all \
  -v /proc:/host/proc:ro \
  nvidia-gpu-monitor:local
```

### Using Docker Compose
```bash
# Build and run local version
docker-compose up nvidia-gpu-monitor

# Or use pre-built image from Docker Hub
DOCKERHUB_USERNAME=yourusername docker-compose --profile hub-image up nvidia-gpu-monitor-hub
```

## Unraid Deployment

### Method 1: Docker Hub Image (Recommended)
1. Go to Unraid Apps tab
2. Click "Add Container"
3. Fill in the following settings:

**Basic Settings:**
- **Name**: `nvidia-gpu-monitor`
- **Repository**: `yourusername/nvidia-gpu-monitor:latest`
- **Network Type**: `bridge`

**Port Mappings:**
- **Container Port**: `5000`
- **Host Port**: `5000` (or any available port)
- **Protocol**: `TCP`

**Volume Mappings:**
- **Container Path**: `/usr/bin/nvidia-smi`
- **Host Path**: `/usr/bin/nvidia-smi`
- **Access Mode**: `Read Only`

- **Container Path**: `/host/proc`
- **Host Path**: `/proc`
- **Access Mode**: `Read Only`

**Environment Variables:**
- **Key**: `FLASK_ENV`
- **Value**: `production`

**Advanced Settings:**
- **Extra Parameters**: `--runtime=nvidia` (if using NVIDIA Container Runtime)

### Method 2: GitHub Repository
If you want to build from source:
1. Use repository: `https://github.com/yourusername/nvidia-gpu-monitor.git`
2. Set build context to repository root
3. Use the same volume and port mappings as above

## Post-Deployment

1. **Access the Web Interface**: 
   - Navigate to `http://your-unraid-ip:5000`

2. **API Endpoints**:
   - Health check: `http://your-unraid-ip:5000/api/v1/health`
   - GPU data: `http://your-unraid-ip:5000/api/v1/gpu`
   - Processes: `http://your-unraid-ip:5000/api/v1/processes`

3. **Verification**:
   - Check container logs for any errors
   - Ensure nvidia-smi is accessible within the container
   - Verify GPU data is being collected

## Troubleshooting

### Common Issues

1. **nvidia-smi not found**:
   - Ensure NVIDIA drivers are installed on host
   - Mount nvidia-smi binary correctly
   - Check NVIDIA library paths

2. **No GPU data**:
   - Verify container has access to GPU device
   - Check if NVIDIA Container Runtime is installed
   - Ensure user has permissions to access GPU

3. **Permission denied on /proc**:
   - Mount /proc as read-only
   - Ensure container runs with appropriate user permissions

### Debug Commands
```bash
# Check if nvidia-smi works inside container
docker exec -it nvidia-gpu-monitor nvidia-smi

# Check container logs
docker logs nvidia-gpu-monitor

# Test API endpoints
curl http://localhost:5000/api/v1/health
curl http://localhost:5000/api/v1/gpu
```

## Security Considerations

- Container runs as non-root user
- Read-only access to host filesystems
- Minimal attack surface with slim Python base image
- No sensitive data stored in container

## Updates

The GitHub Actions workflow automatically builds new images when you push to the main branch. To update your deployment:

1. Pull the latest image: `docker pull yourusername/nvidia-gpu-monitor:latest`
2. Restart the container in Unraid or using `docker-compose restart`