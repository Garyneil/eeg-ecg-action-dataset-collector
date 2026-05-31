# EEG-ECG Multimodal Action Dataset Collector

A lightweight dataset collection system for synchronized EEG and ECG action experiments.

本项目是一个用于 EEG/ECG 多模态动作数据采集的轻量级系统。它通过串口读取 12 通道生理信号数据流，其中包括 8 路 EEG 与 4 路 ECG，并按照预设动作范式完成倒计时引导、试次采集、自动标注、分 session 保存与元数据记录。

---

## 1. Project Overview

This repository focuses on **dataset acquisition**, not model training or online inference. It is designed for experiments related to physiological signal analysis, brain-computer interaction, human action recognition, human-robot interaction, and multimodal intention understanding.

本仓库的核心目标不是训练模型，而是稳定、规范地采集 EEG/ECG 动作数据集。采集得到的数据后续可以用于动作识别、生理状态分析、脑机接口、人机交互、机器人意图识别等任务。

Main features:

- 8-channel EEG + 4-channel ECG serial acquisition
- 12-channel hexadecimal serial stream decoding
- lightweight realtime waveform viewer based on PyQt5 and pyqtgraph
- 12-class action protocol
- real-time preparation countdown
- real-time recording countdown for each action trial
- baseline recording before action trials
- automatic subject ID, session ID, trial ID, action label, and timestamp recording
- one independent session folder for every collection run
- automatic `metadata.json` and `metadata.csv` generation
- configurable parameters through `config.yaml`

---

## 2. Repository Structure

```text
eeg-ecg-action-dataset-collector/
├── README.md              # Project documentation
├── config.yaml            # Acquisition and protocol configuration
├── requirements.txt       # Python dependencies
├── collect_dataset.py     # Main collection script
├── realtime_viewer.py     # Realtime EEG/ECG waveform viewer
├── serial_reader.py       # 12-channel serial data reader
├── recorder.py            # CSV recorder and session metadata manager
├── protocol.py            # 12-action protocol definition
├── preprocess.py          # Basic preprocessing utilities
├── data/
│   ├── raw/               # Raw collected data
│   └── processed/         # Processed data, optional
└── docs/
    └── protocol.md        # Detailed action protocol, optional
```

---

## 3. Environment Setup

Clone the repository:

```bash
git clone https://github.com/Garyneil/eeg-ecg-action-dataset-collector.git
cd eeg-ecg-action-dataset-collector
```

Recommended Python version:

```text
Python 3.8+
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The realtime viewer requires:

```text
PyQt5
pyqtgraph
```

If GUI installation fails on Linux or Jetson, install the Qt system package first:

```bash
sudo apt update
sudo apt install -y python3-pyqt5
pip install pyqtgraph
```

---

## 4. Hardware and Serial Protocol

The current implementation assumes that the acquisition device sends one frame in the following format:

```text
head byte + 12 signed 16-bit channel values + tail byte
```

Default frame structure:

```text
1 + 12 × 2 + 1 = 26 bytes
```

Default channel layout:

| Signal type | Number of channels |
|---|---:|
| EEG | 8 |
| ECG | 4 |
| Total | 12 |

Default serial parameters:

| Item | Default value |
|---|---:|
| Baudrate | 115200 |
| Sampling rate | 250 Hz |
| Head byte | 255 |
| Tail byte | 254 |

---

## 5. Configuration

The main configuration file is `config.yaml`.

Current default serial configuration:

```yaml
runtime:
  source: "serial12hex"
  source_args:
    port: "/dev/ttyTHS0"
    baudrate: 115200
    head: 255
    tail: 254
    fs: 250.0
    scale_eeg: 1.0
    scale_ecg: 1.0
    eeg_channels: 8
    ecg_channels: 4
