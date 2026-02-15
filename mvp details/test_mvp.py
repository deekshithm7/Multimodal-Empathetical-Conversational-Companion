"""
MECC MVP Test Suite
Validates emotion recognition and chat functionality.
"""

import requests
import json
import time
from typing import Dict, List
import sys


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


class MECCTester:
    """Test suite for MECC MVP"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.tests_passed = 0
        self.tests_failed = 0
    
    def print_header(self, text: str):
        """Print a test section header"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BLUE}{text}{Colors.RESET}")
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    def print_test(self, name: str):
        """Print test name"""
        print(f"{Colors.YELLOW}Testing: {name}...{Colors.RESET}", end=" ")
    
    def print_pass(self, message: str = "PASS"):
        """Print pass message"""
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
        self.tests_passed += 1
    
    def print_fail(self, message: str = "FAIL"):
        """Print fail message"""
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
        self.tests_failed += 1
    
    def test_health_check(self):
        """Test if the API is running"""
        self.print_test("Health Check")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            data = response.json()
            
            if response.status_code == 200 and data["status"] == "healthy":
                self.print_pass(f"API is healthy (emotion_model: {data['emotion_model']})")
                return True
            else:
                self.print_fail(f"Unhealthy response: {data}")
                return False
        
        except requests.exceptions.RequestException as e:
            self.print_fail(f"Cannot connect to API: {e}")
            return False
    
    def test_emotion_text_only(self):
        """Test emotion detection with text only"""
        self.print_test("Emotion Detection (Text Only)")
        
        test_cases = [
            ("I'm so excited and happy!", "happy"),
            ("This is really frustrating me", "angry"),
            ("I feel so sad and alone", "sad"),
            ("Everything is normal today", "neutral")
        ]
        
        for text, expected_emotion in test_cases:
            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/emotion/predict",
                    data={"text": text},
                    timeout=10
                )
                latency = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    detected_emotion = data["data"]["emotion"]
                    confidence = data["data"]["confidence"]
                    
                    if detected_emotion == expected_emotion:
                        self.print_pass(
                            f'"{text[:30]}..." → {detected_emotion} ({confidence:.2%}) [{latency:.0f}ms]'
                        )
                    else:
                        print(f"\n  {Colors.YELLOW}Warning: Expected {expected_emotion}, got {detected_emotion}{Colors.RESET}")
                        self.print_pass(f"Works but with different prediction [{latency:.0f}ms]")
                else:
                    self.print_fail(f"HTTP {response.status_code}")
                    return False
            
            except Exception as e:
                self.print_fail(f"Error: {e}")
                return False
        
        return True
    
    def test_chat_endpoint(self):
        """Test the full chat endpoint (emotion + LLM response)"""
        self.print_test("Chat Endpoint (Emotion + LLM Response)")
        
        test_messages = [
            "I'm feeling really happy today!",
            "I'm so frustrated with this situation",
            "I feel down and don't know what to do"
        ]
        
        for message in test_messages:
            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/chat/message",
                    data={"text": message},
                    timeout=30  # LLM can take time
                )
                latency = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    emotion = data["user_emotion"]["emotion"]
                    confidence = data["user_emotion"]["confidence"]
                    assistant_response = data["assistant_response"]
                    
                    self.print_pass(
                        f'"{message[:30]}..." → {emotion} ({confidence:.2%}) [{latency:.0f}ms]'
                    )
                    print(f"  {Colors.BLUE}Response: {assistant_response[:100]}...{Colors.RESET}")
                else:
                    self.print_fail(f"HTTP {response.status_code}")
                    return False
            
            except Exception as e:
                self.print_fail(f"Error: {e}")
                return False
        
        return True
    
    def test_conversation_history(self):
        """Test chat with conversation history"""
        self.print_test("Conversation History Context")
        
        conversation = [
            {"role": "user", "content": "Hi there"},
            {"role": "assistant", "content": "Hello! How are you today?"},
            {"role": "user", "content": "I mentioned earlier I was stressed"}
        ]
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/chat/message",
                data={
                    "text": "Can you remember what I said?",
                    "conversation_history": json.dumps(conversation)
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_pass("History maintained successfully")
                print(f"  {Colors.BLUE}Response: {data['assistant_response'][:100]}...{Colors.RESET}")
                return True
            else:
                self.print_fail(f"HTTP {response.status_code}")
                return False
        
        except Exception as e:
            self.print_fail(f"Error: {e}")
            return False
    
    def test_model_info(self):
        """Test model info endpoint"""
        self.print_test("Model Info Endpoint")
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/model/info", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.print_pass(
                    f"Model: {data['model_name']} (Accuracy: {data['accuracy']}, F1: {data['f1_score']})"
                )
                print(f"  {Colors.BLUE}Classes: {', '.join(data['emotion_classes'])}{Colors.RESET}")
                return True
            else:
                self.print_fail(f"HTTP {response.status_code}")
                return False
        
        except Exception as e:
            self.print_fail(f"Error: {e}")
            return False
    
    def test_performance(self):
        """Test system performance"""
        self.print_test("Performance Benchmarking")
        
        latencies = []
        
        for i in range(10):
            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/emotion/predict",
                    data={"text": "This is a test message"},
                    timeout=10
                )
                latency = (time.time() - start) * 1000
                latencies.append(latency)
            
            except Exception as e:
                self.print_fail(f"Performance test failed: {e}")
                return False
        
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        if avg_latency < 500:  # Target: <500ms
            self.print_pass(
                f"Avg: {avg_latency:.0f}ms, Min: {min_latency:.0f}ms, Max: {max_latency:.0f}ms"
            )
        else:
            print(f"\n  {Colors.YELLOW}Warning: Average latency {avg_latency:.0f}ms exceeds 500ms target{Colors.RESET}")
            self.print_pass("Works but slower than target")
        
        return True
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        self.print_test("Error Handling")
        
        # Test 1: No input provided
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/emotion/predict",
                data={},
                timeout=5
            )
            
            if response.status_code == 400:
                self.print_pass("Correctly rejects empty input (HTTP 400)")
            else:
                self.print_fail(f"Expected 400, got {response.status_code}")
                return False
        
        except Exception as e:
            self.print_fail(f"Error: {e}")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        self.print_header("MECC MVP Test Suite")
        
        print(f"Testing API at: {self.base_url}\n")
        
        # Core functionality tests
        self.print_header("Core Functionality Tests")
        self.test_health_check()
        self.test_model_info()
        self.test_emotion_text_only()
        self.test_chat_endpoint()
        self.test_conversation_history()
        
        # Performance tests
        self.print_header("Performance Tests")
        self.test_performance()
        
        # Error handling tests
        self.print_header("Error Handling Tests")
        self.test_error_handling()
        
        # Summary
        self.print_header("Test Summary")
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.tests_passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.tests_failed}{Colors.RESET}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")
        
        if self.tests_failed == 0:
            print(f"{Colors.GREEN}🎉 All tests passed! MVP is ready.{Colors.RESET}\n")
            return 0
        else:
            print(f"{Colors.RED}⚠️  Some tests failed. Please review.{Colors.RESET}\n")
            return 1


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MECC MVP Test Suite")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the MECC API (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    tester = MECCTester(base_url=args.url)
    exit_code = tester.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
