"""
Standalone test for EEG Visualizer.

Generates simulated EEG data and displays in a window.
"""

import time

import numpy as np

from src.eeg_visualizer import create_eeg_visualizer


print("=" * 60)
print("EEG VISUALIZER TEST")
print("=" * 60)
print()
print("This test:")
print("  1. Opens EEG monitor window")
print("  2. Generates simulated EEG signals (4 channels)")
print("  3. Displays them in real-time")
print()
print("Close the window to end the test.")
print()

# Ask about mode
advanced = input("Use advanced version with MNE (topomaps)? (y/n): ").lower() == 'y'

# Create visualizer
print(f"\n📊 Creating visualizer ({'advanced' if advanced else 'simple'})...")
viz = create_eeg_visualizer(use_advanced=advanced, buffer_duration=5.0)

# Setup window
viz.setup_window()

print("\n✅ Visualizer ready!")
print("🎵 Generating simulated signals...")
print("   Channels:")
print("   - TP9  (left back): Alpha 10 Hz")
print("   - AF7  (left front): Beta 20 Hz")
print("   - AF8  (right front): Alpha + Beta")
print("   - TP10 (right back): Beta 18 Hz")
print()

sample_rate: int = 256
t: float = 0.0
rng = np.random.default_rng(seed=42)

try:
    while viz.is_running:
        # Generate 100ms of data
        duration = 0.1
        n_samples = int(duration * sample_rate)

        # Time vector
        time_vec = np.linspace(t, t + duration, n_samples)

        # Simulated channels
        ch_tp9  = 50 * np.sin(2 * np.pi * 10 * time_vec) + 20 * rng.standard_normal(n_samples)  # Alpha
        ch_af7  = 30 * np.sin(2 * np.pi * 20 * time_vec) + 15 * rng.standard_normal(n_samples)  # Beta
        ch_af8 = (40 * np.sin(2 * np.pi * 12 * time_vec) +
                  25 * np.sin(2 * np.pi * 22 * time_vec) +
                  18 * rng.standard_normal(n_samples))  # Alpha + Beta
        ch_tp10 = 35 * np.sin(2 * np.pi * 18 * time_vec) + 16 * rng.standard_normal(n_samples)  # Beta

        eeg_data = np.column_stack([ch_tp9, ch_af7, ch_af8, ch_tp10])

        # Simulate band powers (changing over time)
        band_powers = {
            'delta': 100 + 20 * np.sin(t * 0.5),
            'theta': 50 + 10 * np.cos(t * 0.7),
            'alpha': 30 + 15 * np.sin(t * 1.0),
            'beta': 20 + 12 * np.cos(t * 1.5),
            'gamma': 10 + 5 * np.sin(t * 2.0),
        }

        # Simulate PER-CHANNEL band powers (different values for each channel!)
        # TP9, AF7, AF8, TP10 have different characteristics
        time_mod_delta = 20 * np.sin(t * 0.5)
        time_mod_theta = 10 * np.cos(t * 0.7)
        time_mod_alpha = 15 * np.sin(t * 1.0)
        time_mod_beta = 12 * np.cos(t * 1.5)
        time_mod_gamma = 5 * np.sin(t * 2.0)

        band_powers_per_channel = {
            'delta': [100 + time_mod_delta, 110 + time_mod_delta, 95 + time_mod_delta, 105 + time_mod_delta],
            'theta': [50 + time_mod_theta, 55 + time_mod_theta, 48 + time_mod_theta, 52 + time_mod_theta],
            'alpha': [25 + time_mod_alpha, 40 + time_mod_alpha, 35 + time_mod_alpha, 22 + time_mod_alpha],  # AF7/AF8 have more alpha
            'beta': [18 + time_mod_beta, 25 + time_mod_beta, 28 + time_mod_beta, 16 + time_mod_beta],   # AF8 has most beta
            'gamma': [10 + time_mod_gamma, 12 + time_mod_gamma, 15 + time_mod_gamma, 8 + time_mod_gamma],
        }

        # Update visualizer with per-channel data
        viz.update_data(eeg_data, band_powers, band_powers_per_channel)
        viz.update_plots()

        t += duration
        time.sleep(0.05)  # ~20 Hz update

except KeyboardInterrupt:
    print("\n\n⏹️  Test stopped by user")

except Exception as e:
    print(f"\n\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    viz.close()
    print("\n✅ Test completed")
    print("\n💡 If test worked, EEG monitor will be available in main application!")
