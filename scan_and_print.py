from __future__ import annotations
import os
import sys
import platform
import tempfile
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
from dataclasses import dataclass

# UI
import tkinter as tk
from tkinter import messagebox

# Imaging
from PIL import Image, ImageDraw, ImageFont

# Windows printing
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    try:
        import win32print
        import win32ui
        from PIL import ImageWin
    except Exception:
        win32print = None
        win32ui = None
        ImageWin = None

# ---------------------- Configuration ---------------------- #
LABEL_W_IN = 3.5
LABEL_H_IN = 1.125
LABEL_DPI = 300
PRINTER_HINT: str | None = "DYMO LabelWriter 450 Turbo"

PRIMARY_FONT_CANDIDATES = [
    "Arial.ttf", "Arial Unicode.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"
]
SECONDARY_FONT_CANDIDATES = [
    "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"
]

TIME_FMT = "%Y-%m-%d %H:%M:%S"
TZ_NAME: str | None = None
MARGIN_PX = 20

# ---------------------- Helpers ---------------------- #

def local_now():
    if TZ_NAME:
        tz = ZoneInfo(TZ_NAME)
        return datetime.now(tz)
    return datetime.now()

def load_font(candidates, size):
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue
    return ImageFont.load_default()

@dataclass
class LabelLayout:
    width_px: int
    height_px: int
    number_font: ImageFont.FreeTypeFont
    time_font: ImageFont.FreeTypeFont

def make_layout() -> LabelLayout:
    w = int(round(LABEL_W_IN * LABEL_DPI))
    h = int(round(LABEL_H_IN * LABEL_DPI))

    number_size = max(16, int(h * 0.55))  # big top line
    time_size = max(12, int(h * 0.22))    # smaller bottom line

    number_font = load_font(PRIMARY_FONT_CANDIDATES, number_size)
    time_font = load_font(SECONDARY_FONT_CANDIDATES, time_size)

    return LabelLayout(w, h, number_font, time_font)

