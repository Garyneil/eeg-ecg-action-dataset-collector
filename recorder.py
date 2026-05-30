import csv
import json
import os
from datetime import datetime


class CSVRecorder:
    def __init__(self, save_root, subject_id, session_id=None, config=None):
        self.save_root = save_root
        self.subject_id = subject_id
        self.session_id = session_id or datetime.now().strftime("session_%Y%m%d_%H%M%S")
        self.subject_dir = os.path.join(save_root, subject_id)
        self.session_dir = os.path.join(self.subject_dir, self.session_id)
        os.makedirs(self.session_dir, exist_ok=False)

        self.config = config or {}
        self.session_start_time = datetime.now().isoformat(timespec="seconds")
        self.trial_records = []

        self.header = [
            "timestamp", "subject_id", "session_id", "trial_id", "action_id", "action_name",
            "eeg_1", "eeg_2", "eeg_3", "eeg_4", "eeg_5", "eeg_6", "eeg_7", "eeg_8",
            "ecg_1", "ecg_2", "ecg_3", "ecg_4",
        ]

    def get_trial_path(self, trial_id, action_id, action_name):
        safe_action_name = str(action_name).replace(" ", "_").replace("/", "_")
        filename = f"trial_{trial_id:03d}_action_{action_id:02d}_{safe_action_name}.csv"
        return os.path.join(self.session_dir, filename)

    def write_trial(self, trial_id, action_id, action_name, samples, duration_sec=None, note=None):
        path = self.get_trial_path(trial_id, action_id, action_name)
        trial_start_time = datetime.now().isoformat(timespec="seconds")

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.header)
            for sample in samples:
                values = list(sample)
                if len(values) != 13:
                    raise ValueError("Each sample must contain timestamp + 8 EEG + 4 ECG values.")
                writer.writerow(
                    [
                        values[0],
                        self.subject_id,
                        self.session_id,
                        f"{trial_id:03d}",
                        f"{action_id:02d}",
                        action_name,
                    ]
                    + values[1:]
                )

        record = {
            "subject_id": self.subject_id,
            "session_id": self.session_id,
            "trial_id": int(trial_id),
            "action_id": int(action_id),
            "action_name": str(action_name),
            "start_time": trial_start_time,
            "duration_sec": duration_sec,
            "num_samples": len(samples),
            "relative_file_path": os.path.relpath(path, self.session_dir),
            "absolute_file_path": os.path.abspath(path),
            "note": note or "",
        }
        self.trial_records.append(record)
        self._write_metadata_files()
        return path

    def _write_metadata_files(self):
        metadata = {
            "subject_id": self.subject_id,
            "session_id": self.session_id,
            "session_start_time": self.session_start_time,
            "session_dir": os.path.abspath(self.session_dir),
            "config": self.config,
            "trials": self.trial_records,
        }

        metadata_json_path = os.path.join(self.session_dir, "metadata.json")
        with open(metadata_json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        metadata_csv_path = os.path.join(self.session_dir, "metadata.csv")
        fieldnames = [
            "subject_id",
            "session_id",
            "trial_id",
            "action_id",
            "action_name",
            "start_time",
            "duration_sec",
            "num_samples",
            "relative_file_path",
            "absolute_file_path",
            "note",
        ]
        with open(metadata_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.trial_records)

    def finalize_session(self):
        self._write_metadata_files()
        return self.session_dir
