"""
RAVDESS Test Runner

Quick test on actors 1-9 to verify pipeline works.
Runs just 2 models: A+T and V+A+T
"""

import subprocess
import sys
import time

def run_training(config_path, description):
    """Run training with given config"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Config: {config_path}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, "train.py", "--config", config_path],
            check=True,
            capture_output=False
        )
        
        elapsed = time.time() - start_time
        print(f"\n✓ {description} completed in {elapsed:.1f}s")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} FAILED!")
        print(f"Error: {e}")
        return False

def main():
    print("="*60)
    print("RAVDESS PIPELINE TEST")
    print("Testing on actors 1-9 with 3 epochs each")
    print("="*60)
    
    # Test configs (just 2 models to verify setup)
    tests = [
        ("../configs/ravdess_at_test.json", "Audio + Text (A+T)"),
        ("../configs/ravdess_vat_test.json", "Video + Audio + Text (V+A+T)")
    ]
    
    results = {}
    total_start = time.time()
    
    for config, desc in tests:
        success = run_training(config, desc)
        results[desc] = success
        
        if not success:
            print("\n⚠️  Test failed! Stopping.")
            break
    
    total_elapsed = time.time() - total_start
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for desc, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {desc}")
    
    print(f"\nTotal time: {total_elapsed/60:.1f} minutes")
    
    if all(results.values()):
        print("\n🎉 All tests passed! Ready for full 24-actor run.")
        print("\nNext steps:")
        print("1. Git commit these changes")
        print("2. Run on PC with all 24 actors")
        print("3. Use ravdess_run_all.py for full ablation")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")

if __name__ == '__main__':
    main()
