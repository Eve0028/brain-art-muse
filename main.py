"""
Brain Art - Main Application.

Integrates Muse S, EEG processing and visualization.
"""

import time
import sys
from typing import Optional, Any
import config

from src.muse_connector import MuseConnector
from src.eeg_processor import EEGProcessor
from src.brain_visualizer import BrainVisualizer
from src.eeg_visualizer import create_eeg_visualizer
from src.motion_processor import MotionProcessor
from src.performance_optimizer import PerformanceOptimizer, EEGVisualizerProcess


class BrainArtApp:
    """
    Main Brain Art application.

    Manages all components and main loop.
    """

    def __init__(self) -> None:
        """
        Initialize Brain Art application.
        """
        print("=" * 50)
        print("BRAIN ART - Muse S Athena")
        print("=" * 50)
        print()

        self.connector: Optional[MuseConnector] = None
        self.processor: Optional[EEGProcessor] = None
        self.motion_processor: Optional[MotionProcessor] = None
        self.visualizer: Optional[BrainVisualizer] = None
        self.eeg_visualizer: Optional[Any] = None  # Can be EEGVisualizer or EEGVisualizerProcess
        self.optimizer: Optional[PerformanceOptimizer] = None
        self.running: bool = False
        self.show_eeg_monitor: bool = config.SHOW_EEG_MONITOR if hasattr(config, 'SHOW_EEG_MONITOR') else False
        self.motion_enabled: bool = config.ENABLE_MOTION if hasattr(config, 'ENABLE_MOTION') else False
        self.use_threading: bool = getattr(config, 'USE_THREADING', True)
        self.use_separate_process: bool = getattr(config, 'EEG_VISUALIZER_SEPARATE_PROCESS', True)

    def setup(self) -> bool:
        """
        Initialize all components.

        :return: True if setup successful
        """
        print("⚙️  Initializing...\n")

        # 1. Connect to Muse
        print("📡 Connecting to Muse S...")
        self.connector = MuseConnector(mode=config.CONNECTION_MODE, enable_motion=self.motion_enabled)

        if not self.connector.connect():
            print("\n❌ Failed to connect to Muse!")
            print("\n💡 Check:")
            print("  1. Muse is on and charged")
            print("  2. Bluetooth is active")
            print("  3. Muse is not connected to another app")

            if config.CONNECTION_MODE == 'lsl':
                print("  4. In separate terminal run: muselsl stream")
                print("     (You can also change CONNECTION_MODE to 'bluetooth' in config.py)")

            return False

        print("✅ Connected to Muse!\n")

        # 2. EEG Processor
        print("🔧 Initializing EEG processor...")
        self.processor = EEGProcessor()
        print("✅ Processor ready!\n")

        # 2b. Motion Processor (optional)
        if self.motion_enabled and self.connector.motion_inlet:
            print("🎮 Initializing motion processor...")
            self.motion_processor = MotionProcessor()
            print("✅ Motion processor ready!")
            print("   📝 Gestures: Nod (change mode), Shake (clear)")
            print("   📝 Head tilt affects visual effects")
            print("   📝 Key 'M' - toggle motion features\n")
        elif self.motion_enabled:
            print("⚠️  Motion enabled in config, but no ACC/GYRO stream")
            print("   (OpenMuse stream must be run with preset containing ACC/GYRO)\n")
            self.motion_enabled = False

        # 3. Performance Optimizer (multithreading, GPU)
        if self.use_threading:
            print("⚡ Initializing performance optimizer...")
            self.optimizer = PerformanceOptimizer(processor=self.processor)
            print("✅ Optimizer ready!\n")

        # 4. Brain Art Visualization
        print("🎨 Initializing Brain Art visualization...")
        self.visualizer = BrainVisualizer()

        # Set callback for quality check
        self.visualizer.quality_check_callback = self.show_quality_report

        print("✅ Brain Art visualization ready!\n")

        # 5. EEG Monitor (optional)
        if self.show_eeg_monitor or input("Open EEG monitor window? (y/n): ").lower() == 'y':
            print("📊 Initializing EEG monitor...")
            try:
                if self.use_separate_process:
                    # NEW: Separate process for EEG visualizer (big FPS boost!)
                    print("   (starting in separate process for better performance)")
                    self.eeg_visualizer = EEGVisualizerProcess(
                        use_advanced=True,
                        buffer_duration=5.0
                    )
                    self.eeg_visualizer.start()
                    time.sleep(0.5)  # Give time to start
                    print("✅ EEG monitor ready (separate process)!\n")
                else:
                    # OLD: In same process (may lower FPS)
                    self.eeg_visualizer = create_eeg_visualizer(
                        use_advanced=True,
                        buffer_duration=5.0
                    )
                    self.eeg_visualizer.setup_window()
                    print("✅ EEG monitor ready!\n")
            except Exception as e:
                print(f"⚠️  Failed to start EEG monitor: {e}")
                print("   Continuing without monitor...\n")
                self.eeg_visualizer = None

        return True

    def calibrate(self) -> None:
        """
        System calibration.
        """
        if self.connector is None or self.processor is None:
            print("❌ Cannot calibrate: required components not initialized")
            return

        print("=" * 50)
        print("🎯 CALIBRATION")
        print("=" * 50)
        print()
        calibration_duration = config.CALIBRATION_TIME
        print(f"For the next {calibration_duration} seconds:")
        print("  • Sit comfortably")
        print("  • Close your eyes")
        print("  • Breathe calmly")
        print("  • Don't think about anything specific")
        print()

        # Wait for readiness
        input("Press ENTER when ready...")
        print()

        # Flush any stale data before calibration
        if self.connector:
            print("🧹 Preparing fresh data stream...")
            self.connector.flush_buffer()
            time.sleep(0.3)  # Wait for fresh data to start flowing

        # Collect data for first seconds
        print("📊 Collecting baseline data...")
        start_time = time.time()

        # Enable calibration display on screen
        if self.visualizer:
            self.visualizer.set_calibration_status(True, calibration_duration)

        while time.time() - start_time < calibration_duration:
            # Get data
            data = self.connector.get_eeg_data(duration=0.5)
            if data is not None:
                self.processor.add_data(data)

            # Show progress and signal quality
            elapsed = time.time() - start_time
            remaining = calibration_duration - elapsed
            overall_quality = self.connector.get_overall_quality()
            quality_bar = "█" * (overall_quality // 10) + "░" * (10 - overall_quality // 10)
            print(f"\r⏱️  Remaining: {remaining:.1f}s | Quality: [{quality_bar}] {overall_quality}%  ", end='')

            # Update calibration display on screen
            if self.visualizer:
                self.visualizer.set_calibration_status(True, remaining)
                # Render frame to show calibration message
                self.visualizer.run_frame()

            time.sleep(0.1)

        # Disable calibration display
        if self.visualizer:
            self.visualizer.set_calibration_status(False, 0.0)

        print("\n")

        # Compute baseline
        print("🧮 Computing baseline values...")
        powers = self.processor.compute_band_powers()

        if powers and any(powers.values()):
            self.processor.baseline = powers.copy()
            self.processor.is_calibrated = True

            print("✅ Calibration complete!")
            print("\nBaseline values:")
            for band, power in powers.items():
                print(f"  {band:8s}: {power:8.2f}")
            print()

            # Show signal quality report
            overall_quality = self.connector.get_overall_quality()
            
            # Show per-channel quality status
            if hasattr(self.connector, 'print_channel_quality_status'):
                self.connector.print_channel_quality_status()
            
            if overall_quality < 60:
                print("⚠️  WARNING: Signal quality below 60%")
                print("💡 Recommendations:")
                warnings = self.connector.get_quality_warnings()
                if warnings:
                    for warning in warnings[:3]:  # Show 3 most important
                        print(f"   {warning}")
                else:
                    print("   - Moisten sensors")
                    print("   - Check if headband fits properly")
                    print("   - Move hair away from sensors")
                print()
        else:
            print("⚠️  Not enough data for calibration")
            print("   Using default values...")
            self.processor.is_calibrated = True
            self.processor.baseline = {
                'delta': 100, 'theta': 50, 'alpha': 30,
                'beta': 20, 'gamma': 10
            }

        print()
        input("Calibration ready! Press ENTER to start...")
        print()

    def show_quality_report(self) -> None:
        """
        Display detailed signal quality report.
        """
        if self.connector is None:
            print("❌ Cannot show quality report: connector not initialized")
            return

        print("\n" + "=" * 60)
        print("🔍 CHECKING SIGNAL QUALITY...")
        print("=" * 60)
        self.connector.print_quality_status()
        print("Press any key to continue...")

    def run(self) -> None:
        """
        Main application loop.
        """
        if self.connector is None or self.processor is None or self.visualizer is None:
            print("❌ Cannot run: required components not initialized")
            return

        print("=" * 50)
        print("🚀 START!")
        print("=" * 50)
        print()
        print("🎨 Starting visualization...")
        print("   Experiment with:")
        print("   • Closing/opening eyes")
        print("   • Concentration (e.g. counting)")
        print("   • Relaxation (deep breathing)")
        print()
        print("Keys:")
        print("  SPACE - clear screen")
        print("  1 - Relaxation mode (Alpha)")
        print("  2 - Attention mode (Beta)")
        print("  3 - Mixed mode")
        print("  S - save screenshot")
        print("  Q - check signal quality")
        if self.motion_enabled and self.motion_processor:
            print("  M - toggle motion features (on/off)")
        if self.eeg_visualizer:
            print("  (EEG Monitor in separate window)")
        print("  ESC - exit")
        print()

        self.running = True
        last_update = time.time()
        last_motion_check = time.time()
        update_interval = config.UPDATE_INTERVAL / 1000.0  # ms -> s
        motion_check_interval = 0.1  # Check motion every 100ms (faster than EEG)

        try:
            while self.running:
                current_time = time.time()

                # Get motion data (more often than EEG, to not block FPS)
                if self.motion_enabled and self.motion_processor and current_time - last_motion_check >= motion_check_interval:
                    motion_data = self.connector.get_motion_data(duration=0.05)
                    if motion_data:
                        acc_data, gyro_data = motion_data
                        # Add all samples to processor
                        for acc_sample, gyro_sample in zip(acc_data, gyro_data):
                            self.motion_processor.add_data(acc_sample, gyro_sample)

                        # Debug motion (if enabled)
                        if config.DEBUG_MOTION if hasattr(config, 'DEBUG_MOTION') else False:
                            metrics = self.motion_processor.get_metrics()
                            print(f"\r🎮 Motion - Acc: [{metrics['acc'][0]:.2f}, {metrics['acc'][1]:.2f}, {metrics['acc'][2]:.2f}] | "
                                  f"Gyro: [{metrics['gyro'][0]:.1f}, {metrics['gyro'][1]:.1f}, {metrics['gyro'][2]:.1f}] | "
                                  f"Intensity: {metrics['motion_intensity']:.2f}  ", end='')

                        # Check gestures (only if enabled)
                        if config.MOTION_GESTURE_CONTROL if hasattr(config, 'MOTION_GESTURE_CONTROL') else True:
                            if self.motion_processor.detect_nod():
                                print("\n👍 Nod detected - changing mode!")
                                self.visualizer.cycle_mode()
                            elif self.motion_processor.detect_shake():
                                print("\n👎 Shake detected - clearing screen!")
                                self.visualizer.clear_screen()

                    last_motion_check = current_time

                # Get EEG data (every UPDATE_INTERVAL)
                if current_time - last_update >= update_interval:
                    data = self.connector.get_eeg_data(duration=0.2) if self.connector else None

                    if data is not None and len(data) > 0:
                        # === Multithreaded processing ===
                        if self.optimizer:
                            # Send data for processing in separate thread
                            self.optimizer.process_eeg_async(data)

                            # Try to get processed results (non-blocking)
                            results = self.optimizer.get_eeg_results()

                            if results:
                                band_powers = results['band_powers']
                                band_powers_per_channel = results['band_powers_per_channel']
                                attention = results['attention']
                                relaxation = results['relaxation']
                            else:
                                # No ready results - use previous values
                                attention = self.processor.current_attention
                                relaxation = self.processor.current_relaxation
                                band_powers = self.processor.current_bands
                                band_powers_per_channel = None
                        else:
                            # === OLD: Synchronous processing ===
                            self.processor.add_data(data)
                            band_powers = self.processor.compute_band_powers()
                            band_powers_per_channel = self.processor.compute_band_powers_per_channel()
                            attention = self.processor.compute_attention()
                            relaxation = self.processor.compute_relaxation()

                        # Get motion metrics (if enabled)
                        motion_metrics = None
                        if self.motion_enabled and self.motion_processor:
                            motion_metrics = self.motion_processor.get_metrics()

                        # Update Brain Art visualization (with motion metrics)
                        self.visualizer.set_metrics(attention, relaxation, motion_metrics)

                        # Update EEG monitor (if active)
                        if self.eeg_visualizer:
                            if isinstance(self.eeg_visualizer, EEGVisualizerProcess):
                                # Send to separate process (non-blocking!)
                                if self.eeg_visualizer.is_running():
                                    self.eeg_visualizer.send_data(data, band_powers, band_powers_per_channel)
                            elif self.eeg_visualizer.is_running:
                                # Update in same process (old way)
                                self.eeg_visualizer.update_data(data, band_powers, band_powers_per_channel)

                        # Debug info with better quality display
                        if config.SHOW_SIGNAL_QUALITY and int(current_time) % 2 == 0 and self.connector:
                            overall_quality = self.connector.get_overall_quality()
                            if overall_quality >= 60:
                                quality_icon = "🟢"
                            elif overall_quality >= 40:
                                quality_icon = "🟡"
                            else:
                                quality_icon = "🔴"
                            print(f"\r{quality_icon} Quality: {overall_quality}% | "
                                  f"Attention: {attention:.2f} | "
                                  f"Relaxation: {relaxation:.2f}  ", end='')

                    last_update = current_time

                # Update EEG monitor (render) - only for old mode
                if self.eeg_visualizer and not isinstance(self.eeg_visualizer, EEGVisualizerProcess):
                    if self.eeg_visualizer.is_running:
                        self.eeg_visualizer.update_plots()

                # Render visualization frame
                if not self.visualizer.run_frame():
                    self.running = False

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped by user")

        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback  # pylint: disable=import-outside-toplevel
            traceback.print_exc()

    def cleanup(self) -> None:
        """
        Cleanup and shutdown.
        """
        print("\n\n🧹 Cleaning up...")

        if self.connector:
            self.connector.disconnect()

        if self.visualizer:
            self.visualizer.close()

        if self.eeg_visualizer:
            self.eeg_visualizer.close()

        # Close optimizer (threads and process pool)
        if self.optimizer:
            self.optimizer.cleanup()

        print("✅ Done!")

    def start(self) -> int:
        """
        Start entire application.

        :return: Exit code (0 = success, 1 = error)
        """
        try:
            # Setup
            if not self.setup():
                return 1

            # Calibration
            self.calibrate()
            # Run
            self.run()
            # Cleanup
            self.cleanup()

            return 0

        except Exception as e:
            print(f"\n❌ Critical error: {e}")
            import traceback    # pylint: disable=import-outside-toplevel
            traceback.print_exc()
            return 1


def main() -> int:
    """
    Application entry point.

    :return: Exit code
    """
    app = BrainArtApp()
    return app.start()


if __name__ == "__main__":
    sys.exit(main())
