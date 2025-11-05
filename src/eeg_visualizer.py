"""
Real-time EEG signal visualization module.

Uses matplotlib and MNE to display:
- Raw EEG traces (all channels)
- Topographic activity maps (topomaps)
- Power spectrogram
"""

from collections import deque
import time
from typing import Any, Optional, Dict, List

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.figure import Figure
from matplotlib.axes import Axes

import config


matplotlib.use('TkAgg')  # Non-blocking backend

# MNE for topographic maps
try:
    from mne.viz import plot_topomap  # type: ignore
    MNE_AVAILABLE = True
except ImportError:
    MNE_AVAILABLE = False
    print("⚠️  MNE not available - advanced visualization disabled")


class EEGVisualizer:
    """
    EEG signal visualization in separate window.

    Displays real-time EEG signals with raw traces and topographic maps.
    """

    def __init__(self, buffer_duration: float = 5.0) -> None:
        """
        Initialize EEG visualizer.

        :param buffer_duration: Length of displayed time window (seconds)
        """
        self.buffer_duration = buffer_duration
        self.sample_rate = config.SAMPLE_RATE
        self.buffer_size = int(buffer_duration * self.sample_rate)

        # Channel names for Muse S Athena
        # Note: Brain Art uses only 4 main channels (TP9, AF7, AF8, TP10)
        # OpenMuse may send 8 channels (4 main + 4 AUX), but we only use the first 4
        self.channel_names = ['TP9', 'AF7', 'AF8', 'TP10']  # Main 4 channels

        # Always use 4 channels (consistent with eeg_processor.py)
        # Even if LSL sends more, we only use the first 4
        self.n_channels = 4

        # Data buffers
        self.eeg_buffer: deque[np.ndarray] = deque(maxlen=self.buffer_size)
        self.time_buffer: deque[float] = deque(maxlen=self.buffer_size)

        # Band power buffer - AVERAGED (one value per band)
        # Example: {'alpha': 30.5, 'beta': 20.2}
        self.band_powers_buffer: deque[Dict[str, float]] = deque(maxlen=50)

        # Band power buffer - PER-CHANNEL (list of values per band)
        # Example: {'alpha': [28.0, 35.0, 32.0, 29.0], 'beta': [18.0, 25.0, 28.0, 16.0]}
        #                      TP9   AF7   AF8   TP10         TP9   AF7   AF8   TP10
        self.band_powers_per_channel_buffer: deque[Dict[str, List[float]]] = deque(maxlen=50)

        # Electrode positions for Muse S (for topomaps)
        # 10-20 system: all available electrodes
        self.electrode_positions: Optional[Dict[str, List[float]]] = self._create_electrode_positions()

        # Matplotlib setup
        self.fig: Optional[Figure] = None
        self.axes: Dict[str, Axes] = {}
        self.lines: List[Any] = []
        self.topomap_artists: Optional[Any] = None
        self.is_running: bool = False

        # Timing
        self.last_update: float = time.time()
        self.update_interval: float = 0.1  # 10 Hz update rate

        # Internal flags
        self._initialized_channels: bool = False
        
        # Throttling for debug output (per-band)
        self._last_debug_output: Dict[str, float] = {}
        self._debug_output_interval: float = 3.0  # Show debug output every 3 seconds

    def _create_electrode_positions(self) -> Optional[Dict[str, List[float]]]:
        """
        Create electrode positions for Muse S Athena in 10-20 system.

        :return: Dictionary of electrode positions (x, y) or None if MNE not available
        """
        if not MNE_AVAILABLE:
            return None

        # Positions in 2D (x, y) normalized
        # TP9 (left back), AF7 (left front), AF8 (right front), TP10 (right back)
        positions = {
            # Main 4 electrodes
            'TP9':  [-0.6, -0.2],   # Left back (behind ear)
            'AF7':  [-0.4,  0.6],   # Left front (above left eye)
            'AF8':  [ 0.4,  0.6],   # Right front (above right eye)
            'TP10': [ 0.6, -0.2],   # Right back (behind ear)
        }

        return positions

    def setup_window(self) -> None:
        """
        Initialize matplotlib window with visualizations.

        Sets up either full layout (with raw traces) or compact layout (topomaps only)
        depending on configuration.
        """
        # Check whether to show raw traces
        show_raw_traces = getattr(config, 'EEG_MONITOR_SHOW_RAW_TRACES', False)

        if show_raw_traces:
            # Layout with raw traces: 2 rows, 2 columns
            self.fig = plt.figure(figsize=(14, 8))
            manager = self.fig.canvas.manager
            if manager is not None:
                manager.set_window_title('Brain Art - EEG Monitor')

            gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

            # 1. Raw EEG traces (top row, full width)
            ax_eeg = self.fig.add_subplot(gs[0, :])
            self._setup_eeg_plot(ax_eeg)
            self.axes['eeg'] = ax_eeg

            # 2. Topomap - Alpha activity (front part)
            ax_topo_alpha = self.fig.add_subplot(gs[1, 0])
            self._setup_topomap_plot(ax_topo_alpha, 'Alpha')
            self.axes['topo_alpha'] = ax_topo_alpha

            # 3. Topomap - Beta activity (front part)
            ax_topo_beta = self.fig.add_subplot(gs[1, 1])
            self._setup_topomap_plot(ax_topo_beta, 'Beta')
            self.axes['topo_beta'] = ax_topo_beta

            print("✅ EEG visualization window opened (with raw traces)")
        else:
            # Layout without raw traces: only topomaps in 1 row
            self.fig = plt.figure(figsize=(12, 6))
            manager = self.fig.canvas.manager
            if manager is not None:
                manager.set_window_title('Brain Art - EEG Monitor (Topomaps)')

            gs = self.fig.add_gridspec(1, 2, hspace=0.3, wspace=0.3)

            # 1. Topomap - Alpha activity
            ax_topo_alpha = self.fig.add_subplot(gs[0, 0])
            self._setup_topomap_plot(ax_topo_alpha, 'Alpha')
            self.axes['topo_alpha'] = ax_topo_alpha

            # 2. Topomap - Beta activity
            ax_topo_beta = self.fig.add_subplot(gs[0, 1])
            self._setup_topomap_plot(ax_topo_beta, 'Beta')
            self.axes['topo_beta'] = ax_topo_beta

            print("✅ EEG visualization window opened (topomaps only)")
            print("💡 Use 'OpenMuse view' to preview raw signals")

        # Set non-blocking mode
        plt.ion()
        plt.show(block=False)

        self.is_running = True

    def _setup_eeg_plot(self, ax: Axes) -> None:
        """
        Set up raw EEG plot.

        :param ax: Matplotlib axes object
        """
        ax.set_title('EEG Signals - Last 5 seconds', fontsize=12, fontweight='bold')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Channel')
        ax.set_xlim(0, self.buffer_duration)

        # Initial setup for 4 channels (will update when we know the count)
        ax.set_ylim(-0.5, 3.5)
        ax.set_yticks(range(4))
        ax.set_yticklabels(self.channel_names)
        ax.grid(True, alpha=0.3)

        # Colors for 4 channels
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A',  # TP9, AF7, AF8, TP10
        ]

        # Create lines for channels (initially 4, will expand if needed)
        self.lines = []
        for i in range(4):
            line, = ax.plot([], [], color=colors[i], linewidth=1.5, label=self.channel_names[i])
            self.lines.append(line)

        ax.legend(loc='upper right', fontsize=8)

    def _setup_topomap_plot(self, ax: Axes, band_name: str) -> None:
        """
        Set up topographic activity map.

        :param ax: Matplotlib axes object
        :param band_name: Name of frequency band (e.g., 'Alpha', 'Beta')
        """
        ax.set_title(f'{band_name} Activity\n(Frontal-temporal region)', 
                     fontsize=10, fontweight='bold')
        ax.axis('off')

        # Placeholder text
        ax.text(0.5, 0.5, f'Waiting for data\n{band_name}...', 
                ha='center', va='center', fontsize=10, color='gray')

    def update_data(self, eeg_data: np.ndarray, 
                    band_powers: Optional[Dict[str, float]] = None, 
                    band_powers_per_channel: Optional[Dict[str, List[float]]] = None) -> None:
        """
        Update data buffers.

        :param eeg_data: Numpy array [samples, channels]
        :param band_powers: Dictionary {'alpha': float, 'beta': float, ...} (averaged)
        :param band_powers_per_channel: Dictionary {'alpha': [ch0, ch1, ch2, ch3], ...} (per-channel)
        """
        if eeg_data is None or len(eeg_data) == 0:
            return

        # Check number of channels in LSL stream
        n_channels_in_lsl = eeg_data.shape[1] if len(eeg_data.shape) > 1 else 1

        # First update - set channel count
        if not self._initialized_channels:
            # ⚠️ IMPORTANT: Use maximum 4 channels
            # (consistent with eeg_processor.py which processes only 4)
            self.n_channels = 4  # Always 4 (as in eeg_processor)
            self._initialized_channels = True

            print(f"📊 EEG Monitor: LSL stream has {n_channels_in_lsl} channels")
            if n_channels_in_lsl > 4:
                print("   ℹ️  Using first 4 channels (consistent with eeg_processor)")
                print(f"   ℹ️  Remaining {n_channels_in_lsl - 4} channels: probably padding/unused")
            elif n_channels_in_lsl == 4:
                print("   ✅ 4 main channels (TP9, AF7, AF8, TP10)")
            else:
                print("   ⚠️  Less than 4 channels! Check OpenMuse preset")

        # Add to EEG buffer
        current_time = time.time()
        for sample in eeg_data:
            self.eeg_buffer.append(sample)
            self.time_buffer.append(current_time)
            current_time += 1.0 / self.sample_rate

        # Add band powers - AVERAGED (one value per band)
        # Format: {'alpha': 30.5, 'beta': 20.2}
        if band_powers:
            self.band_powers_buffer.append(band_powers)

        # Add band powers - PER-CHANNEL (list of values per band for topomaps)
        # Format: {'alpha': [28.0, 35.0, 32.0, 29.0], 'beta': [...]}
        if band_powers_per_channel:
            self.band_powers_per_channel_buffer.append(band_powers_per_channel)

    def update_plots(self) -> None:
        """
        Update plots (call in main loop).

        Throttled to reduce CPU load.
        """
        if not self.is_running:
            return

        # Throttle updates
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return
        self.last_update = current_time

        try:
            # Check if window is closed
            if self.fig is None or not plt.fignum_exists(self.fig.number):
                self.is_running = False
                return

            # Update EEG traces (if they exist)
            if 'eeg' in self.axes:
                self._update_eeg_plot()

            # Update topomaps
            # Use per-channel if available, otherwise fallback to averaged
            if MNE_AVAILABLE and len(self.band_powers_per_channel_buffer) > 0:
                self._update_topomap('alpha', use_per_channel=True)
                self._update_topomap('beta', use_per_channel=True)
            elif MNE_AVAILABLE and len(self.band_powers_buffer) > 0:
                self._update_topomap('alpha', use_per_channel=False)
                self._update_topomap('beta', use_per_channel=False)

            # Refresh canvas
            if self.fig is not None:
                self.fig.canvas.draw_idle()
                self.fig.canvas.flush_events()

        except Exception as e:
            if config.DEBUG:
                print(f"⚠️  Visualization update error: {e}")

    def _update_eeg_plot(self) -> None:
        """
        Update raw EEG plot.
        """
        if len(self.eeg_buffer) < 2:
            return

        # Convert buffers to numpy
        data = np.array(self.eeg_buffer)  # [samples, channels]
        times = np.array(self.time_buffer)

        # Normalize time to 0-buffer_duration
        times = times - times[0]

        # Normalize amplitudes for better visualization
        # Each channel on its own "track"
        for i in range(self.n_channels):
            channel_data = data[:, i]

            # Normalize to range ±0.3 around channel position
            normalized = (channel_data - np.mean(channel_data)) / (np.std(channel_data) + 1e-6)
            normalized = np.clip(normalized * 0.15, -0.3, 0.3)

            # Shift to channel position
            y_data = normalized + i

            # Update line
            self.lines[i].set_data(times, y_data)

        # Update xlim if exceeded
        if times[-1] > self.buffer_duration:
            self.axes['eeg'].set_xlim(times[-1] - self.buffer_duration, times[-1])

    def _update_topomap(self, band_name: str, use_per_channel: bool = True) -> None:
        """
        Update topographic map for given band.

        :param band_name: Band name ('alpha', 'beta', etc.)
        :param use_per_channel: Whether to use per-channel data (True) or averaged (False)
        """
        if not MNE_AVAILABLE:
            return

        # Check which buffer to use
        if (use_per_channel and len(self.band_powers_per_channel_buffer) < 5) or \
           (not use_per_channel and len(self.band_powers_buffer) < 5):
            return

        try:
            # Select appropriate axis
            ax_key = f'topo_{band_name.lower()}'
            ax = self.axes.get(ax_key)
            if ax is None:
                return

            if use_per_channel:
                # ✅ NEW: Use real per-channel values!
                recent_powers: List[Dict[str, List[float]]] = list(self.band_powers_per_channel_buffer)[-10:]  # Last 10 samples

                # Average over time for each channel separately
                powers_per_ch: List[float] = []
                for ch_idx in range(self.n_channels):
                    ch_powers = [p.get(band_name.lower(), [0] * self.n_channels)[ch_idx]
                                 for p in recent_powers if p and len(p.get(band_name.lower(), [])) > ch_idx]
                    if ch_powers:
                        powers_per_ch.append(float(np.mean(ch_powers)))
                    else:
                        powers_per_ch.append(0.0)

                powers = np.array(powers_per_ch)
                avg_power = np.mean(powers)  # For display
                
                # Debug: Show per-channel values (throttled - every 3 seconds)
                if config.DEBUG and len(powers_per_ch) == 4:
                    current_time = time.time()
                    last_output = self._last_debug_output.get(band_name.lower(), 0)
                    if current_time - last_output >= self._debug_output_interval:
                        print(f"\n📊 {band_name} per-channel powers: "
                              f"TP9={powers_per_ch[0]:.2f}, AF7={powers_per_ch[1]:.2f}, "
                              f"AF8={powers_per_ch[2]:.2f}, TP10={powers_per_ch[3]:.2f}")
                        self._last_debug_output[band_name.lower()] = current_time
            else:
                # ❌ OLD: Fallback - use same power for all channels
                recent_powers_avg: List[Dict[str, float]] = list(self.band_powers_buffer)[-10:]
                avg_power = np.mean([p.get(band_name.lower(), 0) for p in recent_powers_avg if p])
                powers = np.array([avg_power] * self.n_channels)
                # Create empty list for per-channel values (fallback mode)
                powers_per_ch = []

            # Electrode positions - 4 main channels only
            # ⚠️ IMPORTANT: Make sure number of positions matches number of data points!
            if self.electrode_positions is None:
                return  # Cannot create topomap without positions
            
            # Always use 4 main channels
            channel_list = self.channel_names
            pos_array = np.array([
                self.electrode_positions['TP9'],
                self.electrode_positions['AF7'],
                self.electrode_positions['AF8'],
                self.electrode_positions['TP10']
            ])

            # 🔧 FIX: Make sure length of powers == length of pos_array
            if len(powers) != len(pos_array):
                if config.DEBUG:
                    print(f"\n⚠️  Length mismatch: powers={len(powers)}, pos={len(pos_array)}")
                    print(f"   Using first {len(pos_array)} channels")
                # Limit to smaller length
                powers = powers[:len(pos_array)]
                # Or pad with zeros if too few
                if len(powers) < len(pos_array):
                    powers = np.pad(powers, (0, len(pos_array) - len(powers)), constant_values=0)

            # Clear previous plot
            ax.clear()
            ax.axis('off')
            title = f'{band_name.capitalize()} Activity\n'
            title += f'(Frontal-temporal region - {self.n_channels} electrode{"s" if self.n_channels != 1 else ""})'
            ax.set_title(title, fontsize=10, fontweight='bold')
            
            # Add current signal values (amplitudes in µV) in top-left corner
            if len(self.eeg_buffer) > 0:
                # Get last few samples (e.g., last 10-20 samples for stability)
                recent_samples = list(self.eeg_buffer)[-min(20, len(self.eeg_buffer)):]
                recent_data = np.array(recent_samples)  # [samples, channels]
                
                # Calculate RMS (Root Mean Square) for each channel for stable values
                # Or use mean absolute value
                channel_values = []
                for ch_idx in range(min(4, recent_data.shape[1] if len(recent_data.shape) > 1 else 1)):
                    if len(recent_data.shape) > 1:
                        ch_data = recent_data[:, ch_idx]
                        # Use RMS for more stable representation
                        rms_value = np.sqrt(np.mean(ch_data ** 2))
                        channel_values.append(rms_value)
                    else:
                        channel_values.append(0.0)
                
                # Format as text: TP9=XX.XX µV, AF7=XX.XX µV, etc.
                signal_text_parts = []
                for ch_idx, (ch_name, value) in enumerate(zip(channel_list[:len(channel_values)], channel_values)):
                    signal_text_parts.append(f"{ch_name}={value:.1f} µV")
                
                signal_text = " | ".join(signal_text_parts)
                
                # Display in top-left corner (x=0.02, y=0.98 in axes coordinates)
                ax.text(0.02, 0.98, signal_text,
                        ha='left', va='top', fontsize=7, transform=ax.transAxes,
                        family='monospace', color='darkblue', weight='bold',
                        bbox={'boxstyle': 'round', 'pad': 0.3, 'facecolor': 'white', 'alpha': 0.85, 'edgecolor': 'navy', 'linewidth': 1})

            # Muse S has electrodes only at front, don't cover whole head

            # FIX: Add small random offset (jitter) to positions
            # to avoid Qhull error for cocircular/cospherical points
            jitter_rng = np.random.default_rng(seed=42)
            pos_jittered = pos_array + jitter_rng.normal(0.0, 0.001, size=pos_array.shape)

            _, _ = plot_topomap(
                powers,
                pos_jittered,  # Use jittered positions
                axes=ax,
                show=False,
                cmap='RdYlBu_r',
                vlim=(powers.min() if powers.max() > powers.min() else 0, 
                      powers.max() if powers.max() > powers.min() else 1),
                contours=3,  # Fewer contours for better readability
                sensors=True,
                names=channel_list,
                sphere=(0, 0.35, 0, 0.45),  # Front of head - smaller interpolation area
                res=64,  # Lower resolution = less "guessing"
                outlines='head',  # Show head outline for context
            )

            # Add colorbar hint and per-channel values
            power_range = powers.max() - powers.min()
            ax.text(0.5, -0.12, f'Power: {avg_power:.1f} µV² (±{power_range / 2:.1f})',
                    ha='center', va='top', fontsize=8, transform=ax.transAxes)
            
            # Add per-channel power values below the topomap
            # Check if powers_per_ch is available and has data (from use_per_channel=True path)
            if use_per_channel and powers_per_ch and len(powers_per_ch) == 4 and len(channel_list) == 4:
                channel_values_text = []
                for ch_name, power_val in zip(channel_list, powers_per_ch):
                    # Format power value (use scientific notation if very large)
                    if power_val > 1000000:
                        power_str = f"{power_val/1000000:.2f}M"
                    elif power_val > 1000:
                        power_str = f"{power_val/1000:.2f}K"
                    else:
                        power_str = f"{power_val:.1f}"
                    channel_values_text.append(f"{ch_name}={power_str}")
                
                values_text = " | ".join(channel_values_text)
                # Position text below the power info (adjust y position to be visible)
                # Use transform=ax.transAxes to position relative to axis (0-1 range)
                ax.text(0.5, -0.20, values_text,
                        ha='center', va='top', fontsize=7, transform=ax.transAxes,
                        family='monospace', color='darkslategray', weight='bold',
                        bbox={'boxstyle': 'round', 'pad': 0.3, 'facecolor': 'white', 'alpha': 0.8, 'edgecolor': 'gray'})

        except Exception as e:
            if config.DEBUG:
                print(f"⚠️  Topomap drawing error {band_name}: {e}")
            # Fallback: show text
            ax_key = f'topo_{band_name.lower()}'
            ax = self.axes.get(ax_key)
            if ax is not None:
                ax.clear()
                ax.axis('off')
                ax.text(0.5, 0.5, f'{band_name}\n{avg_power:.1f} µV²',
                        ha='center', va='center', fontsize=12, fontweight='bold')

    def close(self) -> None:
        """
        Close visualization window.
        """
        if self.fig:
            plt.close(self.fig)
        self.is_running = False
        print("📊 EEG visualization window closed")


