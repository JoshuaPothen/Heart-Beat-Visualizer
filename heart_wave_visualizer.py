"""
Heart Beat Wave Monitor — Serial Visualizer
=============================================
Reads serial data from a Circuit Playground Express running code.py
and renders live, unique wave-pattern visualizations:

  1. Rolling Waveform   — classic ECG-style trace with glow
  2. Radial Pulse        — circular / polar heartbeat ring
  3. Frequency Spectrum  — live FFT bar graph
  4. Lissajous Figure    — X-Y phase portrait (current vs delayed signal)

Controls:
  1-4 keys  → switch between visualizations
  Q / Esc   → quit

Usage:
  python heart_wave_visualizer.py [--port /dev/cu.usbmodem14101] [--baud 115200]

If --port is omitted the script auto-detects the first available serial port.
"""

import argparse
import collections
import sys
import threading
import time

import numpy as np

# Import pygame at module level to avoid circular import issues on Python 3.14
import pygame
import pygame.freetype

# ---------------------------------------------------------------------------
# Serial helpers
# ---------------------------------------------------------------------------

def find_serial_port():
    """Return the first likely Circuit Playground Express serial port."""
    import serial.tools.list_ports
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").lower()
        if any(kw in desc for kw in ("circuit", "playground", "express", "cdc", "usbmodem")):
            return p.device
    # Fallback: just return the first port
    ports = list(serial.tools.list_ports.comports())
    if ports:
        return ports[0].device
    return None


def serial_reader(port, baud, buffer, lock, running):
    """Background thread that continuously reads serial lines into *buffer*."""
    import serial
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"[serial] Connected to {port} @ {baud}")
    except Exception as e:
        print(f"[serial] ERROR opening {port}: {e}")
        running.clear()
        return

    while running.is_set():
        try:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            # code.py prints tuples like "(value,)"
            line = line.strip("()")
            line = line.rstrip(",")
            value = float(line)
            with lock:
                buffer.append(value)
        except (ValueError, UnicodeDecodeError):
            continue
        except Exception:
            continue
    ser.close()


