"""
Muse Device Finder Tool.

Helps find Muse device MAC address and check connection availability.
Supports both LSL (Lab Streaming Layer) and Bluetooth Low Energy methods.
"""

from typing import List, Any


def print_header() -> None:
    """
    Print script header.
    
    Displays the welcome message for the Muse device finder.
    """
    print("=" * 60)
    print("🔍 MUSE DEVICE FINDER")
    print("=" * 60)
    print()


def find_lsl_streams() -> None:
    """
    Find Muse devices via LSL (Lab Streaming Layer) - RECOMMENDED method.
    
    Searches for active LSL streams from Muse devices and displays
    connection information.
    """
    print("📡 Method 1: LSL (Lab Streaming Layer) - RECOMMENDED")
    print("-" * 60)

    try:
        from pylsl import resolve_byprop

        print("✅ pylsl installed")
        print("\n🔍 Searching for LSL streams (timeout 5s)...")

        streams = resolve_byprop('type', 'EEG', timeout=5)

        if streams:
            print(f"\n✅ Found {len(streams)} stream(s):")
            for i, stream in enumerate(streams):
                info = stream.info()
                print(f"\n  {i + 1}. EEG Stream:")
                print(f"     Name: {info.name()}")
                print(f"     Channels: {info.channel_count()}")
                print(f"     Frequency: {info.nominal_srate()} Hz")
                print(f"     Type: {info.type()}")

            print("\n💡 To use this stream:")
            print("   1. Make sure muselsl stream is running")
            print("   2. In config.py set CONNECTION_MODE = 'lsl'")
            print("   3. Run: python main.py")
        else:
            print("\n⚠️  No active LSL streams found")
            print("\n💡 To create a Muse stream:")
            print("   1. Make sure Muse is powered on")
            print("   2. In a separate terminal run:")
            print("      muselsl list")
            print("      muselsl stream --name \"Muse-XXXX\"")
            print("   3. Run this script again")

    except ImportError:
        print("❌ pylsl is not installed")
        print("   Installation: pip install pylsl muselsl")

    except Exception as e:
        print(f"❌ Error: {e}")

    print()
    print()


def scan_bluetooth_devices() -> None:
    """
    Scan for Muse devices via Bluetooth Low Energy (BLE).
    
    Searches for nearby BLE devices and filters for Muse devices.
    Displays MAC addresses and connection instructions.
    """
    print("📶 Method 2: Bluetooth Low Energy (BLE)")
    print("-" * 60)

    try:
        import asyncio
        from bleak import BleakScanner

        print("✅ bleak installed")
        print("\n🔍 Scanning Bluetooth devices (5s)...")
        print("   (Make sure Muse is powered on and in range)")

        async def scan_devices() -> List[Any]:
            """
            Async function to scan for BLE devices.
            
            :return: List of discovered BLE devices
            """
            devices = await BleakScanner.discover(timeout=5.0)
            return devices

        # Run scan
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        devices = loop.run_until_complete(scan_devices())

        if devices:
            # Filter Muse devices
            muse_devices = [d for d in devices if d.name and 'Muse' in d.name]

            if muse_devices:
                print(f"\n✅ Found {len(muse_devices)} Muse device(s):")
                for i, device in enumerate(muse_devices):
                    print(f"\n  {i + 1}. {device.name}")
                    print(f"     MAC Address: {device.address}")
                    print(f"     RSSI: {device.rssi} dBm")

                print("\n💡 To use Bluetooth connection:")
                print("   1. In config.py set:")
                print("      CONNECTION_MODE = 'bluetooth'")
                print(f"      MUSE_ADDRESS = '{muse_devices[0].address}'")
                print("   2. Run: python main.py")
                print("\n⚠️  WARNING: Direct BLE connection is experimental")
                print("   We recommend using LSL (Method 1)")
            else:
                print("\n⚠️  No Muse devices found")
                print(f"   Found {len(devices)} other BLE device(s)")

                # Show a few examples for debugging
                if len(devices) > 0:
                    print("\n   Example devices:")
                    for device in devices[:5]:
                        if device.name:
                            print(f"   - {device.name}: {device.address}")
        else:
            print("\n⚠️  No Bluetooth devices found")
            print("   Check if:")
            print("   • Bluetooth is enabled")
            print("   • Muse is powered on and charged")
            print("   • Muse is in range (~10m)")

    except ImportError:
        print("❌ bleak is not installed")
        print("   Installation: pip install bleak")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print()


def print_summary() -> None:
    """
    Print summary and recommendations.
    
    Displays recommended connection method and step-by-step instructions.
    """
    print("=" * 60)
    print("📝 SUMMARY")
    print("=" * 60)
    print()
    print("✅ RECOMMENDED METHOD: LSL (Lab Streaming Layer)")
    print()
    print("   Step by step:")
    print("   1. Install: pip install .")
    print("   2. Power on Muse S and ensure it's in range")
    print("   3. Open a separate terminal and run:")
    print("      > muselsl list")
    print("      > muselsl stream")
    print("   4. In this terminal run:")
    print("      > python main.py")
    print()
    print("💡 More information: README.md")
    print()


def find_muse_devices() -> None:
    """
    Find Muse devices via LSL and Bluetooth.
    
    Executes LSL and Bluetooth scanning methods and displays results.
    This is the main entry point for programmatic use.
    """
    print_header()
    find_lsl_streams()
    scan_bluetooth_devices()
    print_summary()


def main() -> None:
    """
    Main function to run the Muse device finder.
    
    Executes LSL and Bluetooth scanning methods and displays results.
    """
    find_muse_devices()
    input("\nPress ENTER to exit...")


if __name__ == "__main__":
    main()
