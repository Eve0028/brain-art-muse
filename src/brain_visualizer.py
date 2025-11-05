"""
Brain Art Visualization.

Creates interactive, colorful visualizations based on EEG data.
"""

import random
import math
import time
from datetime import datetime
from typing import Optional, Callable, Any
import os

import pygame
import numpy as np

import config


class Particle:
    """
    Single particle in visualization.

    Uses caching for performance optimization.
    """

    # Cache of pre-rendered particles (shared between all instances)
    _cache: dict[tuple[int, tuple[int, int, int]], pygame.Surface] = {}
    _cache_size_limit = 50  # Maximum 50 different sizes in cache

    def __init__(self, x: float, y: float, color: tuple, size: float,
                 velocity: tuple, lifetime: float) -> None:
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.age: float = 0.0
        self.alpha = 255

    def update(self, dt: float) -> bool:
        """
        Update particle position and state.

        :param dt: Delta time in seconds
        :return: True if particle is still alive
        """
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt

        # Fading
        if self.lifetime > 0:
            self.alpha = int(255 * (1 - self.age / self.lifetime))

        return self.age < self.lifetime

    @classmethod
    def _get_cached_surface(cls, size: float, color: tuple):
        """
        Get or create cached particle surface.

        :param size: Particle size
        :param color: RGB color tuple
        :return: Pygame surface
        """
        # Check if cache is enabled
        if not getattr(config, 'ENABLE_PARTICLE_CACHE', True):
            # Cache disabled - create new surface each time
            cache_size = int(size / 2) * 2
            surf = pygame.Surface((cache_size * 2, cache_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, 255), (cache_size, cache_size), cache_size)
            return surf

        # Round size to nearest even number for better cache hit rate
        cache_size = int(size / 2) * 2
        cache_key = (cache_size, color)

        if cache_key not in cls._cache:
            # Limit cache size
            if len(cls._cache) >= cls._cache_size_limit:
                # Remove random element (simple LRU)
                # cls._cache.pop(next(iter(cls._cache)))
                cls._cache.pop(tuple(cls._cache.keys())[0])

            # Create new surface
            surf = pygame.Surface((cache_size * 2, cache_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, 255), (cache_size, cache_size), cache_size)
            cls._cache[cache_key] = surf

        return cls._cache[cache_key]

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear particle cache (useful when disabling cache).
        """
        cls._cache.clear()

    def draw(self, surface) -> None:
        """
        Draw particle - OPTIMIZED with caching.

        :param surface: Pygame surface to draw on
        """
        if self.alpha <= 10:  # Skip if almost invisible
            return

        try:
            # Use cached surface
            base_surf = self._get_cached_surface(self.size, self.color)

            # Apply alpha only if needed
            if self.alpha < 255:
                # Create copy with alpha (still faster than creating whole surface)
                surf = base_surf.copy()
                surf.set_alpha(self.alpha)
            else:
                surf = base_surf

            # Blit
            pos = (int(self.x - self.size), int(self.y - self.size))
            surface.blit(surf, pos)
        except Exception:
            pass  # Ignore rendering errors


class BrainVisualizer:
    """
    Main visualization class.

    Manages particle system and renders brain art based on EEG metrics.
    """

    def __init__(self) -> None:
        pygame.init()

        # Set up window
        self.width = config.WINDOW_WIDTH
        self.height = config.WINDOW_HEIGHT

        # GPU Acceleration
        display_flags = 0
        if config.FULLSCREEN:
            display_flags |= pygame.FULLSCREEN

        # Enable hardware acceleration if available
        if getattr(config, 'USE_GPU_ACCELERATION', True):
            try:
                # Hardware surface + double buffering for better performance
                display_flags |= pygame.HWSURFACE | pygame.DOUBLEBUF
                if getattr(config, 'PYGAME_USE_OPENGL', False):
                    display_flags |= pygame.OPENGL
            except Exception:
                pass  # Fallback to standard

        try:
            self.screen = pygame.display.set_mode((self.width, self.height), display_flags)
            if config.DEBUG and getattr(config, 'USE_GPU_ACCELERATION', True):
                print("✅ Pygame with hardware acceleration")
        except Exception:
            # Fallback without hardware acceleration
            self.screen = pygame.display.set_mode((self.width, self.height), 
                                                  pygame.FULLSCREEN if config.FULLSCREEN else 0)
            if config.DEBUG:
                print("⚠️  Pygame without hardware acceleration")

        pygame.display.set_caption("Brain Art - Muse S")

        # Drawing surface (with alpha)
        self.canvas = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # FPS
        self.clock = pygame.time.Clock()
        
        # Performance mode configuration
        performance_mode = getattr(config, 'PERFORMANCE_MODE', 'auto').lower()
        if performance_mode == 'high':
            self.fps = 60
            # Higher particle count for high performance mode
            config.MAX_PARTICLES = max(config.MAX_PARTICLES, 200)
            self.auto_optimize = False
        elif performance_mode == 'balanced':
            self.fps = 30
            # Keep original or moderate particle count
            config.MAX_PARTICLES = min(config.MAX_PARTICLES, 150)
            self.auto_optimize = False
        elif performance_mode == 'low':
            self.fps = 15
            # Lower particle count for low performance mode
            config.MAX_PARTICLES = min(config.MAX_PARTICLES, 80)
            self.auto_optimize = False
        else:  # 'auto' or unknown
            self.fps = config.TARGET_FPS
            self.auto_optimize = True
        
        if config.DEBUG and performance_mode != 'auto':
            print(f"⚡ Performance mode: {performance_mode.upper()} (FPS target: {self.fps}, MAX_PARTICLES: {config.MAX_PARTICLES})")

        # Font for text
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        # Particles
        self.particles: list[Particle] = []

        # Visualization state
        self.mode = 'mixed'  # 'alpha', 'beta', 'mixed'
        self.attention = 0.5
        self.relaxation = 0.5

        # Motion features (optional)
        self.motion_metrics: dict[Any, Any] | None = None
        self.motion_active = True  # Whether motion features are enabled

        # Statistics
        self.frame_count = 0
        self.fps_actual: float = 0.0
        self.fps_history: list[float] = []  # Last 60 frames for averaging

        # Auto-optimization (only for 'auto' mode)
        self.last_optimize_check: float = 0.0

        # Fade effect
        self.fade_surface = pygame.Surface((self.width, self.height))
        self.fade_surface.set_alpha(5)  # Slower fading = longer trail
        self.fade_surface.fill((0, 0, 0))

        # Screenshots directory
        if not os.path.exists(config.SCREENSHOTS_DIR):
            os.makedirs(config.SCREENSHOTS_DIR)

        # Quality check callback (set by main app)
        self.quality_check_callback: Optional[Callable[[], None]] = None

        # Calibration display
        self.calibration_active: bool = False
        self.calibration_remaining: float = 0.0

    def set_metrics(self, attention_val: float, relaxation_val: float, motion_metrics: dict[Any, Any] | None = None) -> None:
        """
        Update metrics from EEG and motion.

        :param attention_val: Attention index (0-1)
        :param relaxation_val: Relaxation index (0-1)
        :param motion_metrics: Dictionary with motion metrics (optional)
        """
        self.attention = np.clip(attention_val, 0, 1)
        self.relaxation = np.clip(relaxation_val, 0, 1)
        self.motion_metrics = motion_metrics

    def set_mode(self, mode: str) -> None:
        """
        Change visualization mode.

        :param mode: Mode name ('alpha', 'beta', or 'mixed')
        """
        if mode in config.MODES:
            self.mode = mode
            print(f"🎨 Mode: {config.MODES[mode]}")

    def cycle_mode(self) -> None:
        """
        Cycle to next mode (for gestures).
        """
        modes = list(config.MODES.keys())
        current_idx = modes.index(self.mode) if self.mode in modes else 0
        next_idx = (current_idx + 1) % len(modes)
        self.set_mode(modes[next_idx])

    def clear_screen(self) -> None:
        """
        Clear screen (for gestures).
        """
        self.canvas.fill((0, 0, 0, 0))
        self.particles.clear()
        print("🎨 Screen cleared!")

    def toggle_motion(self) -> None:
        """
        Toggle motion features on/off.
        """
        self.motion_active = not self.motion_active
        status = "enabled" if self.motion_active else "disabled"
        print(f"🎮 Motion features: {status}")

    def set_calibration_status(self, active: bool, remaining: float = 0.0) -> None:
        """
        Set calibration display status.

        :param active: Whether calibration is active
        :param remaining: Remaining time in seconds
        """
        self.calibration_active = active
        self.calibration_remaining = remaining

    def _get_color_for_mode(self) -> tuple:
        """
        Select color based on mode and metrics.

        :return: RGB color tuple
        """
        palette = config.COLOR_PALETTES[self.mode]

        if self.mode == 'alpha':
            # Color depends on relaxation level
            idx = int(self.relaxation * (len(palette) - 1))
            return palette[idx]

        elif self.mode == 'beta':
            # Color depends on attention level
            idx = int(self.attention * (len(palette) - 1))
            return palette[idx]

        else:  # mixed
            # Combination of both
            metric = (self.attention + self.relaxation) / 2
            idx = int(metric * (len(palette) - 1))
            return palette[idx]

    def _spawn_particles(self, dt: float) -> None:
        """
        Create new particles (with optional motion effects).

        :param dt: Delta time in seconds
        """
        # Motion modifiers (if active)
        motion_intensity_mult = 1.0
        motion_tilt_lr = 0.0
        motion_tilt_fb = 0.0

        if self.motion_active and self.motion_metrics:
            # Motion intensity affects particle count
            if config.MOTION_INTENSITY_SCALING if hasattr(config, 'MOTION_INTENSITY_SCALING') else True:
                motion_intensity = self.motion_metrics.get('motion_intensity', 0)
                motion_intensity_mult = 0.5 + motion_intensity * 1.5  # 0.5-2.0x

            # Head tilt affects direction
            if config.MOTION_TILT_EFFECTS if hasattr(config, 'MOTION_TILT_EFFECTS') else True:
                motion_tilt_lr = self.motion_metrics.get('tilt_left_right', 0)  # -1 to 1
                motion_tilt_fb = self.motion_metrics.get('tilt_forward_backward', 0)

                # Debug: show tilt values (if enabled)
                if config.DEBUG_MOTION if hasattr(config, 'DEBUG_MOTION') else False:
                    if abs(motion_tilt_lr) > 0.05 or abs(motion_tilt_fb) > 0.05:
                        tilt_str = []
                        if abs(motion_tilt_lr) > 0.2:
                            tilt_str.append(f"{'←LEFT' if motion_tilt_lr < 0 else 'RIGHT→'}")
                        if abs(motion_tilt_fb) > 0.2:
                            tilt_str.append(f"{'↑FRONT' if motion_tilt_fb < 0 else 'BACK↓'}")
                        status = " ".join(tilt_str) if tilt_str else "---"
                        print(f"  [Tilt] L/R: {motion_tilt_lr:+.2f}, F/B: {motion_tilt_fb:+.2f} → {status}")

        # Particle count depends on metrics + motion
        if self.mode == 'alpha':
            spawn_rate = 100 * self.relaxation * motion_intensity_mult
        elif self.mode == 'beta':
            spawn_rate = 150 * self.attention * motion_intensity_mult
        else:
            spawn_rate = 120 * (self.attention + self.relaxation) / 2 * motion_intensity_mult

        n_particles = int(spawn_rate * dt) + (1 if random.random() < spawn_rate * dt % 1 else 0)

        for _ in range(n_particles):
            # Starting position
            if self.mode == 'alpha':
                # Center (calm)
                angle = random.uniform(0, 2 * math.pi)
                radius = random.uniform(0, 100)
                x = self.width / 2 + radius * math.cos(angle)
                y = self.height / 2 + radius * math.sin(angle)
            else:
                # Random (dynamic)
                x = random.uniform(0, self.width)
                y = random.uniform(0, self.height)

            # Color
            color = self._get_color_for_mode()

            # Size depends on metrics
            if self.mode == 'alpha':
                size = config.PARTICLE_SIZE_MIN + self.relaxation * (config.PARTICLE_SIZE_MAX - config.PARTICLE_SIZE_MIN)
            else:
                size = config.PARTICLE_SIZE_MIN + self.attention * (config.PARTICLE_SIZE_MAX - config.PARTICLE_SIZE_MIN)

            # Speed (with optional motion tilt)
            if self.mode == 'alpha':
                # Slow, smooth movements
                speed = config.PARTICLE_SPEED_MIN + self.relaxation * (config.PARTICLE_SPEED_MAX - config.PARTICLE_SPEED_MIN) * 0.3
                angle = random.uniform(0, 2 * math.pi)
            else:
                # Fast, dynamic
                speed = config.PARTICLE_SPEED_MIN + self.attention * (config.PARTICLE_SPEED_MAX - config.PARTICLE_SPEED_MIN)
                angle = random.uniform(0, 2 * math.pi)

            # Motion tilt effect - head tilt STRONGLY affects particle direction
            # Threshold lowered to 0.05, but effect VERY strong (almost 100% direction control)
            if self.motion_active and (abs(motion_tilt_lr) > 0.05 or abs(motion_tilt_fb) > 0.05):
                # Add STRONG bias towards tilt direction
                # Note: Y on screen grows downward, so we invert motion_tilt_fb
                tilt_angle = math.atan2(-motion_tilt_fb, motion_tilt_lr)
                tilt_strength = min(1.0, math.sqrt(motion_tilt_lr**2 + motion_tilt_fb**2))

                # STRONGER effect: with strong tilt (~0.5+) almost 100% control
                # Use power to increase influence: strength^0.5 increases small values
                adjusted_strength = math.pow(tilt_strength, 0.5)  # 0.5 -> 0.7, 1.0 -> 1.0
                influence = 0.95  # 95% tilt influence on direction!

                # Mix: with strong tilt particles flow ALMOST ONLY in that direction
                angle = angle * (1 - adjusted_strength * influence) + tilt_angle * (adjusted_strength * influence)

            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)

            # Lifetime
            lifetime = config.PARTICLE_LIFETIME * (0.5 + random.random() * 0.5)

            particle = Particle(x, y, color, size, (vx, vy), lifetime)
            self.particles.append(particle)

    def update(self, dt: float) -> None:
        """
        Update visualization state.

        :param dt: Delta time in seconds
        """
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt)]

        # Create new particles
        self._spawn_particles(dt)

        # Limit particle count (performance)
        max_particles = config.MAX_PARTICLES if hasattr(config, 'MAX_PARTICLES') else 200
        if len(self.particles) > max_particles:
            self.particles = self.particles[-max_particles:]

    def draw(self) -> None:
        """
        Draw visualization - OPTIMIZED.
        """
        # Fade effect (slow fading)
        self.canvas.blit(self.fade_surface, (0, 0))

        # Draw particles - BATCH for better performance
        # Group by color for potential batching
        for particle in self.particles:
            particle.draw(self.canvas)

        # Draw on screen
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.canvas, (0, 0))

        # HUD
        self._draw_hud()

        # Flip with optional dirty rect (only changed areas)
        pygame.display.flip()

    def _draw_hud(self) -> None:
        """
        Draw user interface.
        """
        margin = 20

        # Calibration overlay (if active)
        if self.calibration_active:
            # Semi-transparent overlay
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Dark overlay
            self.screen.blit(overlay, (0, 0))

            # Calibration text (large, centered)
            font_large = pygame.font.Font(None, 72)
            remaining_int = int(self.calibration_remaining) + 1  # Round up
            cal_text = font_large.render(
                f"🎯 Kalibracja... {remaining_int}s pozostało",
                True,
                (255, 255, 255)
            )
            text_rect = cal_text.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(cal_text, text_rect)

            # Instructions below
            instr_text = self.font_small.render(
                "Zamknij oczy i oddychaj spokojnie",
                True,
                (200, 200, 200)
            )
            instr_rect = instr_text.get_rect(center=(self.width // 2, self.height // 2 + 60))
            self.screen.blit(instr_text, instr_rect)
            return  # Skip normal HUD during calibration

        # Mode
        mode_text = self.font.render(
            f"Mode: {config.MODES[self.mode]}",
            True,
            (255, 255, 255)
        )
        self.screen.blit(mode_text, (margin, margin))

        # Metrics
        y_offset = margin + 40

        if config.DEBUG:
            metrics_text = [
                f"Attention: {self.attention:.2f}",
                f"Relaxation: {self.relaxation:.2f}",
                f"Particles: {len(self.particles)}"
            ]

            # Add motion info if available
            if self.motion_metrics and self.motion_active:
                metrics_text.append(f"Motion: {self.motion_metrics.get('motion_intensity', 0):.2f}")
                tilt_lr = self.motion_metrics.get('tilt_left_right', 0)
                tilt_fb = self.motion_metrics.get('tilt_forward_backward', 0)

                # Show direction as arrows
                tilt_indicator = ""
                if abs(tilt_lr) > 0.2:
                    tilt_indicator += "←" if tilt_lr < 0 else "→"
                if abs(tilt_fb) > 0.2:
                    tilt_indicator += "↑" if tilt_fb < 0 else "↓"
                if not tilt_indicator:
                    tilt_indicator = "○"

                metrics_text.append(f"Tilt: {tilt_indicator} L/R:{tilt_lr:+.2f} F/B:{tilt_fb:+.2f}")

            for text in metrics_text:
                surf = self.font_small.render(text, True, (200, 200, 200))
                self.screen.blit(surf, (margin, y_offset))
                y_offset += 30

        # FPS
        if config.SHOW_FPS:
            fps_text = self.font_small.render(
                f"FPS: {int(self.fps_actual)}",
                True,
                (150, 150, 150)
            )
            self.screen.blit(fps_text, (self.width - 100, margin))

        # Instructions
        instructions = [
            "SPACE - clear",
            "1/2/3 - mode",
            "S - screenshot",
            "M - motion"
        ]

        # Add motion status if active
        if self.motion_metrics:
            motion_status = "ON" if self.motion_active else "OFF"
            motion_text = self.font_small.render(
                f"Motion: {motion_status}",
                True,
                (100, 255, 100) if self.motion_active else (255, 100, 100)
            )
            self.screen.blit(motion_text, (self.width - 150, margin + 30))

        y_offset = self.height - margin - len(instructions) * 25
        for instr in instructions:
            surf = self.font_small.render(instr, True, (100, 100, 100))
            self.screen.blit(surf, (margin, y_offset))
            y_offset += 25

    def clear(self) -> None:
        """
        Clear canvas.
        """
        self.canvas.fill((0, 0, 0, 0))
        self.particles.clear()

    def save_screenshot(self) -> None:
        """
        Save screenshot.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.SCREENSHOTS_DIR}/brain_art_{timestamp}.png"
        pygame.image.save(self.screen, filename)
        print(f"📸 Screenshot saved: {filename}")

    def handle_events(self) -> bool:
        """
        Handle pygame events.

        :return: True to continue, False to quit
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                elif event.key == pygame.K_SPACE:
                    self.clear()

                elif event.key == pygame.K_1:
                    self.set_mode('alpha')

                elif event.key == pygame.K_2:
                    self.set_mode('beta')

                elif event.key == pygame.K_3:
                    self.set_mode('mixed')

                elif event.key == pygame.K_s:
                    self.save_screenshot()

                elif event.key == pygame.K_m:
                    # Toggle motion features
                    self.toggle_motion()

                elif event.key == pygame.K_q:
                    # Check signal quality (call callback)
                    if self.quality_check_callback is not None:
                        self.quality_check_callback()

        return True

    def run_frame(self) -> bool:
        """
        Execute one frame.

        :return: True to continue, False to quit
        """
        # Delta time
        dt = self.clock.tick(self.fps) / 1000.0

        # Update FPS
        self.fps_actual = self.clock.get_fps()
        self.fps_history.append(self.fps_actual)
        if len(self.fps_history) > 60:
            self.fps_history.pop(0)

        # Auto-optimization every 2 seconds
        if self.auto_optimize and time.time() - self.last_optimize_check > 2.0:
            self._auto_optimize()
            self.last_optimize_check = time.time()

        # Handle events
        if not self.handle_events():
            return False

        # Update and draw
        self.update(dt)
        self.draw()

        self.frame_count += 1
        return True

    def _auto_optimize(self) -> None:
        """
        Automatically adjust settings based on FPS (only for 'auto' performance mode).
        
        Adapts both FPS target and particle count based on actual performance.
        """
        if len(self.fps_history) < 30:
            return

        avg_fps = sum(self.fps_history) / len(self.fps_history)
        performance_mode = getattr(config, 'PERFORMANCE_MODE', 'auto').lower()
        
        # Only auto-optimize if mode is 'auto'
        if performance_mode != 'auto':
            return

        # Adaptive FPS target adjustment
        if avg_fps < 15:
            # Very low FPS - reduce target to 20 and decrease particles
            if self.fps > 20:
                self.fps = 20
                print(f"⚡ Auto-optimization: FPS target → {self.fps} (actual: {avg_fps:.1f})")
        elif avg_fps < 25:
            # Low FPS - reduce target to 25
            if self.fps > 25:
                self.fps = 25
                print(f"⚡ Auto-optimization: FPS target → {self.fps} (actual: {avg_fps:.1f})")
        elif avg_fps > 55 and self.fps < 60:
            # High FPS - can increase target to 60
            self.fps = 60
            print(f"⚡ Auto-optimization: FPS target → {self.fps} (actual: {avg_fps:.1f})")
        elif avg_fps > 35 and self.fps < 30:
            # Good FPS - can increase target to 30
            self.fps = 30
            print(f"⚡ Auto-optimization: FPS target → {self.fps} (actual: {avg_fps:.1f})")

        # Adaptive particle count adjustment
        # If FPS < 20, decrease particle count
        if avg_fps < 20:
            new_max = max(50, config.MAX_PARTICLES - 20)
            if new_max != config.MAX_PARTICLES:
                config.MAX_PARTICLES = new_max
                print(f"⚡ Auto-optimization: MAX_PARTICLES → {new_max} (FPS: {avg_fps:.1f})")

        # If FPS > 50 and we have less than 200, increase
        elif avg_fps > 50 and config.MAX_PARTICLES < 200:
            new_max = min(200, config.MAX_PARTICLES + 20)
            if new_max != config.MAX_PARTICLES:
                config.MAX_PARTICLES = new_max
                print(f"⚡ Auto-optimization: MAX_PARTICLES → {new_max} (FPS: {avg_fps:.1f})")

    def close(self) -> None:
        """
        Close visualization.
        """
        pygame.quit()


# ===== STANDALONE TEST =====

if __name__ == "__main__":
    print("=== Test BrainVisualizer ===")
    print("Starting visualization with synthetic data...")
    print("\nKeys:")
    print("  SPACE - clear")
    print("  1 - Alpha mode")
    print("  2 - Beta mode")
    print("  3 - Mixed mode")
    print("  S - screenshot")
    print("  ESC - exit")

    viz = BrainVisualizer()

    running = True
    elapsed_time: float = 0.0

    while running:
        # Simulate changing metrics
        elapsed_time += 0.01
        attention = 0.5 + 0.3 * math.sin(elapsed_time * 2)
        relaxation = 0.5 + 0.3 * math.cos(elapsed_time * 1.5)

        viz.set_metrics(attention, relaxation)

        running = viz.run_frame()

    viz.close()
    print("\n✅ Test completed!")
