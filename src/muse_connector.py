"""
Module to connect to Muse S Athena.

Supports two modes: LSL (recommended) and direct Bluetooth.
Provides EEG and motion data streaming with signal quality monitoring.
"""

import time
from typing import Optional, Callable, Tuple, List, Any

import numpy as np

import config
from .signal_quality import SignalQualityChecker, quick_quality_check

# LSL imports (for LSL mode)
LSL_AVAILABLE: bool = False
LSL_TYPE: Optional[str] = None
resolve_byprop = None  # Will be set if pylsl is available
resolve_streams = None  # Will be set if mne_lsl is available
StreamInlet = None  # Will be set based on available library

try:
    # Prefer MNE-LSL (used by OpenMuse)
    from mne_lsl.lsl import StreamInlet, resolve_streams  # type: ignore
    LSL_AVAILABLE = True
    LSL_TYPE = "mne_lsl"
except ImportError:
    try:
        # Fallback to pylsl (older version)
        from pylsl import StreamInlet, resolve_byprop  # type: ignore
        LSL_AVAILABLE = True
        LSL_TYPE = "pylsl"
    except ImportError:
        LSL_AVAILABLE = False
        LSL_TYPE = None
        print("⚠️  LSL not available - install: pip install mne-lsl")

# Error messages for LSL availability checks
ERROR_MNE_LSL_RESOLVE_STREAMS = "mne_lsl not available - resolve_streams is None"
ERROR_PYLSL_RESOLVE_BYPROP = "pylsl not available - resolve_byprop is None"
ERROR_MNE_LSL_STREAM_INLET = "mne_lsl not available - StreamInlet is None"
ERROR_PYLSL_STREAM_INLET = "pylsl not available - StreamInlet is None"

# Bluetooth imports (for direct mode)
BLUETOOTH_AVAILABLE: bool = False
try:
    import asyncio
    from bleak import BleakClient, BleakScanner
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    print("⚠️  bleak not available - Bluetooth mode disabled")


