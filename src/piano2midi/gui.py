from __future__ import annotations

import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtGui import QFont, QColor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QProgressBar,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
)

APP_DIR = Path(__file__).resolve().parents[2]
TRANSKUN_EXE = APP_DIR / ".venv-transkun311" / "Scripts" / "transkun.exe"

SUPPORTED_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".ogg", ".m4a",
    ".mp4", ".mov",
}

STYLESHEET = """
QMainWindow, QWidget {
    background: #101722; color: #e4ecf8;
    font-family: "Segoe UI"; font-size: 13px;
}
QLabel#AppTitle { font-size: 22px; font-weight: 700; color: #f1f5fc; background: transparent; }
QLabel#Subtitle { color: #91a3bd; background: transparent; }
QFrame#Card { background: #151f2d; border: 1px solid #27364a; border-radius: 10px; }
QFrame#DropZone { background: #121c2a; border: 2px dashed #35527a; border-radius: 10px; }
QPushButton {
    background: #1a2637; border: 1px solid #30425b; border-radius: 7px;
    padding: 9px 14px; color: #dce7f7; font-weight: 600;
}
QPushButton:hover { background: #24364e; border-color: #4c6d9d; }
QPushButton:disabled { color: #71829b; background: #182231; border-color: #27364a; }
QPushButton#Primary { background: #246ff0; border: 1px solid #246ff0; color: #ffffff; }
QPushButton#Primary:hover { background: #155edb; }
QLineEdit, QComboBox {
    background: #121c2a; border: 1px solid #30425b; border-radius: 7px;
    padding: 8px 10px; min-height: 20px; color: #e4ecf8;
    selection-background-color: #246ff0;
}
QLineEdit:focus, QComboBox:focus { border-color: #4387f5; }
QComboBox QAbstractItemView {
    background: #172233; color: #e4ecf8; selection-background-color: #246ff0;
    border: 1px solid #30425b;
}
QTableWidget {
    background: #151f2d; alternate-background-color: #172333; border: none;
    gridline-color: #27364a; selection-background-color: #203c63; selection-color: #f1f6ff;
}
QTableWidget::item { padding: 7px 8px; border: none; }
QHeaderView::section {
    background: #1b293b; color: #bdcce2; font-weight: 700;
    padding: 10px 8px; border: none; border-bottom: 1px solid #30425b;
}
QScrollBar:vertical {
    background: #121b28; width: 10px; margin: 3px 2px; border-radius: 5px;
}
QScrollBar::handle:vertical { background: #405571; min-height: 28px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: #5b7598; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; border: none; height: 0px; }
QScrollBar:horizontal {
    background: #121b28; height: 10px; margin: 2px 3px; border-radius: 5px;
}
QScrollBar::handle:horizontal { background: #405571; min-width: 28px; border-radius: 5px; }
QScrollBar::handle:horizontal:hover { background: #5b7598; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; border: none; width: 0px; }
"""


class DropZone(QFrame):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(7)

        icon = QLabel("♫")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 32px; color: #4b78b8;")

        title = QLabel("Drag and drop audio or video files here")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 700;")

        subtitle = QLabel("or click to browse")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #64799b;")

        self.browse_button = QPushButton("Browse Files")
        self.browse_button.setObjectName("Primary")
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.browse_button, alignment=Qt.AlignmentFlag.AlignCenter)


    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            # Accept only drops containing local files.
            local_files = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]

            if local_files:
                event.setDropAction(Qt.DropAction.CopyAction)
                event.accept()
                return

        event.ignore()


    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()


    def dropEvent(self, event: QDropEvent):
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]

        if paths:
            self.files_dropped.emit(paths)
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()



