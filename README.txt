# 📸 PictureFramer

Turn that old tablet, laptop, mini‑PC or Raspberry Pi into a beautiful, always‑on digital photo frame. **PictureFramer** shows a full‑screen slideshow of your photos in dynamically generated **grids** (1–5 tiles) with smooth slide‑in/slide‑out animations. Mix your photos with **stylized color blocks** (e.g., Mondrian, 70s palettes) for a gallery‑like look. Optionally, keep a local folder up‑to‑date using **rclone** (e.g., to mirror an album export) and run PictureFramer on boot for “set‑and‑forget” smart‑home displays.

---

## ✨ Features

- **Grid slideshow** with many built‑in layouts (from single image to multi‑pane mosaics).
- **Animated transitions** (images glide in from screen edges; animated exit) with tunable speeds.
- **Aspect‑fill scaling & centered crop** for perfect edge‑to‑edge tiles (no squashed faces).
- **Stylized color blocks** mixed in with photos (or shown alone) using curated palettes:
  - `Mondrian`, `70s` (easily extendable).
- **Bordered tiles** for a clean gallery aesthetic.
- **Fullscreen** or windowed modes.
- **Simple local setup** — just drop images into `./Images`.
- **Keyboard**: `Esc` quits cleanly.
- **(Optional)** Keep the `Images/` folder in sync using **rclone**. _Important API limitation notice below._

---

## 🖼️ How it works (at a glance)

`PhotoFrameGrid.py`:

- Detects your primary display resolution and runs a full‑screen (or windowed) Pygame app.
- Randomly picks one of many predefined **fractional grid layouts** and assigns either a photo or a color block to each pane.
- Loads images, scales them to **aspect‑fill**, and crops the center to fit each pane precisely.
- Animates tiles **in** to their target positions, **holds** for a few seconds, then animates **out** before the next layout.

---

## 📦 Requirements