class MuseConnector:
    """
    Handles connection to Muse S and streaming EEG data.
    
    Supports LSL (Lab Streaming Layer) and direct Bluetooth connections.
    Provides signal quality monitoring and motion data streaming.
    """

    def __init__(self, mode: str = 'lsl', enable_motion: bool = True) -> None:
        """
        Initialize the Muse connector.
        
        :param mode: Connection mode - 'lsl' or 'bluetooth'
        :param enable_motion: Enable motion data streaming
        """
        self.mode: str = mode
        self.inlet: Optional[Any] = None  # LSL inlet for EEG
        self.motion_inlet: Optional[Any] = None  # LSL inlet for ACC/GYRO
        self.enable_motion: bool = enable_motion
        self.client: Optional[Any] = None
        self.is_connected: bool = False
        self.callback: Optional[Callable] = None
        self.loop: Optional[Any] = None

        # Data buffers
        self.eeg_buffer: List[np.ndarray] = []
        self.last_data: Optional[np.ndarray] = None
        self.motion_buffer: List[np.ndarray] = []
        self.last_motion_data: Optional[np.ndarray] = None

        # Signal quality checker
        self.quality_checker: SignalQualityChecker = SignalQualityChecker(sample_rate=config.SAMPLE_RATE)
        self.signal_quality: List[int] = []  # Quality for each channel (0-100), auto-detect 4 or 8
        self.overall_quality: int = 0
        self.quality_warnings: List[str] = []
        self.n_channels: Optional[int] = None  # Detected during connection
        
        # Track last timestamp to detect stale data
        self.last_timestamp: Optional[float] = None
        self.first_timestamp_after_flush: Optional[float] = None
        
        # Track channel names from LSL (for debugging)
        self.lsl_channel_names: Optional[List[str]] = None

    def connect(self) -> bool:
        """
        Establish connection to Muse S device.
        
        Attempts connection using the configured mode (LSL or Bluetooth).
        
        :return: True if connection successful, False otherwise
        """
        if self.mode == 'lsl':
            return self._connect_lsl()
        elif self.mode == 'bluetooth':
            return self._connect_bluetooth()
        else:
            print(f"❌ Unknown mode: {self.mode}")
            return False

    def _connect_lsl(self) -> bool:
        """
        Connect through Lab Streaming Layer.
        
        Requires OpenMuse stream or muselsl stream to be running.
        Auto-detects 4 or 8 channel configurations.
        
        :return: True if connection successful, False otherwise
        """
        if not LSL_AVAILABLE:
            print("❌ LSL not installed!")
            print("💡 Installation: pip install mne-lsl")
            return False

        print(f"🔍 Searching for Muse stream through LSL ({LSL_TYPE})...")

        try:
            # Search for EEG stream
            if LSL_TYPE == "mne_lsl":
                # MNE-LSL (OpenMuse)
                if resolve_streams is None:
                    raise RuntimeError(ERROR_MNE_LSL_RESOLVE_STREAMS)
                streams = resolve_streams(timeout=5)
                # Filter EEG streams - exclude BATTERY, ACCGYRO, OPTICS
                eeg_streams = [s for s in streams 
                              if ('EEG' in s.name or 'Muse' in s.name) 
                              and 'BATTERY' not in s.name 
                              and 'ACCGYRO' not in s.name 
                              and 'ACC' not in s.name 
                              and 'GYRO' not in s.name
                              and 'OPTICS' not in s.name]
                
                # Prioritize streams with "EEG" in name
                eeg_streams.sort(key=lambda s: ('EEG' not in s.name, s.name))
            else:
                # pylsl (old muselsl)
                if resolve_byprop is None:
                    raise RuntimeError(ERROR_PYLSL_RESOLVE_BYPROP)
                eeg_streams = resolve_byprop('type', 'EEG', timeout=5)

            if len(eeg_streams) == 0:
                print("❌ No Muse EEG stream found!")
                print("💡 Run in a separate terminal:")
                print("   OpenMuse stream --address <YOUR_MAC_ADDRESS>")
                print("   or: muselsl stream")
                print("\n📋 Available streams:")
                if LSL_TYPE == "mne_lsl":
                    if resolve_streams is None:
                        raise RuntimeError(ERROR_MNE_LSL_RESOLVE_STREAMS)
                    all_streams = resolve_streams(timeout=2)
                    for s in all_streams:
                        print(f"   - {s.name} ({s.n_channels} channels)")
                return False

            print(f"✅ Found {len(eeg_streams)} EEG stream(s)")

            # Connect to the first (prioritized) EEG stream
            if LSL_TYPE == "mne_lsl":
                # MNE-LSL: StreamInfo is ready
                if StreamInlet is None:
                    raise RuntimeError(ERROR_MNE_LSL_STREAM_INLET)
                self.inlet = StreamInlet(eeg_streams[0])
                # In MNE-LSL we use methods with get_
                stream_info = eeg_streams[0]
                name = stream_info.name
                n_channels = stream_info.n_channels
                srate = stream_info.sfreq
            else:
                # pylsl: need max_buflen
                if StreamInlet is None:
                    raise RuntimeError(ERROR_PYLSL_STREAM_INLET)
                self.inlet = StreamInlet(eeg_streams[0], max_buflen=360)
                if self.inlet is None:
                    raise RuntimeError("Failed to create StreamInlet")
                info = self.inlet.info()
                name = info.name()
                n_channels = info.channel_count()
                srate = info.nominal_srate()

            print(f"📡 Connected: {name}")
            print(f"   Channels: {n_channels}")
            print(f"   Frequency: {srate} Hz")

            # Check channel names (if available)
            try:
                if LSL_TYPE == "mne_lsl":
                    # MNE-LSL: get channel names
                    ch_names = stream_info.get_channel_names() if hasattr(stream_info, 'get_channel_names') else None
                    if ch_names:
                        print(f"   Channel names: {', '.join(ch_names)}")
                        self.lsl_channel_names = ch_names
                        # Warn if order doesn't match expected
                        if len(ch_names) >= 4:
                            expected_order = ['TP9', 'AF7', 'AF8', 'TP10']
                            actual_first_4 = ch_names[:4]
                            if actual_first_4 != expected_order:
                                print("   ⚠️  WARNING: Channel order mismatch!")
                                print(f"      Expected: {expected_order}")
                                print(f"      Got: {actual_first_4}")
                                print("      This may cause topomap misalignment!")
                else:
                    # pylsl: get channel names from XML description
                    ch_names = []
                    ch = info.desc().child("channel")
                    for k in range(n_channels):
                        ch_label = ch.child_value("label")
                        if ch_label:
                            ch_names.append(ch_label)
                        ch = ch.next_sibling()
                    if ch_names:
                        print(f"   Channel names: {', '.join(ch_names)}")
                        self.lsl_channel_names = ch_names
                        # Warn if order doesn't match expected
                        if len(ch_names) >= 4:
                            expected_order = ['TP9', 'AF7', 'AF8', 'TP10']
                            actual_first_4 = ch_names[:4]
                            if actual_first_4 != expected_order:
                                print("   ⚠️  WARNING: Channel order mismatch!")
                                print(f"      Expected: {expected_order}")
                                print(f"      Got: {actual_first_4}")
                                print("      This may cause topomap misalignment!")
            except Exception as e:
                if config.DEBUG:
                    print(f"   (Cannot get channel names: {e})")

            # Save number of channels
            self.n_channels = n_channels
            self.signal_quality = [0] * n_channels

            # Info about channels
            if n_channels == 8:
                print("   ℹ️   8 channels detected (OpenMuse may send 8 channels)")
                print("   💡 Brain Art uses only first 4 channels (TP9, AF7, AF8, TP10)")
                print("   💡 Remaining channels (AUX) are ignored for consistency with eeg_processor")
            elif n_channels == 4:
                print("   ✅ Muse S Athena - 4 main channels")
            else:
                print(f"   ⚠️  Custom number of channels: {n_channels}")

            # Connect to ACC/GYRO stream (optional)
            if self.enable_motion:
                self._connect_motion_stream(streams if LSL_TYPE == "mne_lsl" else None)

            # Flush old buffered data from previous sessions
            self._flush_lsl_buffer()
            
            # Small delay to let stream stabilize after connection
            # This helps ensure fresh data is available
            time.sleep(0.2)

            self.is_connected = True
            return True

        except Exception as e:
            print(f"❌ Error connecting LSL: {e}")
            import traceback  # type: ignore
            traceback.print_exc()
            return False

    def _connect_motion_stream(self, streams: Optional[List[Any]] = None) -> None:
        """
        Connect to ACC/GYRO motion stream.
        
        :param streams: List of all available streams (for MNE-LSL)
        """
        try:
            print("🎮 Searching for ACC/GYRO stream...")

            # Search for ACCGYRO stream
            if LSL_TYPE == "mne_lsl":
                if streams is None:
                    if resolve_streams is None:
                        raise RuntimeError(ERROR_MNE_LSL_RESOLVE_STREAMS)
                    streams = resolve_streams(timeout=2)
                # Filter ACCGYRO streams
                motion_streams = [s for s in streams if 'ACCGYRO' in s.name or 'ACC' in s.name]
            else:
                # pylsl - search by type
                if resolve_byprop is None:
                    raise RuntimeError(ERROR_PYLSL_RESOLVE_BYPROP)
                motion_streams = resolve_byprop('name', 'Muse_ACCGYRO', timeout=2)

            if len(motion_streams) == 0:
                print("   ℹ️  No ACC/GYRO stream found (optional)")
                return

            # Connect to the first stream
            if LSL_TYPE == "mne_lsl":
                if StreamInlet is None:
                    raise RuntimeError(ERROR_MNE_LSL_STREAM_INLET)
                self.motion_inlet = StreamInlet(motion_streams[0])
                stream_info = motion_streams[0]
                name = stream_info.name
                n_channels = stream_info.n_channels
            else:
                if StreamInlet is None:
                    raise RuntimeError(ERROR_PYLSL_STREAM_INLET)
                self.motion_inlet = StreamInlet(motion_streams[0], max_buflen=360)
                if self.motion_inlet is None:
                    raise RuntimeError("Failed to create StreamInlet")
                info = self.motion_inlet.info()
                name = info.name()
                n_channels = info.channel_count()

            print(f"   ✅ Connected: {name} ({n_channels} channels)")

        except Exception as e:
            print(f"   ⚠️  Error connecting to ACC/GYRO: {e}")
            self.motion_inlet = None

    def _connect_bluetooth(self) -> bool:
        """
        Connect directly through Bluetooth (experimental).
        
        Requires bleak library and MAC address in config.
        
        :return: True if connection successful, False otherwise
        """
        if not BLUETOOTH_AVAILABLE:
            print("❌ bleak not installed!")
            return False

        if not config.MUSE_ADDRESS:
            print("❌ No Muse MAC address in config.py")
            print("💡 Run: python find_muse.py")
            return False

        print(f"🔍 Connecting to Muse: {config.MUSE_ADDRESS}")

        # Bluetooth requires asyncio
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._async_connect_bluetooth())
            return self.is_connected
        except Exception as e:
            print(f"❌ Error connecting Bluetooth: {e}")
            return False

    async def _async_connect_bluetooth(self) -> None:
        """
        Asynchronous Bluetooth connection handler.
        
        Establishes BLE connection and subscribes to characteristics.
        Note: This is experimental - LSL mode is recommended.
        """
        try:
            self.client = BleakClient(config.MUSE_ADDRESS)
            await self.client.connect()

            if self.client.is_connected:
                print("✅ Connected to Muse through Bluetooth")
                self.is_connected = True

                # TODO: Subscribe to EEG characteristics
                # Requires knowledge of Muse UUID characteristics
                # This is more advanced - recommend using LSL
            else:
                print("❌ Error connecting")

        except Exception as e:
            print(f"❌ Error: {e}")
            self.is_connected = False

    def get_eeg_data(self, duration: float = 1.0) -> Optional[np.ndarray]:
        """
        Get EEG data from Muse device.
        
        :param duration: Duration of data to retrieve in seconds
        :return: NumPy array of shape [samples, channels] or None if not connected
        """
        if not self.is_connected:
            return None

        if self.mode == 'lsl':
            return self._get_lsl_data(duration)
        elif self.mode == 'bluetooth':
            return self._get_bluetooth_data(duration)

        return None

    def get_motion_data(self, duration: float = 0.1) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get ACC/GYRO motion data from Muse device.
        
        :param duration: Duration of data to retrieve in seconds
        :return: Tuple of (acc_data, gyro_data) where each is array [samples, 3], or None
                 acc_data: [X, Y, Z] acceleration in g
                 gyro_data: [X, Y, Z] angular velocity in deg/s
        """
        if not self.is_connected or not self.motion_inlet:
            return None

        try:
            # Get data from stream
            # Both MNE-LSL and pylsl use the same pull_chunk method for motion data
            samples, timestamps = self.motion_inlet.pull_chunk(timeout=duration)

            if len(samples) > 0:
                # shape: (n_samples, 6) → [ACC_X, ACC_Y, ACC_Z, GYRO_X, GYRO_Y, GYRO_Z]
                motion_data = np.array(samples)
                self.last_motion_data = motion_data

                # Split into ACC and GYRO
                if motion_data.shape[1] >= 6:
                    acc_data = motion_data[:, :3]    # First 3 columns = ACC
                    gyro_data = motion_data[:, 3:6]  # Next 3 columns = GYRO
                    return (acc_data, gyro_data)

        except Exception as e:
            if config.DEBUG:
                print(f"⚠️  Error getting ACC/GYRO data: {e}")

        return None

    def flush_buffer(self) -> None:
        """
        Public method to flush LSL buffer.
        
        Can be called before calibration to ensure fresh data.
        """
        self._flush_lsl_buffer()
    
    def _flush_lsl_buffer(self) -> None:
        """
        Flush old buffered data from LSL stream.
        
        This is important when reconnecting - old data from previous sessions
        can cause quality to be incorrectly calculated.
        """
        if not self.inlet:
            return

        try:
            flush_timeout = 0.1
            max_flush_attempts = 30  # Increased attempts to ensure complete flush
            flushed_count = 0
            
            for _ in range(max_flush_attempts):
                if LSL_TYPE == "mne_lsl":
                    samples, _ = self.inlet.pull_chunk(timeout=flush_timeout)
                else:
                    samples, _ = self.inlet.pull_chunk(timeout=flush_timeout, max_samples=1000)
                
                if len(samples) == 0:
                    # No more buffered data
                    break
                
                # Check if data is old (more than 2 seconds old) - definitely stale
                # Handle timestamps - can be list or numpy array
                # Always flush samples (we're flushing buffer anyway)
                flushed_count += len(samples)
                    
            if config.DEBUG and flushed_count > 0:
                print(f"   🧹 Flushed LSL buffer ({flushed_count} samples cleared)")
            
            # Reset timestamp tracking after flush
            self.last_timestamp = None
            self.first_timestamp_after_flush = None
        except Exception as e:
            if config.DEBUG:
                print(f"   ⚠️  Error flushing buffer: {e}")

    def _get_lsl_data(self, duration: float = 1.0) -> Optional[np.ndarray]:
        """
        Get data from LSL stream.
        
        :param duration: Duration of data to retrieve in seconds
        :return: NumPy array of shape [samples, channels] or None
        """
        if not self.inlet:
            return None

        try:
            # Calculate how many samples we need
            n_samples = int(duration * config.SAMPLE_RATE)

            # Get data from stream
            if LSL_TYPE == "mne_lsl":
                # MNE-LSL returns (samples, timestamps)
                samples, timestamps = self.inlet.pull_chunk(timeout=duration)
            else:
                # pylsl
                samples, timestamps = self.inlet.pull_chunk(
                    timeout=duration,
                    max_samples=n_samples
                )

            if len(samples) > 0:
                eeg_data = np.array(samples)
                
                # Debug: Check if all channels have data (not just zeros)
                if config.DEBUG and eeg_data.shape[0] > 10:
                    n_channels_data = eeg_data.shape[1] if len(eeg_data.shape) > 1 else 1
                    channel_stats = []
                    for ch_idx in range(min(4, n_channels_data)):
                        ch_data = eeg_data[:, ch_idx]
                        ch_mean = np.mean(np.abs(ch_data))
                        ch_std = np.std(ch_data)
                        ch_has_data = ch_mean > 0.1 and ch_std > 0.1
                        channel_stats.append((ch_idx, ch_mean, ch_std, ch_has_data))
                        if not ch_has_data:
                            ch_name = self.lsl_channel_names[ch_idx] if self.lsl_channel_names and ch_idx < len(self.lsl_channel_names) else f"Ch{ch_idx}"
                            print(f"   ⚠️  Channel {ch_idx} ({ch_name}) appears to have no/zero data (mean={ch_mean:.4f}, std={ch_std:.4f})")
                    
                    # Summary: Show which channels have data
                    active_channels = [i for i, _, _, has_data in channel_stats if has_data]
                    if len(active_channels) < 4:
                        print(f"   ⚠️  Only {len(active_channels)}/4 channels have data: {active_channels}")
                        if self.lsl_channel_names and len(self.lsl_channel_names) >= 4:
                            print(f"   📋 LSL channel names: {self.lsl_channel_names[:4]}")
                            print(f"   💡 Expected order: TP9, AF7, AF8, TP10")
                
                # Verify data freshness using timestamps (if available)
                # LSL timestamps are relative to stream start, so we check if they're increasing
                # Check safely for numpy arrays
                try:
                    if timestamps is not None:
                        # Handle numpy arrays and lists
                        if hasattr(timestamps, 'size'):
                            # NumPy array
                            if timestamps.size > 0:
                                ts_list = timestamps.tolist()
                                latest_timestamp = float(max(ts_list))
                            else:
                                latest_timestamp = None
                        elif hasattr(timestamps, '__len__'):
                            # List or other sequence
                            if len(timestamps) > 0:
                                ts_list = list(timestamps)
                                latest_timestamp = float(max(ts_list))
                            else:
                                latest_timestamp = None
                        else:
                            latest_timestamp = None
                    else:
                        latest_timestamp = None
                    
                    if latest_timestamp is not None:
                        # If this is first data after flush, record it
                        if self.first_timestamp_after_flush is None:
                            self.first_timestamp_after_flush = latest_timestamp
                            self.last_timestamp = latest_timestamp
                        else:
                            # Check if timestamp is increasing (data is fresh and new)
                            if self.last_timestamp is not None and latest_timestamp <= self.last_timestamp:
                                # Timestamp didn't increase - might be stale or duplicate
                                if config.DEBUG:
                                    print("   ⚠️  Timestamp not increasing (stale data?)")
                                # Still update timestamp but be cautious
                                self.last_timestamp = latest_timestamp
                            else:
                                # Timestamp increased - fresh data
                                self.last_timestamp = latest_timestamp
                except (ValueError, TypeError, AttributeError) as e:
                    # If we can't parse timestamps, just continue
                    if config.DEBUG:
                        print(f"   ⚠️  Could not parse timestamps: {e}")
                
                self.last_data = eeg_data

                # Update signal quality - always update if we have any data
                # Use quick check for small samples, full check for larger ones
                if eeg_data.shape[0] > 0:
                    self._update_signal_quality(eeg_data)

                return eeg_data

        except Exception as e:
            if config.DEBUG:
                print(f"⚠️  Error getting LSL data: {e}")

        return None

    def _get_bluetooth_data(self, duration: float = 1.0) -> Optional[np.ndarray]:
        """
        Get data from Bluetooth connection (TODO: implementation).
        
        This requires implementation of Bluetooth characteristics handling.
        Muse uses proprietary protocol - LSL is easier to use.
        
        :param duration: Duration of data to retrieve in seconds
        :return: NumPy array of shape [samples, channels] or None
        """

        return None

    def set_callback(self, callback: Callable) -> None:
        """
        Set callback function for new data.
        
        :param callback: Function to call when new data arrives
        """
        self.callback = callback

    def start_stream(self) -> None:
        """
        Start continuous data streaming (for advanced use cases).
        
        Can be implemented in a separate thread if needed.
        """
        # Can be implemented in separate thread
        pass

    def disconnect(self) -> None:
        """
        Disconnect from Muse device.
        
        Closes all streams and cleans up resources.
        """
        print("📡 Disconnecting...")

        if self.mode == 'lsl':
            if self.inlet:
                self.inlet.close_stream()
            if self.motion_inlet:
                self.motion_inlet.close_stream()
            self.inlet = None
            self.motion_inlet = None

        elif self.mode == 'bluetooth' and self.client and self.loop:
            self.loop.run_until_complete(self._async_disconnect_bluetooth())

        # Reset signal quality state
        self.overall_quality = 0
        self.signal_quality = []
        self.quality_warnings = []
        self.last_data = None
        self.last_timestamp = None
        self.first_timestamp_after_flush = None

        self.is_connected = False
        print("✅ Disconnected")

    async def _async_disconnect_bluetooth(self) -> None:
        """
        Asynchronous Bluetooth disconnection.
        
        Safely disconnects the BLE client.
        """
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    def _update_signal_quality(self, eeg_data: np.ndarray) -> None:
        """
        Update signal quality metrics.
        
        :param eeg_data: EEG data array to assess
        """
        try:
            if eeg_data is None or len(eeg_data) == 0:
                return
            
            # For sufficient data (>= 128 samples = ~0.5s at 256Hz) - use full assessment
            if len(eeg_data) >= 128:
                # Use last 256 samples (1 second) for better quality assessment
                data_to_check = eeg_data[-256:] if len(eeg_data) > 256 else eeg_data
                quality_result = self.quality_checker.assess_quality(data_to_check)
                self.signal_quality = quality_result['channel_quality']
                self.overall_quality = quality_result['overall_quality']
                self.quality_warnings = quality_result['warnings']
            elif len(eeg_data) >= 10:
                # For smaller samples (10-127 samples) - use quick check but still update
                # This ensures quality updates even during calibration with short durations
                self.overall_quality = quick_quality_check(eeg_data)
                # For small samples, set channel quality to overall quality (simple approximation)
                if len(self.signal_quality) == 0 and self.n_channels:
                    self.signal_quality = [self.overall_quality] * self.n_channels
                else:
                    # Update all channels with same value (approximation)
                    self.signal_quality = [self.overall_quality] * len(self.signal_quality)
            # For very small samples (< 10), don't update quality (not enough data)
        except Exception as e:
            if config.DEBUG:
                print(f"⚠️  Error checking quality: {e}")

    def get_signal_quality(self) -> List[int]:
        """
        Get signal quality for each channel (0-100).
        
        :return: List of quality scores for each channel
        """
        return self.signal_quality.copy()

    def get_overall_quality(self) -> int:
        """
        Get overall signal quality (0-100).
        
        :return: Overall quality score
        """
        return self.overall_quality
    
    def print_channel_quality_status(self) -> None:
        """
        Print detailed channel quality status for debugging.
        """
        if not self.signal_quality or len(self.signal_quality) == 0:
            print("   📊 Channel quality: Not available yet")
            return
        
        print(f"   📊 Channel quality (overall: {self.overall_quality}%):")
        for ch_idx, ch_quality in enumerate(self.signal_quality[:4]):
            ch_name = self.lsl_channel_names[ch_idx] if self.lsl_channel_names and ch_idx < len(self.lsl_channel_names) else f"Ch{ch_idx}"
            expected_name = ['TP9', 'AF7', 'AF8', 'TP10'][ch_idx] if ch_idx < 4 else f"Ch{ch_idx}"
            status_icon = "🟢" if ch_quality >= 60 else "🟡" if ch_quality >= 40 else "🔴"
            match_info = "✅" if ch_name == expected_name else "⚠️"
            print(f"      {status_icon} {ch_idx}: {ch_name} (expected: {expected_name}) {match_info} - Quality: {ch_quality}%")

    def get_quality_warnings(self) -> List[str]:
        """
        Get list of quality warnings.
        
        :return: List of warning messages
        """
        return self.quality_warnings.copy()

    def print_quality_status(self) -> None:
        """
        Display current signal quality status.
        
        Prints detailed quality report for the most recent data.
        """
        if self.last_data is not None and len(self.last_data) > 0:
            quality_result = self.quality_checker.assess_quality(self.last_data[-512:])  # Last 2s
            self.quality_checker.print_quality_report(quality_result)
        else:
            print("❌ No data available for quality assessment")


# ===== HELPER FUNCTIONS =====

def find_muse_devices() -> None:
    """
    Find available Muse devices.
    
    Scans for devices via LSL streams and Bluetooth.
    Displays all found devices with their properties.
    """
    print("🔍 Searching for Muse devices...")

    # Try via LSL
    if LSL_AVAILABLE:
        print("\n--- LSL Streams ---")
        try:
            if LSL_TYPE == "mne_lsl":
                if resolve_streams is None:
                    raise RuntimeError(ERROR_MNE_LSL_RESOLVE_STREAMS)
                streams = resolve_streams(timeout=3)
            else:
                if resolve_byprop is None:
                    raise RuntimeError(ERROR_PYLSL_RESOLVE_BYPROP)
                streams = resolve_byprop('type', 'EEG', timeout=3)

            if streams:
                for idx, stream in enumerate(streams):
                    # MNE-LSL: stream is StreamInfo with attributes
                    # pylsl: stream.info() returns StreamInfo with methods
                    if LSL_TYPE == "mne_lsl":
                        name = stream.name
                        n_ch = stream.n_channels  # n_channels in MNE-LSL
                        srate = stream.sfreq  # sfreq in MNE-LSL
                    else:
                        info = stream.info() if hasattr(stream, 'info') else stream
                        name = info.name()
                        n_ch = info.channel_count()
                        srate = info.nominal_srate()

                    print(f"{idx + 1}. {name} - {n_ch} channels @ {srate} Hz")
            else:
                print("No active LSL streams")
                print("💡 Run: OpenMuse stream --address <MAC>")
                print("   or: muselsl stream")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    # Try via Bluetooth
    if BLUETOOTH_AVAILABLE:
        print("\n--- Bluetooth Devices ---")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            devices = loop.run_until_complete(_scan_bluetooth())

            if devices:
                for device in devices:
                    print(f"  {device.name}: {device.address}")
            else:
                print("No Bluetooth devices found")
        except Exception as e:
            print(f"Error: {e}")


async def _scan_bluetooth() -> List[Any]:
    """
    Scan for Bluetooth devices.
    
    Discovers nearby Bluetooth devices and filters for Muse devices.
    
    :return: List of Muse devices found
    """
    devices = await BleakScanner.discover(timeout=5.0)
    # Filter only Muse devices
    muse_devices = [d for d in devices if d.name and 'Muse' in d.name]
    return muse_devices


if __name__ == "__main__":
    # Test connection
    print("=== Test MuseConnector ===\n")

    connector = MuseConnector(mode=config.CONNECTION_MODE)

    if connector.connect():
        print("\n✅ Connection successful!")
        print("📊 Testing data retrieval...")

        for i in range(5):
            data = connector.get_eeg_data(duration=0.5)
            if data is not None:
                print(f"  Attempt {i + 1}: {data.shape} - range: [{data.min():.2f}, {data.max():.2f}]")
                quality = connector.get_signal_quality()
                print(f"  Signal quality: {quality}")
            else:
                print(f"  Attempt {i + 1}: No data")
            time.sleep(0.5)

        connector.disconnect()
    else:
        print("\n❌ Failed to connect")
        print("\n💡 Make sure that:")
        print("  1. Muse S is powered on and charged")
        print("  2. Bluetooth is active")
        print("  3. Muse is not connected to another app")
        if config.CONNECTION_MODE == 'lsl':
            print("  4. Stream is running: muselsl stream")
