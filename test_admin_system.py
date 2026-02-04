"""
Test the admin panel configuration system
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_get_config():
    """Test getting current configuration"""
    print("📥 Testing GET /api/dashboard-config...")
    try:
        response = requests.get(f"{API_BASE}/api/dashboard-config")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Successfully loaded config")
            print(f"   Bot Name: {config['branding']['name']}")
            print(f"   Primary Color: {config['colors']['primary']}")
            print(f"   Team Members: {len(config['team'])}")
            print(f"   Features: {len(config['features'])}")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_save_config():
    """Test saving configuration"""
    print("\n💾 Testing POST /api/save-config...")
    
    # First get current config
    try:
        response = requests.get(f"{API_BASE}/api/dashboard-config")
        config = response.json()
        
        # Modify something small
        original_name = config['branding']['name']
        config['branding']['name'] = "Test Bot"
        
        # Save it
        response = requests.post(
            f"{API_BASE}/api/save-config",
            json=config
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully saved config")
            print(f"   Message: {result['message']}")
            
            # Restore original
            config['branding']['name'] = original_name
            requests.post(f"{API_BASE}/api/save-config", json=config)
            print(f"   ✅ Restored original name: {original_name}")
            
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_admin_panel():
    """Test admin panel loads"""
    print("\n🎨 Testing admin panel accessibility...")
    try:
        response = requests.get(f"{API_BASE}/static/admin.html")
        if response.status_code == 200:
            html = response.text
            if 'Dashboard Admin Panel' in html:
                print("✅ Admin panel loads successfully")
                return True
            else:
                print("❌ Admin panel HTML doesn't contain expected content")
                return False
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_main_dashboard():
    """Test main dashboard loads"""
    print("\n🏠 Testing main dashboard...")
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            html = response.text
            if 'Sentinel SOC' in html or 'Dashboard' in html:
                print("✅ Main dashboard loads successfully")
                return True
            else:
                print("⚠️ Dashboard loaded but content seems unusual")
                return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 Admin Panel Configuration System Test")
    print("=" * 60)
    print()
    print("⚠️ Make sure the server is running: python test_dashboard.py")
    print()
    
    results = {
        'Main Dashboard': test_main_dashboard(),
        'Admin Panel': test_admin_panel(),
        'Get Config': test_get_config(),
        'Save Config': test_save_config()
    }
    
    print()
    print("=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s} {status}")
    
    print()
    
    if all(results.values()):
        print("🎉 All tests passed! Admin system is ready to use.")
        print()
        print("🚀 Next Steps:")
        print("   1. Open http://localhost:8000/static/admin.html")
        print("   2. Customize your dashboard settings")
        print("   3. Click Save in each section")
        print("   4. Refresh main dashboard to see changes")
    else:
        print("⚠️ Some tests failed. Check errors above.")
        print()
        print("Common issues:")
        print("   - Server not running? Run: python test_dashboard.py")
        print("   - Port already in use? Kill other processes on port 8000")
        print("   - File permissions? Check api/static/ folder permissions")
    
    print()

if __name__ == "__main__":
    main()
