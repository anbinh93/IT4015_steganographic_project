#!/usr/bin/env python3
# run_tests.py - Test runner for the steganography project

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run all tests for the steganography project"""
    
    print("🧪 Running Steganography Tests...")
    print("=" * 50)
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(current_dir))
    
    try:
        # Try to import and run tests directly
        import unittest
        
        # Discover and run tests
        loader = unittest.TestLoader()
        suite = loader.discover('tests', pattern='test_*.py')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print("\n" + "=" * 50)
        if result.wasSuccessful():
            print("✅ All tests passed!")
            return 0
        else:
            print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
            return 1
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

def run_specific_test(test_name):
    """Run a specific test"""
    try:
        import unittest
        sys.path.insert(0, str(Path(__file__).parent.absolute()))
        
        # Import specific test classes
        from tests.test_steganography import (
            TestImageSteganography, TestAudioSteganography, 
            TestVideoSteganography, TestUtilities, TestExceptions
        )
        
        # Run specific test
        suite = unittest.TestSuite()
        
        if test_name == "image":
            suite.addTest(unittest.makeSuite(TestImageSteganography))
        elif test_name == "audio":
            suite.addTest(unittest.makeSuite(TestAudioSteganography))
        elif test_name == "video":
            suite.addTest(unittest.makeSuite(TestVideoSteganography))
        elif test_name == "utils":
            suite.addTest(unittest.makeSuite(TestUtilities))
        elif test_name == "exceptions":
            suite.addTest(unittest.makeSuite(TestExceptions))
        else:
            print(f"❌ Unknown test: {test_name}")
            print("Available tests: image, audio, video, utils, exceptions")
            return 1
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        # Run all tests
        exit_code = run_tests()
    
    sys.exit(exit_code) 