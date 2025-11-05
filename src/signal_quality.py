"""
EEG signal quality assessment module for Muse S Athena.

Implements various signal quality metrics including variance, amplitude,
spectral power, artifacts detection, and stationarity analysis.
"""

from typing import Dict, List, Any

import numpy as np
from scipy import signal
from scipy.stats import kurtosis

import config


class SignalQualityChecker:
    """
    Assess EEG signal quality based on multiple metrics.
    
    Evaluates signal variance, amplitude, spectral power,
    line noise, artifacts, and stationarity.
    
    :param sample_rate: Sampling frequency in Hz
    """

    def __init__(self, sample_rate: int = 256) -> None:
        self.sample_rate: int = sample_rate
        # Muse S Athena: 4 main channels (Brain Art uses only 4 channels)
        self.channel_names: List[str] = ['TP9', 'AF7', 'AF8', 'TP10']

        # Thresholds for quality assessment
        self.thresholds: Dict[str, float] = {
            'variance_min': 10,      # Minimum variance (µV²)
            'variance_max': 10000,   # Maximum variance (artifacts)
            'amplitude_max': 500,    # Maximum amplitude (µV)
            'alpha_power_min': 0.1,  # Minimum alpha power
            'line_noise_max': 0.3,   # Maximum 50Hz noise ratio
        }

    def assess_quality(self, eeg_data: np.ndarray) -> Dict[str, Any]:
        """
        Comprehensive signal quality assessment.
        
        Analyzes EEG data using multiple quality metrics and provides
        per-channel and overall quality scores.
        
        :param eeg_data: Array of shape [samples, channels] with EEG data
        :return: Dictionary with assessment results containing:
                 - overall_quality: 0-100 (overall quality score)
                 - channel_quality: [0-100] for each channel
                 - channel_metrics: Detailed metrics per channel
                 - warnings: List of warnings
                 - status: Text status description
        """
        if eeg_data is None or len(eeg_data) == 0:
            return self._empty_result()

        # Auto-detect number of channels (4 or 8 for Muse S Athena)
        n_channels = eeg_data.shape[1] if len(eeg_data.shape) > 1 else 1
        channel_qualities: List[int] = []
        channel_metrics: List[Dict] = []
        warnings: List[str] = []

        for ch in range(n_channels):
            data = eeg_data[:, ch]

            # Compute metrics
            metrics = {
                'variance': self._check_variance(data),
                'amplitude': self._check_amplitude(data),
                'alpha_power': self._check_alpha_power(data),
                'line_noise': self._check_line_noise(data),
                'artifacts': self._check_artifacts(data),
                'stationarity': self._check_stationarity(data),
            }

            # Compute overall quality for channel (0-100)
            quality = self._compute_channel_quality(metrics)

            # Add warnings
            ch_warnings = self._generate_warnings(ch, metrics)
            warnings.extend(ch_warnings)

            channel_qualities.append(quality)
            channel_metrics.append(metrics)

        # Overall quality = average across channels
        overall_quality = int(np.mean(channel_qualities))

        return {
            'overall_quality': overall_quality,
            'channel_quality': channel_qualities,
            'channel_metrics': channel_metrics,
            'warnings': warnings,
            'status': self._get_status_text(overall_quality),
        }

    def _check_variance(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Check signal variance.
        
        :param data: Channel data
        :return: Dictionary with variance value, score, and unit
        """
        var = np.var(data)

        # Assessment (0-100)
        if var < self.thresholds['variance_min']:
            score = 20  # Very low - likely poor contact
        elif var > self.thresholds['variance_max']:
            score = 30  # Very high - likely artifacts
        else:
            # Optimal variance: 50-500 µV²
            optimal_range = (50, 500)
            if optimal_range[0] <= var <= optimal_range[1]:
                score = 100
            elif var < optimal_range[0]:
                score = 50 + 50 * (var - self.thresholds['variance_min']) / (optimal_range[0] - self.thresholds['variance_min'])
            else:
                score = 100 - 70 * (var - optimal_range[1]) / (self.thresholds['variance_max'] - optimal_range[1])

        return {
            'value': float(var),
            'score': int(max(0, min(100, score))),
            'unit': 'µV²',
        }

    def _check_amplitude(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Check signal amplitude.
        
        :param data: Channel data
        :return: Dictionary with amplitude value, score, and unit
        """
        peak_to_peak = np.ptp(data)  # Peak-to-peak amplitude

        # Assessment
        if peak_to_peak > self.thresholds['amplitude_max']:
            score = 20  # Too high - artifacts
        elif peak_to_peak < 10:
            score = 30  # Too low - poor contact
        else:
            # Optimal: 50-200 µV
            score = 100 if 50 <= peak_to_peak <= 200 else 70

        return {
            'value': float(peak_to_peak),
            'score': int(score),
            'unit': 'µV',
        }

    def _check_alpha_power(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Check presence of alpha waves (8-13 Hz).
        
        :param data: Channel data
        :return: Dictionary with alpha power value, score, and unit
        """
        if len(data) < 128:
            return {'value': 0, 'score': 50, 'unit': 'µV²'}

        # FFT
        freqs, psd = signal.welch(data, fs=self.sample_rate, nperseg=min(256, len(data)))

        # Power in alpha band
        alpha_mask = (freqs >= 8) & (freqs <= 13)
        alpha_power = np.mean(psd[alpha_mask])

        # Total power
        total_power = np.mean(psd[(freqs >= 1) & (freqs <= 40)])

        # Relative alpha power
        alpha_relative = alpha_power / total_power if total_power > 0 else 0

        # Assessment - alpha presence is good sign
        if alpha_relative > 0.2:
            score = 100  # Clear alpha peak
        elif alpha_relative > 0.1:
            score = 80   # Moderate alpha
        elif alpha_relative > 0.05:
            score = 60   # Weak alpha
        else:
            score = 40   # No alpha (eyes may be open)

        return {
            'value': float(alpha_relative),
            'score': int(score),
            'unit': 'relative',
            'alpha_power_abs': float(alpha_power),
        }

    def _check_line_noise(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Check line noise interference (50Hz in EU, 60Hz in US).
        
        :param data: Channel data
        :return: Dictionary with noise value, score, and unit
        """
        if len(data) < 128:
            return {'value': 0, 'score': 50, 'unit': 'relative'}

        # FFT
        freqs, psd = signal.welch(data, fs=self.sample_rate, nperseg=min(256, len(data)))

        # Power at 50 Hz (±1 Hz)
        noise_50hz = np.mean(psd[(freqs >= 49) & (freqs <= 51)])

        # Total power
        total_power = np.mean(psd[(freqs >= 1) & (freqs <= 40)])

        # Relative noise
        noise_relative = noise_50hz / total_power if total_power > 0 else 0

        # Assessment
        if noise_relative > self.thresholds['line_noise_max']:
            score = 30  # High interference
        elif noise_relative > 0.15:
            score = 60  # Moderate
        else:
            score = 100  # Low interference

        return {
            'value': float(noise_relative),
            'score': int(score),
            'unit': 'relative',
        }

    def _check_artifacts(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Detect artifacts (movement, eye blinks).
        
        Uses kurtosis and gradient analysis to detect signal anomalies.
        
        :param data: Channel data
        :return: Dictionary with kurtosis, gradient, and score
        """
        # Method 1: Kurtosis (detects "spikes")
        kurt = kurtosis(data)

        # Method 2: Derivative (detects sudden changes)
        diff = np.diff(data)
        max_gradient = np.max(np.abs(diff))

        # Assessment
        # High kurtosis = artifacts
        # High derivative = sudden movements
        if kurt > 10 or max_gradient > 100:
            score = 20  # Large artifacts
        elif kurt > 5 or max_gradient > 50:
            score = 50  # Moderate
        else:
            score = 100  # Clean

        return {
            'kurtosis': float(kurt),
            'max_gradient': float(max_gradient),
            'score': int(score),
        }

    def _check_stationarity(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Check signal stationarity (stability over time).
        
        :param data: Channel data
        :return: Dictionary with coefficient of variation and score
        """
        if len(data) < 256:
            return {'value': 0, 'score': 50}

        # Split into 4 parts
        n_parts = 4
        part_size = len(data) // n_parts
        variances = []

        for i in range(n_parts):
            start = i * part_size
            end = (i + 1) * part_size
            variances.append(np.var(data[start:end]))

        # Coefficient of variation of variance
        cv = np.std(variances) / np.mean(variances) if np.mean(variances) > 0 else 0

        # Assessment - low CV = stable signal
        if cv < 0.3:
            score = 100  # Very stable
        elif cv < 0.5:
            score = 80   # Stable
        elif cv < 0.8:
            score = 60   # Moderately stable
        else:
            score = 40   # Unstable

        return {
            'value': float(cv),
            'score': int(score),
            'unit': 'CV',
        }

    def _compute_channel_quality(self, metrics: Dict) -> int:
        """
        Compute overall channel quality from metrics.
        
        :param metrics: Dictionary of metric results
        :return: Overall quality score (0-100)
        """
        # Weights for different metrics
        weights = {
            'variance': 0.3,
            'amplitude': 0.2,
            'alpha_power': 0.15,
            'line_noise': 0.15,
            'artifacts': 0.15,
            'stationarity': 0.05,
        }

        total_score = 0
        for metric_name, weight in weights.items():
            if metric_name in metrics:
                score = metrics[metric_name].get('score', 50)
                total_score += score * weight

        return int(total_score)

    def _generate_warnings(self, channel_idx: int, metrics: Dict) -> List[str]:
        """
        Generate warnings for a channel.
        
        :param channel_idx: Channel index
        :param metrics: Dictionary of metric results
        :return: List of warning messages
        """
        warnings = []
        # Handle case when channel_idx > number of names (fallback)
        ch_name = self.channel_names[channel_idx] if channel_idx < len(self.channel_names) else f"CH{channel_idx}"

        # Check variance
        if metrics['variance']['score'] < 30:
            if metrics['variance']['value'] < self.thresholds['variance_min']:
                warnings.append(f"⚠️  {ch_name}: Very low signal - moisten sensor!")
            else:
                warnings.append(f"⚠️  {ch_name}: Very high noise - check contact")

        # Check amplitude
        if metrics['amplitude']['score'] < 30:
            warnings.append(f"⚠️  {ch_name}: Movement artifacts")

        # Check line noise
        if metrics['line_noise']['score'] < 50:
            warnings.append(f"⚠️  {ch_name}: Electrical interference (50Hz)")

        # Check artifacts
        if metrics['artifacts']['score'] < 40:
            warnings.append(f"⚠️  {ch_name}: Artifacts detected - minimize movement")

        return warnings

    def _get_status_text(self, quality: int) -> str:
        """
        Get text status for quality score.
        
        :param quality: Quality score (0-100)
        :return: Status text with emoji
        """
        if quality >= 80:
            return "🟢 Excellent"
        elif quality >= 60:
            return "🟡 Good"
        elif quality >= 40:
            return "🟠 Acceptable"
        else:
            return "🔴 Poor"

    def _empty_result(self) -> Dict[str, Any]:
        """
        Return empty result when no data available.
        
        :return: Dictionary with empty/default values
        """
        return {
            'overall_quality': 0,
            'channel_quality': [0, 0, 0, 0],
            'channel_metrics': [],
            'warnings': ['❌ No data'],
            'status': '❌ Not connected',
        }

    def print_quality_report(self, quality_result: Dict[str, Any]) -> None:
        """
        Display quality report in readable form.
        
        :param quality_result: Dictionary with quality assessment results
        """
        print("\n" + "=" * 60)
        print("📊 EEG SIGNAL QUALITY REPORT")
        print("=" * 60)

        # Overall quality
        print(f"\n🎯 Overall quality: {quality_result['overall_quality']}/100 - {quality_result['status']}")

        # Per-channel quality
        n_channels = len(quality_result['channel_quality'])
        print(f"\n📡 Channel quality ({n_channels} channels):")
        for i, quality in enumerate(quality_result['channel_quality']):
            ch_name = self.channel_names[i] if i < len(self.channel_names) else f"CH{i}"
            quality_bar = "█" * (quality // 5) + "░" * (20 - quality // 5)
            print(f"  {ch_name}: [{quality_bar}] {quality}/100")

        # Warnings
        if quality_result['warnings']:
            print("\n⚠️  Warnings:")
            for warning in quality_result['warnings']:
                print(f"  {warning}")
        else:
            print("\n✅ No warnings - signal quality is good!")

        # Detailed metrics (optional)
        if config.DEBUG and quality_result['channel_metrics']:
            print("\n🔬 Detailed metrics:")
            for i, metrics in enumerate(quality_result['channel_metrics']):
                ch_name = self.channel_names[i] if i < len(self.channel_names) else f"CH{i}"
                print(f"\n  Channel {ch_name}:")
                for metric_name, metric_data in metrics.items():
                    if isinstance(metric_data, dict) and 'score' in metric_data:
                        value = metric_data.get('value', 'N/A')
                        unit = metric_data.get('unit', '')
                        score = metric_data['score']
                        print(f"    - {metric_name}: {value} {unit} (score: {score}/100)")

        print("=" * 60 + "\n")


# ===== HELPER FUNCTIONS =====

def quick_quality_check(eeg_data: np.ndarray) -> int:
    """
    Quick quality check (0-100).
    
    Use in main application loop for minimal overhead.
    
    :param eeg_data: EEG data array
    :return: Overall quality score (0-100)
    """
    if eeg_data is None or len(eeg_data) == 0:
        return 0

    checker = SignalQualityChecker()
    result = checker.assess_quality(eeg_data)
    return result['overall_quality']


def detailed_quality_check(eeg_data: np.ndarray, print_report: bool = True) -> Dict[str, Any]:
    """
    Detailed quality check with full metrics.
    
    Use during calibration or debugging.
    
    :param eeg_data: EEG data array
    :param print_report: Whether to print detailed report
    :return: Dictionary with full quality assessment results
    """
    checker = SignalQualityChecker()
    result = checker.assess_quality(eeg_data)

    if print_report:
        checker.print_quality_report(result)

    return result


def _run_tests() -> None:
    """Run signal quality checker tests."""
    # Test with simulated data
    print("=== Test Signal Quality Checker ===\n")

    # Simulate data
    rng = np.random.default_rng(seed=42)
    test_sample_rate = 256
    duration = 5  # seconds
    n_samples = test_sample_rate * duration
    time_axis = np.linspace(0, duration, n_samples)

    # Channel 1: Good signal (alpha + noise)
    ch1 = 50 * np.sin(2 * np.pi * 10 * time_axis) + 20 * rng.standard_normal(n_samples)

    # Channel 2: Weak signal (only noise)
    ch2 = 5 * rng.standard_normal(n_samples)

    # Channel 3: Artifacts
    ch3 = 50 * np.sin(2 * np.pi * 10 * time_axis) + 20 * rng.standard_normal(n_samples)
    ch3[500:600] += 300  # Large artifact

    # Channel 4: 50Hz interference
    ch4 = (50 * np.sin(2 * np.pi * 10 * time_axis) +
           100 * np.sin(2 * np.pi * 50 * time_axis) +
           20 * rng.standard_normal(n_samples))

    test_eeg_data = np.column_stack([ch1, ch2, ch3, ch4])

    # Check quality
    detailed_quality_check(test_eeg_data, print_report=True)

    # Quick check
    print("\nQuick check:")
    quick_quality = quick_quality_check(test_eeg_data)
    print(f"Quality: {quick_quality}/100")


if __name__ == "__main__":
    _run_tests()