def render_label(scanned_number: str, when: datetime, layout: LabelLayout) -> Image.Image:
    img = Image.new("1", (layout.width_px, layout.height_px), 1)  # 1-bit B/W
    draw = ImageDraw.Draw(img)

    ts = when.strftime(TIME_FMT)

    num_w, num_h = draw.textbbox((0, 0), scanned_number, font=layout.number_font)[2:]
    time_w, time_h = draw.textbbox((0, 0), ts, font=layout.time_font)[2:]

    total_h = num_h + time_h + int(layout.height_px * 0.08)
    y0 = max(MARGIN_PX, (layout.height_px - total_h) // 2)

    x_num = max(MARGIN_PX, (layout.width_px - num_w) // 2)
    x_time = max(MARGIN_PX, (layout.width_px - time_w) // 2)

    draw.text((x_num, y0), scanned_number, font=layout.number_font, fill=0)
    draw.text((x_time, y0 + num_h + int(layout.height_px * 0.08)), ts, font=layout.time_font, fill=0)

    return img

# ---------------------- Printing ---------------------- #

def find_printer_windows(hint: str | None) -> str | None:
    if not win32print:
        return None
    try:
        printers = win32print.EnumPrinters(2)  # PRINTER_ENUM_LOCAL
        names = [p[2] for p in printers]
        if hint:
            hint_lower = hint.lower()
            for name in names:
                if hint_lower in name.lower():
                    return name
        return win32print.GetDefaultPrinter()
    except Exception:
        return None

def print_image_windows(img: Image.Image, printer_name: str | None) -> None:
    if not (win32print and win32ui and ImageWin):
        raise RuntimeError("pywin32 is required on Windows. Install with: pip install pywin32")

    if not printer_name:
        printer_name = find_printer_windows(PRINTER_HINT)
    if not printer_name:
        raise RuntimeError("No printer found. Install your DYMO driver or set PRINTER_HINT explicitly.")

    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)

    # Rotate for DYMO orientation
    img = img.convert("RGB").rotate(90, expand=True)
    img_w, img_h = img.size

    printable_w = hDC.GetDeviceCaps(8)   # HORZRES
    printable_h = hDC.GetDeviceCaps(10)  # VERTRES
    offset_x = hDC.GetDeviceCaps(112)    # PHYSICALOFFSETX
    offset_y = hDC.GetDeviceCaps(113)    # PHYSICALOFFSETY

    ratio = printable_h / img_h
    scaled_w, scaled_h = int(img_w * ratio), int(img_h * ratio)

    SHIFT_RIGHT = 30  # adjust this value to move right/left
    x0 = offset_x + (printable_w - scaled_w) // 2 + SHIFT_RIGHT
    y0 = offset_y
    x1, y1 = x0 + scaled_w, y0 + scaled_h

    try:
        hDC.StartDoc("Barcode Label")
        hDC.StartPage()
        dib = ImageWin.Dib(img)
        dib.draw(hDC.GetHandleOutput(), (x0, y0, x1, y1))
        hDC.EndPage()
        hDC.EndDoc()
    finally:
        hDC.DeleteDC()

def find_printer_posix(hint: str | None) -> str | None:
    try:
        out = subprocess.check_output(["lpstat", "-p"], text=True)
        candidates = []
        for line in out.splitlines():
            if line.startswith("printer "):
                name = line.split()[1]
                candidates.append(name)
        if hint:
            hint_lower = hint.lower()
            for name in candidates:
                if hint_lower in name.lower():
                    return name
        if len(candidates) == 1:
            return candidates[0]
        return None
    except Exception:
        return None

def print_image_posix(img: Image.Image, printer_name: str | None) -> None:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name
        img.save(tmp_path, "PNG")
    try:
        cmd = ["lp"]
        if printer_name:
            cmd += ["-d", printer_name]
        cmd.append(tmp_path)
        subprocess.check_call(cmd)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

def print_label(img: Image.Image, printer_hint: str | None = PRINTER_HINT):
    if IS_WINDOWS:
        pn = find_printer_windows(printer_hint)
        print_image_windows(img, pn)
    else:
        pn = find_printer_posix(printer_hint)
        print_image_posix(img, pn)

# ---------------------- App ---------------------- #

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Barcode → Label")
        self.geometry("520x220")
        self.resizable(False, False)

        self.layout = make_layout()

        self.lbl = tk.Label(self, text="Scan a barcode (then Enter)", font=("Segoe UI", 14))
        self.lbl.pack(pady=(20, 6))

        self.entry = tk.Entry(self, font=("Consolas", 18))
        self.entry.pack(fill=tk.X, padx=20, pady=6)
        self.entry.focus_set()

        self.print_var = tk.StringVar(value=f"Printer hint: {PRINTER_HINT or 'None'} | Label: {LABEL_W_IN}\"×{LABEL_H_IN}\" @ {LABEL_DPI} dpi")
        self.meta = tk.Label(self, textvariable=self.print_var, font=("Segoe UI", 9))
        self.meta.pack(pady=(0, 10))

        self.status = tk.Label(self, text="Ready", font=("Segoe UI", 10))
        self.status.pack()

        self.bind("<Return>", self.on_enter)

    def on_enter(self, event=None):
        raw = self.entry.get().strip()
        if not raw:
            self.flash_status("Nothing scanned.")
            return
        try:
            ts = local_now()
            img = render_label(raw, ts, self.layout)

            # Save debug PNG
            debug_path = os.path.join(os.getcwd(), f"label_{ts.strftime('%Y%m%d_%H%M%S')}.png")
            img.save(debug_path, "PNG")
            print(f"Saved debug label to {debug_path}")

            # Print
            print_label(img, PRINTER_HINT)
            self.flash_status(f"Printed: {raw} @ {ts.strftime(TIME_FMT)}")

        except Exception as e:
            messagebox.showerror("Print failed", str(e))
            self.flash_status("Print failed. See error.")
        finally:
            self.entry.delete(0, tk.END)

    def flash_status(self, msg: str):
        self.status.config(text=msg)
        self.after(3500, lambda: self.status.config(text="Ready"))

if __name__ == "__main__":
    app = App()
    app.mainloop()
