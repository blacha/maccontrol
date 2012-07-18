import os
import logging

logger = logging.getLogger('maccontrol')
SENSOR_FILE = 'light'
BACKLIGHT_PATH = 'leds/smc::kbd_backlight'


class BackLightControl:
    max_brightness = 0
    current_brightness = 0
    light_sensor = None

    def __init__(self, applesmc):
        self.applesmc = applesmc
        self.light_sensor = os.path.join(self.applesmc, SENSOR_FILE)
        self.brightness_path = os.path.join(self.applesmc, BACKLIGHT_PATH, 'brightness')
        self.__get_max_brightness()
        self.get_brightness()

    def __get_max_brightness(self):
        with open(os.path.join(self.applesmc, BACKLIGHT_PATH, 'max_brightness'), 'r') as f:
            self.max_brightness = int(f.read().strip())

    def get_brightness(self):
        with open(self.brightness_path, 'r') as f:
            self.current_brightness = int(f.read().strip())
            return self.current_brightness

    def set_brightness(self, brightness):
        if self.current_brightness == brightness:
            return

        self.current_brightness = brightness

        with open(self.brightness_path, 'w') as f:
            f.write('%d' % brightness)

    def get_light(self):
        try:
            with open(self.light_sensor, 'r') as f:
                data = f.read().strip()
                self.current_light = int(data[1:data.find(',')])
                return self.current_light
        except IOError, e:
            logger.error('Unable to read %s as %s' % (self.light_sensor, e))
            return 0
