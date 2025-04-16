#!/usr/bin/env python
"""
Main entry point for the Newspaper URL Crawler application
"""
import uvicorn
import logging
import os
import socket

def find_free_port():
    """Find a free port on the system"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    logger = logging.getLogger("main")
    
    # Try to get port from environment or use default
    try:
        port = int(os.getenv("PORT", 8000))
        # Try to check if port is available
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
    except OSError:
        logger.warning(f"Port {port} is already in use or access is denied. Finding a free port...")
        port = find_free_port()
    
    logger.info(f"Starting Newspaper URL Crawler on port {port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)