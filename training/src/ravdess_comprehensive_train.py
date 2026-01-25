"""
RAVDESS Comprehensive Training Runner

Automates training experiments across:
- All modality combinations (T, A, V, A+T, V+A, V+T, V+A+T)
- Varied hyperparameters (lr, dropout, batch_size, weight_decay)
- Early stopping, LR scheduling, L2 normalization
- Results logged to RAVDESS_TRAINING_RESULTS.md

Usage:
    python ravdess_comprehensive_train.py --num_experiments 20  # Random sample
    python ravdess_comprehensive_train.py --full_grid           # All combinations (slow!)
"""

import subprocess
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
import itertools

# Hyperparameter grid
HYPERPARAMS = {
    'lr': [0.0001, 0.0005, 0.001, 0.005],
    'dropout': [0.1, 0.2, 0.3, 0.4, 0.5],
    'batch_size': [8, 16, 32],
    'weight_decay': [0.0, 0.001, 0.01],
    'epochs': [15]  # Fixed, early stopping will control actual epochs
}

# Modality combinations
MODALITIES = [
    ('T', False, False, True, 'Text Only'),
    ('A', False, True, False, 'Audio Only'),
    ('V', True, False, False, 'Vision Only'),
    ('AT', False, True, True, 'Audio+Text'),
    ('VA', True, True, False, 'Vision+Audio'),
    ('VT', True, False, True, 'Vision+Text'),
    ('VAT', True, True, True, 'Vision+Audio+Text')
]

def create_config(name, use_v, use_a, use_t, lr, dropout, batch_size, weight_decay, epochs):
    """Create experiment config"""
    return {
        "dataset": "ravdess",
        "use_v": use_v,
        "use_a": use_a,
        "use_t": use_t,
        "num_classes": 4,
        "batch_size": batch_size,
        "epochs": epochs,
        "lr": lr,
        "dropout": dropout,
        "weight_decay": weight_decay
    }

def run_experiment(config, name, description):
    """Run single training experiment"""
    # Save config
    config_path = Path(f"../configs/exp_{name}.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Experiment: {description}")
    print(f"Config: {config}")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, "train.py", "--config", str(config_path)],
            check=True,
            capture_output=True,
            text=True
        )
        
        elapsed = time.time() - start_time
        
        # Parse results from output
        output = result.stdout
        lines = output.split('\n')
        
        # Extract final metrics (last epoch with best F1)
        best_f1 = 0.0
        best_acc = 0.0
        best_epoch = 0
        
        for line in lines:
            if 'New best F1:' in line:
                try:
                    f1_val = float(line.split('New best F1:')[1].strip())
                    if f1_val > best_f1:
                        best_f1 = f1_val
                except:
                    pass
            if '[epoch' in line and 'acc=' in line:
                try:
                    parts = line.split('acc=')[1].split(',')
                    acc_val = float(parts[0].strip())
                    f1_part = line.split('f1=')[1].split(',')[0].strip()
                    f1_val = float(f1_part)
                    
                    if f1_val > best_f1:
                        best_f1 = f1_val
                        best_acc = acc_val
                        epoch_part = line.split('[epoch ')[1].split(']')[0].strip()
                        best_epoch = int(epoch_part)
                except:
                    pass
        
        return {
            'success': True,
            'name': name,
            'description': description,
            'config': config,
            'accuracy': best_acc,
            'f1': best_f1,
            'best_epoch': best_epoch,
            'time': elapsed,
            'output': output
        }
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"✗ FAILED: {description}")
        print(f"Error: {e}")
        
        return {
            'success': False,
            'name': name,
            'description': description,
            'config': config,
            'time': elapsed,
            'error': str(e)
        }

