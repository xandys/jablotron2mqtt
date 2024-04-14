from setuptools import setup

setup(name='jablotron2mqtt',
      version='0.1',
      description='Bridge for interfacing jablotron 6x alarms via MQTT',
      url='https://github.com/xandys/py-jablotron6x',
      packages=['jablotron2mqtt'],
      install_requires=[
        'jablotron',
        'paho-mqtt',
      ],
      zip_safe=False,
)

