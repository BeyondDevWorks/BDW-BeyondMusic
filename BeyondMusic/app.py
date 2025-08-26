# Copyright 2025 Tobias Polzer & Beyond Development

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# ----------------------------

# app.py
import sys
import os
import json
import random
import ctypes
from pathlib import Path
from io import BytesIO
import webbrowser
import requests  # musst du in requirements aufnehmen
from packaging import version

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QHBoxLayout, QVBoxLayout, QFileDialog, QSlider,
    QMessageBox, QSizePolicy, QFrame, QTabWidget, QLineEdit, QStyle, 
    QTabBar, QProgressBar, QComboBox, QStyleOptionSlider, QScrollArea, QGridLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal, QPropertyAnimation, QVariantAnimation, QUrl
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont, QFontMetrics, QPainterPath, QBrush
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# import vlc
def get_root_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(".")

# 1. Vor dem Import von vlc Umgebungsvariablen setzen
root = get_root_path()
vlc_path = os.path.join(root, "vlc")
vlc_plugin_path = os.path.join(vlc_path, "plugins")

os.environ["VLC_PLUGIN_PATH"] = vlc_plugin_path
os.environ['PATH'] = vlc_path + os.pathsep + os.environ.get('PATH', '')

# 2. vlc importieren (erst jetzt)
import vlc

# 3. VLC Instanz erzeugen
try:
    vlc_instance = vlc.Instance()
    vlc_player = vlc_instance.media_player_new()
    print("VLC Init erfolgreich")
except Exception as e:
    print(f"VLC Init Fehler: {e}")
    sys.exit(1)

# Optional mutagen
try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3, APIC
    MUTAGEN_AVAILABLE = True
except Exception:
    MUTAGEN_AVAILABLE = False

APP_NAME = "BeyondApp"
CONFIG_FILENAME = "player_settings.json"

if sys.platform == "win32":
    base_dir = os.getenv("APPDATA")
else:
    base_dir = os.path.expanduser("~/.config")  # Linux/macOS Standardpfad

APPDATA_DIR = os.path.join(base_dir, APP_NAME)
os.makedirs(APPDATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(APPDATA_DIR, CONFIG_FILENAME)
print("Config wird gespeichert unter:", CONFIG_PATH)

SUPPORTED_FORMATS = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac")
APP_VERSION = "0.1.45"
FORCE_UPDATE_CHECK = False  # Für Development True setzen
GITHUB_REPO = "BeyondDevWorks/BDW-BeyondMusic"  # GitHub User/Repo

DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # für neuere Windows-Versionen

def set_dark_titlebar(hwnd, enabled=True):
    # Windows API Funktion DwmSetWindowAttribute
    value = ctypes.c_int(1 if enabled else 0)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))


# --------- Embedded SVG icons (simple, monochrome) ----------
SVG_PLAY = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M187.2 100.9C174.8 94.1 159.8 94.4 147.6 101.6C135.4 108.8 128 121.9 128 136L128 504C128 518.1 135.5 531.2 147.6 538.4C159.7 545.6 174.8 545.9 187.2 539.1L523.2 355.1C536 348.1 544 334.6 544 320C544 305.4 536 291.9 523.2 284.9L187.2 100.9z"/></svg>"""
SVG_PAUSE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M176 96C149.5 96 128 117.5 128 144L128 496C128 522.5 149.5 544 176 544L240 544C266.5 544 288 522.5 288 496L288 144C288 117.5 266.5 96 240 96L176 96zM400 96C373.5 96 352 117.5 352 144L352 496C352 522.5 373.5 544 400 544L464 544C490.5 544 512 522.5 512 496L512 144C512 117.5 490.5 96 464 96L400 96z"/></svg>"""
SVG_PREV = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M491 100.8C478.1 93.8 462.3 94.5 450 102.6L192 272.1L192 128C192 110.3 177.7 96 160 96C142.3 96 128 110.3 128 128L128 512C128 529.7 142.3 544 160 544C177.7 544 192 529.7 192 512L192 367.9L450 537.5C462.3 545.6 478 546.3 491 539.3C504 532.3 512 518.8 512 504.1L512 136.1C512 121.4 503.9 107.9 491 100.9z"/></svg>"""
SVG_NEXT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M149 100.8C161.9 93.8 177.7 94.5 190 102.6L448 272.1L448 128C448 110.3 462.3 96 480 96C497.7 96 512 110.3 512 128L512 512C512 529.7 497.7 544 480 544C462.3 544 448 529.7 448 512L448 367.9L190 537.5C177.7 545.6 162 546.3 149 539.3C136 532.3 128 518.7 128 504L128 136C128 121.3 136.1 107.8 149 100.8z"/></svg>"""
SVG_SHUFFLE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M467.8 98.4C479.8 93.4 493.5 96.2 502.7 105.3L566.7 169.3C572.7 175.3 576.1 183.4 576.1 191.9C576.1 200.4 572.7 208.5 566.7 214.5L502.7 278.5C493.5 287.7 479.8 290.4 467.8 285.4C455.8 280.4 448 268.9 448 256L448 224L416 224C405.9 224 396.4 228.7 390.4 236.8L358 280L318 226.7L339.2 198.4C357.3 174.2 385.8 160 416 160L448 160L448 128C448 115.1 455.8 103.4 467.8 98.4zM218 360L258 413.3L236.8 441.6C218.7 465.8 190.2 480 160 480L96 480C78.3 480 64 465.7 64 448C64 430.3 78.3 416 96 416L160 416C170.1 416 179.6 411.3 185.6 403.2L218 360zM502.6 534.6C493.4 543.8 479.7 546.5 467.7 541.5C455.7 536.5 448 524.9 448 512L448 480L416 480C385.8 480 357.3 465.8 339.2 441.6L185.6 236.8C179.6 228.7 170.1 224 160 224L96 224C78.3 224 64 209.7 64 192C64 174.3 78.3 160 96 160L160 160C190.2 160 218.7 174.2 236.8 198.4L390.4 403.2C396.4 411.3 405.9 416 416 416L448 416L448 384C448 371.1 455.8 359.4 467.8 354.4C479.8 349.4 493.5 352.2 502.7 361.3L566.7 425.3C572.7 431.3 576.1 439.4 576.1 447.9C576.1 456.4 572.7 464.5 566.7 470.5L502.7 534.5z"/></svg>"""
SVG_REPEAT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M534.6 182.6C547.1 170.1 547.1 149.8 534.6 137.3L470.6 73.3C461.4 64.1 447.7 61.4 435.7 66.4C423.7 71.4 416 83.1 416 96L416 128L256 128C150 128 64 214 64 320C64 337.7 78.3 352 96 352C113.7 352 128 337.7 128 320C128 249.3 185.3 192 256 192L416 192L416 224C416 236.9 423.8 248.6 435.8 253.6C447.8 258.6 461.5 255.8 470.7 246.7L534.7 182.7zM105.4 457.4C92.9 469.9 92.9 490.2 105.4 502.7L169.4 566.7C178.6 575.9 192.3 578.6 204.3 573.6C216.3 568.6 224 556.9 224 544L224 512L384 512C490 512 576 426 576 320C576 302.3 561.7 288 544 288C526.3 288 512 302.3 512 320C512 390.7 454.7 448 384 448L224 448L224 416C224 403.1 216.2 391.4 204.2 386.4C192.2 381.4 178.5 384.2 169.3 393.3L105.3 457.3z"/></svg>"""
SVG_DELETE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M232.7 69.9L224 96L128 96C110.3 96 96 110.3 96 128C96 145.7 110.3 160 128 160L512 160C529.7 160 544 145.7 544 128C544 110.3 529.7 96 512 96L416 96L407.3 69.9C402.9 56.8 390.7 48 376.9 48L263.1 48C249.3 48 237.1 56.8 232.7 69.9zM512 208L128 208L149.1 531.1C150.7 556.4 171.7 576 197 576L443 576C468.3 576 489.3 556.4 490.9 531.1L512 208z"/></svg>"""
SVG_VOLUME = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M533.6 96.5C523.3 88.1 508.2 89.7 499.8 100C491.4 110.3 493 125.4 503.3 133.8C557.5 177.8 592 244.8 592 320C592 395.2 557.5 462.2 503.3 506.3C493 514.7 491.5 529.8 499.8 540.1C508.1 550.4 523.3 551.9 533.6 543.6C598.5 490.7 640 410.2 640 320C640 229.8 598.5 149.2 533.6 96.5zM473.1 171C462.8 162.6 447.7 164.2 439.3 174.5C430.9 184.8 432.5 199.9 442.8 208.3C475.3 234.7 496 274.9 496 320C496 365.1 475.3 405.3 442.8 431.8C432.5 440.2 431 455.3 439.3 465.6C447.6 475.9 462.8 477.4 473.1 469.1C516.3 433.9 544 380.2 544 320.1C544 260 516.3 206.3 473.1 171.1zM412.6 245.5C402.3 237.1 387.2 238.7 378.8 249C370.4 259.3 372 274.4 382.3 282.8C393.1 291.6 400 305 400 320C400 335 393.1 348.4 382.3 357.3C372 365.7 370.5 380.8 378.8 391.1C387.1 401.4 402.3 402.9 412.6 394.6C434.1 376.9 448 350.1 448 320C448 289.9 434.1 263.1 412.6 245.5zM80 416L128 416L262.1 535.2C268.5 540.9 276.7 544 285.2 544C304.4 544 320 528.4 320 509.2L320 130.8C320 111.6 304.4 96 285.2 96C276.7 96 268.5 99.1 262.1 104.8L128 224L80 224C53.5 224 32 245.5 32 272L32 368C32 394.5 53.5 416 80 416z"/></svg>"""
SVG_REMOVEALL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M232.7 69.9L224 96L128 96C110.3 96 96 110.3 96 128C96 145.7 110.3 160 128 160L512 160C529.7 160 544 145.7 544 128C544 110.3 529.7 96 512 96L416 96L407.3 69.9C402.9 56.8 390.7 48 376.9 48L263.1 48C249.3 48 237.1 56.8 232.7 69.9zM512 208L128 208L149.1 531.1C150.7 556.4 171.7 576 197 576L443 576C468.3 576 489.3 556.4 490.9 531.1L512 208z"/></svg>"""
SVG_STOPALL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#FFFFFF" d="M320 576C461.4 576 576 461.4 576 320C576 178.6 461.4 64 320 64C178.6 64 64 178.6 64 320C64 461.4 178.6 576 320 576zM256 224L384 224C401.7 224 416 238.3 416 256L416 384C416 401.7 401.7 416 384 416L256 416C238.3 416 224 401.7 224 384L224 256C224 238.3 238.3 224 256 224z"/></svg>"""
SVG_UPDATEBTN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#63E6BE" d="M384 64C366.3 64 352 78.3 352 96C352 113.7 366.3 128 384 128L466.7 128L265.3 329.4C252.8 341.9 252.8 362.2 265.3 374.7C277.8 387.2 298.1 387.2 310.6 374.7L512 173.3L512 256C512 273.7 526.3 288 544 288C561.7 288 576 273.7 576 256L576 96C576 78.3 561.7 64 544 64L384 64zM144 160C99.8 160 64 195.8 64 240L64 496C64 540.2 99.8 576 144 576L400 576C444.2 576 480 540.2 480 496L480 416C480 398.3 465.7 384 448 384C430.3 384 416 398.3 416 416L416 496C416 504.8 408.8 512 400 512L144 512C135.2 512 128 504.8 128 496L128 240C128 231.2 135.2 224 144 224L224 224C241.7 224 256 209.7 256 192C256 174.3 241.7 160 224 160L144 160z"/></svg>"""


