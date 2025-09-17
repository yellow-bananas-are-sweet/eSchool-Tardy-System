import sys
import os
import csv
import datetime
import openpyxl
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage, QFont
from PyQt6.QtCore import Qt
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import subprocess

CSV_PATH = "CyWoods-Students.csv"
LOG_PATH = "scan_log.xlsx"

# Load students
students = {}
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 3:
            name = row[0].strip()
            grade = row[1].strip()
            sid = row[2].strip()
            students[sid] = {"name": name, "grade": grade}

# Setup log file
if not os.path.exists(LOG_PATH):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Logs"
    ws.append(["Timestamp", "ID", "Name", "Grade"])
    wb.save(LOG_PATH)

# =========================
# Label generation (for printing)
# =========================
def generate_label(student, timestamp):
    """Create a label image with reduced spacing and uniform font size"""
    width, height = 800, 400
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("Merriweather-Regular.ttf", 128)
    except OSError:
        font = ImageFont.load_default()

    lines = [
        student["name"],
        f"Grade: {student['grade']} | ID: {student['id']}",
        timestamp
    ]

    # Calculate total height for vertical centering
    line_heights = [draw.textsize(line, font=font)[1] for line in lines]
    spacing = 15
    total_height = sum(line_heights) + spacing * (len(lines) - 1)
    y = (height - total_height) // 2

    # Draw each line centered
    for line in lines:
        text_w, text_h = draw.textsize(line, font=font)
        x = (width - text_w) // 2
        draw.text((x, y), line, font=font, fill="black")
        y += text_h + spacing

    # Rounded corners
    radius = 30
    mask = Image.new('L', (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=255)
    img.putalpha(mask)

    return img

# =========================
# Main app window
# =========================
class LabelPrinterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Label Printer")
        self.setGeometry(300, 200, 900, 600)

        layout = QVBoxLayout()

        # Instruction
        self.info_label = QLabel("Scan Student ID or Type and Press Enter")
        self.info_label.setFont(QFont("Segoe UI", 18))
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setContentsMargins(0, 5, 0, 5)
        layout.addWidget(self.info_label)

        # Input box (width matches preview)
        self.preview_width = 820
        self.input_box = QLineEdit()
        self.input_box.setFont(QFont("Segoe UI", 18))
        self.input_box.setPlaceholderText("Scan or enter ID...")
        self.input_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_box.setFixedHeight(50)
        self.input_box.setFixedWidth(self.preview_width)
        self.input_box.setStyleSheet("""
            QLineEdit {
                border: 2px solid #555;
                border-radius: 15px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.input_box, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.input_box.returnPressed.connect(self.handle_scan)

        # Preview area
        self.preview_label = QLabel("Tardy Pass Preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(self.preview_width, 420)
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                border: 3px dashed #555;
                border-radius: 20px;
                background-color: #f0f0f0;
                font-size: 24px;
                color: #555;
            }}
        """)
        layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Print button
        self.print_button = QPushButton("Print Label")
        self.print_button.setFont(QFont("Segoe UI", 16))
        self.print_button.setStyleSheet("""
            QPushButton {
                border: 2px solid #555;
                border-radius: 15px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.print_button.clicked.connect(self.handle_scan)
        layout.addWidget(self.print_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        self.last_img = None
        self.input_box.setFocus()

    def handle_scan(self):
        sid = self.input_box.text().strip()
        if not sid:
            return

        if sid not in students:
            QMessageBox.warning(self, "Error", f"No student found for ID: {sid}")
            self.input_box.clear()
            return

        student = students[sid]
        student["id"] = sid

        # Timestamps
        timestamp_log = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_label = datetime.datetime.now().strftime("%b %d, %Y")

        # Generate label (printing)
        img = generate_label(student, timestamp_label)
        self.last_img = img

        # Convert PIL → Qt pixmap for preview
        data = io.BytesIO()
        img.save(data, format="PNG")
        qimg = QImage.fromData(data.getvalue())
        pixmap = QPixmap.fromImage(qimg).scaled(
            self.preview_label.width(), self.preview_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(pixmap)

        # Save to Excel log
        wb = openpyxl.load_workbook(LOG_PATH)
        ws = wb.active
        ws.append([timestamp_log, sid, student["name"], student["grade"]])
        wb.save(LOG_PATH)

        # Save last label as PNG (for printing)
        img.save("last_label.png")

        # Auto print (Windows example)
        try:
            if sys.platform == "win32":
                subprocess.run(["mspaint", "/pt", "last_label.png"], check=True)
        except Exception as e:
            print(f"Printing error: {e}")

        self.input_box.clear()
        self.input_box.setFocus()

# =========================
# Run app
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelPrinterApp()
    window.show()
    sys.exit(app.exec())
