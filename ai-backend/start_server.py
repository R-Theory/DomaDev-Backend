#!/usr/bin/env python3
"""
Dynamic port allocation server startup script.
This script finds an available port and starts the FastAPI server.
"""

import sys
import uvicorn
from app.config import get_settings


def main():
    """Start the server with dynamic port allocation"""
    settings = get_settings()
    
    # Get available port
    port = settings.get_available_port()
    
    print(f"🚀 Starting AI Backend Server...")
    print(f"📍 Host: {settings.host}")
    print(f"🔌 Port: {port}")
    print(f"🌐 URL: http://{settings.host}:{port}")
    print(f"📊 API Docs: http://{settings.host}:{port}/docs")
    print(f"🔧 Auto-reload: {settings.reload}")
    print(f"🐛 Debug mode: {settings.debug}")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=port,
            reload=settings.reload,
            log_level=settings.log_level.lower(),
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
