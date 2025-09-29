#!/usr/bin/env python3
"""
Quick setup script to configure API keys and test the pipeline
"""
import os
import sys
from pathlib import Path

def setup_api_keys():
    """Interactive setup for API keys"""
    print("🚀 YouTube Space Video Pipeline - API Key Setup")
    print("=" * 50)
    
    env_file = Path('.env')
    
    if env_file.exists():
        print("✅ .env file already exists")
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check which keys are already configured
        configured_keys = []
        if 'TTS_OPENAI_API_KEY=' in content and 'your_tts_openai_api_key_here' not in content:
            configured_keys.append('TTS OpenAI')
        if 'PEXELS_API_KEY=' in content and 'your_pexels_api_key_here' not in content:
            configured_keys.append('Pexels')
        if 'UNSPLASH_ACCESS_KEY=' in content and 'your_unsplash_access_key_here' not in content:
            configured_keys.append('Unsplash')
        
        if configured_keys:
            print(f"✅ Already configured: {', '.join(configured_keys)}")
        
        print("\n📝 Please edit the .env file and replace the placeholder values with your actual API keys:")
        print("   - TTS_OPENAI_API_KEY=your_actual_tts_key")
        print("   - PEXELS_API_KEY=your_actual_pexels_key") 
        print("   - UNSPLASH_ACCESS_KEY=your_actual_unsplash_key")
        print("   - NASA_API_KEY=your_actual_nasa_key (optional)")
        
    else:
        print("❌ .env file not found. Please run the setup first.")
        return False
    
    return True

def test_configuration():
    """Test if API keys are properly configured"""
    print("\n🧪 Testing API Configuration...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_keys = {
        'TTS_OPENAI_API_KEY': 'TTS OpenAI',
        'PEXELS_API_KEY': 'Pexels', 
        'UNSPLASH_ACCESS_KEY': 'Unsplash'
    }
    
    missing_keys = []
    placeholder_keys = []
    
    for env_var, service_name in required_keys.items():
        value = os.getenv(env_var)
        if not value:
            missing_keys.append(service_name)
        elif 'your_' in value and '_here' in value:
            placeholder_keys.append(service_name)
        else:
            print(f"✅ {service_name}: Configured")
    
    if missing_keys:
        print(f"❌ Missing keys: {', '.join(missing_keys)}")
    
    if placeholder_keys:
        print(f"⚠️  Placeholder values detected: {', '.join(placeholder_keys)}")
        print("   Please replace with your actual API keys")
    
    nasa_key = os.getenv('NASA_API_KEY', 'DEMO_KEY')
    if nasa_key == 'DEMO_KEY':
        print("ℹ️  NASA: Using DEMO_KEY (limited requests)")
    else:
        print("✅ NASA: Custom key configured")
    
    all_configured = not missing_keys and not placeholder_keys
    
    if all_configured:
        print("\n🎉 All API keys are properly configured!")
        return True
    else:
        print("\n❌ Please configure the missing/placeholder API keys in .env file")
        return False

def run_health_check():
    """Run a health check on all services"""
    print("\n🏥 Running Health Check...")
    
    try:
        # Add pipeline to path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from pipeline import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator()
        health_status = orchestrator.health_check_all_services()
        
        print("\n=== Service Health Status ===")
        for service, status in health_status.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {service}: {'OK' if status else 'FAILED'}")
        
        all_healthy = all(health_status.values())
        if all_healthy:
            print("\n🎉 All services are healthy! Ready to generate videos.")
        else:
            print("\n⚠️  Some services are not available. Check Docker containers and API keys.")
        
        return all_healthy
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    print("🚀 YouTube Space Video Pipeline Setup")
    print("=" * 40)
    
    # Step 1: Setup API keys
    if not setup_api_keys():
        return
    
    input("\n📝 Press Enter after you've configured your API keys in .env file...")
    
    # Step 2: Test configuration
    if not test_configuration():
        return
    
    # Step 3: Health check
    print("\n🔍 Would you like to run a health check? (y/n): ", end="")
    if input().lower().startswith('y'):
        run_health_check()
    
    print("\n🎬 Setup complete! You can now run:")
    print("   python main.py --duration 120 --voice alloy")
    print("   python scheduler.py  # For automated runs")

if __name__ == "__main__":
    main()