- **Python** 3.8+ (3.10/3.11/3.12+ are fine)
- **Python packages**:
  - `pygame` — the display/animation engine. Install via `pip` (Windows/macOS/Linux). [1](https://www.pygame.org/wiki/GettingStarted)[2](https://pypi.org/project/pygame/)  
  - `Pillow` — image metadata/IO (PIL fork). Install via `pip install pillow`. [3](https://pypi.org/project/pillow/)  
  - `screeninfo` — to get monitor geometry across platforms. [4](https://pypi.org/project/screeninfo/)

> **Why these?**  
> - *Pygame* provides hardware‑accelerated blitting, timing and events.  
> - *Pillow* reads image sizes/formats robustly.  
> - *screeninfo* reports monitor width/height on Windows, Linux (X11/DRM), and macOS. [4](https://pypi.org/project/screeninfo/)

---

## 🚀 Quick start

1. **Clone** this repository and `cd` into it.
2. **Create the images folder**:
   ```bash
   mkdir -p Images
   ```
   Drop some `.jpg/.jpeg/.png/.bmp/.gif/.tiff` files in there.
3. **Install dependencies** (ideally in a virtual environment):
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install pygame pillow screeninfo
   ```
   (See the Pygame “Getting Started” page for platform‑specific tips.) [1](https://www.pygame.org/wiki/GettingStarted)
4. **Run**:
   ```bash
   python PhotoFrameGrid.py
   ```

> Tip: Multi‑monitor setups—PictureFramer uses the **first** monitor reported by `screeninfo.get_monitors()[0]`. If detection fails on unusual environments, check `screeninfo` docs or force an enumerator. [4](https://pypi.org/project/screeninfo/)

---

## ⚙️ Configuration

Edit the **top of `PhotoFrameGrid.py`** to adjust behavior:

```python
FOLDER_PATH    = os.getcwd() + "/Images"  # where photos are read from
DISPLAY_TIME   = 3                        # seconds each layout is shown
SQUARES        = "Some"                   # "All", "Some", or "None"
PALETTE        = "Mondrian"               # "Mondrian", "70s", or your own
BORDER_WIDTH   = 10
ANIMATION_SPEED= 15                       # lower = snappier; higher = slower
TICK_SPEED     = 30                       # FPS cap for the animation loop
FULLSCREEN     = True                     # False -> windowed
```

- **SQUARES** controls whether photo tiles are replaced by palette‑colored blocks.
- **PALETTE** chooses the color scheme used for those blocks.
- Add your own palette to `COLOR_PALETTES` as a list of RGB tuples.
- **Heads‑up**: the Pygame window title currently displays `"PhotoRotato"` in code—purely cosmetic.

---

## 🔄 (Optional) Keep your `Images/` folder in sync

### Using rclone (read this first ⚠️)

- **Install rclone** (single binary; official instructions for Linux/macOS/Windows): [5](https://rclone.org/install/)[6](https://github.com/rclone/rclone/blob/master/docs/content/install.md)
- **Important Google Photos API change**: As of **March 31, 2025**, the Google Photos backend in rclone “can only download photos it uploaded,” due to Google policy changes. That means **you can no longer use rclone to fetch your entire historical Google Photos library unless those items were uploaded via rclone**. Review rclone’s Google Photos docs and Limitations carefully. [7](https://rclone.org/googlephotos/)

#### Practical options today

- **Album exports / Takeout**: Use Google Takeout (or export from Google Photos) and copy the exported files into `./Images`.  
- **If you already use rclone uploads**: You can still sync what rclone previously uploaded. Configure a Google Photos remote with `rclone config`, then (example) copy an album to your local folder:
  ```bash
  # After configuring a remote called "gphotos"
  rclone copy gphotos:album/YourAlbum "./Images"
  ```
  See the rclone Google Photos docs for album layout and commands such as `rclone lsd gphotos:album` and `rclone copy`/`sync`. **Note**: Availability and behavior depend on current API limits. [7](https://rclone.org/googlephotos/)

- **Other clouds**: rclone supports many providers (Drive, OneDrive, S3, etc.). Use `rclone sync <remote:path> ./Images` on a schedule if that fits your workflow. Install/usage details: rclone docs. [5](https://rclone.org/install/)

---

## 🏁 Run on boot (Linux, optional)

Use a **systemd** service so PictureFramer starts automatically at login/boot:

1. Create a small launcher script (adjust paths):
   ```bash
   # /usr/local/bin/pictureframer.sh
   #!/usr/bin/env bash
   cd /home/pi/PictureFramer
   /home/pi/PictureFramer/.venv/bin/python PhotoFrameGrid.py
   ```
   ```bash
   sudo chmod +x /usr/local/bin/pictureframer.sh
   ```
2. Create a service unit:
   ```ini
   # /etc/systemd/system/pictureframer.service
   [Unit]
   Description=PictureFramer slideshow
   After=multi-user.target
   Wants=graphical.target

   [Service]
   Type=simple
   Environment=PYGAME_HIDE_SUPPORT_PROMPT=hide
   ExecStart=/usr/local/bin/pictureframer.sh
   Restart=on-failure
   WorkingDirectory=/home/pi/PictureFramer
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=graphical.target
   ```
3. Enable & start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now pictureframer
   ```
   (General systemd approach adapted from common guides.) [8](https://tecadmin.net/setup-autorun-python-script-using-systemd/)

> **Home Assistant / Smart‑Home tip**  
> Expose start/stop/restart as **service calls** (SSH or `systemctl` via an HA command line switch) to integrate with automations (e.g., turn the frame on at sunrise). [8](https://tecadmin.net/setup-autorun-python-script-using-systemd/)

---

## 📁 Project structure

```
PictureFramer/
├─ PhotoFrameGrid.py     # the app
├─ Images/               # your photos live here
└─ README.md
```

---

## 🧩 Extending & theming

- **Add palettes**: Extend `COLOR_PALETTES` with your own color sets.
- **Add layouts**: Append to `laylis` (positions `p` and sizes `s` are **fractions** of screen `width`/`height`, and will be scaled at runtime).
- **Change timings**: Tune `DISPLAY_TIME`, `ANIMATION_SPEED`, `TICK_SPEED`.

---

## 🧪 Known limitations

- **Single monitor**: Uses the first monitor reported by `screeninfo`. Multi‑display selection isn’t surfaced yet. [4](https://pypi.org/project/screeninfo/)
- **No HTTP/Wi‑Fi controls built‑in (yet)**: Current input is only keyboard `Esc`. For smart‑home control today, manage the process via a service manager (e.g., `systemd`) and trigger it from automations.
- **GIFs**: Loaded as static images (first frame) by Pygame.
- **EXIF/rotation/face detection**: Not currently applied; images are cropped centered.

---

## 🧭 Roadmap

- Lightweight **local web API** (Flask or aiohttp) for remote control (pause/next/layout/palette).
- **Album/playlist** concepts (filter subfolders, shuffle modes).
- Optional **face‑aware cropping**.

---

## 🛠️ Troubleshooting

- **Pygame install issues**: Ensure you have a recent `pip` and Python, and follow platform‑specific notes (Windows PATH, macOS versions, Raspberry Pi wheels, etc.). [1](https://www.pygame.org/wiki/GettingStarted)
- **Monitor detection**: If `screeninfo` can’t find a monitor on niche setups, consult its docs or force an enumerator/driver. [4](https://pypi.org/project/screeninfo/)
- **Performance**: Lower `ANIMATION_SPEED` (snappier), tweak `TICK_SPEED` (30–60 FPS), and reduce very large source images if necessary.

---

## 🤝 Contributing

PRs welcome—especially for:
- New palettes & layouts  
- Web control endpoints  
- Packaging (e.g., `requirements.txt`, optional CLI flags)  
- Platform guides (Windows/macOS kiosk mode)

---

## 📜 License

Add a `LICENSE` file (MIT recommended) before publishing.

---

## 🙌 Credits

- Built with **Pygame**, **Pillow**, and **screeninfo**. [1](https://www.pygame.org/wiki/GettingStarted)[3](https://pypi.org/project/pillow/)[4](https://pypi.org/project/screeninfo/)
- Optional sync ideas with **rclone**. [5](https://rclone.org/install/)[7](https://rclone.org/googlephotos/)

---

### 🏃 Next steps

1) Drop a few photos in `Images/`, 2) `pip install pygame pillow screeninfo`, 3) `python PhotoFrameGrid.py`, 4) Enjoy the slideshow! 
