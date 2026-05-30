# EEG-ECG Multimodal Action Dataset Collector（脑电-心电多模态动作数据集采集系统）

A real-time multimodal physiological signal dataset collection system based on EEG and ECG devices. The project is designed to collect synchronized 8-channel EEG and 4-channel ECG signals through a serial 12-channel hexadecimal data stream, while guiding subjects to perform a predefined 12-class action protocol.

本项目是一个基于脑电（EEG）与心电（ECG）设备的多模态生理信号数据集采集系统。系统通过串口读取 12 通道十六进制数据流，其中包括 8 路 EEG 与 4 路 ECG 信号，并按照预设的 12 类动作实验范式进行数据采集、自动标注与保存。

---

## 1. Project Purpose / 项目目标

This repository is not primarily designed for model inference. Instead, it focuses on building a reusable physiological dataset collection platform for machine learning, affective computing, brain-computer interaction, and human-robot interaction research.

本仓库不是以模型推理为核心，而是用于构建一个可复用的 EEG/ECG 生理信号数据集采集平台，后续可服务于机器学习、情感计算、脑机接口、人机交互与机器人意图识别等研究任务。

The system supports:

系统支持：

- Real-time serial acquisition of physiological signals  
  实时串口采集生理信号
- 8-channel EEG and 4-channel ECG data collection  
  8 通道 EEG 与 4 通道 ECG 数据采集
- 12-class action-state experimental protocol  
  12 类动作状态实验范式
- Automatic timestamp, subject ID, trial ID, and action label recording  
  自动记录时间戳、被试编号、试次编号与动作标签
- CSV-based dataset storage  
  基于 CSV 的数据保存方式
- Configurable acquisition parameters through `config.yaml`  
  通过 `config.yaml` 配置采集参数

---

## 2. System Configuration / 系统配置

The default acquisition setting is defined in `config.yaml`.

默认采集配置写在 `config.yaml` 中。

```yaml
runtime:
  device: "cuda"
  window_sec: 0.5
  hop_sec: 0.1
  fs_eeg: 250.0
  fs_ecg: 250.0
  eeg_channels: "auto"
  eeg_channel_names: "auto"
  source: "serial12hex"
  source_args:
    port: "/dev/ttyUSB0"
    baudrate: 115200
    head: 255
    tail: 254
    fs: 250.0
    scale_eeg: 1.0
    scale_ecg: 1.0
    eeg_channels: 8
    ecg_channels: 4
```

The current hardware protocol assumes:

当前硬件协议假设：

| Item | Value | 中文说明 |
|---|---:|---|
| EEG channels | 8 | 8 路脑电通道 |
| ECG channels | 4 | 4 路心电通道 |
| Total channels | 12 | 共 12 路生理信号 |
| Sampling rate | 250 Hz | 采样率 250 Hz |
| Serial baudrate | 115200 | 串口波特率 115200 |
| Data source | serial12hex | 12 通道十六进制串口数据 |

---

## 3. Action Protocol / 动作实验范式

The project defines a 12-class common action protocol for EEG/ECG physiological dataset collection.

本项目设计了一套 12 类通用动作范式，用于 EEG/ECG 生理信号数据采集。

| ID | English Label | 中文动作 | Description / 说明 |
|---:|---|---|---|
| 00 | `rest` | 静息 | Baseline resting state / 基线静息状态 |
| 01 | `left_hand_raise` | 左手抬起 | Left upper-limb movement / 左侧上肢运动 |
| 02 | `right_hand_raise` | 右手抬起 | Right upper-limb movement / 右侧上肢运动 |
| 03 | `both_hands_raise` | 双手抬起 | Bilateral coordinated movement / 双侧协调动作 |
| 04 | `left_hand_grasp` | 左手抓握 | Left-hand fine motor action / 左手精细动作 |
| 05 | `right_hand_grasp` | 右手抓握 | Right-hand fine motor action / 右手精细动作 |
| 06 | `left_arm_reach` | 左臂前伸 | Left reaching action / 左侧到达动作 |
| 07 | `right_arm_reach` | 右臂前伸 | Right reaching action / 右侧到达动作 |
| 08 | `head_turn_left` | 头向左转 | Head movement to the left / 头部左转 |
| 09 | `head_turn_right` | 头向右转 | Head movement to the right / 头部右转 |
| 10 | `walk_forward` | 向前走 | Whole-body locomotion / 全身运动 |
| 11 | `stop` | 停止 | Motion termination state / 运动终止状态 |

---

## 4. Recommended Collection Procedure / 推荐采集流程

For each subject, the recommended protocol is:

每位被试推荐采用如下采集流程：