```

For Jetson UART, the default port is usually:

```yaml
port: "/dev/ttyTHS0"
```

For USB serial devices on Linux or Jetson, change it to something like:

```yaml
port: "/dev/ttyUSB0"
```

On Windows, the port is usually similar to:

```yaml
port: "COM3"
```

Dataset protocol parameters:

```yaml
dataset:
  save_dir: "data/raw"
  baseline_duration_sec: 30
  action_duration_sec: 5
  rest_duration_sec: 3
  trials_per_action: 20
```

Meaning:

| Parameter | Meaning | Default |
|---|---|---:|
| `save_dir` | root folder for raw data | `data/raw` |
| `baseline_duration_sec` | baseline recording duration | 30 s |
| `action_duration_sec` | duration of each action trial | 5 s |
| `rest_duration_sec` | preparation/rest countdown before each trial | 3 s |
| `trials_per_action` | number of trials per action | 20 |

---

## 6. Action Protocol

The project currently defines 12 action classes.

| ID | English label | Chinese label | Description |
|---:|---|---|---|
| 00 | `rest` | 静息 | baseline resting state |
| 01 | `left_hand_raise` | 左手抬起 | left upper-limb movement |
| 02 | `right_hand_raise` | 右手抬起 | right upper-limb movement |
| 03 | `both_hands_raise` | 双手抬起 | bilateral upper-limb movement |
| 04 | `left_hand_grasp` | 左手抓握 | left-hand grasping |
| 05 | `right_hand_grasp` | 右手抓握 | right-hand grasping |
| 06 | `left_arm_reach` | 左臂前伸 | left reaching movement |
| 07 | `right_arm_reach` | 右臂前伸 | right reaching movement |
| 08 | `head_turn_left` | 头向左转 | head turning left |
| 09 | `head_turn_right` | 头向右转 | head turning right |
| 10 | `walk_forward` | 向前走 | forward locomotion |
| 11 | `stop` | 停止 | motion stop state |

The baseline is stored as:

```text
trial_000_action_00_baseline_rest.csv
```

Then the action trials start from `trial_001`.

---

## 7. Realtime Waveform Viewer

The project provides a lightweight realtime viewer for checking the incoming EEG/ECG serial data stream before formal collection.

It can display:

- 8 EEG channels
- 4 ECG channels
- serial connection status
- realtime sampling rate
- accumulated sample count
- recent waveform window
- optional realtime CSV saving

Run the viewer:

```bash
python realtime_viewer.py --config config.yaml
```

Use a longer or shorter display window:

```bash
python realtime_viewer.py --config config.yaml --window-sec 10
```

The viewer is mainly used for signal checking and debugging. Formal dataset collection should still use `collect_dataset.py`.

```text
realtime_viewer.py      realtime signal monitoring
collect_dataset.py      formal dataset collection
```

---

## 8. How to Run on Jetson

### 8.1 Check the serial device

For the current Jetson setup, the default UART port is:

```text
/dev/ttyTHS0
```

Check available UART or USB serial devices:

```bash
ls /dev/ttyTHS*
ls /dev/ttyUSB*
```

Make sure `config.yaml` uses the correct port:

```yaml
runtime:
  source_args:
    port: "/dev/ttyTHS0"
```

### 8.2 Give serial permission

For Jetson UART:

```bash
sudo chmod 666 /dev/ttyTHS0
```

For USB serial:

```bash
sudo chmod 666 /dev/ttyUSB0
```

### 8.3 Install dependencies on Jetson

```bash
sudo apt update
sudo apt install -y python3-pyqt5
pip install -r requirements.txt
```

If `PyQt5` cannot be installed by `pip` on Jetson, keep the system package and only install the rest manually:

```bash
pip install numpy pyyaml pyserial scipy pyqtgraph
```

### 8.4 Run realtime viewer on Jetson

```bash
python realtime_viewer.py --config config.yaml
```

### 8.5 Run dry-run collection on Jetson

Dry-run mode tests the experimental flow without opening the serial port:

```bash
python collect_dataset.py --subject sub001 --config config.yaml --dry-run
```

### 8.6 Run formal collection on Jetson

```bash
python collect_dataset.py --subject sub001 --config config.yaml
```

Use a custom number of trials per action:

```bash
python collect_dataset.py --subject sub001 --config config.yaml --trials 10
```

---

## 9. How to Run on Windows

### 9.1 Check the COM port

Open **Device Manager** and check the serial device port, for example:

```text
COM3
COM4
COM5
```

Then update `config.yaml`:

```yaml
runtime:
  source_args:
    port: "COM3"