def svg_to_icon(svg_str: str, size: int = 64, color: str = "#FFFFFF") -> QIcon:
    """Render embedded SVG string to a QIcon of given size. color currently assumed baked in SVG."""
    # Use QSvgRenderer to render into QPixmap
    renderer = QSvgRenderer(bytearray(svg_str, encoding="utf-8"))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)



def make_default_cover(size=256, text="Cover"):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # Hintergrundrechteck
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2563eb"))
    p.drawRoundedRect(10, 10, size - 20, size - 20, 8, 8)

    # Text
    f = QFont("Segoe UI", max(10, size // 12))
    f.setBold(True)
    p.setFont(f)

    fm = QFontMetrics(f)
    elided_text = fm.elidedText(text, Qt.ElideRight, size - 20)  # Text passt in Rechteck

    p.setPen(QColor("#ffffff"))
    p.drawText(pix.rect(), Qt.AlignCenter, elided_text)

    p.end()
    return pix

def get_latest_version():
    """Prüft das neueste Release auf GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("tag_name", APP_VERSION)  # z. B. "v0.1.46"
    except Exception as e:
        print("Update-Check fehlgeschlagen:", e)
    return APP_VERSION  # fallback: aktuelle Version

def is_update_available():
    latest = get_latest_version().lstrip("v")  # 'v0.1.46' → '0.1.46'
    return FORCE_UPDATE_CHECK or version.parse(latest) > version.parse(APP_VERSION)


# ---------------- SplashScreen (Starting Screen) ----------------

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # App Titel
        self.title = QLabel("Beyond Musik wird geladen…")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: #3B82F6; font-size: 20px; font-weight: bold;")

        # Status Text
        self.status = QLabel("Starte Initialisierung")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #E5E7EB; font-size: 14px;")

        # Ladebalken
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(15)
        self.progress.setStyleSheet("""
            QProgressBar { background-color: #1F2937; border-radius: 7px; }
            QProgressBar::chunk { background-color: #3B82F6; border-radius: 7px; }
        """)

        layout.addWidget(self.title)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)

        # Hintergrund
        self.bg_pix = QPixmap(self.size())
        self.bg_pix.fill(Qt.transparent)
        painter = QPainter(self.bg_pix)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 25, 25)
        painter.fillPath(path, QColor("#111827"))
        painter.end()

         # --- SOUND ABSPIELEN ---
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        root_dir = get_root_path()
        soundStart_path = os.path.join(root_dir, "assets", "start.mp3")
        sound_path = Path(soundStart_path).resolve()  # kleine MP3/WAV Datei ins Projekt legen
        self.player.setSource(QUrl.fromLocalFile(str(sound_path)))
        self.audio_output.setVolume(0.8)
        #self.player.play()

        # Statusmeldungen
        self.status_map = {
            10: "Prüfe auf Updates",
            30: "Initialisiere Module",
            50: "Verbinde mit Servern",
            65: "Synchronisiere Einstellungen",
            75: "Cache wird geleert",
            85: "Starte Audio Engine",
            95: "Lade Benutzeroberfläche",
        }

        # Punkte Animation (Fake Checks)
        self.dots = ""
        self.dot_timer = QTimer()
        self.dot_timer.timeout.connect(self.update_dots)
        self.dot_timer.start(500)

        # Fortschritt
        self.counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)

        # Animationsobjekt behalten
        self.fade_anim = None

    def update_dots(self):
        self.dots += "."
        if len(self.dots) > 3:
            self.dots = ""
        self.status.setText(self.status.text().split("…")[0] + self.dots)

    def update_progress(self):
        self.counter += 2
        self.progress.setValue(self.counter)

        for k in sorted(self.status_map.keys()):
            if self.counter >= k:
                self.status.setText(self.status_map[k] + self.dots)

        if self.counter >= 101:
            self.timer.stop()
            self.dot_timer.stop()
            self.fade_out()

    def fade_out(self):
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(1000)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(lambda: self.finish_splash(vlc_player))
        self.player.play()
        self.fade_anim.start()

    def finish_splash(self, vlc_player):
        self.main_window = OverseerPlayer(vlc_player)  # vlc_player übergeben
        self.main_window.show()
        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.bg_pix)

# ---------------- Playlist Item Widget ----------------
class PlaylistItemWidget(QWidget):
    play_requested = Signal()
    delete_requested = Signal()

    def __init__(self, title: str, cover_pix: QPixmap | None = None, parent=None):
        super().__init__(parent)
        self._is_playing = False
        self.setFixedHeight(64)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 6, 8, 6)
        self.layout.setSpacing(8)

        # cover
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(52, 52)
        if cover_pix:
            self.cover_label.setPixmap(cover_pix.scaled(52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cover_label.setPixmap(make_default_cover(52))
        self.layout.addWidget(self.cover_label)

        # title text
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 13px; color: #dfefff;")
        self.title_label.setWordWrap(False)
        self.layout.addWidget(self.title_label, stretch=1)

        # play button (hidden until hover or active)
        self.btn_play = QPushButton()
        self.btn_play.setIcon(svg_to_icon(SVG_PLAY, size=18))
        self.btn_play.setFixedSize(36, 36)
        self.btn_play.setVisible(False)
        self.btn_play.setCursor(Qt.PointingHandCursor)
        self.btn_play.setStyleSheet(self._button_style(inactive=True))
        self.btn_play.clicked.connect(self.play_requested.emit)
        self.layout.addWidget(self.btn_play)

        # delete button (hidden until hover)
        self.btn_delete = QPushButton()
        self.btn_delete.setIcon(svg_to_icon(SVG_DELETE, size=16))
        self.btn_delete.setFixedSize(36, 36)
        self.btn_delete.setVisible(False)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet(self._button_style(inactive=True))
        self.btn_delete.clicked.connect(self.delete_requested.emit)
        self.layout.addWidget(self.btn_delete)

        # initial background
        self.setStyleSheet("background-color: rgba(255,255,255,0.02); border-radius:8px;")

    def enterEvent(self, event):
        # show controls on hover
        self.btn_play.setVisible(True)
        self.btn_delete.setVisible(True)
        # hover blending over base state
        if self._is_playing:
            self.setStyleSheet("background-color: rgba(34,197,94,0.25); border-radius:8px;")
        else:
            self.setStyleSheet("background-color: rgba(255,255,255,0.04); border-radius:8px;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        # hide hover controls (but keep play visible if playing)
        self.btn_delete.setVisible(False)
        if self._is_playing:
            self.btn_play.setVisible(True)
            self.setStyleSheet("background-color: rgba(34,197,94,0.15); border-radius:8px;")
        else:
            self.btn_play.setVisible(False)
            self.setStyleSheet("background-color: rgba(255,255,255,0.02); border-radius:8px;")
        super().leaveEvent(event)

    def set_playing(self, playing: bool):
        self._is_playing = playing
        if playing:
            self.btn_play.setVisible(True)
            self.btn_play.setIcon(svg_to_icon(SVG_PAUSE, size=18))
            self.btn_play.setStyleSheet(self._button_style(active=True))
            self.setStyleSheet("background-color: rgba(34,197,94,0.15); border-radius:8px;")
        else:
            self.btn_play.setIcon(svg_to_icon(SVG_PLAY, size=18))
            self.btn_play.setStyleSheet(self._button_style(inactive=True))
            self.btn_play.setVisible(False)
            self.setStyleSheet("background-color: rgba(255,255,255,0.02); border-radius:8px;")

    @staticmethod
    def _button_style(active=False, inactive=False):
        if active:
            return "QPushButton{background:#22c55e;color:white;border-radius:8px;}QPushButton:hover{background:#16a34a}"
        else:
            return "QPushButton{background:transparent;color:#cfe8ff;border-radius:8px;}QPushButton:hover{background:rgba(255,255,255,0.06)}"



class InfoCard(QFrame):
    def __init__(self, title, value):
        super().__init__()
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            QFrame {
                background-color: #0a1a33; /* dunkles Blau */
                border: 1px solid #1f3b66;
                border-radius: 6px;
                padding: 8px;
            }
            QLabel {
                font-size: 14px;
                color: #5dade2; /* helleres Blau */
            }
            QLabel.title {
                font-weight: bold;
                font-size: 15px;
                color: #85c1e9;
            }
        """)

        layout = QVBoxLayout(self)
        title_label = QLabel(title)
        title_label.setObjectName("title")
        value_label = QLabel(value)
        value_label.setObjectName("value")
        layout.addWidget(title_label)
        layout.addWidget(value_label)

    def enterEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #123057; /* etwas helleres Blau beim Hover */
                border: 1px solid #2e548c;
                border-radius: 6px;
                padding: 8px;
            }
            QLabel {
                font-size: 14px;
                color: #5dade2;
            }
            QLabel.title {
                font-weight: bold;
                font-size: 15px;
                color: #85c1e9;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #0a1a33;
                border: 1px solid #1f3b66;
                border-radius: 6px;
                padding: 8px;
            }
            QLabel {
                font-size: 14px;
                color: #5dade2;
            }
            QLabel.title {
                font-weight: bold;
                font-size: 15px;
                color: #85c1e9;
            }
        """)
        super().leaveEvent(event)

class InfoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.build()

    def build(self):
        w_layout = QVBoxLayout(self)

        # Header
        header = QLabel("Informationen")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #85c1e9;
                background-color: #0a1a33;
                padding: 10px;
                border-radius: 6px;
            }
        """)
        w_layout.addWidget(header)

        # Karten
        w_layout.addWidget(InfoCard("App-Version", "#-6MVXZPR2A9OA8XKAPA8T-v.0.1.45"))
        w_layout.addWidget(InfoCard("Entwickler", "BeyondDevWorks & Tobias Polzer"))
        w_layout.addWidget(InfoCard("Lizenz", "MIT"))
        w_layout.addWidget(InfoCard("Letztes Update", "2025-08-25"))
        w_layout.addWidget(InfoCard("Support", "https://beyonddevworks.github.io/BDW-Site/#contact"))

        w_layout.addStretch()

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            if self.orientation() == Qt.Horizontal:
                value = QStyle.sliderValueFromPosition(
                    self.minimum(),
                    self.maximum(),
                    pos.x(),
                    self.width()
                )
            else:
                value = QStyle.sliderValueFromPosition(
                    self.minimum(),
                    self.maximum(),
                    self.height() - pos.y(),
                    self.height()
                )
            self.setValue(value)
            event.accept()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        # Erst Standard-Slider mit Stylesheet malen
        super().paintEvent(event)

        # Danach eigene Ticks
        tick_interval = self.tickInterval()
        if tick_interval <= 0:   # Schutz gegen Division durch 0
            return

        steps = (self.maximum() - self.minimum()) // tick_interval
        if steps <= 0:
            return

        painter = QPainter(self)
        painter.setPen(QColor(200, 200, 200, 160))  # helle graue Striche

        if self.orientation() == Qt.Horizontal:
            spacing = self.width() / steps
            y = self.height() // 2
            for i in range(steps + 1):
                x = int(i * spacing)
                painter.drawLine(x, y - 4, x, y + 4)
        else:
            spacing = self.height() / steps
            x = self.width() // 2
            for i in range(steps + 1):
                y = int(i * spacing)
                painter.drawLine(x - 4, y, x + 4, y)

        painter.end()



class EqualizerTab(QWidget):
    def __init__(self, player: vlc.MediaPlayer, parent=None):
        super().__init__(parent)
        self.player = player
        self.eq = vlc.AudioEqualizer()
        self.player.set_equalizer(self.eq)

        main_layout = QVBoxLayout(self)

        # Frequenzbänder definieren
        self.bands = [
            (0, "60 Hz"),
            (1, "170 Hz"),
            (2, "310 Hz"),
            (3, "600 Hz"),
            (4, "1 kHz"),
            (5, "3 kHz"),
            (6, "6 kHz"),
            (7, "12 kHz"),
            (8, "14 kHz"),
            (9, "16 kHz"),
        ]

        # Presets (Gain-Werte pro Band)
        self.presets = {
            "Neutral":        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "Rock":           [5, 3, 2, 0, -2, 0, 2, 4, 5, 5],
            "Pop":            [-1, 2, 3, 4, 3, 2, 1, 0, -1, -2],
            "Jazz":           [0, 2, 3, 2, 0, 2, 3, 2, 1, 0],
            "Bass Boost":     [8, 6, 4, 2, 0, -2, -4, -6, -6, -6],
            "Treble Boost":   [-4, -2, 0, 2, 4, 6, 8, 10, 10, 10],
            "Vocal Boost":    [-2, -1, 2, 4, 5, 5, 3, 1, 0, -1],
            "Classical":      [0, 0, 2, 3, 2, 0, 1, 2, 3, 3],
            "Dance":          [5, 4, 2, 0, -2, 0, 3, 6, 7, 7],
            "Electronic":     [6, 4, 3, 0, -2, 0, 4, 7, 8, 9],
            "Hip-Hop":        [8, 6, 4, 2, 0, -1, 2, 4, 5, 6],
            "Reggae":         [5, 4, 2, 0, -1, 0, 3, 5, 6, 6],
            "Movie":          [3, 2, 1, 0, 0, 2, 3, 4, 5, 5],
            "Gaming":         [6, 5, 3, 0, -1, 2, 4, 6, 7, 8],
            "Podcast":        [-3, -2, 0, 3, 5, 5, 4, 2, 0, -1],
            "Soft":           [-2, -1, 0, 0, 1, 1, 0, -1, -2, -3],
            "Party":          [7, 5, 3, 0, -1, 1, 4, 6, 7, 8],
            "Treble Cut":     [0, 0, -2, -4, -6, -6, -4, -2, 0, 0],
            "Bass Cut":       [-6, -5, -3, 0, 1, 0, -2, -4, -5, -6],
        }

        # Preset-Auswahl
        self.preset_box = QComboBox()
        self.preset_box.addItems(self.presets.keys())
        self.preset_box.currentTextChanged.connect(self.apply_preset)
        self.preset_box.setStyleSheet("""
        QComboBox {
            background-color: #1e1e1e;
            color: #3b82f6;             /* Text blau */
            border: 1px solid #3b82f6;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 14px;
        }
        QComboBox::drop-down {
            border: none;
            background: #3b82f6;
            width: 24px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 7px solid transparent;
            border-right: 7px solid transparent;
            border-top: 10px solid #3b82f6;   /* Pfeil in Blau */
            margin-right: 4px;
        }
        QComboBox QAbstractItemView {
            background-color: #2a2a2a;
            border: 1px solid #3b82f6;
            selection-background-color: #3b82f6;
            selection-color: white;
            color: #3b82f6;                    /* Items normal blau */
        }
        """)
        main_layout.addWidget(QLabel("Preset auswählen:"))
        main_layout.addWidget(self.preset_box)

        # Slider nebeneinander
        slider_row = QHBoxLayout()
        self.sliders = {}

        for index, label in self.bands:
            band_layout = QVBoxLayout()

            band_label = QLabel(label, alignment=Qt.AlignCenter)

            self.eqslider = ClickableSlider(Qt.Vertical)  # klassischer EQ-Look
            self.eqslider.setRange(-20, 20)       # dB-Bereich
            self.eqslider.setValue(0)
            self.eqslider.setTickPosition(QSlider.TicksBothSides)
            self.eqslider.setTickInterval(5)
            self.eqslider.setStyleSheet("""
            QSlider::groove:vertical {
                width: 6px;
                background: rgba(255,255,255,0.08);
                border-radius: 3px;
            }
            QSlider::handle:vertical {
                background: #3b82f6;
                height: 14px;
                width: 14px;
                border-radius: 7px;
                margin: 0 -4px; /* verschiebt den Knopf ins Groove-Zentrum */
            }
            """)

            self.eqslider.valueChanged.connect(
                lambda value, i=index: self.set_band_gain(i, value)
            )

            band_layout.addWidget(band_label)
            band_layout.addWidget(self.eqslider)

            slider_row.addLayout(band_layout)
            self.sliders[index] = self.eqslider

        main_layout.addLayout(slider_row)
        self.setLayout(main_layout)

    def set_band_gain(self, band_index, gain_value):
        """Setzt den Gain für ein bestimmtes Band"""
        self.eq.set_amp_at_index(float(gain_value), band_index)
        self.player.set_equalizer(self.eq)

        # Automatisch speichern
        if hasattr(self.parent(), "save_settings"):
            self.parent().save_settings()

    def apply_preset(self, preset_name):
        """Preset-Werte auf die Slider anwenden"""
        values = self.presets[preset_name]
        for i, gain in enumerate(values):
            self.sliders[i].blockSignals(True)
            self.sliders[i].setValue(gain)
            self.sliders[i].blockSignals(False)
            self.eq.set_amp_at_index(float(gain), i)

        self.player.set_equalizer(self.eq)

        # Automatisch speichern
        if hasattr(self.parent(), "save_settings"):
            self.parent().save_settings()
    
    def get_current_eq_values(self):
        """Gibt die aktuellen Slider-Werte als Liste zurück"""
        return [self.sliders[i].value() for i in range(len(self.sliders))]

    def set_eq_values(self, values):
        """Setzt Slider auf gespeicherte Werte"""
        for i, gain in enumerate(values):
            self.sliders[i].blockSignals(True)
            self.sliders[i].setValue(gain)
            self.sliders[i].blockSignals(False)
            self.eq.set_amp_at_index(float(gain), i)
        self.player.set_equalizer(self.eq)
    
    def get_current_preset(self):
        """Gibt den aktuell ausgewählten Preset-Namen zurück"""
        return self.preset_box.currentText()

    def set_preset(self, preset_name):
        """Setzt einen Preset-Namen und wendet ihn an"""
        if preset_name in self.presets:
            self.preset_box.setCurrentText(preset_name)
            self.apply_preset(preset_name)


# ---------------- Main Player ----------------
class OverseerPlayer(QMainWindow):
    def __init__(self, vlc_player):
        super().__init__()
        self.player = vlc_player
        self.vlc_instance = vlc.Instance()
        def get_root_path():
            # Wenn als EXE kompiliert
            if getattr(sys, 'frozen', False):
                return os.path.dirname(sys.executable)
            # Normaler Python-Start
            return os.path.dirname(os.path.abspath(__file__))

        root_dir = get_root_path()
        icon_path = os.path.join(root_dir, "assets", "icon.ico")

        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Beyond Music")
        self.resize(1200, 800)

        # Fensterhandle holen (HWND)
        hwnd = self.winId().__int__()

        # Dark Mode für Titelleiste aktivieren
        set_dark_titlebar(hwnd, True)

                # ---------------- Medienstatus ----------------
        self.playlist = []
        self.is_user_seeking = False
        self.current_index = -1           # aktuell gespieltes Playlist-Item
        self.current_media_type = None    # "playlist" oder "stream"
        self.is_playing = False
        self._old_volume = 100            # für Mute/Unmute

        # settings
        self.settings = {"volume": 80, "shuffle": False, "repeat": False, "last_playlist": []}
        self.load_settings()

        # UI build
        self._build_ui()

        # timers
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start()

        # apply settings
        self.volume_slider.setValue(self.settings.get("volume", 80))
        self.player.audio_set_volume(self.volume_slider.value())
        self.shuffle_btn.setChecked(self.settings.get("shuffle", False))
        self.repeat_btn.setChecked(self.settings.get("repeat", False))

        # restore playlist
        if self.settings.get("last_playlist"):
            valid = [p for p in self.settings["last_playlist"] if os.path.exists(p)]
            if valid:
                self.load_playlist(valid)

        self.setAcceptDrops(True)

    def _build_ui(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(12, 12, 12, 12)
        self.setCentralWidget(root)

        latest_version = get_latest_version().lstrip("v")

        # -----------------------------------------------------
        # Top Bar
        # -----------------------------------------------------
        top_row = QHBoxLayout()
        label = QLabel(f"Beyond Music")
        label.setStyleSheet("font-weight:700; font-size:18px; color:#60A5FA;")
        top_row.addWidget(label)

        # Update-Button
        btn_update = QPushButton(f"Update verfügbar! (aktuell: v{APP_VERSION} → neu: v{latest_version})")
        btn_update.setIcon(svg_to_icon(SVG_UPDATEBTN, 20))
        btn_update.setToolTip("Neue Version verfügbar! Jetzt herunterladen")
        btn_update.clicked.connect(lambda: webbrowser.open("https://beyonddevworks.github.io/BDW-Site/#home"))
        btn_update.setVisible(is_update_available())  # nur anzeigen, wenn nötig
        btn_update.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;   /* dunkler Hintergrund */
                border: 2px solid #3b82f6;  /* blaue Umrandung */
                border-radius: 8px;          /* runde Ecken */
                padding: 6px 12px;
                color: #09D62F;              /* helle Schrift */
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.3);   /* hover blau */
                color: #09D62F;
            }
            QPushButton:pressed {
                background-color: #2563eb;   /* dunkleres Blau beim Klick */
            }
        """)
        top_row.addWidget(btn_update)

        top_row.addStretch()

        # Stop all Button
        btn_stop_all = QPushButton()
        btn_stop_all.setIcon(svg_to_icon(SVG_STOPALL, 20))
        btn_stop_all.setToolTip("Stop all playing audios and streams")
        btn_stop_all.clicked.connect(self.stop_all)
        top_row.addWidget(btn_stop_all)

        # Remove all Button
        btn_remove_all = QPushButton()
        btn_remove_all.setIcon(svg_to_icon(SVG_REMOVEALL, 20))
        btn_remove_all.setToolTip("Remove all from playlist")
        btn_remove_all.clicked.connect(self.remove_all)
        top_row.addWidget(btn_remove_all)

        root_layout.addLayout(top_row)

        # Tabs: Playlist / Webradio
        self.tabs = QTabWidget()
        self.tab_playlist = QWidget()
        self.tab_webradio = QWidget()
        self.tab_equalizer = EqualizerTab(self.player, parent=self)  # player ist dein vlc.MediaPlayer
        self.tab_info = InfoTab()
        self.tabs.addTab(self.tab_playlist, "Playlist")
        self.tabs.addTab(self.tab_webradio, "Webradio")
        self.tabs.addTab(self.tab_equalizer, "Equalizer")
        self.tabs.addTab(self.tab_info, "Info")
        root_layout.addWidget(self.tabs, stretch=1)

        # ---------------- EQ ----------------
        if "eq_values" in self.settings:
            self.tab_equalizer.set_eq_values(self.settings["eq_values"])
        if "eq_preset" in self.settings:
            self.tab_equalizer.set_preset(self.settings["eq_preset"])

        # Playlist tab layout
        p_layout = QHBoxLayout(self.tab_playlist)
        self.playlist_widget = QListWidget()
        self.playlist_widget.setSpacing(6)
        self.playlist_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        p_layout.addWidget(self.playlist_widget, stretch=3)

        # right panel with cover/meta
        right_panel = QVBoxLayout()
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(260, 260)
        self.cover_label.setPixmap(make_default_cover(260))
        right_panel.addWidget(self.cover_label, alignment=Qt.AlignCenter)
        self.meta_label = QLabel("Kein Titel geladen")
        self.meta_label.setWordWrap(True)
        right_panel.addWidget(self.meta_label, alignment=Qt.AlignTop)
        right_panel.addStretch()
        p_layout.addLayout(right_panel, stretch=1)

        # ---------------- Webradio Tab ----------------
        w_layout = QVBoxLayout(self.tab_webradio)

        # Suchfeld
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Sender suchen...")
        w_layout.addWidget(self.search_bar)

        # ScrollArea für Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w_layout.addWidget(scroll)
        scroll.setStyleSheet("""
                background: #161b22; 
                border-radius: 8px; 
                padding: 6px; 
                border: 1px solid #1f2937; 
                outline: none; /* Fokus-Rahmen aus */
        """)

        # Container-Widget für Grid
        grid_container = QWidget()
        scroll.setWidget(grid_container)
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        grid_container.setStyleSheet("""
                border: none !important; /* Fokus-Rahmen aus */
        """)

        # Beispiel-Streams
        self.streams = {
            "TECHNOBASE.FM": "https://listener1.aachd.tb-group.fm/tb-hd.aac",
            "HOUSETIME.FM": "https://listener1.aachd.tb-group.fm/ht-hd.aac",
            "HARDBASE.FM": "https://listener1.aachd.tb-group.fm/hb-hd.aac",
            "TRANCEBASE.FM": "https://listener1.aachd.tb-group.fm/trb-hd.aac",
            "CORETIME.FM": "https://listener1.aachd.tb-group.fm/ct-hd.aac",
            "CLUBTIME.FM": "https://listener1.aachd.tb-group.fm/clt-hd.aac",
            "TEATIME.FM": "https://listener1.aachd.tb-group.fm/tt-hd.aac",
            "REPLAY.FM": "https://listener1.aachd.tb-group.fm/rp-hd.aac",
            "Rottal-Radio": "https://rottalpunktradio.stream.laut.fm/rottalpunktradio"
        }

        self._original_streams = list(self.streams.keys())
        self.stream_buttons = {}  # <--- hier wird das Dictionary angelegt
        self.stream_boxes = {}  # Name -> Box Widget

        def add_stream_box(name, row, col):
            widget = QWidget()
            widget.setMinimumSize(200, 120)
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            widget.setStyleSheet("""
                background-color: #161b22;
                border: 1px solid #3b82f6;
                border-radius: 8px;
            """)

            layout = QVBoxLayout(widget)
            layout.setContentsMargins(6, 6, 6, 6)
            layout.setSpacing(4)

            cover = QLabel()
            cover.setPixmap(make_default_cover(48, name[0]))
            cover.setFixedSize(48, 48)
            cover.setAlignment(Qt.AlignCenter)
            layout.addWidget(cover, alignment=Qt.AlignHCenter)
            cover.setStyleSheet("""
                background: transparent;
                border: none !important; /* Fokus-Rahmen aus */
            """)

            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                background: transparent;
                color: #dfefff;
                font-weight: 600;
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                border: none !important; /* Fokus-Rahmen aus */
            """)

            def adjust_font():
                w = label.width()
                # passt die Schrift proportional an die Breite an
                size = max(10, min(20, w // 10))  # min 10px, max 20px
                label.setStyleSheet(f"""
                    background: transparent;
                    color: #dfefff;
                    font-weight: 600;
                    font-size: {size}px;
                    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                    border: none !important; /* Fokus-Rahmen aus */
                """)

            label.resizeEvent = lambda event: adjust_font()
            layout.addWidget(label)

            btn = QPushButton()
            btn.setIcon(svg_to_icon(SVG_PLAY))
            btn.setIconSize(QSize(36, 36))
            btn.setFixedSize(40, 40)
            btn.clicked.connect(lambda checked, n=name: self.toggle_stream(n))
            layout.addWidget(btn, alignment=Qt.AlignHCenter)

            # Beim Abspielen ändern

            self.grid_layout.addWidget(widget, row, col)
            self.stream_boxes[name] = widget  # speichern für Search / Markierung
                # speichern
            self.stream_buttons[name] = btn

        cols = 3
        for index, name in enumerate(self._original_streams):
            row = index // cols
            col = index % cols
            add_stream_box(name, row, col)

        # Suche: Ein-/Ausblenden der Boxen
        def filter_streams(text):
            for name, box in self.stream_boxes.items():
                if text.lower() in name.lower():
                    box.show()
                else:
                    box.hide()

        self.search_bar.textChanged.connect(filter_streams)

        # Suchfeld Styling
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #0A1F44;
                color: #4DA3FF;
                border: 2px solid #1E3A70;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4DA3FF;
                background-color: #0F2A5F;
            }
        """)

        # timeline
        timeline_row = QHBoxLayout()
        self.time_cur = QLabel("00:00")
        self.time_tot = QLabel("00:00")
        self.timeline = ClickableSlider(Qt.Horizontal)
        self.timeline.setRange(0, 1000)
        self.timeline.sliderPressed.connect(self._timeline_pressed)
        self.timeline.sliderReleased.connect(self._timeline_released)
        timeline_row.addWidget(self.time_cur)
        timeline_row.addWidget(self.timeline, stretch=1)
        timeline_row.addWidget(self.time_tot)
        root_layout.addLayout(timeline_row)
        self.timeline.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; }
            QSlider::handle:horizontal { background: #3b82f6; border-radius:7px; margin:-4px 0; }
        """)

        # bottom player bar
        bar = QFrame()
        bar.setFrameShape(QFrame.StyledPanel)
        bar.setFixedHeight(80)  # Höhe der Leiste
        bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 41, 59, 230),  /* leicht transparentes dunkles Blau */
                    stop:1 rgba(17, 24, 39, 230)   /* dunkleres Blau/Grau unten */
                );
                border-radius: 16px;
                border: 1px solid rgba(59, 130, 246, 180); /* sanfter blauer Rand */
            }
        """)

        # Optional: sanfter Schatten für "Floating"-Effekt
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 100))
        bar.setGraphicsEffect(shadow)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(8, 8, 8, 8)

        # small cover + now
        self.small_cover = QLabel()
        self.small_cover.setFixedSize(56, 56)
        self.small_cover.setPixmap(make_default_cover(56))
        bl.addWidget(self.small_cover)
        self.now_label = QLabel("Keine Wiedergabe")
        bl.addWidget(self.now_label, stretch=1)
        self.small_cover.setStyleSheet("""
            background: transparent;
            border-radius: 0px;   /* Hälfte der Größe → rund */
            border: none; 
        """)

        # controls center
        controls = QHBoxLayout()
        controls.setSpacing(12)

        base_btn_style = """
            QPushButton {
                background-color: rgba(255,255,255,0.03);
                border: none;
                color: #e6eef8;
                border-radius: 18px;
                font-size: 16px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.07);
            }
            QPushButton:checked {
                background-color: #22c55e;
                color: white;
            }
        """

        # Shuffle
        self.shuffle_btn = QPushButton()
        self.shuffle_btn.setIcon(svg_to_icon(SVG_SHUFFLE, 18))
        self.shuffle_btn.setFixedSize(40, 40)  # Höhe = Breite → wird rund
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.setCursor(Qt.PointingHandCursor)
        self.shuffle_btn.setToolTip("Shuffle")
        self.shuffle_btn.setStyleSheet(base_btn_style)
        controls.addWidget(self.shuffle_btn)

        # Prev
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(svg_to_icon(SVG_PREV, 18))
        self.prev_btn.setFixedSize(40, 40)  # Höhe = Breite → wird rund
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(base_btn_style)
        self.prev_btn.clicked.connect(self.play_previous)
        controls.addWidget(self.prev_btn)

        # Play/Pause (prominent)
        self.play_btn = QPushButton()
        self.play_btn.setObjectName("play_btn")
        self.play_btn.setCheckable(True)
        self.play_btn.setFixedSize(56, 56)
        self.play_btn.setIcon(svg_to_icon(SVG_PLAY, 24))
        self.play_btn.setToolTip("Play / Pause")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        # style for main play button
        self.play_btn.setStyleSheet("""
            QPushButton#play_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1f6feb, stop:1 #3b82f6);
                color: white;
                border-radius: 28px;
                font-weight: 700;
            }
            QPushButton#play_btn:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563eb, stop:1 #1f6feb); }
        """)
        self.play_btn.clicked.connect(self._on_play_button_toggled)
        controls.addWidget(self.play_btn)

        # Next
        self.next_btn = QPushButton()
        self.next_btn.setIcon(svg_to_icon(SVG_NEXT, 18))
        self.next_btn.setFixedSize(40, 40)  # Höhe = Breite → wird rund
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(base_btn_style)
        self.next_btn.clicked.connect(self.play_next)
        controls.addWidget(self.next_btn)

        # Repeat
        self.repeat_btn = QPushButton()
        self.repeat_btn.setIcon(svg_to_icon(SVG_REPEAT, 18))
        self.repeat_btn.setFixedSize(40, 40)  # Höhe = Breite → wird rund
        self.repeat_btn.setCheckable(True)
        self.repeat_btn.setCursor(Qt.PointingHandCursor)
        self.repeat_btn.setToolTip("Repeat")
        self.repeat_btn.setStyleSheet(base_btn_style)
        controls.addWidget(self.repeat_btn)

        bl.addLayout(controls)

        # volume right
        
        self._old_volume = self.settings["volume"]
        self.settings = {"volume": self._old_volume}

        vol_layout = QHBoxLayout()
        vol_layout.addStretch()
        vol_icon = QPushButton()
        vol_icon.setIcon(svg_to_icon(SVG_VOLUME, 18).pixmap(18, 18))
        vol_icon.clicked.connect(self.vol_mute)
        vol_layout.addWidget(vol_icon)
        self.volume_slider = ClickableSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(160)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; }
            QSlider::handle:horizontal { background: #3b82f6; width: 14px; height: 14px; border-radius:7px; margin:-4px 0; }
        """)
        self.volume_slider.valueChanged.connect(self.set_volume)
        vol_layout.addWidget(self.volume_slider)
        bl.addLayout(vol_layout)
        root_layout.addWidget(bar)

        # menu file open
        men = self.menuBar()
        mfile = men.addMenu("Datei")
        act_open = mfile.addAction("Dateien öffnen...")
        act_open.triggered.connect(self.open_files)
        act_folder = mfile.addAction("Ordner öffnen...")
        act_folder.triggered.connect(self.open_folder)
       
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow { 
                background: #0d1117; 
                color: #cdd9e5; 
                font-family: Segoe UI, sans-serif; 
                font-size: 13px;
            }

            /* Menüleiste */
            QMenuBar {
                background-color: #0d1117;
                color: #cdd9e5;
                padding: 4px;
            }
            QMenuBar::item:selected {
                background: rgba(88,166,255,0.1);
                border-radius: 4px;
            }
            QMenu {
                background-color: #161b22;
                color: #cdd9e5;
                border: 1px solid #30363d;
            }
            QMenu::item:selected {
                background-color: rgba(88,166,255,0.2);
            }

            /* Tabs */
            QTabWidget::pane { 
                border: none; 
            }

            QTabBar::tab { 
                background: #121a29; 
                color: #dfefff; 
                padding: 6px 20px; 
                border-radius: 8px 8px 0 0; 
                margin-right: 8px; 
                left: 7.5%;
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                font-weight: 700;        /* dickere Schrift */
                font-size: 14px;          /* etwas größere Schrift für bessere Lesbarkeit */
                letter-spacing: 0.5px;    /* leichtes Tracking für bessere Erkennbarkeit */
                border: 2px solid #1f2937; 
            }

            QTabBar::tab:selected { 
                background: #1e40af; 
                color: #ffffff; 
                border: 2px solid #3b82f6; 
            }

            QTabBar::tab:hover { 
                background: #3b82f6; 
                color: #ffffff; 
                border: 2px solid #60a5fa; 
            }

            /* Playlist / QListWidget */
            QListWidget { 
                background: #161b22; 
                border-radius: 8px; 
                padding: 6px; 
                border: 1px solid #1f2937; 
                color: #dfefff;
                outline: none; /* Fokus-Rahmen aus */
            }
            QListWidget::item { 
                border-radius: 8px; 
                background: transparent;
            }
            QListWidget::item:selected {
                background: rgba(88,166,255,0.2);
                color: white;
            }

            /* Labels */
            QLabel { 
                color: #cdd9e5; 
            }

            /* Buttons allgemein */
            QPushButton { 
                background: transparent; 
                border: none; 
                color: #58a6ff; 
                font-size: 16px;
            }
            QPushButton:hover { 
                background: rgba(88,166,255,0.1); 
                border-radius: 6px; 
            }
            QPushButton:checked { 
                background: rgba(88,166,255,0.2); 
                border-radius: 6px; 
            }

            /* Play Hauptbutton */
            QPushButton#playButton {
                background: #238636;
                color: white;
                border-radius: 26px;
                font-weight: bold;
                font-size: 18px;
                min-width: 52px;
                min-height: 52px;
            }
            QPushButton#playButton:hover {
                background: #2ea043;
            }

            /* Slider */
            QSlider::groove:horizontal { 
                height: 8px; 
                background: #21262d; 
                border-radius: 6px; 
            }
            QSlider::handle:horizontal { 
                background: #58a6ff; 
                width: 14px; 
                border-radius: 7px; 
            }

            /* Scrollbar vertikal */
            QScrollBar:vertical {
                background: #0f1720;
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #3b82f6;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2563eb;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Danach unbedingt dem Play-Button den objectName setzen:
        self.play_btn.setObjectName("playButton")



    # ---------------- Drag & Drop ----------------
    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()

    def dropEvent(self, ev):
        urls = ev.mimeData().urls()
        added = False
        for u in urls:
            p = u.toLocalFile()
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        if f.lower().endswith(SUPPORTED_FORMATS):
                            self._add_to_playlist(os.path.join(root, f))
                            added = True
            else:
                if p.lower().endswith(SUPPORTED_FORMATS):
                    self._add_to_playlist(p)
                    added = True
        if added and not self.is_playing and self.current_index == -1 and self.playlist:
            self.play_track(0)

    # ---------------- Playlist management ----------------
    def _add_to_playlist(self, path):
        if path in self.playlist:
            return
        self.playlist.append(path)
        cover = self._cover_pixmap(path, size=52)
        widget = PlaylistItemWidget(os.path.basename(path), cover)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.UserRole, path)
        self.playlist_widget.addItem(item)
        self.playlist_widget.setItemWidget(item, widget)

        # connect signals
        widget.play_requested.connect(lambda p=path: self._on_item_play(p))
        widget.delete_requested.connect(lambda p=path: self._on_item_delete(p))

    def _on_item_play(self, path):
        try:
            idx = self.playlist.index(path)
            self.play_track(idx)
        except ValueError:
            pass

    def _on_item_delete(self, path):
        try:
            idx = self.playlist.index(path)
            self._delete_by_index(idx)
        except ValueError:
            pass

    def _delete_by_index(self, idx):
        if idx < 0 or idx >= len(self.playlist):
            return
        was_current = (idx == self.current_index)
        path = self.playlist.pop(idx)
        item = self.playlist_widget.takeItem(idx)
        del item
        if was_current:
            self.stop_audio()
            self.current_index = -1
        else:
            if self.current_index > idx:
                self.current_index -= 1
        self._refresh_highlight()

    def remove_all(self):
        self.stop_audio()
        self.playlist.clear()
        self.playlist_widget.clear()
        self.current_index = -1
        self.update_ui_for_stop()

    def stop_all(self):
        self.stop_audio()
        self.current_index = -1
        self.update_ui_for_stop()

    def load_playlist(self, paths):
        self.playlist = []
        self.playlist_widget.clear()
        for p in paths:
            if os.path.exists(p) and p.lower().endswith(SUPPORTED_FORMATS):
                self._add_to_playlist(p)

    # ---------------- Files dialogs ----------------
    def open_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Audio-Dateien wählen", "", "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a)")
        if files:
            for f in files:
                self._add_to_playlist(f)
            if not self.is_playing and self.current_index == -1 and self.playlist:
                self.play_track(0)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Ordner wählen")
        if folder:
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(SUPPORTED_FORMATS):
                        self._add_to_playlist(os.path.join(root, f))
            if not self.is_playing and self.current_index == -1 and self.playlist:
                self.play_track(0)

    # ---------------- Playback ----------------

    def play_track(self, index):
        if index < 0 or index >= len(self.playlist):
            return
        path = self.playlist[index]
        self.current_index = index
        media = self.vlc_instance.media_new(path)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True
        self._refresh_highlight()
        self._update_meta(path)
        self.play_btn.setChecked(True)
        self.play_btn.setIcon(svg_to_icon(SVG_PAUSE, 24))
        self.mark_stream_as_playing(None)  # Kein Stream markiert

    def _on_play_button_toggled(self):
        if self.play_btn.isChecked():
            # Start oder Resume
            if self.current_index == -1 and self.current_media_type != "playlist" and self.playlist:
                self.play_track(0)
            else:
                try:
                    if self.current_media_type == "stream":
                        # Stream immer neu starten
                        current_name = self.now_label.text().replace("Stream: ", "")
                        current_url = self.streams.get(current_name)
                        if current_url:
                            # Stream starten
                            self.play_stream(current_url, current_name)
                            # Stream markieren
                            self.mark_stream_as_playing(current_name)
                            # Playlist-Markierung entfernen
                            self.mark_playlist_as_playing(-1)
                    else:
                        # Playlist kann pausiert/resumed werden
                        self.player.play()
                        self.is_playing = True
                        self.play_btn.setIcon(svg_to_icon(SVG_PAUSE, 24))
                        # Playlist markieren
                        self.mark_playlist_as_playing(self.current_index)
                        # Stream-Markierung entfernen
                        self.mark_stream_as_playing(None)
                except Exception:
                    pass
        else:
            # Pause / Stop
            try:
                if self.current_media_type == "playlist":
                    self.player.pause()
                    self.is_playing = False
                    self.play_btn.setIcon(svg_to_icon(SVG_PLAY, 24))
                    # Playlist bleibt markiert
                    self.mark_playlist_as_playing(self.current_index)
                    # Stream-Markierung entfernen
                    self.mark_stream_as_playing(None)
                else:
                    # Stream stoppen + alle Markierungen entfernen
                    self.stop_audio()
            except Exception:
                pass

        self._refresh_highlight()

    def pause_audio(self):
        if self.current_media_type == "playlist":
            try:
                self.player.pause()
                self.is_playing = False
                self.play_btn.setChecked(False)
                self.play_btn.setIcon(svg_to_icon(SVG_PLAY, 24))
            except Exception:
                pass
            self._refresh_highlight()
        else:
            # Stream = stop
            self.stop_audio()

    # Stoppt die aktuelle Wiedergabe (Playlist oder Stream)
    def stop_audio(self):
        try:
            if self.player.is_playing():
                self.player.stop()
        except Exception:
            pass
        self.is_playing = False
        self.play_btn.setChecked(False)
        self.play_btn.setIcon(svg_to_icon(SVG_PLAY, 24))
        self.update_ui_for_stop()
        self.update_button_playing(None)  # alle zurücksetzen
        self.now_label.setText("")
        self.mark_stream_as_playing(None)

    def play_next(self):
        if not self.playlist:
            return
        if self.shuffle_btn.isChecked():
            nxt = random.randint(0, len(self.playlist) - 1)
        else:
            nxt = self.current_index + 1
        if nxt >= len(self.playlist):
            if self.repeat_btn.isChecked():
                nxt = 0
            else:
                self.stop_audio()
                return
        self.play_track(nxt)

    def play_previous(self):
        if not self.playlist:
            return
        if self.shuffle_btn.isChecked():
            prev = random.randint(0, len(self.playlist) - 1)
        else:
            prev = self.current_index - 1
        if prev < 0:
            if self.repeat_btn.isChecked():
                prev = len(self.playlist) - 1
            else:
                self.stop_audio()
                return
        self.play_track(prev)

    def set_volume(self, val):
        self.player.audio_set_volume(val)
        self.settings["volume"] = val

    def vol_mute(self):
        current_vol = self.player.audio_get_volume()

        if current_vol == 0:
            # zurück zur alten Lautstärke
            self.player.audio_set_volume(self._old_volume)
            self.volume_slider.setValue(self._old_volume)
            self.settings["volume"] = self._old_volume
        else:
            # Lautstärke merken und stummschalten
            self._old_volume = current_vol
            self.player.audio_set_volume(0)
            self.volume_slider.setValue(0)
            self.settings["volume"] = 0

    # ---------------- Timeline & Timer ----------------
    def _timeline_pressed(self):
        self.is_user_seeking = True

    def _timeline_released(self):
        self.is_user_seeking = False
        if self.player.get_media():
            length = self.player.get_length()
            pos = self.timeline.value()
            if length > 0:
                seek = int((pos / 1000) * length)
                try:
                    self.player.set_time(seek)
                except Exception:
                    pass

    def _on_timer(self):
        if self.player:
            state = self.player.get_state()
            if state == vlc.State.Ended:
                self.play_next()
                return
            if state in (vlc.State.Playing, vlc.State.Paused):
                length = self.player.get_length()
                cur = self.player.get_time()
                if length > 0 and cur >= 0:
                    val = int((cur / length) * 1000)
                    if not self.is_user_seeking:
                        self.timeline.blockSignals(True)
                        self.timeline.setValue(val)
                        self.timeline.blockSignals(False)
                    self.time_cur.setText(self._ms_to_time(cur))
                    self.time_tot.setText(self._ms_to_time(length))
                else:
                    self.time_cur.setText("00:00")
                    self.time_tot.setText("00:00")

    @staticmethod
    def _ms_to_time(ms):
        if ms < 0:
            return "00:00"
        s = int(ms // 1000)
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"

    # ---------------- UI helpers ----------------
    def _refresh_highlight(self):
        # iterate items, set playing style on the matching widget
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            widget = self.playlist_widget.itemWidget(item)
            # ensure userRole path matches
            if i < len(self.playlist):
                item.setData(Qt.UserRole, self.playlist[i])
            if widget:
                widget.set_playing(i == self.current_index and self.is_playing)

    def _update_meta(self, path):
        pix = self._cover_pixmap(path, size=260)
        if pix:
            self.cover_label.setPixmap(pix)
            self.small_cover.setPixmap(pix.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cover_label.setPixmap(make_default_cover(260))
            self.small_cover.setPixmap(make_default_cover(56))
        title = os.path.basename(path)
        if MUTAGEN_AVAILABLE:
            try:
                mf = MutagenFile(path, easy=True)
                if mf and mf.tags:
                    t = mf.tags.get("title", [None])[0]
                    a = mf.tags.get("artist", [None])[0]
                    if t:
                        title = f"{t} — {a or ''}"
            except Exception:
                pass
        else:
            try:
                m = self.vlc_instance.media_new(path)
                m.parse()
                t = m.get_meta(vlc.Meta.Title)
                a = m.get_meta(vlc.Meta.Artist)
                if t:
                    title = f"{t} — {a or ''}"
            except Exception:
                pass
        self.meta_label.setText(title)
        self.now_label.setText(os.path.basename(path))

    def _cover_pixmap(self, path, size=128):
        # try mutagen embedded
        try:
            if MUTAGEN_AVAILABLE:
                mf = MutagenFile(path)
                if mf is not None and hasattr(mf, "tags") and mf.tags:
                    if path.lower().endswith(".mp3") and isinstance(mf.tags, ID3):
                        for tag in mf.tags.values():
                            if isinstance(tag, APIC):
                                data = tag.data
                                pix = QPixmap()
                                if pix.loadFromData(data):
                                    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    pics = getattr(mf, "pictures", None)
                    if pics:
                        data = pics[0].data
                        pix = QPixmap()
                        if pix.loadFromData(data):
                            return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception:
            pass

        # try vlc meta artwork
        try:
            m = self.vlc_instance.media_new(path)
            try:
                m.parse()
            except Exception:
                pass
            art = m.get_meta(vlc.Meta.ArtworkURL)
            if art:
                if art.startswith("file://"):
                    art_path = art.replace("file://", "")
                    if os.path.exists(art_path):
                        pix = QPixmap(art_path)
                        if not pix.isNull():
                            return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                elif art.startswith("data:"):
                    try:
                        header, b64 = art.split(",", 1)
                        import base64
                        data = base64.b64decode(b64)
                        pix = QPixmap()
                        if pix.loadFromData(data):
                            return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    except Exception:
                        pass
                else:
                    if os.path.exists(art):
                        pix = QPixmap(art)
                        if not pix.isNull():
                            return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception:
            pass

        # local cover image same name
        base = os.path.splitext(path)[0]
        for ext in (".jpg", ".png", ".jpeg"):
            p = base + ext
            if os.path.exists(p):
                pix = QPixmap(p)
                if not pix.isNull():
                    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        return None

    def update_ui_for_stop(self):
        self.cover_label.setPixmap(make_default_cover(260))
        self.small_cover.setPixmap(make_default_cover(56))
        self.now_label.setText("Keine Wiedergabe")
        self.meta_label.setText("Kein Titel geladen")
        self.time_cur.setText("00:00")
        self.time_tot.setText("00:00")
        self.timeline.setValue(0)
        self.play_btn.setChecked(False)
        self.play_btn.setIcon(svg_to_icon(SVG_PLAY, 24))
        self.is_playing = False
        self._refresh_highlight()

    # ---------------- Webradio ----------------

    # Funktion um den aktiven Stream zu markieren
    def mark_stream_as_playing(self, name):
        for stream_name, widget in self.stream_boxes.items():
            if stream_name == name:
                widget.setStyleSheet("""
                    background-color: rgba(0, 128, 0, 0.025);
                    border: 4px solid #0f8000;
                    border-radius: 8px;
                """)
            else:
                widget.setStyleSheet("""
                    background-color: #161b22;
                    border: 1px solid #3b82f6;
                    border-radius: 8px;
                """)

    # Beispiel im Stream-Start (oder wo immer du den Stream startest)
    # Optional: Klick erneut auf aktiven Stream stoppt ihn
    def toggle_stream(self, name):
        url = self.streams[name]
        # prüfen, ob gerade gespielt wird
        if self.is_playing and self.now_label.text() == f"Stream: {name}":
            self.stop_audio()
            self.update_button_playing(None)  # alle zurücksetzen
            self.is_playing = False
            self.now_label.setText("")
            self.mark_stream_as_playing(None)  # stoppen
        else:
            self.play_stream(url, name)  # starten

    # Stream starten (immer neu starten)
    def play_stream(self, url, name=None):
        # Vorherige Wiedergabe stoppen
        self.stop_audio()
        
        # Stream neu laden
        media = self.vlc_instance.media_new(url)
        self.player.set_media(media)
        self.player.play()
        self.update_button_playing(name)
        self.is_playing = True
        self.now_label.setText(f"Stream: {name}")
        self.mark_stream_as_playing(name)
        self.play_btn.setChecked(True)
        self.play_btn.setIcon(svg_to_icon(SVG_PAUSE, 24))
        
        # Markiere Stream im UI
        if name:
            self.now_label.setText(f"Stream: {name}")
        else:
            self.now_label.setText(f"Stream: {url}")
        self.meta_label.setText("Webradio")
        self.cover_label.setPixmap(make_default_cover(260, "Stream"))
        self.small_cover.setPixmap(make_default_cover(56, "S"))
        
        # Playlist-Index deaktivieren
        self.current_index = -1
        self.mark_stream_as_playing(name)
        self._refresh_highlight()
    
    def update_button_playing(self, name=None):
        """
        Aktualisiert alle Buttons: 
        - der aktive Stream bekommt Pause-Icon
        - alle anderen bekommen Play-Icon
        """
        for n, btn in self.stream_buttons.items():
            if n == name:
                btn.setIcon(svg_to_icon(SVG_PAUSE))
            else:
                btn.setIcon(svg_to_icon(SVG_PLAY))

    # ---------------- Settings ----------------
    def save_settings(self):
        self.settings["volume"] = self.volume_slider.value()
        self.settings["shuffle"] = self.shuffle_btn.isChecked()
        self.settings["repeat"] = self.repeat_btn.isChecked()
        self.settings["last_playlist"] = self.playlist.copy()

        # ---------------- EQ ----------------
        eq_values = self.tab_equalizer.get_current_eq_values()
        self.settings["eq_values"] = eq_values
        self.settings["eq_preset"] = self.tab_equalizer.get_current_preset()
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Save settings failed:", e)

    def load_settings(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self.settings.update(json.load(f))
            except Exception:
                pass

    # ---------------- Exit ----------------
    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    sys.exit(app.exec())
