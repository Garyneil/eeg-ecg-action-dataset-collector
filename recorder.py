import csv
import os


class CSVRecorder:
    def __init__(self, save_root, subject_id):
        self.save_root = save_root
        self.subject_id = subject_id
        self.subject_dir = os.path.join(save_root, subject_id)
        os.makedirs(self.subject_dir, exist_ok=True)
        self.header = [
            "timestamp", "subject_id", "trial_id", "action_id", "action_name",
            "eeg_1", "eeg_2", "eeg_3", "eeg_4", "eeg_5", "eeg_6", "eeg_7", "eeg_8",
            "ecg_1", "ecg_2", "ecg_3", "ecg_4",
        ]

    def get_trial_path(self, trial_id, action_id, action_name):
        filename = f"trial_{trial_id:03d}_action_{action_id:02d}_{action_name}.csv"
        return os.path.join(self.subject_dir, filename)

    def write_trial(self, trial_id, action_id, action_name, samples):
        path = self.get_trial_path(trial_id, action_id, action_name)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.header)
            for sample in samples:
                values = list(sample)
                if len(values) != 13:
                    raise ValueError("Each sample must contain timestamp + 8 EEG + 4 ECG values.")
                writer.writerow(
                    [values[0], self.subject_id, f"{trial_id:03d}", f"{action_id:02d}", action_name]
                    + values[1:]
                )
        return path