```

### 9.2 Install dependencies on Windows

```powershell
pip install -r requirements.txt
```

If the GUI packages are missing, install them manually:

```powershell
pip install PyQt5 pyqtgraph
```

### 9.3 Run realtime viewer on Windows

```powershell
python realtime_viewer.py --config config.yaml
```

### 9.4 Run dry-run collection on Windows

```powershell
python collect_dataset.py --subject sub001 --config config.yaml --dry-run
```

### 9.5 Run formal collection on Windows

```powershell
python collect_dataset.py --subject sub001 --config config.yaml
```

Use a custom number of trials per action:

```powershell
python collect_dataset.py --subject sub001 --config config.yaml --trials 10
```

---

## 10. Real-Time Countdown During Collection

The collector provides countdown guidance for both preparation and recording.

Example terminal output:

```text
Action 01 | left_hand_raise | 左手抬起 | trial 1/20
Prepare: Raise the left hand naturally.
  remaining: 03s
Now perform action: left_hand_raise / 左手抬起
  recording countdown: 05s | samples: 0
  recording countdown: 04s | samples: 249
  recording countdown: 03s | samples: 501
  recording countdown: 02s | samples: 752
  recording countdown: 01s | samples: 1001
  recording countdown: 00s | samples: 1250
Saved: data/raw/sub001/session_20260530_153012/trial_001_action_01_left_hand_raise.csv
```

This makes it clear when the subject should prepare, start the action, and stop.

---

## 11. Data Saving Structure

Every run creates a new independent session folder to avoid overwriting previous data.

Example:

```text
data/raw/
└── sub001/
    └── session_20260530_153012/
        ├── trial_000_action_00_baseline_rest.csv
        ├── trial_001_action_01_left_hand_raise.csv
        ├── trial_002_action_01_left_hand_raise.csv
        ├── ...
        ├── metadata.json
        └── metadata.csv
