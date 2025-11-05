"""
EEG Signal Processing.

Frequency band extraction and attention/relaxation metrics computation.
"""

from collections import deque
from typing import Dict, Deque, List, Tuple
import time
import hashlib

import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq

import config


class EEGProcessor:
    """
    Processes raw EEG data into useful metrics.

    Performs FFT analysis and computes attention/relaxation indices.
    """

    def __init__(self) -> None:
        self.sample_rate = config.SAMPLE_RATE
        self.window_size = config.WINDOW_SIZE

        # Buffers for each channel
        self.buffers: Dict[int, Deque[float]] = {
            channel: deque(maxlen=self.window_size * 3)
            for channel in range(4)  # 4 channels Muse S
        }

        # Baseline values from calibration
        self.baseline = {
            'alpha': 0.0,
            'beta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'delta': 0.0
        }
        self.is_calibrated = False

        # Band-pass filters
        self.filters = self._create_filters()

        # Notch filter for power line interference (50Hz in EU, 60Hz in US)
        self.notch_filter = self._create_notch_filter()

        # Metrics history (for smoothing)
        self.metric_history: Dict[str, Deque[float]] = {
            'attention': deque(maxlen=5),
            'relaxation': deque(maxlen=5),
        }

        # Current values
        self.current_bands: Dict[str, float] = {}
        self.current_attention = 0.0
        self.current_relaxation = 0.0

        # Internal flag for channel detection tracking
        self._channels_detected = False

        # FFT cache (if enabled)
        self.fft_cache: Dict[Tuple[int, bytes], Tuple[np.ndarray, np.ndarray]] = {}
        self.fft_cache_max_size = 100  # Maximum cache entries
        self.enable_fft_cache = getattr(config, 'ENABLE_FFT_CACHE', False)

    def _create_filters(self) -> dict:
        """
        Create band-pass filters for different frequencies.

        :return: Dictionary of filters for each band
        """
        filters = {}

        for band_name, (low, high) in config.BANDS.items():
            # 4th order Butterworth filter
            nyquist = self.sample_rate / 2
            low_norm = low / nyquist
            high_norm = high / nyquist

            # Ensure frequencies are in range (0, 1)
            low_norm = max(0.01, min(0.99, low_norm))
            high_norm = max(0.01, min(0.99, high_norm))

            if low_norm < high_norm:
                sos = signal.butter(4, [low_norm, high_norm],
                                    btype='band', output='sos')
                filters[band_name] = sos

        return filters

    def _create_notch_filter(self) -> tuple:
        """
        Create notch filter for power line interference.

        50Hz in Europe, 60Hz in USA.

        :return: Filter coefficients (b, a)
        """
        # Automatic region detection (default 50Hz for Europe)
        power_line_freq = getattr(config, 'POWER_LINE_FREQ', 50)

        # Quality factor - notch width
        # Q=30 means ±1.67 Hz cutout around central frequency
        quality_factor = 30

        # Notch (band-stop) IIR filter
        b, a = signal.iirnotch(power_line_freq, quality_factor, self.sample_rate)

        return (b, a)

    def add_data(self, data: np.ndarray) -> None:
        """
        Add new EEG data to buffers.

        :param data: Array [samples, channels]
        """
        if data is None or len(data) == 0:
            return

        # Debug: check number of channels
        if not self._channels_detected:
            actual_channels = data.shape[1] if len(data.shape) > 1 else 1
            if config.DEBUG and actual_channels != 4:
                print(f"\n📊 EEG Processor: Detected {actual_channels} channels (using 4)")
            self._channels_detected = True

        # Add to buffers for each channel (only first 4)
        n_channels = min(4, data.shape[1])
        for ch in range(n_channels):
            channel_data = data[:, ch]
            # Debug: Check raw data values to understand scaling
            if config.DEBUG and len(channel_data) > 10 and not hasattr(self, '_raw_data_checked'):
                ch_mean = np.mean(np.abs(channel_data))
                ch_std = np.std(channel_data)
                ch_min = np.min(channel_data)
                ch_max = np.max(channel_data)
                print(f"   📊 Raw EEG data (channel {ch}): mean={ch_mean:.2f}, std={ch_std:.2f}, range=[{ch_min:.2f}, {ch_max:.2f}]")
                if ch == 3:  # After checking all 4 channels
                    self._raw_data_checked = True
                    if ch_mean > 1000 or ch_std > 1000:
                        print(f"   ⚠️  WARNING: Raw values seem very high (>1000)")
                        print(f"      This may indicate data is not in µV units")
                        print(f"      Or there may be scaling issue with OpenMuse/LSL")
            # Debug: Check if channel has valid data
            if config.DEBUG and len(channel_data) > 10:
                ch_mean = np.mean(np.abs(channel_data))
                ch_std = np.std(channel_data)
                if ch_mean < 0.1 and ch_std < 0.1:
                    print(f"   ⚠️  EEG Processor: Channel {ch} has very low/zero data (mean={ch_mean:.4f}, std={ch_std:.4f})")
            for sample in channel_data:
                self.buffers[ch].append(sample)

    def _compute_fft_cached(self, window: np.ndarray, channel: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute FFT with optional caching.

        :param window: Window of data to process
        :param channel: Channel index (for cache key)
        :return: Tuple of (frequencies, power_spectrum)
        """
        if not self.enable_fft_cache:
            # Cache disabled - compute directly
            n = len(window)
            fft_vals = fft(window)
            fft_freq = fftfreq(n, 1.0 / self.sample_rate)
            pos_mask = fft_freq > 0
            freqs = fft_freq[pos_mask]
            # Normalize power spectrum properly
            # FFT returns values that scale with N, so we need proper normalization
            # For power spectral density: PSD = |FFT|² / (N * fs)
            # But for band power, we typically use: Power = |FFT|² / N²
            # This gives us power in units of (signal_units)²
            # Assuming OpenMuse sends data already in µV, this should give µV²
            power_spectrum = (np.abs(fft_vals[pos_mask]) / n) ** 2
            return (freqs, power_spectrum)

        # Create cache key from window data hash and channel
        # Use hash of window data to detect identical windows
        window_hash = hashlib.md5(window.tobytes()).digest()
        cache_key = (channel, window_hash)

        if cache_key in self.fft_cache:
            # Cache hit - return cached result
            return self.fft_cache[cache_key]

        # Cache miss - compute FFT
        n = len(window)
        fft_vals = fft(window)
        fft_freq = fftfreq(n, 1.0 / self.sample_rate)
        pos_mask = fft_freq > 0
        freqs = fft_freq[pos_mask]
        # Normalize power spectrum properly
        # FFT returns values that scale with N, so we need proper normalization
        # For power spectral density: PSD = |FFT|² / (N * fs)
        # But for band power, we typically use: Power = |FFT|² / N²
        # This gives us power in units of (signal_units)²
        # Assuming OpenMuse sends data already in µV, this should give µV²
        power_spectrum = (np.abs(fft_vals[pos_mask]) / n) ** 2

        # Store in cache (limit size)
        if len(self.fft_cache) >= self.fft_cache_max_size:
            # Remove oldest entry (simple FIFO)
            self.fft_cache.pop(next(iter(self.fft_cache)))

        self.fft_cache[cache_key] = (freqs, power_spectrum)

        return (freqs, power_spectrum)

    def compute_band_powers(self) -> dict:
        """
        Compute power in different frequency bands.

        :return: Dictionary with power for each band (averaged across channels)
        """
        band_powers = dict.fromkeys(config.BANDS, 0.0)

        # Check if we have enough data
        if len(self.buffers[0]) < self.window_size:
            return band_powers

        # Average across all channels
        for ch in range(4):
            if len(self.buffers[ch]) < self.window_size:
                continue

            # Get last window of data
            window = np.array(list(self.buffers[ch])[-self.window_size:])

            # Remove trend (detrend)
            window = signal.detrend(window)

            # Notch filter - remove 50Hz/60Hz interference
            try:
                b, a = self.notch_filter
                window = signal.filtfilt(b, a, window)
            except Exception:
                pass  # If filter doesn't work, continue without it

            # Apply Hanning window
            window = window * np.hanning(len(window))

            # FFT (with optional caching)
            freqs, power_spectrum = self._compute_fft_cached(window, ch)

            # Compute power for each band
            for band_name, (low, high) in config.BANDS.items():
                band_mask = (freqs >= low) & (freqs <= high)
                if np.any(band_mask):
                    band_powers[band_name] += np.mean(power_spectrum[band_mask])

        # Average across channels
        for band_name in band_powers:
            band_powers[band_name] /= 4.0

        self.current_bands = band_powers
        return band_powers

    def compute_band_powers_per_channel(self) -> dict:
        """
        Compute power in different frequency bands PER CHANNEL.

        :return: Dictionary with power for each band as list [ch0, ch1, ch2, ch3]
                 Example: {'alpha': [28.0, 35.0, 32.0, 29.0], 'beta': [...], ...}
        """
        # Initialize with empty lists
        band_powers_per_ch: Dict[str, List[float]] = {band_name: [] for band_name in config.BANDS}

        # Check if we have enough data
        if len(self.buffers[0]) < self.window_size:
            # Return zeros for each channel
            return {band_name: [0.0] * 4 for band_name in config.BANDS}

        # For each channel
        for ch in range(4):
            if len(self.buffers[ch]) < self.window_size:
                # Add zeros for this channel
                for band_name in config.BANDS:
                    band_powers_per_ch[band_name].append(0.0)
                continue

            # Get last window of data
            window = np.array(list(self.buffers[ch])[-self.window_size:])

            # Remove trend (detrend)
            window = signal.detrend(window)

            # Notch filter - remove 50Hz/60Hz interference
            try:
                b, a = self.notch_filter
                window = signal.filtfilt(b, a, window)
            except Exception:
                pass  # If filter doesn't work, continue without it

            # Apply Hanning window
            window = window * np.hanning(len(window))

            # FFT (with optional caching)
            freqs, power_spectrum = self._compute_fft_cached(window, ch)

            # Compute power for each band for this channel
            for band_name, (low, high) in config.BANDS.items():
                band_mask = (freqs >= low) & (freqs <= high)
                if np.any(band_mask):
                    # Mean power in the frequency band
                    band_power = np.mean(power_spectrum[band_mask])
                    # Debug: Check if values are still too high
                    if config.DEBUG and band_power > 10000 and ch == 0:
                        print(f"   ⚠️  High {band_name} power on channel {ch}: {band_power:.2f} µV²")
                        print(f"      (If consistently >10K, check signal scaling)")
                    band_powers_per_ch[band_name].append(band_power)
                else:
                    band_powers_per_ch[band_name].append(0.0)

        return band_powers_per_ch

    def calibrate(self, duration: int = 10) -> None:
        """
        Calibration - establish baseline values.

        Best when user is relaxed with eyes closed.

        :param duration: Calibration time in seconds
        """
        print(f"🎯 Calibration ({duration}s)...")
        print("   Sit still with eyes closed")

        calibration_data: Dict[str, List[float]] = {band_name: [] for band_name in config.BANDS}

        # Fewer samples = faster calibration
        n_samples = max(5, int(duration * 2))  # ~2 Hz sampling during calibration

        for i in range(n_samples):
            band_powers_result = self.compute_band_powers()
            for band_name, power_value in band_powers_result.items():
                if power_value > 0:  # Only if we have data
                    calibration_data[band_name].append(power_value)
            time.sleep(duration / n_samples)  # Evenly distributed samples

            # Show progress
            progress = (i + 1) / n_samples * 100
            print(f"\r   Progress: {progress:.0f}%", end='')

        print()

        # Compute average baseline values
        for band_name in config.BANDS:
            if len(calibration_data[band_name]) > 0:
                self.baseline[band_name] = float(np.median(calibration_data[band_name]))
                print(f"   {band_name}: {self.baseline[band_name]:.2f}")

        self.is_calibrated = True
        print("✅ Calibration complete!")

    def compute_attention(self) -> float:
        """
        Compute attention index (0-1).

        High beta/gamma activity = high attention.

        :return: Attention level 0-1
        """
        if not self.is_calibrated or not self.current_bands:
            return 0.5

        # Attention: combination of beta and gamma
        beta = self.current_bands.get('beta', 0)
        gamma = self.current_bands.get('gamma', 0)

        beta_baseline = self.baseline.get('beta', 1.0)
        gamma_baseline = self.baseline.get('gamma', 1.0)

        # Normalize relative to baseline
        beta_norm = (beta / beta_baseline) if beta_baseline > 0 else 0
        gamma_norm = (gamma / gamma_baseline) if gamma_baseline > 0 else 0

        # Combination (beta 70%, gamma 30%)
        attention_value = 0.7 * beta_norm + 0.3 * gamma_norm

        # Clip to [0, 2] and map to [0, 1]
        attention_value = np.clip(attention_value, 0, 2) / 2.0

        # Smooth
        self.metric_history['attention'].append(attention_value)
        attention_smooth = float(np.mean(list(self.metric_history['attention'])))

        self.current_attention = attention_smooth
        return attention_smooth

    def compute_relaxation(self) -> float:
        """
        Compute relaxation index (0-1).

        High alpha activity = high relaxation.

        :return: Relaxation level 0-1
        """
        if not self.is_calibrated or not self.current_bands:
            return 0.5

        # Relaxation: mainly alpha
        alpha = self.current_bands.get('alpha', 0)
        theta = self.current_bands.get('theta', 0)

        alpha_baseline = self.baseline.get('alpha', 1.0)
        theta_baseline = self.baseline.get('theta', 1.0)

        # Normalize relative to baseline
        alpha_norm = (alpha / alpha_baseline) if alpha_baseline > 0 else 0
        theta_norm = (theta / theta_baseline) if theta_baseline > 0 else 0

        # Combination (alpha 80%, theta 20%)
        relaxation_value = 0.8 * alpha_norm + 0.2 * theta_norm

        # Clip to [0, 2] and map to [0, 1]
        relaxation_value = np.clip(relaxation_value, 0, 2) / 2.0

        # Smooth
        self.metric_history['relaxation'].append(relaxation_value)
        relaxation_smooth = float(np.mean(list(self.metric_history['relaxation'])))

        self.current_relaxation = relaxation_smooth
        return relaxation_smooth

    def get_metrics(self) -> dict:
        """
        Return all metrics.

        :return: Dictionary with metrics: attention, relaxation, band_powers
        """
        return {
            'attention': self.current_attention,
            'relaxation': self.current_relaxation,
            'band_powers': self.current_bands.copy(),
            'is_calibrated': self.is_calibrated
        }

    def reset(self) -> None:
        """
        Reset buffers and calibration.
        """
        for buffer in self.buffers.values():
            buffer.clear()
        self.is_calibrated = False
        self.baseline = dict.fromkeys(config.BANDS, 0.0)
        # Clear FFT cache on reset
        if self.enable_fft_cache:
            self.fft_cache.clear()

    def clear_fft_cache(self) -> None:
        """
        Clear FFT cache manually (useful for memory management).
        """
        self.fft_cache.clear()


if __name__ == "__main__":
    print("=== Test EEGProcessor ===\n")

    processor = EEGProcessor()

    # Simulate data
    print("📊 Generating synthetic EEG data...")
    rng = np.random.default_rng(seed=42)
    t = np.linspace(0, 1, config.SAMPLE_RATE)

    # Test signal: alpha (10 Hz) + beta (20 Hz) + noise
    synthetic_alpha = np.sin(2 * np.pi * 10 * t)
    synthetic_beta = 0.5 * np.sin(2 * np.pi * 20 * t)
    noise = 0.1 * rng.standard_normal(len(t))

    test_signal = synthetic_alpha + synthetic_beta + noise

    # 4 channels with slightly different signals
    test_data = np.column_stack([
        test_signal,
        test_signal * 0.9,
        test_signal * 1.1,
        test_signal * 0.95
    ])

    processor.add_data(test_data)

    print("\n📈 Calculating the band powers...")
    powers = processor.compute_band_powers()

    for band, power in powers.items():
        print(f"  {band}: {power:.2f}")

    print("\n🎯 Metrics test (no calibration):")
    processor.is_calibrated = True  # Simulate calibration
    processor.baseline = powers.copy()

    # Add more data with more alpha (relaxation)
    synthetic_alpha_high = 2.0 * np.sin(2 * np.pi * 10 * t)
    test_signal_relaxed = synthetic_alpha_high + synthetic_beta + noise
    test_data_relaxed = np.column_stack([test_signal_relaxed] * 4)

    processor.add_data(test_data_relaxed)

    attention = processor.compute_attention()
    relaxation = processor.compute_relaxation()

    print(f"  Attention: {attention:.2f}")
    print(f"  Relaxation: {relaxation:.2f}")
    print("\n✅ Test completed!")
