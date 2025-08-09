#!/usr/bin/env python3
"""
AI Backend Test Suite
Tests all endpoints for the Gateway (port 5050) and vLLM (port 8000) servers.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

# Configuration
GATEWAY_BASE_URL = "http://localhost:5050"
VLLM_BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text: str, color: str = Colors.WHITE):
    """Print colored text to console"""
    print(f"{color}{text}{Colors.END}")

def print_header(text: str):
    """Print a formatted header"""
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(f"{text.center(60)}", Colors.BOLD + Colors.CYAN)
    print_colored(f"{'='*60}", Colors.CYAN)

def print_test(test_name: str, success: bool, details: str = ""):
    """Print test result"""
    status = f"{'✅ PASS' if success else '❌ FAIL'}"
    color = Colors.GREEN if success else Colors.RED
    print_colored(f"{status} {test_name}", color)
    if details:
        print_colored(f"     {details}", Colors.WHITE)

def make_request(method: str, url: str, **kwargs) -> tuple[bool, Optional[Dict[Any, Any]], str]:
    """Make HTTP request and return (success, response_data, error_message)"""
    try:
        response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
        
        if response.status_code >= 400:
            return False, None, f"HTTP {response.status_code}: {response.text[:200]}"
        
        try:
            data = response.json()
        except:
            data = {"raw_response": response.text}
        
        return True, data, ""
    
    except requests.exceptions.ConnectionError:
        return False, None, "Connection refused - server not running?"
    except requests.exceptions.Timeout:
        return False, None, f"Request timeout after {TIMEOUT}s"
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"

def test_health_endpoints():
    """Test health check endpoints"""
    print_header("HEALTH CHECK TESTS")
    
    # Gateway health
    success, data, error = make_request("GET", f"{GATEWAY_BASE_URL}/health")
    if success:
        print_test("Gateway Health Check", True, f"Status: {data.get('status', 'unknown')}")
    else:
        print_test("Gateway Health Check", False, error)
    
    # vLLM health
    success, data, error = make_request("GET", f"{VLLM_BASE_URL}/health")
    if success:
        print_test("vLLM Health Check", True, "Server responding")
    else:
        print_test("vLLM Health Check", False, error)

def test_models_endpoints():
    """Test model listing endpoints"""
    print_header("MODEL LISTING TESTS")
    
    # Gateway models
    success, data, error = make_request("GET", f"{GATEWAY_BASE_URL}/api/models")
    if success:
        models = data.get('data', []) if isinstance(data, dict) else []
        model_names = [m.get('id', 'unknown') for m in models] if models else []
        print_test("Gateway Models List", True, f"Found {len(models)} models: {model_names}")
    else:
        print_test("Gateway Models List", False, error)
    
    # vLLM models
    success, data, error = make_request("GET", f"{VLLM_BASE_URL}/v1/models")
    if success:
        models = data.get('data', []) if isinstance(data, dict) else []
        model_names = [m.get('id', 'unknown') for m in models] if models else []
        print_test("vLLM Models List", True, f"Found {len(models)} models: {model_names}")
    else:
        print_test("vLLM Models List", False, error)

def test_chat_endpoints():
    """Test chat completion endpoints"""
    print_header("CHAT COMPLETION TESTS")
    
    # Gateway chat payload (simplified format)
    gateway_chat_payload = {
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "message": "Hello! Can you tell me a very short joke?",
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    # vLLM chat payload (OpenAI format)
    vllm_chat_payload = {
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "messages": [
            {"role": "user", "content": "Hello! Can you tell me a very short joke?"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    # Gateway chat
    print_colored("Testing Gateway Chat...", Colors.YELLOW)
    success, data, error = make_request("POST", f"{GATEWAY_BASE_URL}/api/chat", json=gateway_chat_payload)
    if success:
        if 'choices' in data and len(data['choices']) > 0:
            response_text = data['choices'][0].get('message', {}).get('content', '').strip()
            print_test("Gateway Chat Completion", True, f"Response: '{response_text[:100]}...'")
        else:
            print_test("Gateway Chat Completion", False, "No response content in reply")
    else:
        print_test("Gateway Chat Completion", False, error)
    
    # Direct vLLM chat
    print_colored("Testing Direct vLLM Chat...", Colors.YELLOW)
    success, data, error = make_request("POST", f"{VLLM_BASE_URL}/v1/chat/completions", json=vllm_chat_payload)
    if success:
        if 'choices' in data and len(data['choices']) > 0:
            response_text = data['choices'][0].get('message', {}).get('content', '').strip()
            print_test("Direct vLLM Chat", True, f"Response: '{response_text[:100]}...'")
        else:
            print_test("Direct vLLM Chat", False, "No response content in reply")
    else:
        print_test("Direct vLLM Chat", False, error)

def test_embeddings_endpoints():
    """Test embeddings endpoints"""
    print_header("EMBEDDINGS TESTS")
    
    embeddings_payload = {
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "input": "This is a test sentence for embeddings"
    }
    
    # Gateway embeddings
    success, data, error = make_request("POST", f"{GATEWAY_BASE_URL}/api/embeddings", json=embeddings_payload)
    if success:
        if 'data' in data and len(data['data']) > 0:
            embedding = data['data'][0].get('embedding', [])
            print_test("Gateway Embeddings", True, f"Generated {len(embedding)}-dimensional embedding")
        else:
            print_test("Gateway Embeddings", False, "No embedding data in response")
    else:
        print_test("Gateway Embeddings", False, error)
    
    # Direct vLLM embeddings
    success, data, error = make_request("POST", f"{VLLM_BASE_URL}/v1/embeddings", json=embeddings_payload)
    if success:
        if 'data' in data and len(data['data']) > 0:
            embedding = data['data'][0].get('embedding', [])
            print_test("Direct vLLM Embeddings", True, f"Generated {len(embedding)}-dimensional embedding")
        else:
            print_test("Direct vLLM Embeddings", False, "No embedding data in response")
    else:
        print_test("Direct vLLM Embeddings", False, error)

def test_streaming_chat():
    """Test streaming chat endpoint"""
    print_header("STREAMING CHAT TEST")
    
    # Gateway streaming payload (simplified format, correct endpoint)
    gateway_stream_payload = {
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "message": "Count from 1 to 5",
        "max_tokens": 30
    }
    
    # Test Gateway streaming
    try:
        print_colored("Testing Gateway Streaming...", Colors.YELLOW)
        response = requests.post(
            f"{GATEWAY_BASE_URL}/api/chat/stream",  # Correct endpoint for Gateway streaming
            json=gateway_stream_payload, 
            stream=True, 
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            chunks = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        chunks.append(line_str[6:])  # Remove 'data: ' prefix
                        if len(chunks) >= 3:  # Get first few chunks
                            break
            
            if chunks:
                print_test("Gateway Streaming Chat", True, f"Received {len(chunks)} stream chunks")
            else:
                print_test("Gateway Streaming Chat", False, "No stream chunks received")
        else:
            print_test("Gateway Streaming Chat", False, f"HTTP {response.status_code}")
    
    except Exception as e:
        print_test("Gateway Streaming Chat", False, f"Error: {str(e)}")

def test_performance():
    """Basic performance test"""
    print_header("PERFORMANCE TEST")
    
    # Gateway format for performance test
    simple_payload = {
        "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "message": "Hi",
        "max_tokens": 10
    }
    
    # Time the request
    start_time = time.time()
    success, data, error = make_request("POST", f"{GATEWAY_BASE_URL}/api/chat", json=simple_payload)
    end_time = time.time()
    
    response_time = end_time - start_time
    
    if success:
        print_test("Performance Test", True, f"Response time: {response_time:.2f}s")
        if response_time < 5.0:
            print_colored("     ⚡ Fast response!", Colors.GREEN)
        elif response_time < 10.0:
            print_colored("     ⏱️  Moderate response time", Colors.YELLOW)
        else:
            print_colored("     🐌 Slow response time", Colors.RED)
    else:
        print_test("Performance Test", False, error)

def main():
    """Run all tests"""
    print_colored("🚀 AI Backend Test Suite", Colors.BOLD + Colors.MAGENTA)
    print_colored(f"Gateway: {GATEWAY_BASE_URL}", Colors.CYAN)
    print_colored(f"vLLM: {VLLM_BASE_URL}", Colors.CYAN)
    
    # Run all test suites
    test_health_endpoints()
    test_models_endpoints()
    test_chat_endpoints()
    test_embeddings_endpoints()
    test_streaming_chat()
    test_performance()
    
    print_header("TESTING COMPLETE")
    print_colored("💡 If any tests failed, check that both servers are running:", Colors.YELLOW)
    print_colored("   - Run START-HERE.bat to launch servers", Colors.WHITE)
    print_colored("   - Wait for both terminals to show 'Application startup complete'", Colors.WHITE)
    print_colored("   - Then run this test script again", Colors.WHITE)

if __name__ == "__main__":
    main()