```

The session folder name is automatically generated from the current time:

```text
session_YYYYMMDD_HHMMSS
```

Example:

```text
session_20260530_153012
```

---

## 12. CSV Data Format

Each trial is saved as an individual CSV file.

CSV header:

```csv
timestamp,subject_id,session_id,trial_id,action_id,action_name,eeg_1,eeg_2,eeg_3,eeg_4,eeg_5,eeg_6,eeg_7,eeg_8,ecg_1,ecg_2,ecg_3,ecg_4
```

Example row:

```csv
0.004,sub001,session_20260530_153012,001,01,left_hand_raise,12.0,15.0,10.0,13.0,9.0,14.0,11.0,16.0,100.0,102.0,98.0,101.0
```

Column description:

| Column | Meaning |
|---|---|
| `timestamp` | relative timestamp generated by the serial reader |
| `subject_id` | subject ID specified by `--subject` |
| `session_id` | current collection session |
| `trial_id` | trial index |
| `action_id` | action class ID |
| `action_name` | action label |
| `eeg_1` ~ `eeg_8` | EEG channels |
| `ecg_1` ~ `ecg_4` | ECG channels |

The realtime viewer CSV format is simpler and is used only for quick signal checking:

```csv
timestamp,EEG1,EEG2,EEG3,EEG4,EEG5,EEG6,EEG7,EEG8,ECG1,ECG2,ECG3,ECG4
```

---

## 13. Metadata Files

Each session automatically generates two metadata files:

```text
metadata.json
metadata.csv
```

They record the full collection session and each trial.

Main fields:

| Field | Meaning |
|---|---|
| `subject_id` | subject ID |
| `session_id` | session folder name |
| `trial_id` | trial index |
| `action_id` | action class ID |
| `action_name` | action label |
| `start_time` | trial start time |
| `duration_sec` | configured duration |
| `num_samples` | number of collected samples |
| `relative_file_path` | trial CSV path relative to the session folder |
| `absolute_file_path` | absolute trial CSV path |
| `note` | additional note, such as local trial index |

`metadata.json` also stores the configuration used for the session.

This is useful for:

- checking whether trials were recorded successfully
- verifying the number of samples per trial
- tracing each CSV file back to its action label
- documenting the dataset collection process for experiments or papers

---

## 14. Recommended Collection Workflow

Recommended workflow for each subject:

```text
1. Connect EEG/ECG device
2. Check serial port and config.yaml
3. Run realtime_viewer.py to inspect the waveform
4. Check whether the sampling rate is stable
5. Run dry-run mode
6. Confirm countdown and action order
7. Start formal collection
8. Check generated session folder
9. Check metadata.csv and metadata.json
10. Back up the session folder
```

Jetson example:

```bash
sudo chmod 666 /dev/ttyTHS0
python realtime_viewer.py --config config.yaml
python collect_dataset.py --subject sub001 --config config.yaml --dry-run
python collect_dataset.py --subject sub001 --config config.yaml
```

Windows example:

```powershell
python realtime_viewer.py --config config.yaml
python collect_dataset.py --subject sub001 --config config.yaml --dry-run
python collect_dataset.py --subject sub001 --config config.yaml
```

---

## 15. Common Problems

### 15.1 `TypeError: 'NoneType' object is not subscriptable`

This usually means `config.yaml` is empty or broken.

Make sure `config.yaml` does not contain copied HTML tags such as:

```text
<br/>
```

### 15.2 Serial port permission denied on Jetson or Linux

For Jetson UART:

```bash
sudo chmod 666 /dev/ttyTHS0
```

For USB serial:

```bash
sudo chmod 666 /dev/ttyUSB0
```

### 15.3 Wrong serial port

On Jetson or Linux, check available devices:

```bash
ls /dev/ttyTHS*
ls /dev/ttyUSB*
```

On Windows, check the port in **Device Manager** and update `config.yaml`, for example:

```yaml
port: "COM3"
```

### 15.4 Realtime viewer does not open on Jetson

Install the Qt system package:

```bash
sudo apt update
sudo apt install -y python3-pyqt5
pip install pyqtgraph
```

If you are using SSH without desktop forwarding, run the viewer directly on a Jetson desktop environment, or use a proper X11 forwarding setup.

### 15.5 Realtime waveform is flat or abnormal

Check:

- whether the EEG/ECG device is powered on
- whether the serial baudrate is correct
- whether the frame head and tail bytes match the hardware protocol
- whether electrode contact is stable
- whether `scale_eeg` and `scale_ecg` are set properly

### 15.6 Data not saved where expected

Formal collection saves data inside a session folder:

```text
data/raw/<subject_id>/<session_id>/
```

Example:

```text
data/raw/sub001/session_20260530_153012/
```

### 15.7 Repeated collection overwrites old data

This should not happen in the current version. Every formal run creates a new session folder.

---

## 16. Notes for Dataset Quality

For cleaner data, follow these rules:

- keep electrode contact stable before starting
- keep the subject relaxed during baseline recording
- check realtime waveform before formal collection
- keep each action execution consistent across trials
- avoid unnecessary body movement during upper-limb actions
- record abnormal events manually if they occur
- check `num_samples` in `metadata.csv` after collection
- back up each completed session folder immediately

---

## 17. Future Work

Planned improvements:

- automatic signal quality assessment
- GUI-based experiment guidance
- audio prompts for each action
- support for additional modalities such as EDA, respiration, or temperature
- optional LSL/XDF synchronization backend
- dataset export scripts for machine learning pipelines

---

## Author

Garyneil

GitHub: [Garyneil](https://github.com/Garyneil)