class SimpleEEGVisualizer:
    """
    Simplified version without MNE (fallback).

    Used when MNE is not available - shows only raw traces.
    """

    def __init__(self, buffer_duration: float = 5.0) -> None:
        self.buffer_duration = buffer_duration
        self.sample_rate = config.SAMPLE_RATE
        self.buffer_size = int(buffer_duration * self.sample_rate)

        # Muse S Athena: 4 main channels
        self.channel_names = ['TP9', 'AF7', 'AF8', 'TP10']
        self.n_channels = 4  # Always 4 channels

        self.eeg_buffer: deque[np.ndarray] = deque(maxlen=self.buffer_size)
        self.time_buffer: deque[float] = deque(maxlen=self.buffer_size)

        self.fig: Optional[Figure] = None
        self.axes: Dict[str, Axes] = {}
        self.lines: List[Any] = []
        self.is_running: bool = False
        self.last_update: float = time.time()
        self.update_interval: float = 0.1

        # Internal flags
        self._initialized: bool = False
        

    def setup_window(self) -> None:
        """
        Simpler version - only raw traces.
        """
        self.fig, ax = plt.subplots(figsize=(12, 6))
        manager = self.fig.canvas.manager
        if manager is not None:
            manager.set_window_title('Brain Art - EEG Monitor (Simple)')

        ax.set_title('EEG Signals - Last 5 seconds', fontsize=12, fontweight='bold')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Channel')
        ax.set_xlim(0, self.buffer_duration)
        ax.set_ylim(-0.5, self.n_channels - 0.5)
        ax.set_yticks(range(self.n_channels))
        ax.set_yticklabels(self.channel_names)
        ax.grid(True, alpha=0.3)

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        self.lines = []
        for i, color in enumerate(colors):
            line, = ax.plot([], [], color=color, linewidth=1.5, label=self.channel_names[i])
            self.lines.append(line)

        ax.legend(loc='upper right')
        self.axes['eeg'] = ax

        plt.ion()
        plt.show(block=False)
        self.is_running = True

        print("✅ EEG visualization window opened (simple mode)")

    def update_data(self, eeg_data: np.ndarray, 
                    _band_powers: Optional[Dict[str, float]] = None) -> None:
        """
        Update buffers.

        :param eeg_data: EEG data array
        :param band_powers: Band powers dictionary (optional)
        """

        if eeg_data is None or len(eeg_data) == 0:
            return

        # Auto-detect number of channels
        if not self._initialized:
            n_ch = eeg_data.shape[1] if len(eeg_data.shape) > 1 else 1
            # Always use 4 channels (consistent with eeg_processor)
            self.n_channels = 4
            print(f"📊 EEG Monitor (simple): LSL stream has {n_ch} channels, using 4")
            self._initialized = True

        current_time = time.time()
        for sample in eeg_data:
            self.eeg_buffer.append(sample)
            self.time_buffer.append(current_time)
            current_time += 1.0 / self.sample_rate

    def update_plots(self) -> None:
        """
        Update plot.
        """
        if not self.is_running:
            return

        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return
        self.last_update = current_time

        try:
            if self.fig is None:
                self.is_running = False
                return
            
            if not plt.fignum_exists(self.fig.number):
                self.is_running = False
                return

            if len(self.eeg_buffer) < 2:
                return

            data = np.array(self.eeg_buffer)
            times = np.array(self.time_buffer)
            times = times - times[0]

            for i in range(self.n_channels):
                channel_data = data[:, i]
                normalized = (channel_data - np.mean(channel_data)) / (np.std(channel_data) + 1e-6)
                normalized = np.clip(normalized * 0.15, -0.3, 0.3)
                y_data = normalized + i
                self.lines[i].set_data(times, y_data)

            if times[-1] > self.buffer_duration:
                self.axes['eeg'].set_xlim(times[-1] - self.buffer_duration, times[-1])

            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()

        except Exception as e:
            if config.DEBUG:
                print(f"⚠️  Visualization error: {e}")

    def close(self) -> None:
        """
        Close window.
        """
        if self.fig:
            plt.close(self.fig)
        self.is_running = False


