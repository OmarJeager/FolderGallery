import os
import sys
import re
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QSize, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QComboBox, QScrollArea, QGridLayout,
    QFrame, QMessageBox, QSplitter, QSizePolicy
)

APP_NAME = "Folder Gallery"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff"}

DARK_STYLE = """
QWidget { background: #0b1020; color: #edf2ff; font-family: 'Segoe UI'; font-size: 10pt; }
QMainWindow { background: #0b1020; }
QFrame#Sidebar { background: #111a2e; border: 1px solid #202b45; border-radius: 18px; }
QFrame#Panel { background: #111a2e; border: 1px solid #202b45; border-radius: 18px; }
QLabel#HeroTitle { font-size: 25pt; font-weight: 800; color: #ffffff; }
QLabel#Muted { color: #94a3bd; }
QLineEdit, QComboBox { background: #0b1223; border: 1px solid #2b3857; border-radius: 10px; padding: 11px 12px; color: #f3f6ff; selection-background-color: #ff8a24; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #ff922e; }
QComboBox QAbstractItemView { background: #111a2e; selection-background-color: #ff922e; }
QPushButton { background: #1c2943; border: 1px solid #2a3958; border-radius: 10px; padding: 10px 14px; font-weight: 600; }
QPushButton:hover { background: #293a5d; border-color: #ff922e; }
QPushButton#Primary { background: #ff922e; color: #17111a; border: none; }
QPushButton#Primary:hover { background: #ffad5e; }
QScrollArea { border: none; background: transparent; }
QFrame#ImageCard { background: #151f35; border: 1px solid #263653; border-radius: 14px; }
QFrame#ImageCard:hover { border: 1px solid #ff922e; background: #1a2943; }
QLabel#ImagePreview { background: #0b1223; border-radius: 9px; }
QLabel#ImageName { font-weight: 700; }
QLabel#Tiny { color: #8fa0bd; font-size: 9pt; }
QLabel#Stat { color: #ffb76d; font-size: 17pt; font-weight: 800; }
"""

def app_root():
    # For PyInstaller builds, use the folder containing the executable.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

