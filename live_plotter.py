from collections import deque
from typing import List, Optional

import numpy as np


class LiveWaveformPlotter:
    """Embedded realtime waveform plotter used by collect_dataset.py.

    This class is intentionally lightweight. It does not open the serial port.
    The dataset collector reads the serial stream once, then pushes each sample
    into this plotter while still saving the same samples to CSV.
    """

    def __init__(self, eeg_channels: int = 8, ecg_channels: int = 4, fs: float = 250.0, window_sec: float = 5.0):
        try:
            from PyQt5.QtWidgets import QApplication
            import pyqtgraph as pg
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Live viewer requires PyQt5 and pyqtgraph. "
                "Please run: pip install PyQt5 pyqtgraph"
            ) from exc

        self.QApplication = QApplication
        self.pg = pg

        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])

        self.eeg_channels = int(eeg_channels)
        self.ecg_channels = int(ecg_channels)
        self.total_channels = self.eeg_channels + self.ecg_channels
        self.fs = float(fs)
        self.window_sec = float(window_sec)
        self.max_points = max(10, int(self.fs * self.window_sec))

        self.t_buffer = deque(maxlen=self.max_points)
        self.y_buffers = [deque(maxlen=self.max_points) for _ in range(self.total_channels)]

        self.pg.setConfigOptions(antialias=True)

        self.window = self.pg.GraphicsLayoutWidget(show=True, title="EEG-ECG Live Waveform During Collection")
        self.window.resize(1300, 800)

        self.status_label = self.pg.LabelItem(justify="left")
        self.window.addItem(self.status_label, row=0, col=0)

        self.eeg_plot = self.window.addPlot(row=1, col=0, title="EEG Channels")
        self.eeg_plot.setLabel("left", "Amplitude")
        self.eeg_plot.setLabel("bottom", "Time", units="s")
        self.eeg_plot.showGrid(x=True, y=True)
        self.eeg_plot.addLegend(offset=(10, 10))

        self.ecg_plot = self.window.addPlot(row=2, col=0, title="ECG Channels")
        self.ecg_plot.setLabel("left", "Amplitude")
        self.ecg_plot.setLabel("bottom", "Time", units="s")
        self.ecg_plot.showGrid(x=True, y=True)
        self.ecg_plot.addLegend(offset=(10, 10))

        self.eeg_curves = []
        self.ecg_curves = []

        for i in range(self.eeg_channels):
            pen = self.pg.intColor(i, hues=max(self.eeg_channels, 1))
            self.eeg_curves.append(self.eeg_plot.plot(name=f"EEG{i + 1}", pen=pen))

        for i in range(self.ecg_channels):
            pen = self.pg.intColor(i, hues=max(self.ecg_channels, 1))
            self.ecg_curves.append(self.ecg_plot.plot(name=f"ECG{i + 1}", pen=pen))

        self.sample_count = 0
        self.current_action = "idle"
        self.current_trial = "--"
        self.update_status()
        self.app.processEvents()

    def set_context(self, trial_id: Optional[int], action_id: Optional[int], action_name: str, round_idx: Optional[int] = None):
        if trial_id is None:
            self.current_trial = "baseline"
        else:
            self.current_trial = f"trial={trial_id:03d}"

        if action_id is None:
            self.current_action = action_name
        else:
            prefix = f"round={round_idx:03d} | " if round_idx is not None else ""
            self.current_action = f"{prefix}action={action_id:02d} | {action_name}"

        self.update_status()
        self.app.processEvents()

    def push_sample(self, sample: List[float]):
        expected_len = self.total_channels + 1
        if len(sample) != expected_len:
            return

        timestamp = float(sample[0])
        values = [float(v) for v in sample[1:]]

        self.t_buffer.append(timestamp)
        for i, value in enumerate(values):
            self.y_buffers[i].append(value)

        self.sample_count += 1

        # Updating every sample is unnecessarily expensive. About 20-25 FPS is enough.
        if self.sample_count % 10 == 0:
            self.update_plots()

    def update_status(self):
        self.status_label.setText(
            f"<b>Status:</b> collecting | <b>{self.current_trial}</b> | "
            f"<b>{self.current_action}</b> | samples={self.sample_count}"
        )

    def update_plots(self):
        if len(self.t_buffer) < 2:
            self.app.processEvents()
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

        self.update_status()
        self.app.processEvents()

    def close(self):
        self.update_plots()
        self.app.processEvents()
