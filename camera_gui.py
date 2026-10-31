import os
import time
import tkinter as tk
from tkinter import ttk

import cv2
from PIL import Image, ImageTk

from camera import Camera

CAPTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captures")
RESOLUTIONS = {"640x480": (640, 480), "1280x720": (1280, 720), "1920x1080": (1920, 1080)}
REFRESH_MS = 15


class CameraGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Camera test")
        self.camera = None
        self.last_image = None
        self.photo = None

        bar = ttk.Frame(root, padding=6)
        bar.pack(fill="x")
        ttk.Label(bar, text="Camera").pack(side="left")
        self.index_var = tk.StringVar(value="0")
        ttk.Combobox(bar, textvariable=self.index_var, values=["0", "1", "2"],
                     width=3, state="readonly").pack(side="left", padx=4)
        self.res_var = tk.StringVar(value="1280x720")
        ttk.Combobox(bar, textvariable=self.res_var, values=list(RESOLUTIONS),
                     width=10, state="readonly").pack(side="left", padx=4)
        self.toggle_btn = ttk.Button(bar, text="Start", command=self.toggle)
        self.toggle_btn.pack(side="left", padx=4)
        self.snap_btn = ttk.Button(bar, text="Snapshot", command=self.snapshot, state="disabled")
        self.snap_btn.pack(side="left", padx=4)

        self.view = ttk.Label(root, anchor="center")
        self.view.pack(fill="both", expand=True)
        self.status = tk.StringVar(value="Stopped")
        ttk.Label(root, textvariable=self.status, padding=6).pack(fill="x")

        root.protocol("WM_DELETE_WINDOW", self.close)
        self.tick()

    def toggle(self) -> None:
        if self.camera is None:
            w, h = RESOLUTIONS[self.res_var.get()]
            cam = Camera(index=int(self.index_var.get()), width=w, height=h)
            try:
                cam.start()
            except RuntimeError as e:
                self.status.set(f"Error: {e}")
                return
            self.camera = cam
            self.toggle_btn.config(text="Stop")
            self.snap_btn.config(state="normal")
        else:
            self.camera.stop()
            self.camera = None
            self.toggle_btn.config(text="Start")
            self.snap_btn.config(state="disabled")
            self.status.set("Stopped")

    def snapshot(self) -> None:
        if self.last_image is None:
            return
        os.makedirs(CAPTURE_DIR, exist_ok=True)
        path = os.path.join(CAPTURE_DIR, time.strftime("capture_%Y%m%d_%H%M%S.png"))
        cv2.imwrite(path, self.last_image)
        self.status.set(f"Saved {path}")

    def tick(self) -> None:
        if self.camera is not None:
            frame = self.camera.read()
            if frame is not None:
                self.last_image = frame.image
                self.show(frame.image)
                cam = self.camera
                self.status.set(
                    f"{cam.width}x{cam.height}  {cam.measured_fps:.1f} fps  "
                    f"frame age {(time.monotonic() - frame.t) * 1000:.0f} ms")
        self.root.after(REFRESH_MS, self.tick)

    def show(self, image) -> None:
        # Fit to the label's current size, keeping aspect ratio.
        avail_w = max(self.view.winfo_width(), 320)
        avail_h = max(self.view.winfo_height(), 240)
        h, w = image.shape[:2]
        scale = min(avail_w / w, avail_h / h, 1.0)
        if scale < 1.0:
            image = cv2.resize(image, (int(w * scale), int(h * scale)))
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.photo = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.view.config(image=self.photo)

    def close(self) -> None:
        if self.camera is not None:
            self.camera.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("960x640")
    CameraGUI(root)
    root.mainloop()