# Factory function
def create_eeg_visualizer(use_advanced: bool = True, buffer_duration: float = 5.0):
    """
    Create EEG visualizer.

    :param use_advanced: Whether to use advanced version with MNE (topomaps)
    :param buffer_duration: Length of time window (seconds)
    :return: EEGVisualizer or SimpleEEGVisualizer instance
    """
    if use_advanced and MNE_AVAILABLE:
        return EEGVisualizer(buffer_duration)
    else:
        if use_advanced and not MNE_AVAILABLE:
            print("⚠️  MNE not available - using simple version")
        return SimpleEEGVisualizer(buffer_duration)


if __name__ == "__main__":
    # Visualizer test with simulated data
    print("=== Test EEG Visualizer ===\n")

    viz = create_eeg_visualizer(use_advanced=True, buffer_duration=5.0)
    viz.setup_window()

    print("Generating simulated EEG data...")
    print("Close the window to end the test.\n")

    sample_rate = 256
    t = 0.
    rng = np.random.default_rng(seed=42)

    try:
        while viz.is_running:
            # Simulate EEG data (4 channels)
            duration = 0.1  # 100ms
            n_samples = int(duration * sample_rate)

            # Generate waves
            time_vec = np.linspace(t, t + duration, n_samples)
            ch1 = 50 * np.sin(2 * np.pi * 10 * time_vec) + 20 * rng.normal(0.0, 1.0, n_samples)  # Alpha
            ch2 = 30 * np.sin(2 * np.pi * 20 * time_vec) + 15 * rng.normal(0.0, 1.0, n_samples)  # Beta
            ch3 = 40 * np.sin(2 * np.pi * 12 * time_vec) + 18 * rng.normal(0.0, 1.0, n_samples)  # Alpha
            ch4 = 35 * np.sin(2 * np.pi * 18 * time_vec) + 16 * rng.normal(0.0, 1.0, n_samples)  # Beta

            simulated_eeg_data = np.column_stack([ch1, ch2, ch3, ch4])

            # Simulate band powers
            simulated_band_powers = {
                'alpha': 30 + 10 * np.sin(t),
                'beta': 20 + 8 * np.cos(t * 1.5),
                'gamma': 10 + 5 * np.sin(t * 2),
            }

            # Update
            viz.update_data(simulated_eeg_data, simulated_band_powers)
            viz.update_plots()

            t += duration
            time.sleep(0.05)  # ~20 Hz

    except KeyboardInterrupt:
        print("\n⏹️  Test stopped")

    viz.close()
    print("\n✅ Test completed")