def save_results(results, output_file):
    """Save experiment results to markdown"""
    output_path = Path(output_file)
    
    # Create results markdown
    md_lines = []
    md_lines.append(f"# RAVDESS Training Experiments")
    md_lines.append(f"\n**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append(f"**Total Experiments**: {len(results)}")
    md_lines.append(f"**Successful**: {sum(1 for r in results if r['success'])}")
    md_lines.append(f"**Failed**: {sum(1 for r in results if not r['success'])}")
    
    # Summary table
    md_lines.append("\n## Experiment Results Summary\n")
    md_lines.append("| # | Modality | LR | Dropout | Batch | WD | Accuracy | F1 | Epoch | Time |")
    md_lines.append("|---|----------|----|---------| ------|------|----------|-----|-------|------|")
    
    for i, result in enumerate(results, 1):
        if result['success']:
            config = result['config']
            md_lines.append(
                f"| {i} | {result['name']} | {config['lr']} | {config['dropout']} | "
                f"{config['batch_size']} | {config['weight_decay']} | "
                f"**{result['accuracy']:.1%}** | **{result['f1']:.3f}** | "
                f"{result['best_epoch']} | {result['time']:.1f}s |"
            )
        else:
            md_lines.append(
                f"| {i} | {result['name']} | - | - | - | - | ✗ FAILED | - | - | {result['time']:.1f}s |"
            )
    
    # Best models per modality
    md_lines.append("\n## Best Models by Modality\n")
    
    successful = [r for r in results if r['success']]
    modality_groups = {}
    for result in successful:
        mod = result['name'].split('_')[0]
        if mod not in modality_groups:
            modality_groups[mod] = []
        modality_groups[mod].append(result)
    
    for modality, exps in sorted(modality_groups.items()):
        best = max(exps, key=lambda x: x['f1'])
        md_lines.append(f"\n### {modality}: {best['description']}")
        md_lines.append(f"- **Accuracy**: {best['accuracy']:.1%}")
        md_lines.append(f"- **F1-Score**: {best['f1']:.3f}")
        md_lines.append(f"- **Config**: LR={best['config']['lr']}, "
                      f"Dropout={best['config']['dropout']}, "
                      f"Batch={best['config']['batch_size']}")
        md_lines.append(f"- **Checkpoint**: `checkpoints/exp_{best['name']}.pth`")
    
    # Write file
    with open(output_path, 'w') as f:
        f.write('\n'.join(md_lines))
    
    print(f"\nResults saved to: {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RAVDESS Comprehensive Training')
    parser.add_argument('--num_experiments', type=int, default=20, 
                      help='Number of random experiments (default: 20)')
    parser.add_argument('--full_grid', action='store_true',
                      help='Run full grid search (WARNING: very slow!)')
    parser.add_argument('--modalities', type=str, nargs='+', 
                      help='Specific modalities to test (e.g., A T AT VAT)')
    parser.add_argument('--output', type=str, default='../RAVDESS_TRAINING_RESULTS.md',
                      help='Output results file')
    
    args = parser.parse_args()
    
    # Filter modalities if specified
    modalities_to_test = MODALITIES
    if args.modalities:
        modalities_to_test = [m for m in MODALITIES if m[0] in args.modalities]
    
    # Generate experiment configs
    experiments = []
    
    if args.full_grid:
        # Full grid search
        for mod_name, use_v, use_a, use_t, desc in modalities_to_test:
            for lr in HYPERPARAMS['lr']:
                for dropout in HYPERPARAMS['dropout']:
                    for batch_size in HYPERPARAMS['batch_size']:
                        for weight_decay in HYPERPARAMS['weight_decay']:
                            config = create_config(
                                mod_name, use_v, use_a, use_t,
                                lr, dropout, batch_size, weight_decay,
                                HYPERPARAMS['epochs'][0]
                            )
                            exp_name = f"{mod_name}_lr{lr}_d{dropout}_b{batch_size}_wd{weight_decay}"
                            experiments.append((config, exp_name, desc))
        
        print(f"Full grid search: {len(experiments)} total experiments")
    else:
        # Random sampling
        for mod_name, use_v, use_a, use_t, desc in modalities_to_test:
            # At least 2 experiments per modality
            num_per_mod = max(2, args.num_experiments // len(modalities_to_test))
            
            for i in range(num_per_mod):
                lr = random.choice(HYPERPARAMS['lr'])
                dropout = random.choice(HYPERPARAMS['dropout'])
                batch_size = random.choice(HYPERPARAMS['batch_size'])
                weight_decay = random.choice(HYPERPARAMS['weight_decay'])
                
                config = create_config(
                    mod_name, use_v, use_a, use_t,
                    lr, dropout, batch_size, weight_decay,
                    HYPERPARAMS['epochs'][0]
                )
                exp_name = f"{mod_name}_{i+1}"
                experiments.append((config, exp_name, f"{desc} (exp{i+1})"))
        
        print(f"Random sampling: {len(experiments)} experiments")
    
    # Run experiments
    results = []
    total_start = time.time()
    
    for i, (config, name, desc) in enumerate(experiments, 1):
        print(f"\n{'#'*70}")
        print(f"Running experiment {i}/{len(experiments)}")
        print(f"{'#'*70}")
        
        result = run_experiment(config, name, desc)
        results.append(result)
        
        # Save intermediate results every 5 experiments
        if i % 5 == 0:
            save_results(results, args.output)
    
    total_elapsed = time.time() - total_start
    
    # Final save
    save_results(results, args.output)
    
    print(f"\n{'='*70}")
    print("EXPERIMENTS COMPLETE")
    print(f"{'='*70}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print(f"Results saved to: {args.output}")
    
    # Print summary
    successful = [r for r in results if r['success']]
    if successful:
        best = max(successful, key=lambda x: x['f1'])
        print(f"\n🏆 BEST MODEL: {best['description']}")
        print(f"   Accuracy: {best['accuracy']:.1%}")
        print(f"   F1-Score: {best['f1']:.3f}")

if __name__ == '__main__':
    main()
