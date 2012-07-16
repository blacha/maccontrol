import os
import json
import logging

DEFAULT_CONFIG = {
    "sleep": 2,
    "window": 3,
    "backlight": [
        {"sensor": 10, "brightness": 50},
        {"sensor": 10, "brightness": 50},
        {"sensor": 7, "brightness": 100},
        {"sensor": 6, "brightness": 150},
        {"sensor": 5, "brightness": 175},
        {"sensor": 4, "brightness": 200},
        {"sensor": 3, "brightness": 225}
    ],
    "fan": [{
        "fans":[0, 1],
        "max_speed": 6000,
        "min_speed": 2000,
        "sensors":["Core 1", "Core 2", "Core 3", "Core 0"],
        "sensor_type":"average",
        "control":[
            {"temp": 30, "speed":0.0},
            {"temp": 40, "speed":0.2},
            {"temp": 50, "speed":0.4},
            {"temp": 75, "speed":0.8},
            {"temp": 80, "speed":1}
        ]
    }]
}

logger = logging.getLogger('maccontrol')

SLEEP_TIME = 2
SLIDING_WINDOW = 3


class FanConfig:
    sliding_window = 5
    sleep_time = 2

    def __init__(self, config_file):
        self.load_config(config_file)

    def load_config(self, config_file):
        if not os.path.isfile(config_file):
            logger.warn('Config file "%s" does not exist using defaults' % config_file)
            self.cfg = DEFAULT_CONFIG
            return self.__verify_config(self.cfg)

        with open(config_file, 'r') as config:
            cfg = json.load(config)

        self.sensors = []
        self.fans = []

        self.sliding_window = cfg.get('window', SLIDING_WINDOW)
        self.sleep_time = cfg.get('sleep', SLEEP_TIME)

        if self.sleep_time < 0.5:
            logger.error('Unable to set sleep time < 0.5 seconds')
            self.sleep_time = 0.5

        self.backlight = cfg.get('backlight', None)

        fan_config = cfg['fan']
        for controls in fan_config:
            self.sensors.extend(controls['sensors'])
            self.fans.extend(controls['fans'])

        self.fans = list(set(self.fans))
        self.sensors = list(set(self.sensors))

        self.cfg = cfg

    def get_required_sensors(self):
        return self.sensors

    def get_required_fans(self):
        return self.fans

    def get_keyboard_brightness(self, light):
        if self.backlight is None:
            return 100

        brightness = 0
        for sensor in self.backlight:
            if light < sensor.get('sensor'):
                brightness = sensor.get('brightness')

        return brightness

    def get_fan_speed(self, temp):
        fans = {}
        for controls in self.cfg['fan']:
            sensor_type = controls.get('sensor_type', None)
            if sensor_type is None or sensor_type == 'average':
                current_temp = self.__get_average(controls['sensors'], temp)
            else:
                current_temp = self.__get_max(controls['sensors'], temp)

            speed = 0

            for con in controls['control']:
                if con['temp'] > current_temp:
                    break

                speed = con['speed']

            if speed > 1:
                speed = 1
            if speed < 0:
                speed = 0

            # Actual speed of the fan is MinSpeed - MaxSpeed
            max_speed = controls['max_speed']
            min_speed = controls['min_speed']

            speed_diff = max_speed - min_speed

            speed_diff = speed_diff * speed

            speed = speed_diff + min_speed

            # if this speed is the fastest setting found for the fan
            # update its speed to match
            for fan in controls['fans']:
                fanspeed = fans.get(fan, None)

                if fanspeed is None:
                    fanspeed = 0

                if fanspeed < speed:
                    fans[fan] = speed

        return fans

    def __get_average(self, sensors, temps):
        total = 0.0
        count = 0
        for sensor in sensors:
            total += temps.get(sensor)['current']
            count += 1

        return total / count

    def __get_max(self, sensors, temps):
        max_temp = 0.0

        for sensor in sensors:
            current = temps.get(sensor)['current']
            if current > max_temp:
                max_temp = current

        return max_temp
