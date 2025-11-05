"""
Motion Tilt Test - Head Tilt Detection Testing.

This script displays tilt values in real-time.
"""

import time

from src.muse_connector import MuseConnector
from src.motion_processor import MotionProcessor


def main() -> None:
    """
    Main function for head tilt testing.
    
    Displays real-time tilt values for left/right and forward/backward movements.
    """
    print("=" * 70)
    print("🧭 HEAD TILT TEST")
    print("=" * 70)
    print()
    print("This script shows tilt values in real-time.")
    print()
    print("📝 Perform the following movements:")
    print("  1. Tilt head SIDEWAYS (ear to shoulder)")
    print("     → You should see changes in 'Tilt L/R'")
    print("  2. Tilt head FORWARD/BACKWARD")
    print("     → You should see changes in 'Tilt F/B'")
    print()
    print("💡 Values:")
    print("  • Tilt L/R: -1.0 (left) ... 0.0 (center) ... +1.0 (right)")
    print("  • Tilt F/B: -1.0 (forward) ... 0.0 (center) ... +1.0 (backward)")
    print()
    print("Press Ctrl+C to exit.")
    print()

    # Connect to Muse
    print("📡 Connecting to Muse S (via LSL)...")
    connector = MuseConnector(mode='lsl', enable_motion=True)

    if not connector.connect():
        print("\n❌ Failed to connect!")
        return

    if not connector.motion_inlet:
        print("\n❌ No ACC/GYRO stream!")
        return

    print("✅ Connected!\n")

    # Create motion processor
    motion_processor = MotionProcessor()

    print("🔍 Collecting data...")
    print("   Wait 2 seconds for buffers to fill...\n")

    # Collect initial data
    start_time = time.time()
    while time.time() - start_time < 2:
        motion_data = connector.get_motion_data(duration=0.1)
        if motion_data:
            acc_data, gyro_data = motion_data
            for acc, gyro in zip(acc_data, gyro_data):
                motion_processor.add_data(acc, gyro)
        time.sleep(0.05)

    print("✅ Ready!\n")
    print("=" * 70)
    print("🎯 PERFORM MOVEMENTS - Observe values:")
    print("=" * 70)
    print()

    last_print = time.time()
    baseline_printed = False

    try:
        while True:
            # Get motion data
            motion_data = connector.get_motion_data(duration=0.05)
            if motion_data:
                acc_data, gyro_data = motion_data
                for acc, gyro in zip(acc_data, gyro_data):
                    motion_processor.add_data(acc, gyro)

            # Display metrics every 0.2s
            current_time = time.time()
            if current_time - last_print >= 0.2:
                metrics = motion_processor.get_metrics()

                tilt_lr = metrics['tilt_left_right']
                tilt_fb = metrics['tilt_forward_backward']
                acc = metrics['acc']

                # Baseline at first display
                if not baseline_printed:
                    print("📍 BASELINE (head straight):")
                    print(f"   ACC: [{acc[0]:+.2f}, {acc[1]:+.2f}, {acc[2]:+.2f}] g")
                    print(f"   Tilt L/R: {tilt_lr:+.2f}, F/B: {tilt_fb:+.2f}")
                    print()
                    print("Now tilt your head...\n")
                    baseline_printed = True

                # Visual indicators
                lr_bar = create_bar(tilt_lr, -1, 1, 20, 'L', 'R')
                fb_bar = create_bar(tilt_fb, -1, 1, 20, 'F', 'B')

                # Status
                status = []
                if abs(tilt_lr) > 0.3:
                    status.append(f"{'LEFT' if tilt_lr < 0 else 'RIGHT'} ←→")
                if abs(tilt_fb) > 0.3:
                    status.append(f"{'FORWARD' if tilt_fb < 0 else 'BACK'} ↕")

                status_str = " ".join(status) if status else "---"

                print(f"\r"
                      f"L/R: [{lr_bar}] {tilt_lr:+.2f} | "
                      f"F/B: [{fb_bar}] {tilt_fb:+.2f} | "
                      f"ACC: [{acc[0]:+.2f},{acc[1]:+.2f},{acc[2]:+.2f}] | "
                      f"{status_str:20s}  ",
                      end='', flush=True)

                last_print = current_time

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n\n⏹️  Test stopped!")

    finally:
        connector.disconnect()
        print("👋 Disconnected.")


def create_bar(value: float, min_val: float, max_val: float, width: int,
               left_label: str, right_label: str) -> str:
    """
    Create ASCII bar for value visualization.
    
    :param value: Current value to display
    :param min_val: Minimum value of range
    :param max_val: Maximum value of range
    :param width: Width of bar in characters
    :param left_label: Label for left end
    :param right_label: Label for right end
    :return: ASCII bar string
    """
    # Normalize to 0-1
    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0, min(1, normalized))

    # Marker position
    pos = int(normalized * (width - 1))

    # Create bar
    bar_chars = ['-'] * width
    bar_chars[pos] = '█'

    return f"{left_label}|{''.join(bar_chars)}|{right_label}"


if __name__ == "__main__":
    main()