# ---------------------------------------------------------------------------
# Visualization with pygame
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Heart Beat Wave Visualizer")
    parser.add_argument("--port", type=str, default=None, help="Serial port (auto-detect if omitted)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default 115200)")
    parser.add_argument("--buf", type=int, default=500, help="Sample buffer length")
    args = parser.parse_args()

    # --- Find port ---
    port = args.port or find_serial_port()
    if port is None:
        print("No serial port found. Please specify with --port.")
        sys.exit(1)

    # --- Shared data ---
    BUF_LEN = args.buf
    buffer = collections.deque(maxlen=BUF_LEN)
    lock = threading.Lock()
    running = threading.Event()
    running.set()

    # Start serial reader thread
    t = threading.Thread(target=serial_reader, args=(port, args.baud, buffer, lock, running), daemon=True)
    t.start()

    # --- Pygame setup ---
    pygame.init()
    pygame.freetype.init()
    WIDTH, HEIGHT = 1100, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("💓 Heart Beat Wave Monitor")
    clock = pygame.time.Clock()

    # Use freetype with the default built-in font (avoids sysfont circular import on Python 3.14)
    # pygame.freetype.Font(None) uses the built-in pygame default font
    _ft_font = pygame.freetype.Font(None, 16)
    _ft_title = pygame.freetype.Font(None, 22)

    def render_text(text, color, large=False):
        """Render text to a Surface using freetype."""
        ft = _ft_title if large else _ft_font
        surf, _ = ft.render(text, color)
        return surf

    # Colors
    BG = (10, 10, 18)
    GRID = (30, 30, 50)
    RED = (255, 50, 80)
    PINK = (255, 100, 130)
    CYAN = (0, 220, 255)
    GREEN = (0, 255, 130)
    ORANGE = (255, 160, 50)
    WHITE = (220, 220, 230)
    DIM = (80, 80, 100)

    mode = 1  # 1-4
    mode_names = {
        1: "Rolling Waveform",
        2: "Radial Pulse",
        3: "Frequency Spectrum",
        4: "Lissajous Phase Portrait",
    }

    # Pre-create glow surfaces (small translucent circles) for waveform glow
    def make_glow(radius, color, alpha=60):
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            a = int(alpha * (r / radius))
            pygame.draw.circle(s, (*color, a), (radius, radius), r)
        return s

    glow_red = make_glow(18, RED, 50)
    glow_cyan = make_glow(14, CYAN, 40)

    def get_samples():
        """Snapshot of the current buffer as a numpy array."""
        with lock:
            return np.array(list(buffer), dtype=float)

    # -----------------------------------------------------------------------
    # Drawing helpers
    # -----------------------------------------------------------------------

    def draw_grid(surface, w, h):
        for x in range(0, w, 50):
            pygame.draw.line(surface, GRID, (x, 0), (x, h))
        for y in range(0, h, 50):
            pygame.draw.line(surface, GRID, (0, y), (w, y))

    def draw_hud(surface, w, h, data):
        # Mode label
        label = render_text(mode_names[mode], WHITE, large=True)
        surface.blit(label, (20, 15))
        # Instructions
        info = render_text("Keys: 1-4 switch view  |  R reset  |  Q quit", DIM)
        surface.blit(info, (20, h - 30))
        # Stats
        if len(data) > 1:
            mn, mx = data.min(), data.max()
            bpm_text = ""
            # Rough BPM estimate from zero-crossings
            crossings = np.where(np.diff(np.sign(data)))[0]
            if len(crossings) >= 2:
                avg_period = np.mean(np.diff(crossings)) * 0.025  # ~25 ms per sample
                if avg_period > 0:
                    bpm = 60.0 / (avg_period * 2)
                    bpm_text = f"  ~{bpm:.0f} BPM"
            stats = render_text(f"samples={len(data)}  range=[{mn:.0f}, {mx:.0f}]{bpm_text}", DIM)
            surface.blit(stats, (w - stats.get_width() - 20, 15))

    # --- 1. Rolling Waveform ------------------------------------------------
    def draw_waveform(surface, w, h, data):
        if len(data) < 2:
            return
        mn, mx = data.min(), data.max()
        rng = mx - mn if mx != mn else 1

        margin = 80
        plot_h = h - margin * 2
        plot_w = w - margin * 2

        # Centre line
        cy = margin + plot_h // 2
        pygame.draw.line(surface, (40, 40, 60), (margin, cy), (margin + plot_w, cy), 1)

        points = []
        for i, v in enumerate(data[-plot_w:]):
            x = margin + i
            y = int(cy - (v / rng) * (plot_h * 0.45))
            points.append((x, y))

        # Glow trail
        for i, (px, py) in enumerate(points):
            alpha = int(255 * i / len(points))
            surface.blit(glow_red, (px - 18, py - 18), special_flags=pygame.BLEND_ADD)

        # Main line
        if len(points) >= 2:
            pygame.draw.aalines(surface, RED, False, points)
            # Brighter leading edge
            if len(points) > 10:
                pygame.draw.aalines(surface, PINK, False, points[-10:])

        # Leading dot
        if points:
            px, py = points[-1]
            pygame.draw.circle(surface, (255, 255, 255), (px, py), 5)

    # --- 2. Radial Pulse ----------------------------------------------------
    def draw_radial(surface, w, h, data):
        if len(data) < 10:
            return
        cx, cy = w // 2, h // 2
        base_r = min(w, h) * 0.28

        mn, mx = data.min(), data.max()
        rng = mx - mn if mx != mn else 1
        norm = (data - mn) / rng  # 0-1

        n = len(data)
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)

        points = []
        for i in range(n):
            r = base_r + norm[i] * base_r * 0.6
            x = int(cx + r * np.cos(angles[i]))
            y = int(cy + r * np.sin(angles[i]))
            points.append((x, y))

        # Draw filled polygon with slight transparency
        if len(points) >= 3:
            # Outer ring
            pygame.draw.polygon(surface, (40, 10, 20), points, 0)
            pygame.draw.aalines(surface, RED, True, points)

            # Inner glow ring
            inner_pts = []
            for i in range(n):
                r = base_r * 0.3 + norm[i] * base_r * 0.15
                x = int(cx + r * np.cos(angles[i]))
                y = int(cy + r * np.sin(angles[i]))
                inner_pts.append((x, y))
            pygame.draw.aalines(surface, CYAN, True, inner_pts)

        # Centre dot pulsing with latest value
        pulse = int(8 + norm[-1] * 20)
        pygame.draw.circle(surface, RED, (cx, cy), pulse)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), max(3, pulse // 3))

    # --- 3. Frequency Spectrum (FFT) ----------------------------------------
    def draw_spectrum(surface, w, h, data):
        if len(data) < 32:
            return
        # Use last power-of-2 samples
        n = 1
        while n * 2 <= len(data):
            n *= 2
        segment = data[-n:]
        # Windowed FFT
        window = np.hanning(n)
        fft = np.abs(np.fft.rfft(segment * window))
        fft = fft[1:]  # drop DC
        if len(fft) == 0:
            return

        fft_db = 20 * np.log10(fft + 1e-6)
        fft_db = np.clip(fft_db, 0, None)

        margin = 80
        plot_w = w - margin * 2
        plot_h = h - margin * 2
        num_bars = min(len(fft_db), 64)
        bar_w = max(2, plot_w // num_bars - 2)
        max_val = fft_db.max() if fft_db.max() > 0 else 1

        for i in range(num_bars):
            val = fft_db[i] / max_val
            bar_h = int(val * plot_h)
            x = margin + i * (bar_w + 2)
            y = margin + plot_h - bar_h

            # Gradient color: green → orange → red
            if val < 0.5:
                color = (int(255 * val * 2), 255, 50)
            else:
                color = (255, int(255 * (1 - val) * 2), 50)
            pygame.draw.rect(surface, color, (x, y, bar_w, bar_h))
            # Bright cap
            pygame.draw.rect(surface, WHITE, (x, y, bar_w, 2))

        # Axis label
        lbl = render_text("Frequency ->", DIM)
        surface.blit(lbl, (w // 2 - lbl.get_width() // 2, h - margin + 10))

    # --- 4. Lissajous Phase Portrait ----------------------------------------
    def draw_lissajous(surface, w, h, data):
        if len(data) < 40:
            return
        delay = len(data) // 4  # quarter-period offset
        x_data = data[:-delay]
        y_data = data[delay:]
        n = min(len(x_data), len(y_data))
        x_data = x_data[:n]
        y_data = y_data[:n]

        mn_x, mx_x = x_data.min(), x_data.max()
        mn_y, mx_y = y_data.min(), y_data.max()
        rng_x = mx_x - mn_x if mx_x != mn_x else 1
        rng_y = mx_y - mn_y if mx_y != mn_y else 1

        cx, cy = w // 2, h // 2
        scale = min(w, h) * 0.35

        points = []
        for i in range(n):
            px = int(cx + ((x_data[i] - mn_x) / rng_x - 0.5) * 2 * scale)
            py = int(cy - ((y_data[i] - mn_y) / rng_y - 0.5) * 2 * scale)
            points.append((px, py))

        if len(points) >= 2:
            # Fading trail
            seg_len = len(points)
            for i in range(1, seg_len):
                t = i / seg_len
                r = int(50 + 205 * t)
                g = int(200 * (1 - t))
                b = int(255 * t)
                pygame.draw.line(surface, (r, g, b), points[i - 1], points[i], 2)

            # Leading dot
            px, py = points[-1]
            surface.blit(glow_cyan, (px - 14, py - 14), special_flags=pygame.BLEND_ADD)
            pygame.draw.circle(surface, CYAN, (px, py), 5)

        # Cross-hairs
        pygame.draw.line(surface, GRID, (cx - int(scale), cy), (cx + int(scale), cy), 1)
        pygame.draw.line(surface, GRID, (cx, cy - int(scale)), (cx, cy + int(scale)), 1)

    # -----------------------------------------------------------------------
    # Main loop
    # -----------------------------------------------------------------------
    draw_funcs = {1: draw_waveform, 2: draw_radial, 3: draw_spectrum, 4: draw_lissajous}

    while running.is_set():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running.clear()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running.clear()
                elif event.key == pygame.K_1:
                    mode = 1
                elif event.key == pygame.K_2:
                    mode = 2
                elif event.key == pygame.K_3:
                    mode = 3
                elif event.key == pygame.K_4:
                    mode = 4
                elif event.key == pygame.K_r:
                    with lock:
                        buffer.clear()
            elif event.type == pygame.WINDOWRESIZED:
                WIDTH, HEIGHT = event.x, event.y
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

        data = get_samples()

        screen.fill(BG)
        draw_grid(screen, WIDTH, HEIGHT)
        draw_funcs[mode](screen, WIDTH, HEIGHT, data)
        draw_hud(screen, WIDTH, HEIGHT, data)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print("Done.")


if __name__ == "__main__":
    main()
