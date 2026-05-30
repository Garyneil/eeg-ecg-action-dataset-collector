import time
from typing import Iterator, List

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


class Serial12HexReader:
    """Read 8-channel EEG and 4-channel ECG samples from a serial hex stream.

    This implementation assumes each frame is:
    head byte + 12 signed 16-bit channel values + tail byte.

    Default frame length:
    1 + 12 * 2 + 1 = 26 bytes.
    """

    def __init__(self, port, baudrate=115200, head=255, tail=254, eeg_channels=8, ecg_channels=4, fs=250.0, scale_eeg=1.0, scale_ecg=1.0):
        if serial is None:
            raise ImportError("pyserial is required. Please run: pip install pyserial")
        self.port = port
        self.baudrate = baudrate
        self.head = head
        self.tail = tail
        self.eeg_channels = eeg_channels
        self.ecg_channels = ecg_channels
        self.total_channels = eeg_channels + ecg_channels
        self.fs = fs
        self.scale_eeg = scale_eeg
        self.scale_ecg = scale_ecg
        self.frame_len = 1 + self.total_channels * 2 + 1
        self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=1)

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _read_frame(self):
        while True:
            b = self.ser.read(1)
            if not b:
                continue
            if b[0] == self.head:
                payload = self.ser.read(self.total_channels * 2)
                tail = self.ser.read(1)
                if len(payload) == self.total_channels * 2 and tail and tail[0] == self.tail:
                    return payload

    def _decode_payload(self, payload: bytes) -> List[float]:
        values = []
        for i in range(self.total_channels):
            start = i * 2
            raw = int.from_bytes(payload[start:start + 2], byteorder="big", signed=True)
            if i < self.eeg_channels:
                values.append(raw * self.scale_eeg)
            else:
                values.append(raw * self.scale_ecg)
        return values

    def samples(self) -> Iterator[List[float]]:
        start_time = time.time()
        while True:
            payload = self._read_frame()
            values = self._decode_payload(payload)
            timestamp = time.time() - start_time
            yield [timestamp] + values
