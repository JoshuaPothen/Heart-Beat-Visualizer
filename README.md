# Heart Beat Wave Monitor

A real-time heartbeat visualizer that reads live sensor data from an **Adafruit Circuit Playground Express** and displays it as four unique, animated wave patterns on your computer screen.

> **📌 Source & Credit**
> The board-side sensor code (`code.py`) is based on the official Adafruit tutorial:
> **[Make It Pulse — CircuitPython](https://learn.adafruit.com/make-it-pulse/circuitpython)**
> by Adafruit Industries. All credit for the original light-sensor heartbeat detection approach goes to Adafruit. The computer-side visualizer (`heart_wave_visualizer.py`) was built on top of that example.

---

## 📋 Table of Contents

1. [What You Need](#-what-you-need)
2. [How It Works (Big Picture)](#-how-it-works-big-picture)
3. [Step-by-Step Installation](#-step-by-step-installation)
   - [Step 1 – Install Python](#step-1--install-python)
   - [Step 2 – Install CircuitPython on the board](#step-2--install-circuitpython-on-the-board)
   - [Step 3 – Put the sensor code on the board](#step-3--put-the-sensor-code-on-the-board)
   - [Step 4 – Set up the visualizer on your computer](#step-4--set-up-the-visualizer-on-your-computer)
4. [Running the Visualizer](#-running-the-visualizer)
5. [Keyboard Controls](#-keyboard-controls)
6. [Troubleshooting](#-troubleshooting)
7. [How the Outputs Are Created](#-how-the-outputs-are-created)
   - [The Raw Serial Data](#the-raw-serial-data)
   - [Visualizer 1 – Rolling Waveform](#visualizer-1--rolling-waveform)
   - [Visualizer 2 – Radial Pulse](#visualizer-2--radial-pulse)
   - [Visualizer 3 – Frequency Spectrum](#visualizer-3--frequency-spectrum)
   - [Visualizer 4 – Lissajous Phase Portrait](#visualizer-4--lissajous-phase-portrait)
   - [BPM Estimate](#bpm-estimate)

---

## 🛒 What You Need

| Item | Notes |
|------|-------|
| **Adafruit Circuit Playground Express** | The microcontroller board with a built-in light sensor |
| **USB cable** | The board uses a Micro-USB cable |
| **A Mac, Windows, or Linux computer** | With a free USB port |
| **Python 3.9 or newer** | Installed on your computer (not the board) |

> **What is the Circuit Playground Express?**  
> It's a small circular green board about the size of a cookie. It has coloured LEDs around the edge, buttons, and lots of built-in sensors. The light sensor on it picks up changes in light intensity — when your finger is placed over it, the subtle variations caused by blood flow let us detect your heartbeat.

---

## 🔍 How It Works (Big Picture)

```
Your finger on the light sensor
        ↓
Circuit Playground Express reads light values ~40 times per second
        ↓
Board sends numbers over USB to your computer  (e.g. "(-342.5,)")
        ↓
heart_wave_visualizer.py reads those numbers
        ↓
Numbers are drawn as animated wave patterns on screen
```

There are **two separate pieces of code**:

| File | Runs on | Does what |
|------|---------|-----------|
| `code.py` | The **Circuit Playground Express board** | Reads the light sensor, calculates the heartbeat signal, and sends numbers via USB |
| `heart_wave_visualizer.py` | Your **computer** | Receives those numbers and draws the visualizations |

---

## 🛠 Step-by-Step Installation

### Step 1 – Install Python

> Skip this step if you already have Python 3.9+ installed. To check, open Terminal and type `python3 --version`.

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button
3. Open the downloaded file and follow the installer (click Continue / Agree / Install)
4. When it finishes, open **Terminal** (Mac: press `Cmd + Space`, type `Terminal`, press Enter)
5. Type `python3 --version` and press Enter — you should see something like `Python 3.12.2`

---

### Step 2 – Install CircuitPython on the board

CircuitPython is a special version of Python that runs directly on the Circuit Playground Express. `code.py` needs it.

1. Plug the board into your computer with the USB cable
2. **Double-press the small reset button** in the centre of the board — the LEDs should turn green and a drive called **CPLAYBOOT** appears on your computer (like a USB stick)
3. Go to **https://circuitpython.org/board/circuitplayground_express/**
4. Click **"Download .UF2 Now"** (the latest stable version)
5. Drag the downloaded `.uf2` file onto the **CPLAYBOOT** drive
6. The board will restart automatically — a new drive called **CIRCUITPY** will appear

---

### Step 3 – Put the sensor code on the board

1. Open the **CIRCUITPY** drive (it appears like a USB stick / external drive)
2. Copy `code.py` from this project folder into the root of **CIRCUITPY**
3. The board restarts automatically when it detects the new file
4. You should see the LED at position 9 (on the edge of the board) start blinking red in time with your pulse when you place your finger over the light sensor

> **How to find the light sensor:** It's a small clear lens on the front of the board, labelled with a sun icon (☀). Hold your fingertip gently over it — not pressing hard, just resting on it.

---

### Step 4 – Set up the visualizer on your computer

Open **Terminal** and run these commands one at a time. Copy each line exactly, paste it in, and press **Enter** after each one.

**Navigate to the project folder:**
```bash
cd "/Users/your directory/filepath/heartbeatwavemonitor" -> replace with your file path
```

**Create a virtual environment** (a self-contained Python sandbox — keeps things tidy):
```bash
python3 -m venv .venv
```

**Activate the virtual environment:**
```bash
source .venv/bin/activate
```
> Your terminal prompt will now show `(.venv)` at the start — that means it's active.

**Install the required packages:**
```bash
pip install pygame-ce pyserial numpy
```

> This installs three things:
> - **pygame-ce** — draws the graphics window and handles keyboard input
> - **pyserial** — reads data from the USB serial port
> - **numpy** — does the math (FFT, averaging, etc.)

Installation is complete! You only need to do Steps 1–4 once.

---

## ▶️ Running the Visualizer

Every time you want to use it:

1. **Plug in** the Circuit Playground Express via USB
2. Open **Terminal**
3. Navigate to the project folder and activate the environment:
   ```bash
   cd "path/to/Heart beat wave monitor" -> replace with your file path
   source .venv/bin/activate
   ```
4. Run the visualizer:
   ```bash
   python heart_wave_visualizer.py
   ```

A window will open. **Place your fingertip over the light sensor** on the board and the wave patterns will start moving in a few seconds.

> **If the port isn't found automatically**, find it manually:
> - Mac/Linux: `ls /dev/cu.*` in Terminal — look for something like `/dev/cu.usbmodem101`
> - Then run: `python heart_wave_visualizer.py --port /dev/cu.usbmodem101`

---

## ⌨️ Keyboard Controls

| Key | Action |
|-----|--------|
| `1` | Switch to **Rolling Waveform** |
| `2` | Switch to **Radial Pulse** |
| `3` | Switch to **Frequency Spectrum** |
| `4` | Switch to **Lissajous Phase Portrait** |
| `R` | **Reset** — clears all samples and starts fresh |
| `Q` or `Esc` | **Quit** the visualizer |

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| "No serial port found" | Make sure the board is plugged in. Try running `ls /dev/cu.*` (Mac) to find the port name, then use `--port` |
| Window opens but nothing moves | Check that `code.py` is on the board and the board's LED is blinking. Try pressing `R` to reset |
| "ModuleNotFoundError" | Make sure you activated the venv (`source .venv/bin/activate`) and ran `pip install pygame-ce pyserial numpy` |
| Board drive doesn't appear | Try a different USB cable — some cables are charge-only and don't carry data |
| LEDs stay white/rainbow on boot | CircuitPython isn't installed — go back to Step 2 |

---

## 📊 How the Outputs Are Created

### The Raw Serial Data

`code.py` on the board reads the built-in light sensor roughly **40 times per second**. Each reading is "centered" — the running average is subtracted so the signal oscillates above and below zero rather than sitting at some large absolute number.

The board sends each value over USB as a Python tuple, one per line:

```
(-12.5,)
(-45.2,)
(-89.1,)
(-120.4,)
(-98.3,)
(-40.0,)
(15.7,)
(88.2,)
(210.5,)
(342.0,)    ← heartbeat peak (blood pulse pushes through fingertip, changes light)
(280.3,)
(190.1,)
(88.4,)
(10.2,)
(-55.6,)
(-100.3,)   ← back to baseline
```

`heart_wave_visualizer.py` strips the brackets and comma, converts to a float, and stores the last **500 samples** in a rolling buffer. All four visualizers read from this same buffer.

---

### Visualizer 1 – Rolling Waveform

**What it does:** Scrolls the signal left-to-right like a hospital ECG monitor.

**How the data becomes the picture:**

Each sample in the buffer is mapped to a pixel column. The value determines how high or low the dot sits vertically:

```
Sample value  →  Y position on screen

   +342       →  near the TOP  (large positive = pulse peak)
      0        →  centre line
   -120       →  below centre (baseline dip)
```

Example — if the buffer contains:
```
[0, 20, 80, 200, 342, 280, 100, 10, -40, -100, -80, -20, 0, ...]
```
This draws a smooth curve that rises sharply to a peak (the heartbeat) and then falls back down — exactly like the spike you see on an ECG.

- The **glow** is added by drawing semi-transparent red circles along each point
- The **bright leading edge** is the last 10 points drawn in a lighter pink
- The **white dot** is the very latest sample

---

### Visualizer 2 – Radial Pulse

**What it does:** Bends the signal into a circle. A regular heartbeat creates a flower-like pulsing ring.

**How the data becomes the picture:**

The 500 samples are spread evenly around a full 360° circle. Each sample's value controls how far from the centre that point sits:

```
Angle = (sample index / total samples) × 360°
Radius = base_radius + (normalised_value × extra_radius)

normalised_value is scaled 0.0 → 1.0 from min to max in the buffer
```

Example — with a repeated heartbeat pattern:
```
Flat signal (all zeros)  →  Perfect circle
Heartbeat pulse arriving →  A spike pokes outward at that angle
Full buffer of heartbeats →  A star/flower shape with regular spikes around the ring
```

- The **inner cyan ring** mirrors the data at a smaller radius
- The **centre dot** grows and shrinks based on the most recent sample — it literally pulses with your heartbeat in real time

---

### Visualizer 3 – Frequency Spectrum

**What it does:** Shows *which frequencies* are present in your heartbeat signal, as a bar chart.

**How the data becomes the picture:**

A mathematical operation called an **FFT (Fast Fourier Transform)** breaks the signal into its component frequencies — similar to how a prism splits white light into a rainbow.

```
Time-domain signal (what you measured):
  [0, 88, 342, 280, 10, -100, -80, 0, 88, 342, 280, ...]
                ↓  FFT
Frequency-domain (what frequencies are present):
  0.8 Hz  →  tall bar   ← this is your heartbeat (~48 BPM)
  1.6 Hz  →  medium bar ← second harmonic
  2.4 Hz  →  small bar  ← third harmonic
  10+ Hz  →  tiny bars  ← noise
```

A healthy resting heartbeat of **60 BPM = 1 Hz** — so the tallest bar should be somewhere between **0.8–2 Hz** (48–120 BPM range).

- Bar **height** = how much energy at that frequency (in decibels)
- Bar **colour** grades green → orange → red based on relative strength
- The bright cap on each bar marks the peak

---

### Visualizer 4 – Lissajous Phase Portrait

**What it does:** Plots the signal against a *delayed version of itself*, creating looping organic shapes. A perfectly regular heartbeat creates a smooth ellipse; a real complex one makes a twisted figure-8 or teardrop.

**How the data becomes the picture:**

The buffer is split into two overlapping slices with a time offset (¼ of the buffer length):

```
X axis = samples[0 ... 375]      (current signal)
Y axis = samples[125 ... 500]    (same signal, 125 samples later ≈ 3 seconds)

For each pair (X[i], Y[i]), plot a dot at that coordinate on screen.
```

Example with a simple repeating heartbeat:
```
X:  [0,  88, 342, 280,  10, -100,  0,  88, 342, ...]
Y:  [88, 342, 280,  10, -100,   0, 88, 342, 280, ...]

→ Each (X, Y) pair traces a path that loops back on itself
→ A pure sine wave → ellipse
→ A sharp heartbeat spike → pointed teardrop or figure-8
```

- The **trail colour fades from blue → red** over time so you can see the direction of travel
- The **cyan dot** marks the very latest point
- The **cross-hairs** show the centre (zero, zero)

---

### BPM Estimate

Shown in the **top-right corner** of every visualizer.

The code counts **zero-crossings** — the moments where the signal crosses from negative to positive. Each crossing represents half a heartbeat cycle.

```
Serial data crossing zero:
  ... -80, -20, +15, +88 ...   ← zero-crossing detected here!
                     ... -30, +5 ...   ← another one, N samples later

Time between crossings = N × 0.025 seconds   (each sample ≈ 25ms)
Full period = 2 × that time
BPM = 60 ÷ period
```

**Example:**
```
20 samples between zero-crossings
→ half-period = 20 × 0.025s = 0.5s
→ full period = 1.0s
→ BPM = 60 ÷ 1.0 = 60 BPM  ✓
```

> The BPM number updates continuously as new samples arrive. It's an estimate — for medical-grade accuracy you'd want a dedicated pulse sensor, but it gives a reliable ballpark reading.
