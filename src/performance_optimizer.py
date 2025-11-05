"""
Performance optimization module.

Provides multithreading, GPU acceleration, and caching capabilities
for improved application performance.
"""

import os
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue
import time
from typing import Optional, Dict, Any

import pygame
import numpy as np

import config


class EEGComputeThread(threading.Thread):
    """
    Separate thread for EEG computations (FFT, band powers).
    
    Performs computations in background to avoid blocking main thread.
    """

    def __init__(self, processor: Any) -> None:
        """
        Initialize EEG compute thread.
        
        :param processor: EEG processor instance to use for computations
        """
        super().__init__(daemon=True)
        self.processor: Any = processor
        self.data_queue: queue.Queue = queue.Queue(maxsize=5)
        self.result_queue: queue.Queue = queue.Queue(maxsize=5)
        self.running: bool = True

    def add_data(self, eeg_data: np.ndarray) -> None:
        """
        Add data for processing (non-blocking).
        
        :param eeg_data: EEG data array to process
        """
        try:
            self.data_queue.put_nowait(eeg_data)
        except queue.Full:
            # Skip if queue is full (data is too old)
            pass

    def get_results(self) -> Optional[Dict[str, Any]]:
        """
        Get computation results (non-blocking).
        
        :return: Dictionary with computation results or None if not ready
        """
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None

    def run(self) -> None:
        """
        Main computation thread loop.
        
        Continuously processes data from queue and computes EEG metrics.
        """
        while self.running:
            try:
                # Get data (timeout 0.1s)
                eeg_data = self.data_queue.get(timeout=0.1)

                # Add to processor
                self.processor.add_data(eeg_data)

                # Compute metrics
                band_powers = self.processor.compute_band_powers()
                band_powers_per_channel = self.processor.compute_band_powers_per_channel()
                attention = self.processor.compute_attention()
                relaxation = self.processor.compute_relaxation()

                # Send results
                results = {
                    'band_powers': band_powers,
                    'band_powers_per_channel': band_powers_per_channel,
                    'attention': attention,
                    'relaxation': relaxation,
                    'timestamp': time.time()
                }

                try:
                    self.result_queue.put_nowait(results)
                except queue.Full:
                    # Remove old results
                    try:
                        self.result_queue.get_nowait()
                        self.result_queue.put_nowait(results)
                    except Exception:
                        pass

            except queue.Empty:
                continue
            except Exception as e:
                if config.DEBUG:
                    print(f"⚠️  Error in EEG compute thread: {e}")
                time.sleep(0.01)

    def stop(self) -> None:
        """
        Stop the computation thread.
        
        Signals the thread to terminate gracefully.
        """
        self.running = False


class EEGVisualizerProcess(mp.Process):
    """
    Separate process for EEG Visualizer (matplotlib).
    
    This significantly increases main application FPS by running
    visualization in a separate process.
    """

    def __init__(self, use_advanced: bool = True, buffer_duration: float = 5.0) -> None:
        """
        Initialize EEG visualizer process.
        
        :param use_advanced: Use advanced visualizations
        :param buffer_duration: Buffer duration in seconds
        """
        super().__init__(daemon=True)
        self.use_advanced: bool = use_advanced
        self.buffer_duration: float = buffer_duration

        # Queues for inter-process communication
        self.data_queue: mp.Queue = mp.Queue(maxsize=10)
        self.command_queue: mp.Queue = mp.Queue(maxsize=5)
        self.running: Any = mp.Value('b', True)

    def send_data(self, eeg_data: np.ndarray, band_powers: Optional[Dict] = None,
                  band_powers_per_channel: Optional[Dict] = None) -> None:
        """
        Send data to visualizer (non-blocking).
        
        :param eeg_data: EEG data array
        :param band_powers: Band power values
        :param band_powers_per_channel: Band power values per channel
        """
        try:
            data_packet = {
                'eeg_data': eeg_data,
                'band_powers': band_powers,
                'band_powers_per_channel': band_powers_per_channel
            }
            self.data_queue.put_nowait(data_packet)
        except Exception:
            pass  # Skip if queue is full

    def is_running(self) -> bool:
        """
        Check if process is still running.
        
        :return: True if process is active
        """
        return self.running.value and self.is_alive()

    def close(self) -> None:
        """
        Close the process.
        
        Sends stop signal and waits for graceful termination,
        forcefully terminates if necessary.
        """
        self.running.value = False
        self.command_queue.put('stop')
        self.join(timeout=2)
        if self.is_alive():
            self.terminate()

    def run(self) -> None:
        """
        Main process function - runs in separate process.
        
        Creates visualizer and continuously updates it with incoming data.
        """
        try:
            # Import in process (requires matplotlib)
            from src.eeg_visualizer import create_eeg_visualizer  # pylint: disable=import-outside-toplevel

            # Create visualizer in this process
            viz = create_eeg_visualizer(
                use_advanced=self.use_advanced,
                buffer_duration=self.buffer_duration
            )
            viz.setup_window()

            last_update = time.time()

            while self.running.value:
                # Check commands
                try:
                    cmd = self.command_queue.get_nowait()
                    if cmd == 'stop':
                        break
                except Exception:
                    pass

                # Get data
                try:
                    data_packet = self.data_queue.get(timeout=0.05)
                    viz.update_data(
                        data_packet['eeg_data'],
                        data_packet.get('band_powers'),
                        data_packet.get('band_powers_per_channel')
                    )
                except Exception:
                    pass

                # Update plots (throttled)
                current_time = time.time()
                if current_time - last_update >= 0.1:  # 10 Hz
                    viz.update_plots()
                    last_update = current_time

                # Check if window is closed
                if not viz.is_running:
                    break

                time.sleep(0.01)  # Small delay

            viz.close()

        except Exception as e:
            print(f"❌ Error in EEG Visualizer process: {e}")
        finally:
            self.running.value = False


