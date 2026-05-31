import argparse
import csv
import sys
import time
from collections import deque
from pathlib import Path
from typing import List, Optional

import numpy as np
import yaml
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import pyqtgraph as pg

from serial_reader import Serial12HexReader


DEFAULT_WINDOW_SEC = 5.0
DEFAULT_FS = 250.0
DEFAULT_EEG_CHANNELS = 8
DEFAULT_ECG_CHANNELS = 4


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if cfg is None:
        raise ValueError("config.yaml is empty. Please check the file content.")
    if "runtime" not in cfg:
        raise ValueError("Missing required config section: runtime")
    if "source_args" not in cfg["runtime"]:
        raise ValueError("Missing required config section: runtime.source_args")

    return cfg


def build_channel_names(eeg_channels: int, ecg_channels: int) -> List[str]:
    eeg_names = [f"EEG{i + 1}" for i in range(eeg_channels)]
    ecg_names = [f"ECG{i + 1}" for i in range(ecg_channels)]
    return eeg_names + ecg_names


class SerialWorker(QThread):
    sample_received = pyqtSignal(list)
    status_changed = pyqtSignal(str)

    def __init__(self, source_args: dict):
        super().__init__()
        self.source_args = dict(source_args)
        self.running = False
        self.reader: Optional[Serial12HexReader] = None

    def run(self):
        self.running = True
        try:
            self.reader = Serial12HexReader(**self.source_args)
            port = self.source_args.get("port", "unknown")
            self.status_changed.emit(f"Serial connected: {port}")

            for sample in self.reader.samples():
                if not self.running:
                    break
                self.sample_received.emit(sample)

        except Exception as exc:
            if self.running:
                self.status_changed.emit(f"Serial error: {exc}")
        finally:
            self._close_reader()
            self.status_changed.emit("Serial stopped")

    def stop(self):
        self.running = False
        self._close_reader()

    def _close_reader(self):
        if self.reader is not None:
            try:
                self.reader.close()
            except Exception:
                pass


