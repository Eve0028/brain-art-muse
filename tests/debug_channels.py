"""
EEG Channel Debug Script - Comprehensive Stream Analysis.

This script analyzes LSL streams from OpenMuse and provides detailed
information about channels, including which channels contain actual data.
"""

import time
from typing import Optional, List, Tuple, Any

import numpy as np
from mne_lsl.lsl import resolve_streams, StreamInlet  # type: ignore


def print_header() -> None:
    """Print script header."""
    print("=" * 70)
    print("🔍 EEG CHANNEL DEBUG - Comprehensive Analysis")
    print("=" * 70)
    print()
    print("Make sure OpenMuse stream is running!")
    print()


def find_streams() -> List[Any]:
    """
    Find available LSL streams.
    
    :return: List of available stream information objects
    """
    print("Searching for LSL streams...")
    streams = resolve_streams(timeout=5)
    
    if len(streams) == 0:
        print("❌ No streams found!")
        print("Run: OpenMuse stream --address <ADDRESS> --preset p20")
        exit(1)
    
    print(f"✅ Found {len(streams)} stream(s)\n")
    return streams


def display_stream_info(stream_info: Any, stream_idx: int) -> None:
    """
    Display basic information about a stream.
    
    :param stream_info: Stream information object
    :param stream_idx: Stream index number
    """
    print(f"{'=' * 70}")
    print(f"Stream #{stream_idx + 1}")
    print(f"{'=' * 70}")
    
    print(f"Name: {stream_info.name}")
    print(f"Type: {stream_info.stype}")
    print(f"Channels: {stream_info.n_channels}")
    print(f"Frequency: {stream_info.sfreq} Hz")
    print(f"Format: {stream_info.dtype}")


def get_channel_names(stream_info: Any) -> Optional[List[str]]:
    """
    Get channel names from stream.
    
    :param stream_info: Stream information object
    :return: List of channel names or None if not available
    """
    ch_names = None
    try:
        if hasattr(stream_info, 'get_channel_names'):
            ch_names = stream_info.get_channel_names()
            if ch_names:
                print("\n📋 CHANNEL NAMES:")
                for idx, name in enumerate(ch_names):
                    print(f"   Channel {idx + 1}: {name}")
            else:
                print("\n📋 CHANNEL NAMES: (none - None returned)")
        else:
            print("\n📋 CHANNEL NAMES: (no get_channel_names method)")
    except Exception as e:
        print(f"\n📋 CHANNEL NAMES: Error - {e}")
    
    return ch_names


def collect_sample_data(stream_info: Any, ch_names: Optional[List[str]]) -> Optional[np.ndarray]:
    """
    Collect sample data from stream if it's EEG or motion.
    
    :param stream_info: Stream information object
    :param ch_names: Channel names if available
    :return: NumPy array of samples or None
    """
    if 'EEG' not in stream_info.name and 'ACCGYRO' not in stream_info.name:
        return None
    
    print("\n📊 Sample data:")
    try:
        inlet = StreamInlet(stream_info)
        time.sleep(1.0)  # Give time for buffering
        
        # Get data (mne-lsl API)
        samples, timestamps = inlet.pull_chunk(timeout=2.0)
        
        if samples is not None and len(samples) > 0:
            print(f"   Collected {len(samples)} samples")
            print(f"   Shape: {len(samples)}x{len(samples[0])} (samples x channels)")
            print("   Example sample:")
            for ch_idx in range(min(8, len(samples[0]))):
                if ch_names and ch_idx < len(ch_names):
                    ch_name = ch_names[ch_idx]
                else:
                    ch_name = f"Ch{ch_idx + 1}"
                print(f"      {ch_name}: {samples[0][ch_idx]:.6f}")
            
            return np.array(samples)
        else:
            print("   (no data - try again)")
    except Exception as e:
        print(f"   Error collecting data: {e}")
        import traceback  # pylint: disable=import-outside-toplevel
        traceback.print_exc()
    
    return None


