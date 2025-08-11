# Dynamic Port Allocation System

## Overview
The AI Backend now includes a comprehensive dynamic port allocation system that automatically finds available ports and makes all server configuration easily configurable through environment variables.

## Features

### 🔧 **Dynamic Port Allocation**
- **Automatic Port Discovery**: Automatically finds free ports in a configurable range
- **Fallback System**: Uses configured port first, then finds free port if busy
- **Configurable Range**: Set custom port ranges for auto-allocation

### 📝 **Environment-Based Configuration**
- **All Settings Configurable**: Every aspect of the server can be configured via environment variables
- **Example Configuration**: Comprehensive example file with all options
- **Flexible Defaults**: Sensible defaults with easy override

### 🚀 **Easy Startup**
- **Smart Startup Script**: `start_server.py` with beautiful startup messages
- **Windows Batch File**: `start-dynamic.bat` for easy Windows startup
- **Port Information**: Shows exact URLs and ports on startup

## Configuration Options

### Port Management
```bash
# Fixed port (default)
API_PORT=5050
AUTO_FIND_PORT=false

# Dynamic port allocation
AUTO_FIND_PORT=true
PORT_RANGE_START=5050
PORT_RANGE_END=5100

# Try specific port first, then auto-find
API_PORT=5050
AUTO_FIND_PORT=true
PORT_RANGE_START=5051
PORT_RANGE_END=5100
```

### Server Configuration
```bash
HOST=0.0.0.0                    # Server host
LOG_LEVEL=INFO                   # Logging level
DEBUG=false                      # Debug mode
RELOAD=true                      # Auto-reload
```

## Usage Examples

### 1. Quick Start (Dynamic Port)
```bash
# Copy example config
cp config.example.env .env

# Start with dynamic port allocation
python start_server.py
```

### 2. Fixed Port
```bash
# Set fixed port
echo "API_PORT=5050" > .env
echo "AUTO_FIND_PORT=false" >> .env

# Start server
python start_server.py
```

### 3. Development Mode
```bash
# Development settings
echo "DEBUG=true" > .env
echo "RELOAD=true" >> .env
echo "LOG_LEVEL=DEBUG" >> .env
echo "AUTO_FIND_PORT=true" >> .env

# Start server
python start_server.py
```

### 4. Production Mode
```bash
# Production settings
echo "DEBUG=false" > .env
echo "RELOAD=false" >> .env
echo "LOG_LEVEL=INFO" >> .env
echo "AUTH_REQUIRED=true" >> .env
echo "API_PORT=5050" >> .env
echo "AUTO_FIND_PORT=false" >> .env

# Start server
python start_server.py
```

## Files Added/Modified

### New Files
- `start_server.py` - Dynamic port allocation startup script
- `start-dynamic.bat` - Windows batch file for easy startup
- `config.example.env` - Comprehensive configuration example
- `DYNAMIC_PORT_SYSTEM.md` - This documentation

### Modified Files
- `app/config.py` - Added dynamic port allocation and new configuration options
- `README.md` - Updated with new startup options and configuration

## Benefits

### ✅ **No More Port Conflicts**
- Automatically finds free ports
- No manual port hunting
- Works in development and production

### ✅ **Easy Configuration**
- All settings in one place
- Environment variable based
- Clear examples and documentation

### ✅ **Flexible Deployment**
- Works on Windows and Linux
- Supports both fixed and dynamic ports
- Easy to customize for different environments

### ✅ **Better Developer Experience**
- Clear startup messages
- Shows exact URLs and ports
- Easy to understand configuration

## Technical Implementation

### Port Finding Algorithm
```python
def find_free_port(start_port: int = 5050, max_attempts: int = 100) -> int:
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")
```

### Configuration Integration
- Uses Pydantic Settings for type safety
- Environment variable fallbacks
- Automatic validation and defaults
- LRU cache for performance

## Migration Guide

### From Old System
1. **No Breaking Changes**: Old configuration still works
2. **Optional Upgrade**: Can gradually adopt new features
3. **Backward Compatible**: All existing environment variables still supported

### To New System
1. Copy `config.example.env` to `.env`
2. Customize settings as needed
3. Use `python start_server.py` instead of direct uvicorn
4. Enjoy automatic port allocation!

## Troubleshooting

### Port Still in Use
- Check if other processes are using the port
- Increase `PORT_RANGE_END` for more options
- Use `netstat -ano | findstr :<PORT>` to find processes

### Configuration Not Loading
- Ensure `.env` file is in the project root
- Check environment variable names match exactly
- Verify file encoding is UTF-8

### Server Won't Start
- Check Python environment and dependencies
- Verify database migration is complete
- Check logs for specific error messages
