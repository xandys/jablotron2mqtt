#!/usr/bin/env python

import sys
import logging
import paho.mqtt.client as mqtt
from time import sleep
from jablotron import Jablotron6x
from jablotron.jablotron6x import remove_duplicities


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

	alarm=None
	mqttc=None
	topic=""
	mqtt_connected=False
	reconnect_timeout=30

	@property
	def _msg_handlers(self):
		return {
			"key/press": self.on_mqtt_key_press
			}

	@property
	def _mqtt_topics(self):
		return [ self.topic + "/" + t  for t in self._msg_handlers.keys() ]

	def __init__(self, jablotron_port="/dev/ttyUSB0", 
			mqtt_host="127.0.0.1", mqtt_port=1883,
			mqtt_topic="alarm"):

		self._setup_mqtt(mqtt_host, mqtt_port, mqtt_topic)
		self._setup_jablotron(jablotron_port)

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
		self.alarm.register_callback(remove_duplicities, mask=[0xe0])
		self.alarm.register_callback(self.on_alarm_message)

		self.alarm.on_key_press = self.on_alarm_key
		self.alarm.on_mode_change = self.on_alarm_mode
		self.alarm.on_display_change = self.on_alarm_display
		self.alarm.on_led_change = self.on_alarm_led

		self.alarm.connect()

	def publish(self, topic, msg, retain=False):
		if not self.mqtt_connected:
			return False

		info = self.mqttc.publish("{0}/{1}".format(self.topic, topic), msg, retain=retain)
		return info.rc == mqtt.MQTT_ERR_SUCCESS

	def on_mqtt_connect(self, client, userdata, flags, rc, properties):
		for topic in self._mqtt_topics:
			logging.debug("Subscribed: " + topic)
			client.subscribe(topic)
		self.mqtt_connected=True
		self.publish("online", 1, retain=True)
		ip=client.socket().getsockname()[0]
		self.publish("ip", ip, retain=True)
		logging.info("Connected to mqtt ...")

	def on_mqtt_disconnect(self, client, userdata, rc):
		logging.warning("Disconnected from mqtt ...")
		self.mqtt_connected=False

	def on_mqtt_message(self, client, userdata, msg):
		logging.debug("Message received {0}: {1}".format(msg.topic, msg.payload))
		if msg.topic not in self._mqtt_topics:
			print("{0} not in {1}".format(msg.topic, self._mqtt_topics))
			return

		topic = msg.topic[len(self.topic)+1:]
		logging.debug("Known topic received ... " + topic)

		self._msg_handlers[topic](client, msg.payload)

	def on_mqtt_key_press(self, client, msg):
		logging.debug("Pressing keys: "+msg)
		try:
			self.alarm.send_keys(msg)
		except ValueError as e:
			self.publish("key", "Error: invalid key")

	def on_alarm_message(self, buf):
		msg=" ".join(["%02x" % c for c in buf])
		logging.debug("Alarm message: " + msg)
		self.publish("raw", msg)
		return False   # pass the message to other registered handlers

	def on_alarm_key(self, key):
		logging.debug("Alarm registered key press: " + key)
		self.publish("key", key)

	def on_alarm_mode(self, mode):
		logging.debug("Alarm mode changed: " + mode)
		for mqtt_mode, func in MODE_MAP:
			if func(mode):
				break;
		logging.debug("Jablotron mode %s translated to mqtt mode %s" % (mode, mqtt_mode))
		self.publish("mode", mqtt_mode, retain=True)

	def on_alarm_display(self, text):
		logging.debug("Alarm display changed: " + text)
		self.publish("display", text, retain=True)

	def on_alarm_led(self, **kwargs):
		for (key, val) in kwargs.items():
			logging.debug("Alarm led {0} changed to: {1}".format(key, "on" if val else "off"))
			self.publish("leds/{0}".format(key), int(val), retain=True)

	def loop_forever(self):

		time_disconnected=0

		while True :
			self.mqttc.loop(timeout=0.1)
			if self.mqtt_connected:
				self.alarm.loop()
				time_disconnected=0
			else:
				if time_disconnected > self.reconnect_timeout:
					logging.info("Reconnecting to mqtt ...")
					self.mqttc.reconnect()
					time_disconnected=0
				time_disconnected+=0.1
				sleep(0.1)


if __name__ == "__main__":

	logging.basicConfig(level=logging.DEBUG)

	with Jablotron2mqtt("/dev/ttyUSB0", "mqtt") as j2m:
		j2m.loop_forever()

