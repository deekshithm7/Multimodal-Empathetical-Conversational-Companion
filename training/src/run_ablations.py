import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_ablations():
    """
    Run all 7 ablation studies:
    V, A, T, VA, VT, AT, VAT
    """
    
    ablations = [
        ('vision_only', 'Vision Only'),
        ('audio_only', 'Audio Only'),
        ('text_only', 'Text Only'),
        ('va', 'Vision + Audio'),
        ('vt', 'Vision + Text'),
        ('at', 'Audio + Text'),
        ('vat', 'Vision + Audio + Text'),
    ]
    
    results = {}
    
    print("="*60)
    print("Starting Ablation Studies - IEMOCAP 4-Class Emotion Recognition")
    print("="*60)
    
    for config_name, description in ablations:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Config: ../configs/{config_name}.json")
        print(f"{'='*60}\n")
        
        config_path = f"../configs/{config_name}.json"
        
        # Run training
        cmd = [
            r".\venv311\Scripts\python.exe",
            "train.py",
            "--config", config_path,
            "--train_index", "../train_index.json",
            "--test_index", "../test_index.json"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(result.stdout)
            
            # Parse the last line for metrics (this is a simple approach)
            # You might need to save metrics to a file in train.py for more robust parsing
            results[description] = "Completed"
            
        except subprocess.CalledProcessError as e:
            print(f"Error running {description}:")
            print(e.stderr)
            results[description] = "Failed"
    
    # Save summary
    summary_file = Path("../checkpoints/ablation_results.json")
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2)
    
    print("\n" + "="*60)
    print("Ablation Studies Complete!")
    print("="*60)
    print(f"Results saved to: {summary_file}")
    
    for desc, status in results.items():
        print(f"  {desc:<30} {status}")


if __name__ == '__main__':
    run_ablations()
