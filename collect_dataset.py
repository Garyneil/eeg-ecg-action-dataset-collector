import argparse
import time

import yaml

from protocol import get_actions
from recorder import CSVRecorder
from serial_reader import Serial12HexReader


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_samples(reader, duration_sec):
    samples = []
    start = time.time()
    stream = reader.samples()
    while time.time() - start < duration_sec:
        samples.append(next(stream))
    return samples


def countdown(message, seconds):
    print(message)
    for remain in range(int(seconds), 0, -1):
        print(f"  {remain} s", end="\r")
        time.sleep(1)
    print(" " * 20, end="\r")


def main():
    parser = argparse.ArgumentParser(description="EEG/ECG 12-action dataset collector")
    parser.add_argument("--subject", required=True, help="Subject ID, e.g., sub001")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--trials", type=int, default=None, help="Trials per action")
    parser.add_argument("--dry-run", action="store_true", help="Run protocol without opening serial port")
    args = parser.parse_args()

    cfg = load_config(args.config)
    source_args = cfg["runtime"]["source_args"]
    dataset_cfg = cfg["dataset"]

    trials_per_action = args.trials or int(dataset_cfg.get("trials_per_action", 20))
    baseline_duration = float(dataset_cfg.get("baseline_duration_sec", 30))
    action_duration = float(dataset_cfg.get("action_duration_sec", 5))
    rest_duration = float(dataset_cfg.get("rest_duration_sec", 3))
    save_dir = dataset_cfg.get("save_dir", "data/raw")

    recorder = CSVRecorder(save_dir, args.subject)
    actions = get_actions()

    print("EEG-ECG Multimodal Action Dataset Collector")
    print(f"Subject: {args.subject}")
    print(f"Trials per action: {trials_per_action}")
    print(f"Save directory: {recorder.subject_dir}")

    if args.dry_run:
        print("Dry-run mode enabled. No serial data will be recorded.")
        for action in actions:
            for trial in range(1, trials_per_action + 1):
                print(f"[DRY RUN] Action {action.action_id:02d}: {action.name}, trial {trial:03d}")
        return

    reader = Serial12HexReader(**source_args)

    try:
        print("Collecting baseline data...")
        countdown("Please keep relaxed for baseline recording.", 3)
        baseline_samples = collect_samples(reader, baseline_duration)
        baseline_path = recorder.write_trial(0, 0, "baseline_rest", baseline_samples)
        print(f"Baseline saved: {baseline_path}")

        trial_id = 1
        for action in actions:
            for local_trial in range(1, trials_per_action + 1):
                print("=" * 60)
                print(
                    f"Action {action.action_id:02d} | {action.name} | {action.zh_name} | "
                    f"trial {local_trial}/{trials_per_action}"
                )
                countdown(f"Prepare: {action.description}", rest_duration)
                print("Recording...")
                samples = collect_samples(reader, action_duration)
                path = recorder.write_trial(trial_id, action.action_id, action.name, samples)
                print(f"Saved: {path}")
                trial_id += 1

    finally:
        reader.close()
        print("Serial port closed.")


if __name__ == "__main__":
    main()
