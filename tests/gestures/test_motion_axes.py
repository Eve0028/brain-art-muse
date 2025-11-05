"""
Motion Axes Test - Accelerometer and Gyroscope Axis Identification.

This script helps identify which axis corresponds to which movement.
"""

from typing import Any
import time

import numpy as np

from src.muse_connector import MuseConnector


def main() -> None:
    """
    Main function for motion axes testing.
    
    Tests different head movements to identify which accelerometer
    and gyroscope axes correspond to specific motions.
    """
    print("=" * 70)
    print("🧭 ACCELEROMETER AND GYROSCOPE AXES TEST - Muse S")
    print("=" * 70)
    print()
    print("This script helps identify which axis corresponds to which movement.")
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
        return

    print("✅ Connected!\n")

    # Collect reference data (head still)
    print("📍 CALIBRATION - Sit still for 2 seconds...")
    print("   Keep your head straight, look forward.\n")
    time.sleep(1)

    baseline_acc = np.zeros(3)
    baseline_gyro = np.zeros(3)
    samples = 0

    start = time.time()
    while time.time() - start < 2:
        motion_data = connector.get_motion_data(duration=0.1)
        if motion_data:
            acc_data, gyro_data = motion_data
            baseline_acc += np.sum(acc_data, axis=0)
            baseline_gyro += np.sum(gyro_data, axis=0)
            samples += len(acc_data)
        time.sleep(0.05)

    baseline_acc /= samples
    baseline_gyro /= samples

    print(f"✅ Baseline ACC: [{baseline_acc[0]:.2f}, {baseline_acc[1]:.2f}, {baseline_acc[2]:.2f}] g")
    print(f"✅ Baseline GYRO: [{baseline_gyro[0]:.1f}, {baseline_gyro[1]:.1f}, {baseline_gyro[2]:.1f}] °/s")
    print()

    # Tests for each movement
    tests = [
        {
            'name': 'NOD (bow forward - look down)',
            'instruction': 'Slowly lower your head FORWARD (look down), then lift to neutral position.',
            'expected_axis': 'ACC Y or ACC Z',
        },
        {
            'name': 'HEAD TILT (ear to shoulder)',
            'instruction': 'Tilt your head to the LEFT (ear to left shoulder), then return to center.',
            'expected_axis': 'ACC X',
        },
        {
            'name': 'SHAKE (NO - left-right)',
            'instruction': 'QUICKLY shake your head SIDEWAYS (left-right-left).',
            'expected_axis': 'GYRO Z',
        },
    ]

    for test_idx, test in enumerate(tests):
        print("=" * 70)
        print(f"TEST {test_idx + 1}/3: {test['name']}")
        print("=" * 70)
        print()
        print(f"📝 Instruction: {test['instruction']}")
        print(f"🎯 Expected axis: {test['expected_axis']}")
        print()
        input("Press ENTER when ready...")
        print()
        print("⏱️  You have 3 seconds to perform the movement!")
        print("   Starting in: 3...")
        time.sleep(1)
        print("   2...")
        time.sleep(1)
        print("   1...")
        time.sleep(1)
        print("   START! Perform the movement...\n")

        # Collect data for 3 seconds
        # max_acc_diff = np.zeros(3)
        # max_gyro_diff = np.zeros(3)
        all_acc: list[Any] = []
        all_gyro: list[Any] = []

        start = time.time()
        while time.time() - start < 3:
            motion_data = connector.get_motion_data(duration=0.05)
            if motion_data:
                acc_data, gyro_data = motion_data
                all_acc.extend(acc_data)
                all_gyro.extend(gyro_data)
            time.sleep(0.02)

        print("⏹️  Stop!\n")

        # Analysis
        if len(all_acc) > 0:
            all_acc = np.array(all_acc)  # type: ignore[assignment]
            all_gyro = np.array(all_gyro)  # type: ignore[assignment]

            # Calculate range for each axis
            acc_ranges = np.max(all_acc, axis=0) - np.min(all_acc, axis=0)
            gyro_ranges = np.max(np.abs(all_gyro), axis=0)

            # Calculate mean change from baseline
            # acc_mean_diff = np.abs(np.mean(all_acc, axis=0) - baseline_acc)

            print("📊 RESULTS:")
            print()
            print("   ACCELEROMETER (Range - change span):")
            print(f"      ACC X: {acc_ranges[0]:.3f} g  {'<<< LARGEST' if acc_ranges[0] == max(acc_ranges) else ''}")
            print(f"      ACC Y: {acc_ranges[1]:.3f} g  {'<<< LARGEST' if acc_ranges[1] == max(acc_ranges) else ''}")
            print(f"      ACC Z: {acc_ranges[2]:.3f} g  {'<<< LARGEST' if acc_ranges[2] == max(acc_ranges) else ''}")
            print()
            print("   GYROSCOPE (Max angular velocity):")
            print(f"      GYRO X: {gyro_ranges[0]:.1f} °/s  {'<<< LARGEST' if gyro_ranges[0] == max(gyro_ranges) else ''}")
            print(f"      GYRO Y: {gyro_ranges[1]:.1f} °/s  {'<<< LARGEST' if gyro_ranges[1] == max(gyro_ranges) else ''}")
            print(f"      GYRO Z: {gyro_ranges[2]:.1f} °/s  {'<<< LARGEST' if gyro_ranges[2] == max(gyro_ranges) else ''}")
            print()

            # Determine dominant axis
            dominant_acc_axis = ['X', 'Y', 'Z'][np.argmax(acc_ranges)]
            dominant_gyro_axis = ['X', 'Y', 'Z'][np.argmax(gyro_ranges)]

            print(f"   ✅ Dominant ACC axis: {dominant_acc_axis} (change: {max(acc_ranges):.3f} g)")
            print(f"   ✅ Dominant GYRO axis: {dominant_gyro_axis} (max: {max(gyro_ranges):.1f} °/s)")
            print()

        print("=" * 70)
        print()
        time.sleep(1)

    print()
    print("🎉 Test completed!")
    print()
    print("📝 SUMMARY - Which axes correspond to which movements:")
    print("   Save this information to update the code!")
    print()

    connector.disconnect()


if __name__ == "__main__":
    main()
