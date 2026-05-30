import argparse
import re
import time
from pathlib import Path

import yaml

from protocol import get_actions
from recorder import CSVRecorder
from serial_reader import Serial12HexReader


REQUIRED_TOP_LEVEL_KEYS = ("runtime", "dataset")
REQUIRED_RUNTIME_KEYS = ("source", "source_args")
REQUIRED_SOURCE_ARGS_KEYS = ("port", "baudrate")


def _remove_html_breaks(text: str) -> str:
    """Remove accidental HTML line-break tags copied from chat or webpages."""
    return re.sub(r"<br\s*/?>", "", text, flags=re.IGNORECASE)


def load_config(path):
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw_text = config_path.read_text(encoding="utf-8")
    cleaned_text = _remove_html_breaks(raw_text)

    try:
        cfg = yaml.safe_load(cleaned_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML config file: {config_path}\n{exc}") from exc

    if cfg is None:
        raise ValueError(
            f"Config file is empty or only contains comments: {config_path}. "
            "Please check config.yaml."
        )
    if not isinstance(cfg, dict):
        raise ValueError(f"Config root must be a YAML mapping/dictionary: {config_path}")

    missing_top_keys = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in cfg]
    if missing_top_keys:
        raise ValueError(f"Missing top-level config key(s): {missing_top_keys}")

    runtime_cfg = cfg.get("runtime")
    dataset_cfg = cfg.get("dataset")
    if not isinstance(runtime_cfg, dict):
        raise ValueError("Config key 'runtime' must be a mapping/dictionary.")
    if not isinstance(dataset_cfg, dict):
        raise ValueError("Config key 'dataset' must be a mapping/dictionary.")

    missing_runtime_keys = [key for key in REQUIRED_RUNTIME_KEYS if key not in runtime_cfg]
    if missing_runtime_keys:
        raise ValueError(f"Missing runtime config key(s): {missing_runtime_keys}")

    source_args = runtime_cfg.get("source_args")
    if not isinstance(source_args, dict):
        raise ValueError("Config key 'runtime.source_args' must be a mapping/dictionary.")

    missing_source_args = [key for key in REQUIRED_SOURCE_ARGS_KEYS if key not in source_args]
    if missing_source_args:
        raise ValueError(f"Missing runtime.source_args key(s): {missing_source_args}")

    return cfg


def _format_remaining(seconds_left: float) -> str:
    seconds_left = max(0, int(seconds_left + 0.999))
    return f"{seconds_left:02d}s"


def countdown(message, seconds):
    """Blocking countdown used before recording starts."""
    print(message)
    start = time.monotonic()
    duration = float(seconds)
    last_display = None

    while True:
        elapsed = time.monotonic() - start
        remaining = duration - elapsed
        if remaining <= 0:
            break

        display = _format_remaining(remaining)
        if display != last_display:
            print(f"  remaining: {display}", end="\r", flush=True)
            last_display = display
        time.sleep(0.05)

    print(" " * 40, end="\r", flush=True)
    print("  remaining: 00s")


def collect_samples(reader, duration_sec, message="Recording"):
    """Collect serial samples while showing a real-time countdown."""
    samples = []
    stream = reader.samples()
    start = time.monotonic()
    duration = float(duration_sec)
    last_display = None

    print(message)
    while True:
        elapsed = time.monotonic() - start
        remaining = duration - elapsed
        if remaining <= 0:
            break

        display = _format_remaining(remaining)
        if display != last_display:
            print(f"  recording countdown: {display} | samples: {len(samples)}", end="\r", flush=True)
            last_display = display

        samples.append(next(stream))

    print(" " * 70, end="\r", flush=True)
    print(f"  recording countdown: 00s | samples: {len(samples)}")
    return samples


def main():
    parser = argparse.ArgumentParser(description="EEG/ECG 12-action dataset collector")
    parser.add_argument("--subject", required=True, help="Subject ID, e.g., sub001")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--trials", type=int, default=None, help="Trials per action")
    parser.add_argument("--dry-run", action="store_true", help="Run protocol without opening serial port")
    args = parser.parse_args()

    cfg = load_config(args.config)
    runtime_cfg = cfg["runtime"]
    source_args = runtime_cfg["source_args"]
    dataset_cfg = cfg["dataset"]

    if runtime_cfg.get("source") != "serial12hex":
        raise ValueError(
            "Only runtime.source='serial12hex' is currently supported by collect_dataset.py."
        )

    trials_per_action = args.trials or int(dataset_cfg.get("trials_per_action", 20))
    baseline_duration = float(dataset_cfg.get("baseline_duration_sec", 30))
    action_duration = float(dataset_cfg.get("action_duration_sec", 5))
    rest_duration = float(dataset_cfg.get("rest_duration_sec", 3))
    save_dir = dataset_cfg.get("save_dir", "data/raw")

    recorder = CSVRecorder(save_dir, args.subject, config=cfg)
    actions = get_actions()

    print("EEG-ECG Multimodal Action Dataset Collector")
    print(f"Subject: {args.subject}")
    print(f"Session ID: {recorder.session_id}")
    print(f"Trials per action: {trials_per_action}")
    print(f"Baseline duration: {baseline_duration:.1f}s")
    print(f"Action duration: {action_duration:.1f}s")
    print(f"Rest/prepare duration: {rest_duration:.1f}s")
    print(f"Save directory: {recorder.session_dir}")
    print(f"Serial port: {source_args.get('port')}")
    print(f"Baudrate: {source_args.get('baudrate')}")

    if args.dry_run:
        print("Dry-run mode enabled. No serial data will be recorded.")
        for action in actions:
            for trial in range(1, trials_per_action + 1):
                print("=" * 60)
                print(f"[DRY RUN] Action {action.action_id:02d}: {action.name}, trial {trial:03d}")
                countdown(f"Prepare: {action.description}", rest_duration)
                countdown(f"Simulated recording: {action.name}", action_duration)
        recorder.finalize_session()
        print(f"Dry-run session metadata saved: {recorder.session_dir}")
        return

    reader = Serial12HexReader(**source_args)

    try:
        print("Collecting baseline data...")
        countdown("Please keep relaxed. Baseline recording will start soon.", 3)
        baseline_samples = collect_samples(
            reader,
            baseline_duration,
            message="Baseline recording: keep relaxed and still.",
        )
        baseline_path = recorder.write_trial(
            0,
            0,
            "baseline_rest",
            baseline_samples,
            duration_sec=baseline_duration,
            note="baseline",
        )
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
                samples = collect_samples(
                    reader,
                    action_duration,
                    message=f"Now perform action: {action.name} / {action.zh_name}",
                )
                path = recorder.write_trial(
                    trial_id,
                    action.action_id,
                    action.name,
                    samples,
                    duration_sec=action_duration,
                    note=f"local_trial={local_trial}",
                )
                print(f"Saved: {path}")
                trial_id += 1

    finally:
        reader.close()
        session_dir = recorder.finalize_session()
        print("Serial port closed.")
        print(f"Session finalized: {session_dir}")
        print(f"Metadata saved: {session_dir}/metadata.json and {session_dir}/metadata.csv")


if __name__ == "__main__":
    main()
