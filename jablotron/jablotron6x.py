#!/usr/bin/env python
import serial
import sys
import collections
import logging
from time import sleep

# Key mapping for keypad to serial codes
KEY_MAP = {
    '0': 0x80, '1': 0x81, '2': 0x82, '3': 0x83, '4': 0x84,
    '5': 0x85, '6': 0x86, '7': 0x87, '8': 0x88, '9': 0x89,
    'N': 0x8E, 'F': 0x8F,
}
KEY_MAP_INVERSED = {v: k for k, v in list(KEY_MAP.items())}

# Display character mappings for status events
DISPLAY_MAP = {
    0x01: ' 1', 0x02: ' 2', 0x03: ' 3', 0x04: ' 4', 0x05: ' 5',
    0x06: ' 6', 0x07: ' 7', 0x08: ' 8', 0x09: ' 9', 0x0A: '10',
    0x0B: '11', 0x0C: '12', 0x0D: '13', 0x0E: '14', 0x0F: '15',
    0x10: '16', 0x11: ' A', 0x13: ' C', 0x14: ' d', 0x17: ' U',
    0x19: '  ', 0x1A: ' P', 0x1B: ' -', 0x1C: ' L', 0x1D: ' J',
    0x1E: '| ', 0x1F: ' |', 0x21: 'c1', 0x22: 'c2', 0x23: 'c3',
    0x24: 'c4', 0x25: 'c5', 0x26: 'c6', 0x27: 'c7', 0x28: 'c8',
}

# LED indicator mappings
LED_MAP = {
    0x01: 'power', 0x02: 'alarm', 0x04: 'tamper',
    0x10: 'lock', 0x20: 'blinking_lock', 0x40: 'wireless',
}

# Operational mode mappings
MODE_MAP = {
    0x00: 'service mode', 0x20: 'user mode', 0x40: 'disarmed',
    0x41: 'armed', 0x44: 'tamper alarm', 0x51: 'arming',
    0x61: 'armedA', 0x63: 'armedB', 0x71: 'armingA', 0x73: 'armingB',
}

EVENT_CONSUMED = True
EVENT_NOT_CONSUMED = False
_callback = collections.namedtuple('callback', 'function mask')

class Jablotron6x(object):
    """Interface with Jablotron 6x alarms using Ja-80T cable."""

    def __init__(self, device):
        self._device = device
        self._read_buffer = []
        self._callbacks = []
        self._on_key_press = None
        self._on_mode_change = None
        self._on_led_change = None
        self._on_display_change = None
        self.leds = 0x00
        self.mode = None
        self.display = None
        self._con = serial.Serial(
            baudrate=9600, parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS, dsrdtr=True, timeout=0.1)
        self._con.port = self._device
        self._register_internal_callbacks()

    def _register_internal_callbacks(self):
        for mask in list(KEY_MAP.values()):
            self.register_callback(self._handle_on_key_press, [mask])
        self.register_callback(self._handle_status_update, [0xe0])

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        self._con.open()
        return self

    def disconnect(self):
        if self._con.is_open:
            self._con.flush()
            self._con.close()
        return self

    def send(self, buf):
        for b in buf:
            self._con.write(bytes([b]))
        self._con.flush()
        return self

    def send_keys(self, keys):
        try:
            for k in keys:
                self.send([KEY_MAP[k]])
                sleep(0.1)
        except KeyError:
            raise ValueError("Invalid Keys: %s" % keys)
        return self

    def register_callback(self, callback, mask=None):
        c = _callback(function=callback, mask=mask if mask is not None else [])
        self._callbacks.append(c)
        return self

    def _handle_event(self, buf):
        for cb in self._callbacks:
            match = True
            for b, c in zip(buf, cb.mask):
                if c is None:
                    continue
                if b != c:
                    match = False
                    break
            if match:
                consume_event = cb.function(buf)
                if consume_event:
                    return

    def loop(self):
        while True:
            if not self._con.is_open:
                break
            b = self._con.read()
            if len(b) == 0:
                break
            b = ord(b)
            self._read_buffer.append(b)
            if (b == 0xFF):
                self._handle_event(self._read_buffer)
                self._read_buffer = []
        return self

    def loop_forever(self):
        while True:
            self.loop()

    def _handle_on_key_press(self, buf):
        for b in buf:
            try:
                key = KEY_MAP_INVERSED[b]
                self.on_key_press(key)
            except TypeError:
                pass
            except KeyError:
                pass
        return EVENT_NOT_CONSUMED

    @property
    def on_key_press(self):
        return self._on_key_press

    @on_key_press.setter
    def on_key_press(self, func):
        self._on_key_press = func

    def _handle_status_update(self, buf):
        if len(buf) < 4:
            logging.warning("Status frame too short (%d bytes)" % len(buf))
            return EVENT_NOT_CONSUMED

        if buf[1] != self.mode:
            self.mode = buf[1]
            try:
                text = MODE_MAP[self.mode]
            except KeyError:
                logging.error("MODE_MAP missing 0x%02x" % self.mode)
                text = "Mode 0x%02x" % self.mode
            if self.on_mode_change is not None:
                self.on_mode_change(text)

        if buf[2] != self.leds:
            args = {}
            for mask, name in list(LED_MAP.items()):
                new = buf[2] & mask
                old = self.leds & mask
                if new != old:
                    args[name] = bool(new)
            self.leds = buf[2]
            if self.on_led_change is not None:
                self.on_led_change(**args)

        if buf[3] != self.display:
            self.display = buf[3]
            try:
                text = DISPLAY_MAP[self.display & 0b01111111]
            except KeyError:
                logging.error("DISPLAY_MAP missing 0x%02x" % self.display)
                text = "0x%02x" % self.display
            if self.on_display_change is not None:
                self.on_display_change(text)

        return EVENT_NOT_CONSUMED

    @property
    def on_mode_change(self):
        return self._on_mode_change

    @on_mode_change.setter
    def on_mode_change(self, func):
        self._on_mode_change = func

    @property
    def on_led_change(self):
        return self._on_led_change

    @on_led_change.setter
    def on_led_change(self, func):
        self._on_led_change = func

    @property
    def on_display_change(self):
        return self._on_display_change

    @on_display_change.setter
    def on_display_change(self, func):
        self._on_display_change = func

def print_buffer(buf):
    print(("%s" % " ".join(["%02x" % c for c in buf])))
    return EVENT_NOT_CONSUMED

def consume_event(buf):
    return EVENT_CONSUMED

class RemoveDuplicities:
    def __init__(self):
        self._last = 0

    def __call__(self, buf):
        checksum = buf[len(buf)-2]
        if self._last == checksum:
            return EVENT_CONSUMED
        self._last = checksum
        return EVENT_NOT_CONSUMED

if __name__ == "__main__":
    with Jablotron6x("/dev/ttyUSB0") as j:
        j.register_callback(RemoveDuplicities(), mask=[0xe0])
        j.register_callback(print_buffer)
        j.loop_forever()