class RealtimeViewer(QMainWindow):
    def __init__(self, cfg: dict, window_sec: float = DEFAULT_WINDOW_SEC):
        super().__init__()
        self.cfg = cfg
        self.source_args = dict(cfg["runtime"]["source_args"])

        self.fs = float(self.source_args.get("fs", DEFAULT_FS))
        self.eeg_channels = int(self.source_args.get("eeg_channels", DEFAULT_EEG_CHANNELS))
        self.ecg_channels = int(self.source_args.get("ecg_channels", DEFAULT_ECG_CHANNELS))
        self.total_channels = self.eeg_channels + self.ecg_channels
        self.channel_names = build_channel_names(self.eeg_channels, self.ecg_channels)

        self.window_sec = float(window_sec)
        self.max_points = max(10, int(self.fs * self.window_sec))

        self.t_buffer = deque(maxlen=self.max_points)
        self.y_buffers = [deque(maxlen=self.max_points) for _ in range(self.total_channels)]

        self.worker: Optional[SerialWorker] = None
        self.sample_count = 0
        self.start_wall_time: Optional[float] = None

        self.saving = False
        self.csv_file = None
        self.csv_writer = None
        self.save_path: Optional[str] = None

        self._build_ui()

        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(40)

    def _build_ui(self):
        self.setWindowTitle("EEG-ECG Realtime Data Viewer")
        self.resize(1300, 820)
        pg.setConfigOptions(antialias=True)

        root_layout = QVBoxLayout()

        info_layout = QHBoxLayout()
        self.status_label = QLabel("Status: idle")
        self.port_label = QLabel(f"Port: {self.source_args.get('port', 'unknown')}")
        self.fs_label = QLabel(f"Fs: {self.fs:.1f} Hz")
        self.count_label = QLabel("Samples: 0")
        self.rate_label = QLabel("Realtime rate: -- Hz")
        self.save_label = QLabel("CSV: not saving")

        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.port_label)
        info_layout.addWidget(self.fs_label)
        info_layout.addWidget(self.count_label)
        info_layout.addWidget(self.rate_label)
        info_layout.addWidget(self.save_label)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start View")
        self.stop_button = QPushButton("Stop")
        self.save_button = QPushButton("Start Save CSV")
        self.clear_button = QPushButton("Clear Buffer")

        self.start_button.clicked.connect(self.start_stream)
        self.stop_button.clicked.connect(self.stop_stream)
        self.save_button.clicked.connect(self.toggle_save)
        self.clear_button.clicked.connect(self.clear_buffer)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.clear_button)

        self.eeg_plot = pg.PlotWidget(title="EEG Channels")
        self.eeg_plot.setLabel("left", "Amplitude")
        self.eeg_plot.setLabel("bottom", "Time", units="s")
        self.eeg_plot.showGrid(x=True, y=True)
        self.eeg_plot.addLegend(offset=(10, 10))

        self.ecg_plot = pg.PlotWidget(title="ECG Channels")
        self.ecg_plot.setLabel("left", "Amplitude")
        self.ecg_plot.setLabel("bottom", "Time", units="s")
        self.ecg_plot.showGrid(x=True, y=True)
        self.ecg_plot.addLegend(offset=(10, 10))

        self.eeg_curves = []
        self.ecg_curves = []

        for i in range(self.eeg_channels):
            pen = pg.intColor(i, hues=max(self.eeg_channels, 1))
            self.eeg_curves.append(self.eeg_plot.plot(name=f"EEG{i + 1}", pen=pen))

        for i in range(self.ecg_channels):
            pen = pg.intColor(i, hues=max(self.ecg_channels, 1))
            self.ecg_curves.append(self.ecg_plot.plot(name=f"ECG{i + 1}", pen=pen))

        root_layout.addLayout(info_layout)
        root_layout.addLayout(button_layout)
        root_layout.addWidget(self.eeg_plot)
        root_layout.addWidget(self.ecg_plot)

        container = QWidget()
        container.setLayout(root_layout)
        self.setCentralWidget(container)

    def start_stream(self):
        if self.worker is not None and self.worker.isRunning():
            return

        self.clear_buffer()
        self.sample_count = 0
        self.start_wall_time = time.time()

        self.worker = SerialWorker(self.source_args)
        self.worker.sample_received.connect(self.on_sample)
        self.worker.status_changed.connect(self.on_status)
        self.worker.start()

    def stop_stream(self):
        if self.worker is not None:
            self.worker.stop()
            self.worker.wait(1500)
            self.worker = None

        if self.saving:
            self.toggle_save()

    def clear_buffer(self):
        self.t_buffer.clear()
        for buf in self.y_buffers:
            buf.clear()
        self.sample_count = 0
        self.count_label.setText("Samples: 0")
        self.rate_label.setText("Realtime rate: -- Hz")

    def toggle_save(self):
        if not self.saving:
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save realtime CSV",
                "realtime_stream.csv",
                "CSV Files (*.csv)",
            )
            if not save_path:
                return

            try:
                self.csv_file = open(save_path, "w", newline="", encoding="utf-8")
                self.csv_writer = csv.writer(self.csv_file)
                self.csv_writer.writerow(["timestamp"] + self.channel_names)
            except OSError as exc:
                QMessageBox.critical(self, "Save Error", f"Cannot open CSV file:\n{exc}")
                self.csv_file = None
                self.csv_writer = None
                return

            self.saving = True
            self.save_path = save_path
            self.save_button.setText("Stop Save CSV")
            self.save_label.setText(f"CSV: saving to {Path(save_path).name}")
        else:
            self.saving = False
            if self.csv_file is not None:
                self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
            self.save_button.setText("Start Save CSV")
            self.save_label.setText("CSV: not saving")

    def on_sample(self, sample: list):
        expected_len = self.total_channels + 1
        if len(sample) != expected_len:
            self.status_label.setText(f"Status: wrong sample length {len(sample)}, expected {expected_len}")
            return

        timestamp = float(sample[0])
        values = [float(v) for v in sample[1:]]

        self.t_buffer.append(timestamp)
        for i, value in enumerate(values):
            self.y_buffers[i].append(value)

        self.sample_count += 1
        self.count_label.setText(f"Samples: {self.sample_count}")

        if self.start_wall_time is not None:
            elapsed = max(time.time() - self.start_wall_time, 1e-6)
            real_rate = self.sample_count / elapsed
            self.rate_label.setText(f"Realtime rate: {real_rate:.1f} Hz")

        if self.saving and self.csv_writer is not None:
            self.csv_writer.writerow([timestamp] + values)

    def on_status(self, message: str):
        self.status_label.setText(f"Status: {message}")

    def update_plots(self):
        if len(self.t_buffer) < 2:
            return

        t = np.asarray(self.t_buffer, dtype=float)
        t = t - t[-1]

        for i, curve in enumerate(self.eeg_curves):
            y = np.asarray(self.y_buffers[i], dtype=float)
            if len(y) == len(t):
                curve.setData(t, y)

        for i, curve in enumerate(self.ecg_curves):
            channel_idx = self.eeg_channels + i
            y = np.asarray(self.y_buffers[channel_idx], dtype=float)
            if len(y) == len(t):
                curve.setData(t, y)

    def closeEvent(self, event):
        self.stop_stream()
        event.accept()


def main():
    parser = argparse.ArgumentParser(description="Realtime EEG/ECG waveform viewer")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--window-sec", type=float, default=DEFAULT_WINDOW_SEC, help="Display window length in seconds")
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
    except Exception as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    app = QApplication(sys.argv)
    viewer = RealtimeViewer(cfg, window_sec=args.window_sec)
    viewer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