```text
Wear EEG/ECG devices and check signal quality
佩戴脑电/心电设备并检查信号质量
        ↓
Input subject ID
输入被试编号
        ↓
Collect 30-second baseline data
采集 30 秒静息基线数据
        ↓
Run 12-class action protocol
执行 12 类动作实验范式
        ↓
Repeat each action for multiple trials
每个动作重复多个试次
        ↓
Record timestamp, subject ID, trial ID, action label, EEG, and ECG
记录时间戳、被试编号、试次编号、动作标签、EEG 与 ECG
        ↓
Save dataset files as CSV
保存为 CSV 数据文件
```

Default trial design:

默认试次设计：

| Parameter | Default | 中文说明 |
|---|---:|---|
| Baseline duration | 30 s | 静息基线 30 秒 |
| Action duration | 5 s | 每个动作持续 5 秒 |
| Rest duration | 3 s | 动作间休息 3 秒 |
| Trials per action | 20 | 每类动作 20 次 |
| Sampling rate | 250 Hz | 采样率 250 Hz |

---

## 5. Dataset Format / 数据集格式

Each recorded row contains timestamp, subject information, action labels, and physiological channels.

每一行数据包含时间戳、被试信息、动作标签以及生理信号通道。

```csv
timestamp,subject_id,trial_id,action_id,action_name,eeg_1,eeg_2,eeg_3,eeg_4,eeg_5,eeg_6,eeg_7,eeg_8,ecg_1,ecg_2,ecg_3,ecg_4
```

Example:

示例：

```csv
0.000,sub001,001,00,rest,0.12,0.14,0.10,0.11,0.09,0.13,0.15,0.12,0.31,0.33,0.30,0.32
```

---

## 6. Project Structure / 项目结构

```text
eeg-ecg-action-dataset-collector/
├── README.md              # Bilingual project documentation / 中英双语项目说明
├── config.yaml            # Acquisition and protocol configuration / 采集与实验配置
├── requirements.txt       # Python dependencies / Python 依赖
├── collect_dataset.py     # Main collection entry point / 主采集入口
├── serial_reader.py       # 12-channel serial reader / 12 通道串口读取
├── protocol.py            # 12-action protocol definition / 12 类动作范式
├── recorder.py            # CSV dataset recorder / CSV 数据保存
├── preprocess.py          # Basic filtering and normalization utilities / 基础预处理工具
├── data/
│   ├── raw/               # Raw collected data / 原始采集数据
│   └── processed/         # Processed data / 处理后数据
└── docs/
    └── protocol.md        # Detailed action protocol / 动作范式说明
```

---

## 7. Installation / 环境安装

```bash
git clone https://github.com/Garyneil/eeg-ecg-action-dataset-collector.git
cd eeg-ecg-action-dataset-collector
pip install -r requirements.txt
```

---

## 8. Usage / 使用方法

Connect the EEG/ECG acquisition device and check the serial port in `config.yaml`.

连接 EEG/ECG 采集设备，并检查 `config.yaml` 中的串口配置。

```yaml
port: "/dev/ttyUSB0"
baudrate: 115200
```

Start collection:

开始采集：

```bash
python collect_dataset.py --subject sub001 --config config.yaml
```

Use a custom number of trials per action:

自定义每个动作的重复次数：

```bash
python collect_dataset.py --subject sub001 --trials 10 --config config.yaml
```

The collected files will be saved to:

采集数据将保存到：

```text
data/raw/sub001/
```

---

## 9. Notes / 注意事项

- Ensure that the EEG/ECG device is correctly connected before data collection.  
  采集前请确认 EEG/ECG 设备已正确连接。
- Make sure the serial port path matches the actual device path.  
  请确认串口路径与实际设备一致。
- Keep the subject relaxed during baseline recording.  
  静息基线采集时请保持被试放松。
- Keep action execution consistent across trials.  
  每个动作在不同试次中应尽量保持执行方式一致。
- This project provides the dataset collection framework; downstream model training should be implemented separately.  
  本项目提供数据集采集框架，后续模型训练可在其他项目中完成。

---

## 10. Future Work / 后续计划

- Add real-time waveform visualization  
  增加实时波形可视化
- Add automatic data quality assessment  
  增加自动数据质量评估
- Add GUI-based experiment guidance  
  增加图形化实验引导界面
- Support additional physiological modalities such as EDA and respiration  
  支持 EDA、呼吸等更多生理模态
- Add dataset export tools for machine learning pipelines  
  增加面向机器学习的数据导出工具

---

## Author / 作者

Garyneil

GitHub: [Garyneil](https://github.com/Garyneil)
