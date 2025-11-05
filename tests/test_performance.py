"""
Brain Art Performance Test.

Check how well optimization works on your system.
"""

import time
import sys
import multiprocessing as mp
import platform
import threading

import pygame
import numpy as np

import config


def test_cpu_info() -> None:
    """
    Display CPU and system information.
    
    Shows system details including CPU cores, Python version, etc.
    """
    print("=" * 60)
    print("🖥️  SYSTEM INFORMATION")
    print("=" * 60)
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Processor: {platform.processor()}")
    print(f"CPU cores: {mp.cpu_count()}")
    print(f"Python: {sys.version.split()[0]}")
    print()


def test_pygame_fps() -> None:
    """
    Test pygame FPS performance.
    
    Measures rendering performance with and without GPU acceleration.
    """
    print("=" * 60)
    print("🎮 PYGAME FPS TEST")
    print("=" * 60)

    pygame.init()

    # Test with GPU acceleration
    try:
        if config.USE_GPU_ACCELERATION:
            screen = pygame.display.set_mode((800, 600), pygame.HWSURFACE | pygame.DOUBLEBUF)
            print("✅ GPU acceleration: ENABLED")
        else:
            screen = pygame.display.set_mode((800, 600))
            print("⚠️  GPU acceleration: DISABLED")
    except Exception:
        screen = pygame.display.set_mode((800, 600))
        print("⚠️  GPU acceleration: UNAVAILABLE")

    pygame.display.set_caption("FPS Test")
    clock = pygame.time.Clock()

    # Rendering test
    print("\nRendering test (5 seconds)...")
    print("Drawing 100 circles per frame...\n")

    frames = 0
    start_time = time.time()
    test_duration = 5.0

    while time.time() - start_time < test_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # Draw something (Brain Art simulation)
        screen.fill((0, 0, 0))
        for i in range(100):
            color = (255, 100, 100)
            pos = (50 + i * 7, 300)
            pygame.draw.circle(screen, color, pos, 20)

        pygame.display.flip()
        clock.tick(60)  # Target 60 FPS
        frames += 1

    elapsed = time.time() - start_time
    avg_fps = frames / elapsed

    print("✅ Results:")
    print(f"   Frames: {frames}")
    print(f"   Average FPS: {avg_fps:.1f}")
    print(f"   Min FPS: {clock.get_fps():.1f}")

    if avg_fps >= 50:
        print("   🟢 Rating: EXCELLENT")
    elif avg_fps >= 30:
        print("   🟡 Rating: GOOD")
    else:
        print("   🔴 Rating: POOR - Enable optimizations!")

    pygame.quit()
    print()


def test_threading() -> None:
    """
    Test multithreading performance.
    
    Compares synchronous vs asynchronous computation performance.
    """
    print("=" * 60)
    print("🧵 THREADING TEST")
    print("=" * 60)

    if not config.USE_THREADING:
        print("⚠️  Threading DISABLED in config.py")
        print()
        return

    print("Testing computations in separate threads...")

    rng = np.random.default_rng(seed=42)

    def heavy_computation() -> None:
        """Simulate heavy computations (FFT)."""
        for _ in range(10):
            data = rng.standard_normal(1000)
            np.fft.fft(data)

    # Synchronous test
    start = time.time()
    for _ in range(4):
        heavy_computation()
    sync_time = time.time() - start

    # Asynchronous test
    start = time.time()
    threads = []
    for _ in range(4):
        t = threading.Thread(target=heavy_computation)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    async_time = time.time() - start

    speedup = sync_time / async_time

    print("\n✅ Results:")
    print(f"   Synchronous: {sync_time:.3f}s")
    print(f"   Asynchronous: {async_time:.3f}s")
    print(f"   Speedup: {speedup:.2f}x")

    if speedup >= 2.0:
        print("   🟢 Threading works GREAT!")
    elif speedup >= 1.3:
        print("   🟡 Threading works WELL")
    else:
        print("   🔴 Threading NOT WORKING (check config)")

    print()


def _dummy_process_func() -> str:
    """
    Simple test process - must be top-level for Windows.
    
    :return: Status string
    """
    time.sleep(0.3)
    return "OK"


def test_multiprocessing() -> None:
    """
    Test separate process functionality.
    
    Verifies that multiprocessing works correctly on the system.
    """
    print("=" * 60)
    print("⚙️  MULTIPROCESSING TEST")
    print("=" * 60)

    if not config.EEG_VISUALIZER_SEPARATE_PROCESS:
        print("⚠️  Separate process DISABLED in config.py")
        print()
        return

    print("Testing process creation...")

    try:
        start = time.time()
        p = mp.Process(target=_dummy_process_func)
        p.start()
        p.join(timeout=2)
        elapsed = time.time() - start

        if p.exitcode == 0:
            print(f"\n✅ Process created and finished in {elapsed:.3f}s")
            print("   🟢 Multiprocessing WORKS!")
        else:
            print(f"\n⚠️  Process finished with code: {p.exitcode}")
            print("   🟡 Multiprocessing partially works")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   🔴 Multiprocessing NOT WORKING")
        print("   💡 This is normal on some systems - app will use fallback")

    print()


def test_config() -> None:
    """
    Check optimization configuration.
    
    Displays current optimization settings and recommendations.
    """
    print("=" * 60)
    print("⚙️  OPTIMIZATION CONFIGURATION")
    print("=" * 60)

    configs = [
        ("USE_THREADING", "Threading for EEG computations"),
        ("USE_PROCESS_POOL", "Process pool"),
        ("EEG_VISUALIZER_SEPARATE_PROCESS", "EEG Monitor in separate process"),
        ("USE_GPU_ACCELERATION", "GPU acceleration"),
        ("PYGAME_USE_OPENGL", "OpenGL (experimental)"),
        ("ENABLE_PARTICLE_CACHE", "Particle cache"),
    ]

    print()
    for name, desc in configs:
        value = getattr(config, name, None)
        if value is None:
            status = "❌ MISSING"
        elif value:
            status = "✅ ENABLED"
        else:
            status = "⚠️  DISABLED"

        print(f"{status} {name}")
        print(f"         {desc}")

    print()

    # Summary
    enabled_count = sum(getattr(config, name, False) for name, _ in configs if name != "PYGAME_USE_OPENGL")

    if enabled_count >= 4:
        print("🟢 RATING: Optimizations enabled! Should work great.")
    elif enabled_count >= 2:
        print("🟡 RATING: Some optimizations enabled. Consider enabling more.")
    else:
        print("🔴 RATING: Few optimizations. Enable more in config.py!")

    print()
    print("💡 Recommended for maximum performance:")
    print("   USE_THREADING = True")
    print("   EEG_VISUALIZER_SEPARATE_PROCESS = True")
    print("   USE_GPU_ACCELERATION = True")
    print("   ENABLE_PARTICLE_CACHE = True")
    print()


def main() -> None:
    """
    Run all performance tests.
    
    Executes comprehensive performance testing suite.
    """
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "BRAIN ART PERFORMANCE TEST" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    try:
        # Tests
        test_cpu_info()
        test_config()
        test_threading()
        test_multiprocessing()
        test_pygame_fps()

        # Summary
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        print()
        print("📖 More information: docs/OPTIMIZATION.md")
        print()

    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback  # pylint: disable=import-outside-toplevel
        traceback.print_exc()


if __name__ == "__main__":
    # Windows multiprocessing requires this!
    mp.freeze_support()
    main()