class ImageCard(QFrame):
    def __init__(self, path: Path, open_callback):
        super().__init__()
        self.path = path
        self.setObjectName("ImageCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(205, 224)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(7)
        preview = QLabel()
        preview.setObjectName("ImagePreview")
        preview.setAlignment(Qt.AlignCenter)
        preview.setFixedSize(183, 145)
        pix = QPixmap(str(path))
        if not pix.isNull():
            preview.setPixmap(pix.scaled(preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            preview.setText("Preview unavailable")
        name = QLabel(path.name)
        name.setObjectName("ImageName")
        name.setToolTip(str(path))
        name.setWordWrap(True)
        name.setMaximumHeight(34)
        folder = QLabel(path.parent.name)
        folder.setObjectName("Tiny")
        folder.setToolTip(str(path.parent))
        layout.addWidget(preview)
        layout.addWidget(name)
        layout.addWidget(folder)
        self.open_callback = open_callback

    def mouseDoubleClickEvent(self, event):
        self.open_callback(self.path)
        super().mouseDoubleClickEvent(event)

class GalleryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1320, 850)
        self.setMinimumSize(900, 600)
        self.roots = []
        self.all_images = []
        self.visible_cards = []
        self.current_folder = None
        self._build_ui()
        self._animate_intro()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(22, 18, 22, 20)
        root_layout.setSpacing(16)

        top = QHBoxLayout()
        brand = QVBoxLayout()
        eyebrow = QLabel("LOCAL • PRIVATE • OFFLINE")
        eyebrow.setObjectName("Muted")
        title = QLabel("Folder Gallery")
        title.setObjectName("HeroTitle")
        subtitle = QLabel("Find any image across your nested folders — without uploading anything.")
        subtitle.setObjectName("Muted")
        brand.addWidget(eyebrow)
        brand.addWidget(title)
        brand.addWidget(subtitle)
        top.addLayout(brand)
        top.addStretch()
        self.add_btn = QPushButton("＋  Add main folder")
        self.add_btn.setObjectName("Primary")
        self.add_btn.clicked.connect(self.add_root)
        self.scan_btn = QPushButton("↻  Rescan")
        self.scan_btn.clicked.connect(self.scan)
        top.addWidget(self.add_btn)
        top.addWidget(self.scan_btn)
        root_layout.addLayout(top)

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setMinimumWidth(260)
        sidebar.setMaximumWidth(330)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 18, 16, 16)
        side.setSpacing(12)
        side.addWidget(QLabel("LIBRARY"))
        self.root_combo = QComboBox()
        self.root_combo.setMinimumHeight(42)
        self.root_combo.addItem("All main folders", None)
        self.root_combo.currentIndexChanged.connect(self.root_changed)
        side.addWidget(self.root_combo)
        side.addWidget(QLabel("Browse subfolders"))
        self.folder_combo = QComboBox()
        self.folder_combo.setMinimumHeight(42)
        self.folder_combo.addItem("All subfolders", None)
        self.folder_combo.currentIndexChanged.connect(self.folder_changed)
        side.addWidget(self.folder_combo)
        self.root_list = QVBoxLayout()
        side.addSpacing(4)
        side.addWidget(QLabel("QUICK ACCESS"))
        self.root_hint = QLabel("Add your two main folders to begin.")
        self.root_hint.setObjectName("Muted")
        self.root_hint.setWordWrap(True)
        side.addWidget(self.root_hint)
        side.addStretch()
        note = QLabel("🔒  Your files stay on this computer.")
        note.setObjectName("Muted")
        note.setWordWrap(True)
        side.addWidget(note)

        content = QFrame()
        content.setObjectName("Panel")
        main = QVBoxLayout(content)
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(13)
        searchrow = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("⌕   Search by image filename, e.g. d54544548 or g44874")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.apply_filters)
        searchrow.addWidget(self.search, 1)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name A–Z", "Name Z–A", "Newest first", "Oldest first"])
        self.sort_combo.currentIndexChanged.connect(self.apply_filters)
        searchrow.addWidget(self.sort_combo)
        main.addLayout(searchrow)

        stats = QHBoxLayout()
        self.results_label = QLabel("0 images")
        self.results_label.setObjectName("Stat")
        self.path_label = QLabel("Choose or add a main folder")
        self.path_label.setObjectName("Muted")
        stats.addWidget(self.results_label)
        stats.addSpacing(12)
        stats.addWidget(self.path_label, 1)
        main.addLayout(stats)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(3, 3, 3, 3)
        self.grid.setSpacing(13)
        self.scroll.setWidget(self.grid_host)
        main.addWidget(self.scroll, 1)
        split.addWidget(sidebar)
        split.addWidget(content)
        split.setSizes([285, 1000])
        root_layout.addWidget(split, 1)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("Double-click an image to open it in your default viewer."))
        footer.addStretch()
        self.status = QLabel("Ready")
        self.status.setObjectName("Muted")
        footer.addWidget(self.status)
        root_layout.addLayout(footer)

    def _animate_intro(self):
        # Small native Qt fade-in; app still works if animation is unavailable.
        try:
            from PySide6.QtCore import QPropertyAnimation
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect(self.centralWidget())
            self.centralWidget().setGraphicsEffect(effect)
            animation = QPropertyAnimation(effect, b"opacity", self)
            animation.setDuration(420)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.start()
            self._intro_animation = animation
        except Exception:
            pass

    def add_root(self):
        path = QFileDialog.getExistingDirectory(self, "Choose a main folder containing image folders")
        if not path:
            return
        path = str(Path(path).resolve())
        if any(str(r) == path for r in self.roots):
            QMessageBox.information(self, "Already added", "This folder is already in your library.")
            return
        self.roots.append(Path(path))
        self.root_combo.addItem(Path(path).name, path)
        self.root_combo.setCurrentIndex(self.root_combo.count() - 1)
        self.scan()

    def scan(self):
        if not self.roots:
            self.status.setText("Add a main folder to start.")
            return
        self.status.setText("Scanning folders…")
        QApplication.processEvents()
        images = []
        for root in self.roots:
            try:
                for p in root.rglob("*"):
                    if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
                        images.append(p)
            except (PermissionError, OSError):
                continue
        self.all_images = sorted(set(images), key=lambda p: str(p).lower())
        self.refresh_folder_combo()
        self.apply_filters()
        self.status.setText(f"Scanned {len(self.roots)} main folder(s)")

    def refresh_folder_combo(self):
        selected = self.folder_combo.currentData()
        self.folder_combo.blockSignals(True)
        self.folder_combo.clear()
        self.folder_combo.addItem("All subfolders", None)
        folders = set()
        selected_root = self.root_combo.currentData()
        roots = [Path(selected_root)] if selected_root else self.roots
        for image in self.all_images:
            for root in roots:
                try:
                    rel = image.relative_to(root)
                    parts = rel.parts[:-1]
                    for i in range(1, len(parts) + 1):
                        folders.add(str(root.joinpath(*parts[:i])))
                except ValueError:
                    pass
        for folder in sorted(folders, key=lambda x: x.lower()):
            p = Path(folder)
            depth = len(p.parts)
            self.folder_combo.addItem("  " * max(0, depth - 2) + "📁 " + p.name, folder)
        idx = self.folder_combo.findData(selected)
        self.folder_combo.setCurrentIndex(max(0, idx))
        self.folder_combo.blockSignals(False)

    def root_changed(self):
        self.refresh_folder_combo()
        self.apply_filters()

    def folder_changed(self):
        self.apply_filters()

    def apply_filters(self):
        if not hasattr(self, "grid"):
            return
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        query = self.search.text().strip().casefold()
        root_data = self.root_combo.currentData()
        folder_data = self.folder_combo.currentData()
        matches = []
        for p in self.all_images:
            if root_data:
                try:
                    p.relative_to(Path(root_data))
                except ValueError:
                    continue
            if folder_data:
                try:
                    p.relative_to(Path(folder_data))
                except ValueError:
                    continue
            if query and query not in p.name.casefold() and query not in str(p.parent).casefold():
                continue
            matches.append(p)
        sort_index = self.sort_combo.currentIndex()
        if sort_index == 0:
            matches.sort(key=lambda p: p.name.casefold())
        elif sort_index == 1:
            matches.sort(key=lambda p: p.name.casefold(), reverse=True)
        elif sort_index == 2:
            matches.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        else:
            matches.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0)
        self.results_label.setText(f"{len(matches):,} image{'s' if len(matches) != 1 else ''}")
        if folder_data:
            self.path_label.setText(folder_data)
        elif root_data:
            self.path_label.setText(root_data)
        else:
            self.path_label.setText("All main folders")
        self.root_hint.setText("\n".join(f"📁 {r.name}" for r in self.roots) or "Add your two main folders to begin.")
        cols = max(1, self._columns())
        for i, p in enumerate(matches):
            card = ImageCard(p, self.open_image)
            self.grid.addWidget(card, i // cols, i % cols)
        if not matches:
            empty = QLabel("No images found. Try another folder or search term.")
            empty.setObjectName("Muted")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(150)
            self.grid.addWidget(empty, 0, 0, 1, cols)
        self.grid_host.adjustSize()

    def _columns(self):
        width = max(600, self.scroll.viewport().width())
        return max(1, width // 220)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.all_images:
            self.apply_filters()

    def open_image(self, path):
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(DARK_STYLE)
    window = GalleryWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
