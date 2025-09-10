#!/usr/bin/env python3
"""
Regression Test Suite for RAS Room Manager
Tests the basic functionality of creating, listing, and deleting public chat rooms.
"""

import subprocess
import sys
import time
import random
import string
from datetime import datetime

class RASRegressionTest:
    def __init__(self, script_path="./ras-room-mgr.py"):
        self.script_path = script_path
        self.test_room_name = None
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = datetime.now()
        
    def generate_test_room_name(self):
        """Generate a unique test room name to avoid conflicts."""
        timestamp = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
        self.test_room_name = f"RegressionTest_{timestamp}_{random_suffix}"
        return self.test_room_name
    
    def run_command(self, args):
        """Run a RAS room manager command and return result."""
        try:
            cmd = [self.script_path] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result
        except subprocess.TimeoutExpired:
            print(f"    TIMEOUT: Command took too long: {' '.join(cmd)}")
            return None
        except Exception as e:
            print(f"    ERROR: Failed to run command: {e}")
            return None
    
    def check_room_exists(self, room_name, should_exist=True):
        """Check if a room exists in the public room list."""
        result = self.run_command(["get", "public"])
        
        if result is None or result.returncode != 0:
            return False, "Failed to get room list"
        
        room_found = room_name in result.stdout
        
        if should_exist and room_found:
            return True, f"Room '{room_name}' found in list"
        elif not should_exist and not room_found:
            return True, f"Room '{room_name}' not found in list (as expected)"
        elif should_exist and not room_found:
            return False, f"Room '{room_name}' not found in list (should exist)"
        else:  # not should_exist and room_found
            return False, f"Room '{room_name}' found in list (should not exist)"
    
    def test_create_room(self):
        """Test creating a public chat room."""
        print(f"  Creating public room: {self.test_room_name}")
        
        result = self.run_command(["create", "public", self.test_room_name])
        
        if result is None:
            return False, "Command failed to execute"
        
        if result.returncode == 0 and "created successfully" in result.stdout:
            return True, "Room created successfully"
        else:
            return False, f"Creation failed: {result.stdout} {result.stderr}"
    
    def test_delete_room(self):
        """Test deleting a public chat room."""
        print(f"  Deleting public room: {self.test_room_name}")
        
        result = self.run_command(["delete", "public", self.test_room_name])
        
        if result is None:
            return False, "Command failed to execute"
        
        if result.returncode == 0 and "deleted successfully" in result.stdout:
            return True, "Room deleted successfully"
        else:
            return False, f"Deletion failed: {result.stdout} {result.stderr}"
    
    def test_list_rooms(self):
        """Test listing public chat rooms."""
        print(f"  Listing public rooms")
        
        result = self.run_command(["get", "public"])
        
        if result is None:
            return False, "Command failed to execute"
        
        if result.returncode == 0 and "Successfully retrieved" in result.stdout:
            return True, "Room list retrieved successfully"
        else:
            return False, f"List failed: {result.stdout} {result.stderr}"
    
    def run_test(self, test_name, test_func):
        """Run a single test and track results."""
        print(f"\nRunning test: {test_name}")
        
        try:
            success, message = test_func()
            
            if success:
                print(f"  PASS: {message}")
                self.passed_tests += 1
            else:
                print(f"  FAIL: {message}")
                self.failed_tests += 1
                
            return success
            
        except Exception as e:
            print(f"  ERROR: Test crashed: {e}")
            self.failed_tests += 1
            return False
    
    def cleanup_test_room(self):
        """Clean up any leftover test room."""
        if self.test_room_name:
            print(f"\nCleaning up test room: {self.test_room_name}")
            result = self.run_command(["delete", "public", self.test_room_name])
            if result and result.returncode == 0:
                print(f"  Test room cleaned up")
            else:
                print(f"  Could not clean up test room (may not exist)")
    
    def run_full_regression_test(self):
        """Run the complete regression test suite."""
        print(f"Starting RAS Room Manager Regression Tests")
        print(f"Test started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Script path: {self.script_path}")
        print(f"=" * 60)
        
        # Generate unique test room name
        self.generate_test_room_name()
        print(f"Test room name: {self.test_room_name}")
        
        # Clean up any existing test room first
        self.cleanup_test_room()
        
        # Test 1: Basic room listing (should work even with no rooms)
        self.run_test("List Public Rooms (Initial)", self.test_list_rooms)
        
        # Test 2: Verify test room doesn't exist initially
        def test_room_not_exists():
            return self.check_room_exists(self.test_room_name, should_exist=False)
        self.run_test("Verify Test Room Doesn't Exist Initially", test_room_not_exists)
        
        # Test 3: Create test room
        create_success = self.run_test("Create Public Room", self.test_create_room)
        
        if create_success:
            # Give server a moment to process
            time.sleep(1)
            
            # Test 4: Verify room exists after creation
            def test_room_exists():
                return self.check_room_exists(self.test_room_name, should_exist=True)
            self.run_test("Verify Room Exists After Creation", test_room_exists)
            
            # Test 5: List rooms again (should show our new room)
            self.run_test("List Public Rooms (With Test Room)", self.test_list_rooms)
            
            # Test 6: Delete the test room
            delete_success = self.run_test("Delete Public Room", self.test_delete_room)
            
            if delete_success:
                # Give server a moment to process
                time.sleep(1)
                
                # Test 7: Verify room no longer exists
                def test_room_deleted():
                    return self.check_room_exists(self.test_room_name, should_exist=False)
                self.run_test("Verify Room Deleted Successfully", test_room_deleted)
                
                # Test 8: Final room list (should not show our room)
                self.run_test("List Public Rooms (Final)", self.test_list_rooms)
        
        # Final cleanup
        self.cleanup_test_room()
        
        # Print results
        self.print_test_results()
    
    def print_test_results(self):
        """Print final test results."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        total_tests = self.passed_tests + self.failed_tests
        
        print(f"\n" + "=" * 60)
        print(f"TEST RESULTS SUMMARY")
        print(f"=" * 60)
        print(f"Total duration: {duration.total_seconds():.2f} seconds")
        print(f"Total tests run: {total_tests}")
        print(f"Tests passed: {self.passed_tests}")
        print(f"Tests failed: {self.failed_tests}")
        
        if self.failed_tests == 0:
            print(f"ALL TESTS PASSED! RAS Room Manager is working correctly.")
            success_rate = 100.0
        else:
            success_rate = (self.passed_tests / total_tests) * 100 if total_tests > 0 else 0
            print(f"Some tests failed. Success rate: {success_rate:.1f}%")
        
        print(f"Success rate: {success_rate:.1f}%")
        print(f"=" * 60)
        
        # Return exit code based on results
        return 0 if self.failed_tests == 0 else 1

def main():
    """Main function to run regression tests."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Regression test suite for RAS Room Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Test with default script path
  %(prog)s --script ./ras-room-mgr.py        # Test with specific script path
  %(prog)s --script /path/to/ras-room-mgr.py # Test with full path
        """
    )
    
    parser.add_argument(
        "--script",
        default="./ras-room-mgr.py",
        help="Path to the ras-room-mgr.py script (default: ./ras-room-mgr.py)"
    )
    
    args = parser.parse_args()
    
    # Create and run test suite
    test_suite = RASRegressionTest(args.script)
    exit_code = test_suite.run_full_regression_test()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
