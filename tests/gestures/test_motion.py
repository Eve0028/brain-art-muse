"""
Motion Features Test - Gesture Detection Testing.

Use this script to test gestures without running the full application.
"""

import time

from src.muse_connector import MuseConnector
from src.motion_processor import MotionProcessor


def main() -> None:
    """
    Main function for motion features testing.
    
    Tests gesture detection (nod and shake) without running
    the full Brain Art application.
    """
    print("=" * 60)
    print("🎮 MOTION FEATURES TEST")
    print("=" * 60)
    print()
    print("This script allows you to test gesture detection")
    print("without running the full Brain Art application.")
    print()
    print("📝 Gestures to test:")
    print("  1. NOD (bow head forward - look down)")
    print("     → Changes visualization mode")
    print("  2. SHAKE (fast left-right-left)")
    print("     → Clears screen")
    print()
    print("💡 Tips:")
    print("  • Nod: Clear bow forward, like saying 'YES'")
    print("  • Shake: Fast side movement, like saying 'NO'")
    print("  • Cooldown between gestures: 1.5s")
    print()
    print("Press Ctrl+C to exit.")
    print()

    # Connect to Muse
    print("📡 Connecting to Muse S (via LSL)...")
    connector = MuseConnector(mode='lsl', enable_motion=True)

    if not connector.connect():
        print("\n❌ Failed to connect!")
        print("💡 Make sure OpenMuse stream is running:")
        print("   OpenMuse stream --address <MAC> --preset p20")
        return

    if not connector.motion_inlet:
        print("\n❌ No ACC/GYRO stream!")
        print("💡 Make sure you're using a preset with ACC/GYRO (p20, p21, p1041)")
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

    print("✅ Ready for testing!\n")
    print("=" * 60)
    print("🎯 Perform gestures, the system will detect them:")
    print("=" * 60)
    print()

    last_print = time.time()

    try:
        while True:
            # Get motion data
            motion_data = connector.get_motion_data(duration=0.05)
            if motion_data:
                acc_data, gyro_data = motion_data
                for acc, gyro in zip(acc_data, gyro_data):
                    motion_processor.add_data(acc, gyro)

            # Check gestures
            if motion_processor.detect_nod():
                print("\n" + "=" * 60)
                print("✅ 👍 NOD DETECTED!")
                print("=" * 60 + "\n")

            if motion_processor.detect_shake():
                print("\n" + "=" * 60)
                print("✅ 👎 SHAKE DETECTED!")
                print("=" * 60 + "\n")

            # Display metrics every 0.5s
            current_time = time.time()
            if current_time - last_print >= 0.5:
                metrics = motion_processor.get_metrics()

                # Format output
                acc = metrics['acc']
                gyro = metrics['gyro']
                intensity = metrics['motion_intensity']
                tilt_lr = metrics['tilt_left_right']
                tilt_fb = metrics['tilt_forward_backward']

                print(f"\r"
                      f"ACC: [{acc[0]:+.2f}, {acc[1]:+.2f}, {acc[2]:+.2f}] g | "
                      f"GYRO: [{gyro[0]:+4.0f}, {gyro[1]:+4.0f}, {gyro[2]:+4.0f}] °/s | "
                      f"Intensity: {intensity:.2f} | "
                      f"Tilt L/R: {tilt_lr:+.2f}, F/B: {tilt_fb:+.2f}  ",
                      end='', flush=True)

                last_print = current_time

            time.sleep(0.02)  # 50 Hz

    except KeyboardInterrupt:
        print("\n\n⏹️  Test stopped!")

    finally:
        connector.disconnect()
        print("👋 Disconnected.")


if __name__ == "__main__":
    main()