class TranscriptionWorker(QThread):
    log_line = Signal(str)
    job_started = Signal(int)
    job_finished = Signal(int, bool, str)
    batch_finished = Signal()

    def __init__(self, jobs, output_dir, device):
        super().__init__()
        self.jobs = jobs
        self.output_dir = Path(output_dir)
        self.device = device
        self.cancel_requested = False
        self.process = None

    def cancel(self):
        self.cancel_requested = True
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def run(self):
        for index, job in enumerate(self.jobs):
            if self.cancel_requested:
                break

            self.job_started.emit(index)
            source = job["source"]

            command = [
                sys.executable,
                "-m", "piano2midi.cli",
                "--output-dir", str(self.output_dir),
                "--device", self.device,
            ]
            if TRANSKUN_EXE.exists():
                command += ["--transkun-executable", str(TRANSKUN_EXE)]

            if job["is_url"]:
                command += ["--url", source]
            else:
                command.append(source)

            self.log_line.emit(f"Input: {source}")
            self.log_line.emit(f"Device: {self.device}")
            self.log_line.emit("Starting transcription...")

            try:
                self.process = subprocess.Popen(
                    command,
                    cwd=str(APP_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                )
                output_lines = []
                for line in self.process.stdout:
                    line = line.rstrip()
                    if line:
                        print(line, flush=True)
                        output_lines.append(line)
                        self.log_line.emit(line)

                self.process.wait()
                output_text = "\n".join(output_lines)
                success = self.process.returncode == 0
                self.job_finished.emit(index, success, output_text)
            except Exception as exc:
                self.log_line.emit(f"Error: {exc}")
                self.job_finished.emit(index, False, str(exc))
            finally:
                self.process = None

        self.batch_finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Piano2MIDI", "Piano2MIDI")
        self.setWindowTitle("Piano2MIDI")
        self.resize(1050, 760)
        self.setMinimumSize(800, 620)

        self.jobs = []
        self.worker = None
        self.active_original_indices = []
        self.completed_in_batch = 0
        self.build_ui()
        self.setStyleSheet(STYLESHEET)

    def build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(13)

        title_row = QHBoxLayout()
        brand_icon = QLabel("▥")
        brand_icon.setStyleSheet("font-size: 30px; color: #193965;")
        title_box = QVBoxLayout()
        title = QLabel("Piano2MIDI")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Convert piano audio or video into MIDI")
        subtitle.setObjectName("Subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        title_row.addWidget(brand_icon)
        title_row.addLayout(title_box)
        title_row.addStretch()
        root.addLayout(title_row)

        self.drop_zone = DropZone()
        self.drop_zone.browse_button.clicked.connect(self.browse_files)
        self.drop_zone.files_dropped.connect(self.add_local_files)
        root.addWidget(self.drop_zone)

        # Optional online link input.
        link_row = QHBoxLayout()
        link_label = QLabel("Or paste a link")
        link_label.setStyleSheet("font-weight: 600;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube, Instagram, or another supported URL")
        self.url_input.returnPressed.connect(self.add_url)
        add_link_button = QPushButton("Add Link")
        add_link_button.clicked.connect(self.add_url)
        link_row.addWidget(link_label)
        link_row.addWidget(self.url_input, 1)
        link_row.addWidget(add_link_button)
        root.addLayout(link_row)

        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Output folder"))

        saved_output_dir = self.settings.value(
            "output_dir",
            str(APP_DIR / "output"),
            type=str,
        )

        self.output_input = QLineEdit(saved_output_dir)
        self.output_input.textChanged.connect(self.save_output_directory)

        options_row.addWidget(self.output_input, 1)
        output_button = QPushButton("Change")
        output_button.clicked.connect(self.choose_output_folder)
        options_row.addWidget(output_button)
        options_row.addSpacing(8)
        options_row.addWidget(QLabel("Device"))
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cuda", "cpu"])
        self.device_combo.setCurrentText("cuda")
        options_row.addWidget(self.device_combo)
        root.addLayout(options_row)

        queue_card = QFrame()
        queue_card.setObjectName("Card")
        queue_layout = QVBoxLayout(queue_card)
        queue_layout.setContentsMargins(10, 10, 10, 10)
        queue_layout.setSpacing(8)

        queue_header = QHBoxLayout()
        self.queue_title = QLabel("Transcription Queue (0)")
        self.queue_title.setStyleSheet("font-size: 19px; font-weight: 700; background: transparent;")
        queue_header.addWidget(self.queue_title)
        queue_header.addStretch()
        clear_button = QPushButton("Clear Queue")
        clear_button.clicked.connect(self.clear_queue)
        queue_header.addWidget(clear_button)
        add_more_button = QPushButton("Add More")
        add_more_button.clicked.connect(self.browse_files)
        queue_header.addWidget(add_more_button)
        queue_layout.addLayout(queue_header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["File", "Status", "Output"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(125)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        queue_layout.addWidget(self.table, 1)
        root.addWidget(queue_card, 3)


        action_row = QHBoxLayout()
        self.processing_label = QLabel("Ready")
        self.processing_label.setStyleSheet("color: #5c7192;")
        action_row.addWidget(self.processing_label)
        action_row.addStretch()
        self.start_button = QPushButton("Start Transcription")
        self.start_button.setObjectName("Primary")
        self.start_button.clicked.connect(self.start_transcription)
        action_row.addWidget(self.start_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_transcription)
        action_row.addWidget(self.cancel_button)
        root.addLayout(action_row)


        self.setCentralWidget(central)

    def browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose audio or video files",
            str(Path.home()),
            "Media files (*.mp3 *.wav *.flac *.ogg *.m4a *.mp4 *.mov *.mkv *.webm *.avi);;All files (*.*)",
        )
        self.add_local_files(paths)

    def add_local_files(self, paths):
        existing = {job["source"] for job in self.jobs}
        for path in paths:
            path = str(Path(path).resolve())
            if Path(path).suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if path in existing:
                continue
            self.jobs.append({
                "source": path,
                "is_url": False,
                "status": "Queued",
                "output": "—",
            })
            existing.add(path)
        self.refresh_table()

    def add_url(self):
        url = self.url_input.text().strip()
        if not url:
            return
        if not url.lower().startswith(("https://", "http://")):
            QMessageBox.warning(self, "Invalid link", "Enter a valid http:// or https:// link.")
            return
        if any(job["source"] == url for job in self.jobs):
            self.url_input.clear()
            return
        self.jobs.append({
            "source": url,
            "is_url": True,
            "status": "Queued",
            "output": "—",
        })
        self.url_input.clear()
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.jobs))
        self.queue_title.setText(f"Transcription Queue ({len(self.jobs)})")

        for row, job in enumerate(self.jobs):
            name = job["source"] if job["is_url"] else Path(job["source"]).name
            if len(name) > 64:
                name = name[:61] + "..."

            file_item = QTableWidgetItem(name)
            file_item.setToolTip(job["source"])

            # The status is displayed directly in the Status column.
            status = job["status"]
            if status not in ("Queued", "Processing", "Completed"):
                status = "Queued"
            status_item = QTableWidgetItem(status)

            if status == "Queued":
                status_item.setForeground(QColor("#f1f5fc"))
            elif status == "Processing":
                status_item.setForeground(QColor("#4d9aff"))
            elif status == "Completed":
                status_item.setForeground(QColor("#35c779"))

            output_item = QTableWidgetItem(job["output"])

            self.table.setItem(row, 0, file_item)
            self.table.setItem(row, 1, status_item)
            self.table.setItem(row, 2, output_item)

    def save_output_directory(self, folder):
        self.settings.setValue("output_dir", folder)

    def choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose output folder", self.output_input.text() or str(APP_DIR)
        )
        if folder:
            self.output_input.setText(folder)

    def start_transcription(self):
        if self.worker and self.worker.isRunning():
            return
        pending_indices = [
            i for i, job in enumerate(self.jobs) if job["status"] == "Queued"
        ]
        if not pending_indices:
            QMessageBox.information(self, "Nothing to do", "Add a file or link to the queue first.")
            return

        output_dir = Path(self.output_input.text()).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(self, "Output folder error", str(exc))
            return

        cli_path = APP_DIR / "src" / "piano2midi" / "cli.py"
        if not cli_path.exists():
            QMessageBox.critical(self, "CLI not found", f"Could not find:\n{cli_path}")
            return

        self.active_original_indices = pending_indices
        self.completed_in_batch = 0
        jobs_to_run = [self.jobs[i] for i in pending_indices]
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.processing_label.setText(f"Processing 1/{len(jobs_to_run)}...")

        self.worker = TranscriptionWorker(
            jobs_to_run, output_dir, self.device_combo.currentText()
        )
        self.worker.job_started.connect(self.on_job_started)
        self.worker.job_finished.connect(self.on_job_finished)
        self.worker.batch_finished.connect(self.on_batch_finished)
        self.worker.start()

    def on_job_started(self, local_index):
        original_index = self.active_original_indices[local_index]
        self.jobs[original_index]["status"] = "Processing"
        self.processing_label.setText(
            f"Processing {local_index + 1}/{len(self.active_original_indices)}..."
        )
        self.refresh_table()

    def on_job_finished(self, local_index, success, output_text):
        original_index = self.active_original_indices[local_index]
        job = self.jobs[original_index]
        job["status"] = "Completed" if success else "Queued"

        # Best-effort: extract a MIDI output path from CLI output, if present.
        matches = re.findall(
            r"""(?i)(?:[A-Z]:\\[^\r\n"]+?\.mid|/[^\r\n"]+?\.mid|[^\s"'<>]+\.mid)""",
            output_text,
        )
        if matches:
            candidate = Path(matches[-1].strip().strip(".,"))
            if not candidate.is_absolute():
                candidate = APP_DIR / candidate
            job["output"] = str(candidate)

        self.completed_in_batch += 1
        self.refresh_table()
        if not success:
            QMessageBox.warning(
                self,
                "Transcription failed",
                f"Could not transcribe:\\n{job['source']}\\n\\n{output_text[-1800:]}",
            )
    def on_batch_finished(self):
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.processing_label.setText("Queue processing finished.")
        if self.worker is not None:
            self.worker.finished.connect(self.release_worker)

    def release_worker(self):
        worker = self.worker
        self.worker = None
        if worker is not None:
            worker.deleteLater()

    def cancel_transcription(self):
        if self.worker and self.worker.isRunning():
            self.processing_label.setText("Cancelling...")
            self.worker.cancel()
            self.cancel_button.setEnabled(False)

    def clear_queue(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Queue is running", "Cancel transcription before clearing the queue.")
            return
        self.jobs.clear()
        self.refresh_table()
        self.processing_label.setText("Ready")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
