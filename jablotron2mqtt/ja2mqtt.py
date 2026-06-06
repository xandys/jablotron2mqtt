#!/usr/bin/env python

import logging
import paho.mqtt.client as mqtt
from time import sleep
from jablotron import Jablotron6x
from jablotron.jablotron6x import RemoveDuplicities


# translates modes from jablotron to modes
# expected by home assistant mqtt panel
MODE_MAP = [
	('armed_home', lambda mode: mode == 'armedA'),
	('armed_away', lambda mode: mode.startswith('armed')),
	('pending', lambda mode: mode.startswith('arming')),
	('triggered', lambda mode: 'alarm' in mode),
	('disarmed', lambda mode: True),
]

class Jablotron2mqtt(object):

	def __init__(self, jablotron_port="/dev/ttyUSB0",
			mqtt_host="127.0.0.1", mqtt_port=1883,
			mqtt_topic="alarm",
			mqtt_username="",mqtt_password=""):

		self.alarm = None
		self.mqttc = None
		self.topic = ""
		self.mqtt_connected = False
		self.reconnect_timeout = 30
		self._cached_mode = None
		self._cached_display = None
		self._cached_leds = {}

		self._setup_mqtt(mqtt_host, mqtt_port, mqtt_topic, mqtt_username, mqtt_password)
		self._setup_jablotron(jablotron_port)

		self._msg_handlers = {
			"key/press": self.on_mqtt_key_press,
			"config/request": self.on_mqtt_config_request,
		}
		self._mqtt_topics = [self.topic + "/" + t for t in self._msg_handlers]

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.publish("online", 0, retain=True)
		self.mqttc.disconnect()
		self.alarm.__exit__(exc_type, exc_val, exc_tb)


	def _setup_mqtt(self, host, port, topic, username, password):

		self.topic = topic

		self.mqttc=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5, client_id="jablotron")
		
		logger = logging.getLogger(__name__)
		self.mqttc.enable_logger(logger)

		self.mqttc.username_pw_set(username, password)

		self.mqttc.on_connect=self.on_mqtt_connect
		self.mqttc.on_message=self.on_mqtt_message
		self.mqttc.on_disconnect=self.on_mqtt_disconnect

		self.mqttc.will_set("{0}/online".format(self.topic), 0, retain=True)

		self.mqttc.connect(host, port=int(port), keepalive=60)

	def _setup_jablotron(self, port):
		self.alarm = Jablotron6x(port)
		self.alarm.register_callback(RemoveDuplicities(), mask=[0xe0])
		self.alarm.register_callback(self.on_alarm_message)

		self.alarm.on_key_press = self.on_alarm_key
		self.alarm.on_mode_change = self.on_alarm_mode
		self.alarm.on_display_change = self.on_alarm_display
		self.alarm.on_led_change = self.on_alarm_led

		self.alarm.__enter__()

	def publish(self, topic, msg, retain=False):
		if not self.mqtt_connected:
			return False

		info = self.mqttc.publish("{0}/{1}".format(self.topic, topic), msg, retain=retain)
		return info.rc == mqtt.MQTT_ERR_SUCCESS

	def on_mqtt_connect(self, client, userdata, flags, rc, properties):
		if rc.value != 0:
			logging.error("MQTT connection refused: %s", rc)
			return
		for topic in self._mqtt_topics:
			logging.debug("Subscribed: " + topic)
			client.subscribe(topic)
		self.mqtt_connected = True
		self.publish("online", 1, retain=True)
		ip = client.socket().getsockname()[0]
		self.publish("ip", ip, retain=True)
		if self._cached_mode is not None:
			self.publish("mode", self._cached_mode, retain=True)
		if self._cached_display is not None:
			self.publish("display", self._cached_display, retain=True)
		for name, val in self._cached_leds.items():
			self.publish("leds/{0}".format(name), val, retain=True)
		logging.info("Connected to mqtt ...")

	def on_mqtt_disconnect(self, client, userdata, flags, rc, properties):
		logging.warning("Disconnected from mqtt ...")
		self.mqtt_connected=False

	def on_mqtt_message(self, client, userdata, msg):
		logging.debug("Message received {0}: {1}".format(msg.topic, msg.payload))
		if msg.topic not in self._mqtt_topics:
			logging.warning("{0} not in {1}".format(msg.topic, self._mqtt_topics))
			return

		topic = msg.topic[len(self.topic)+1:]
		logging.debug("Known topic received ... " + topic)

		self._msg_handlers[topic](client, msg.payload)

	def on_mqtt_config_request(self, client, msg):
		try:
			cmd = msg.decode('utf-8').strip().lower()
		except UnicodeDecodeError:
			return
		if cmd in ('gsm', 'all'):
			logging.debug("Requesting GSM config dump")
			self.alarm.send([0xec, 0x40, 0x07, 0x36, 0xff])
		if cmd in ('text', 'all'):
			logging.debug("Requesting GSM text dump")
			self.alarm.send([0xec, 0x40, 0x05, 0x19, 0xff])

	def on_mqtt_key_press(self, client, msg):
		try:
			key = msg.decode('utf-8')
		except UnicodeDecodeError:
			self.publish("key", "Error: invalid payload")
			return
		logging.debug("Pressing keys: " + key)
		try:
			self.alarm.send_keys(key)
		except ValueError:
			self.publish("key", "Error: invalid key")

	def on_alarm_message(self, buf):
		msg=" ".join(["%02x" % c for c in buf])
		logging.debug("Alarm message: " + msg)
		self.publish("raw", msg)
		if buf[0] == 0xe6:
			self._parse_e6(buf)
		elif buf[0] == 0xec:
			self._parse_ec(buf)
		return False   # pass the message to other registered handlers

	def _parse_e6(self, buf):
		# Format: e6 [?] [setting_id] [value] [checksum] [0xff]
		if len(buf) < 6:
			return
		setting_id = buf[2]
		value = buf[3]
		logging.debug("Switchboard config: setting %d = %d", setting_id, value)
		self.publish("config/switchboard/%d" % setting_id, value, retain=True)

	def _parse_ec(self, buf):
		# Format: ec [msg_type] [msg_id] [payload...] [checksum] [0xff]
		if len(buf) < 4:
			return
		msg_type = buf[1]
		msg_id = buf[2]
		payload = bytes(buf[3:-2])

		if msg_type == 0x00:
			logging.debug("GSM config: list terminator")
			return
		elif msg_type == 0x01:
			parts = payload.split(b'\x00')
			value = ','.join(p.decode('latin-1') for p in parts if p)
		elif msg_type == 0x02:
			value = str(payload[0]) if payload else "0"
		elif msg_type == 0x03:
			value = ' '.join('%02x' % b for b in payload)
		elif msg_type >> 4 == 0x02:
			base_id = (msg_type & 0x0f) * 100
			text = payload.rstrip(b'\x00').decode('latin-1', errors='replace')
			logging.debug("GSM config text: %d/%d = %r", base_id, msg_id, text)
			self.publish("config/gsm/text/%d/%d" % (base_id, msg_id), text, retain=True)
			return
		else:
			logging.debug("GSM config: unknown msg_type 0x%02x", msg_type)
			return

		logging.debug("GSM config: type 0x%02x id %d = %r", msg_type, msg_id, value)
		self.publish("config/gsm/%02x/%d" % (msg_type, msg_id), value, retain=True)

	def on_alarm_key(self, key):
		logging.debug("Alarm registered key press: " + key)
		self.publish("key", key)

	def on_alarm_mode(self, mode):
		logging.debug("Alarm mode changed: " + mode)
		for mqtt_mode, func in MODE_MAP:
			if func(mode):
				break
		logging.debug("Jablotron mode %s translated to mqtt mode %s" % (mode, mqtt_mode))
		self._cached_mode = mqtt_mode
		self.publish("mode", mqtt_mode, retain=True)

	def on_alarm_display(self, text):
		logging.debug("Alarm display changed: " + text)
		self._cached_display = text
		self.publish("display", text, retain=True)

	def on_alarm_led(self, **kwargs):
		for (key, val) in kwargs.items():
			logging.debug("Alarm led {0} changed to: {1}".format(key, "on" if val else "off"))
			self._cached_leds[key] = int(val)
			self.publish("leds/{0}".format(key), int(val), retain=True)

	def loop_forever(self):

		time_disconnected = 0

		while True:
			self.mqttc.loop(timeout=0.1)
			self.alarm.loop()
			if self.mqtt_connected:
				time_disconnected = 0
			else:
				time_disconnected += 0.1
				if time_disconnected > self.reconnect_timeout:
					logging.info("Reconnecting to mqtt ...")
					self.mqttc.reconnect()
					time_disconnected = 0
				sleep(0.1)


if __name__ == "__main__":

	logging.basicConfig(level=logging.DEBUG)

	with Jablotron2mqtt("/dev/ttyUSB0", "mqtt") as j2m:
		j2m.loop_forever()

