"""
Brain Art system test script.

Tests all components with synthetic data.
"""

import io
import time
import sys

import numpy as np


# Encoding fix for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("BRAIN ART SYSTEM TEST")
print("=" * 60)
print()

# Test 1: Imports
print("1. Testing imports...")
try:
    import pygame
    import scipy
    import config
    from src.muse_connector import MuseConnector
    from src.eeg_processor import EEGProcessor
    from src.brain_visualizer import BrainVisualizer
    print("   ✅ Core modules OK")

    # Test OpenMuse (optional)
    try:
        import OpenMuse
        print("   ✅ OpenMuse installed")
    except ImportError:
        print("   ⚠️  OpenMuse not found (install: pip install .)")

    # Test LSL
    try:
        from mne_lsl.lsl import StreamInlet
        print("   ✅ MNE-LSL installed (OpenMuse)")
    except ImportError:
        try:
            from pylsl import StreamInlet
            print("   ⚠️  pylsl (old) - we recommend MNE-LSL")
        except ImportError:
            print("   ⚠️  No LSL")

except ImportError as e:
    print(f"   ❌ Import error: {e}")
    print("   Run: pip install .")
    sys.exit(1)

print()

# Test 2: EEG Processor
print("2️⃣  Testing EEG Processor...")
try:
    processor = EEGProcessor()

    # Generate synthetic data
    rng = np.random.default_rng(seed=42)
    t = np.linspace(0, 2, 512)  # 2 seconds
    alpha_wave = np.sin(2 * np.pi * 10 * t)  # 10 Hz = alpha
    beta_wave = 0.5 * np.sin(2 * np.pi * 20 * t)  # 20 Hz = beta
    noise = 0.1 * rng.standard_normal(len(t))

    signal = alpha_wave + beta_wave + noise
    data = np.column_stack([signal] * 4)  # 4 channels

    processor.add_data(data)
    powers = processor.compute_band_powers()

    print(f"   Alpha: {powers['alpha']:.2f}")
    print(f"   Beta: {powers['beta']:.2f}")

    # Simulate calibration
    processor.baseline = powers.copy()
    processor.is_calibrated = True

    attention = processor.compute_attention()
    relaxation = processor.compute_relaxation()

    print(f"   Attention: {attention:.2f}")
    print(f"   Relaxation: {relaxation:.2f}")
    print("   ✅ EEG Processor working")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Visualizer (short)
print("3️⃣  Testing Visualizer...")
print("   (Will close automatically after 3 seconds)")
try:
    viz = BrainVisualizer()

    start = time.time()
    frames = 0

    while time.time() - start < 3:
        # Synthetic metrics
        elapsed_time: float = time.time() - start
        synthetic_attention: float = float(0.5 + 0.3 * np.sin(elapsed_time * 2))
        synthetic_relaxation: float = float(0.5 + 0.3 * np.cos(elapsed_time * 1.5))

        viz.set_metrics(synthetic_attention, synthetic_relaxation)

        if not viz.run_frame():
            break

        frames += 1

    fps = frames / 3.0
    viz.close()

    print(f"   FPS: {fps:.1f}")
    print("   ✅ Visualizer working")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: OpenMuse
print("4️⃣  Testing OpenMuse (optional)")
test_openmuse = input("   Do you want to test OpenMuse find? (y/n): ")

if test_openmuse.lower() == 'y':
    print("   Testing OpenMuse...")
    print("   Make sure Muse S is powered on!")
    print()
    try:
        import subprocess
        result = subprocess.run(
            ["OpenMuse", "find"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False
        )
        print(result.stdout)
        if result.returncode == 0:
            print("   ✅ OpenMuse working!")
        else:
            print("   ⚠️  OpenMuse did not find devices")
    except FileNotFoundError:
        print("   ❌ OpenMuse not installed")
        print("      pip install git+https://github.com/Eve0028/OpenMuse.git")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
else:
    print("   ⏭️  Skipped OpenMuse test")

print()
print("=" * 60)
print("✅ TESTS COMPLETED")
print("=" * 60)
print()
print("📝 Next steps:")
print("   1. Find Muse S: OpenMuse find")
print("   2. Stream: OpenMuse stream --address <MAC>")
print("   3. Application: python main.py")
print("   4. Documentation: README.md")
print()