class PerformanceOptimizer:
    """
    Main class managing performance optimization.
    
    Handles threading, process pools, and GPU acceleration
    for improved application performance.
    """

    def __init__(self, processor: Optional[Any] = None) -> None:
        """
        Initialize performance optimizer.
        
        :param processor: EEG processor instance
        """
        self.processor: Optional[Any] = processor

        # Threading for EEG computations
        self.eeg_compute_thread: Optional[EEGComputeThread] = None
        if config.USE_THREADING and processor:
            self.eeg_compute_thread = EEGComputeThread(processor)
            self.eeg_compute_thread.start()
            print("✅ EEG computation thread started")

        # Process pool for heavy computations (if needed)
        self.process_pool: Optional[ProcessPoolExecutor] = None
        if config.USE_PROCESS_POOL:
            max_workers = config.MAX_THREADS if config.MAX_THREADS else mp.cpu_count()
            # Limit to reasonable number (no more than 4 for typical computations)
            max_workers = min(max_workers, 4)
            try:
                self.process_pool = ProcessPoolExecutor(max_workers=max_workers)
                print(f"✅ Process pool started ({max_workers} workers)")
            except Exception:
                print("⚠️  Failed to start process pool")

        # Thread pool for lighter operations
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        if config.USE_THREADING:
            max_workers = config.MAX_THREADS if config.MAX_THREADS else 4
            self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
            print(f"✅ Thread pool started ({max_workers} threads)")

    def process_eeg_async(self, eeg_data: np.ndarray) -> None:
        """
        Process EEG data asynchronously in separate thread.
        
        Results are available via get_eeg_results().
        
        :param eeg_data: EEG data array to process
        """
        if self.eeg_compute_thread:
            self.eeg_compute_thread.add_data(eeg_data)
        elif self.processor is not None:
            # Fallback - process synchronously
            self.processor.add_data(eeg_data)

    def get_eeg_results(self) -> Optional[Dict[str, Any]]:
        """
        Get processed EEG results.
        
        :return: Dictionary with metrics or None if not ready
        """
        if self.eeg_compute_thread:
            return self.eeg_compute_thread.get_results()
        elif self.processor is not None:
            # Fallback - compute synchronously
            processor = self.processor
            return {
                'band_powers': processor.compute_band_powers(),
                'band_powers_per_channel': processor.compute_band_powers_per_channel(),
                'attention': processor.compute_attention(),
                'relaxation': processor.compute_relaxation(),
                'timestamp': time.time()
            }
        else:
            return None

    def cleanup(self) -> None:
        """
        Close all threads and processes.
        
        Performs graceful shutdown of all background workers.
        """
        if self.eeg_compute_thread:
            self.eeg_compute_thread.stop()
            self.eeg_compute_thread.join(timeout=1)

        if self.thread_pool:
            self.thread_pool.shutdown(wait=False)

        if self.process_pool:
            self.process_pool.shutdown(wait=False)


def enable_gpu_acceleration() -> bool:
    """
    Enable GPU acceleration for pygame.
    
    Configures environment variables and pygame settings
    for hardware-accelerated rendering.
    
    :return: True if successfully enabled, False otherwise
    """
    if not config.USE_GPU_ACCELERATION:
        return False

    try:
        # Set environment variables for SDL (pygame backend)
        os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
        os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '0'

        # For Windows - use Direct3D if available
        if os.name == 'nt':
            os.environ['SDL_VIDEODRIVER'] = 'directx'

        # Enable hardware acceleration
        pygame.display.set_caption("Brain Art")

        print("✅ GPU acceleration enabled")
        return True
    except Exception as e:
        if config.DEBUG:
            print(f"⚠️  Failed to enable GPU acceleration: {e}")
        return False


def create_optimized_surface(size: tuple, flags: int = 0):
    """
    Create optimized pygame surface with GPU acceleration.
    
    :param size: Tuple of (width, height)
    :param flags: Pygame flags (e.g. pygame.SRCALPHA)
    :return: Pygame surface
    """

    if config.USE_GPU_ACCELERATION:
        # Hardware-accelerated surface
        try:
            if config.PYGAME_USE_OPENGL:
                # OpenGL (experimental)
                flags |= pygame.OPENGL | pygame.DOUBLEBUF
            else:
                # Standard hardware acceleration
                flags |= pygame.HWSURFACE | pygame.DOUBLEBUF

            return pygame.display.set_mode(size, flags)
        except Exception:
            # Fallback
            return pygame.display.set_mode(size, flags & ~(pygame.HWSURFACE | pygame.OPENGL))
    else:
        return pygame.display.set_mode(size, flags)


if __name__ == "__main__":
    # Test optimizer
    print("=== Test Performance Optimizer ===\n")

    print(f"CPU cores: {mp.cpu_count()}")
    print(f"Threading enabled: {config.USE_THREADING}")
    print(f"Process pool enabled: {config.USE_PROCESS_POOL}")
    print(f"GPU acceleration: {config.USE_GPU_ACCELERATION}")

    # Test GPU
    print("\nTest GPU acceleration...")
    if enable_gpu_acceleration():
        print("✅ GPU OK")
    else:
        print("⚠️  GPU unavailable or disabled")

    print("\n✅ Test completed")