def analyze_channel_activity(data: np.ndarray) -> Tuple[List[int], List[int]]:
    """
    Analyze which channels are active (contain real data).
    
    :param data: EEG data array
    :return: Tuple of (active_channels, inactive_channels) as channel indices (1-based)
    """
    n_channels = data.shape[1]
    active_channels = []
    inactive_channels = []
    
    print("\n" + "=" * 70)
    print("📊 DETAILED CHANNEL ANALYSIS:")
    print("=" * 70)
    print()
    
    for ch_idx in range(n_channels):
        ch_data = data[:, ch_idx]
        
        # Statistics
        mean = np.mean(ch_data)
        std = np.std(ch_data)
        min_val = np.min(ch_data)
        max_val = np.max(ch_data)
        range_val = max_val - min_val
        
        # Check if channel has data (threshold: std > 0.1 or range > 1)
        has_data = std > 0.1 or range_val > 1.0
        
        status = "✅ ACTIVE" if has_data else "❌ INACTIVE (padding?)"
        
        print(f"Channel {ch_idx + 1}:")
        print(f"  Status:  {status}")
        print(f"  Mean:    {mean:.2f}")
        print(f"  Std Dev: {std:.2f}")
        print(f"  Range:   [{min_val:.2f}, {max_val:.2f}] (span: {range_val:.2f})")
        
        # Show sample values
        sample_values = ch_data[:5]
        print(f"  Sample:  {[f'{v:.2f}' for v in sample_values]}")
        print()
        
        if has_data:
            active_channels.append(ch_idx + 1)
        else:
            inactive_channels.append(ch_idx + 1)
    
    return active_channels, inactive_channels


def print_summary(active_channels: List[int], total_channels: int) -> None:
    """
    Print summary of channel analysis.
    
    :param active_channels: List of active channel indices
    :param total_channels: Total number of channels
    """
    print("=" * 70)
    print("📈 SUMMARY:")
    print("=" * 70)
    print()
    
    print(f"Active channels: {active_channels}")
    print(f"Active count: {len(active_channels)} / {total_channels}")
    print()
    
    if len(active_channels) < total_channels:
        inactive = [i for i in range(1, total_channels + 1) if i not in active_channels]
        print(f"⚠️  Inactive channels: {inactive}")
        print("   Probably padding/unused in LSL structure")
    else:
        print("✅ All channels active!")
    
    print()
    print("=" * 70)
    print("💡 CONCLUSION:")
    print("=" * 70)
    print()
    
    if len(active_channels) == 4:
        print("Preset p20 sends 4 active EEG channels (as per documentation)")
        print("Remaining channels are probably padding in LSL structure")
    elif len(active_channels) == 8:
        print("Preset p20 actually sends 8 active EEG channels!")
        print("GitHub documentation may be outdated")
    else:
        print(f"Preset p20 sends {len(active_channels)} active channels")
    
    print()
    print("💡 Update docs/OPENMUSE_PRESETS.md with the real channel names")
    print("   if they were found!")
    print()


def main() -> None:
    """
    Main function for channel debugging.
    
    Performs comprehensive analysis of LSL streams and channels.
    """
    print_header()
    
    # Find streams
    streams = find_streams()
    
    # Analyze each stream
    for i, stream_info in enumerate(streams):
        display_stream_info(stream_info, i)
        
        # Get channel names
        ch_names = get_channel_names(stream_info)
        
        # Collect and analyze sample data
        data = collect_sample_data(stream_info, ch_names)
        
        # If EEG stream and has data, perform detailed analysis
        if data is not None and 'EEG' in stream_info.name:
            active_channels, inactive_channels = analyze_channel_activity(data)
            print_summary(active_channels, data.shape[1])
        
        print()
    
    print("=" * 70)
    print("✅ Debug completed")
    print("=" * 70)


if __name__ == "__main__":
    main()
