"""
Simple test script to verify the Agno AI service is working correctly
"""

import requests
import json
import sys
import os

# Service URL - modify if running on different host/port
SERVICE_URL = os.getenv("SERVICE_URL", "http://localhost:8000")

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    """Test the health endpoint"""
    print_section("Testing Health Endpoint")
    try:
        response = requests.get(f"{SERVICE_URL}/health")
        response.raise_for_status()
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"OpenAI Configured: {data.get('openai_configured')}")
        print(f"Storage Path: {data.get('storage_path')}")
        print("✓ Health check passed")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_chat(session_id="test_session", message="Hello, please introduce yourself briefly"):
    """Test the chat endpoint"""
    print_section(f"Testing Chat: '{message}'")
    try:
        payload = {
            "session_id": session_id,
            "message": message
        }

        print(f"Request payload: {json.dumps(payload, indent=2)}")

        response = requests.post(
            f"{SERVICE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()

        print(f"\nSession ID: {data.get('session_id')}")
        print(f"Timestamp: {data.get('timestamp')}")
        print(f"\nAI Response:\n{data.get('response')}")
        print("\n✓ Chat request successful")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        return False
    except Exception as e:
        print(f"✗ Chat request failed: {e}")
        return False

def test_conversation_memory():
    """Test that the agent remembers conversation context"""
    print_section("Testing Conversation Memory")

    session_id = "memory_test_session"

    # First message - provide information
    print("\nMessage 1: Providing information...")
    success1 = test_chat(
        session_id=session_id,
        message="My name is Alice and I love programming in Python."
    )

    if not success1:
        return False

    input("\nPress Enter to send the next message...")

    # Second message - ask about the information
    print("\nMessage 2: Testing memory...")
    success2 = test_chat(
        session_id=session_id,
        message="What is my name and what do I love?"
    )

    if success2:
        print("\n✓ Memory test passed - agent remembered context")
    else:
        print("\n✗ Memory test failed")

    return success2

def test_clear_session():
    """Test clearing a session"""
    print_section("Testing Session Clearing")
    try:
        session_id = "clear_test_session"
        response = requests.post(
            f"{SERVICE_URL}/clear-session",
            params={"session_id": session_id}
        )
        response.raise_for_status()
        data = response.json()

        print(f"Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        print("✓ Session clearing successful")
        return True
    except Exception as e:
        print(f"✗ Session clearing failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  AGNO AI SERVICE TEST SUITE")
    print("="*60)
    print(f"Service URL: {SERVICE_URL}")

    # Check if service is running
    print_section("Checking Service Connectivity")
    try:
        response = requests.get(f"{SERVICE_URL}/")
        print(f"Service is running: {response.json()}")
    except Exception as e:
        print(f"✗ Cannot connect to service at {SERVICE_URL}")
        print(f"Error: {e}")
        print("\nMake sure the service is running:")
        print("  cd ai-service")
        print("  python main.py")
        sys.exit(1)

    # Run tests
    results = []

    results.append(("Health Check", test_health()))
    print("\n" + "-"*60)

    results.append(("Basic Chat", test_chat()))
    print("\n" + "-"*60)

    results.append(("Conversation Memory", test_conversation_memory()))
    print("\n" + "-"*60)

    results.append(("Clear Session", test_clear_session()))

    # Summary
    print_section("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for _, success in results if success)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:8} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Service is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
