"""
Test Dashboard Server
Quick script to test the new Sentinel SOC dashboard
"""

import uvicorn
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🛡️  SENTINEL SOC DASHBOARD TEST SERVER")
    print("="*60)
    print("\n📍 Dashboard will be available at:")
    print("   → http://localhost:8000/")
    print("\n📚 API Documentation:")
    print("   → http://localhost:8000/docs")
    print("\n📊 Stats Endpoint:")
    print("   → http://localhost:8000/api/stats")
    print("\n" + "="*60)
    print("Press CTRL+C to stop the server\n")
    
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
