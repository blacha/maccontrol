import glob
import os
import fnmatch
import logging
import time
import control.config as config
from control.fan import FanControl
from control.backlight import BackLightControl
logger = logging.getLogger('maccontrol')


class MacControl():

    def __init__(self, config_file):
        self.config_file = config_file
        self.coretemp = None
        self.applesmc = None
        if not self.__find_sys_dirs():
            if self.applesmc is None:
                logger.error('Unable to find applesmc directory in /sys')
                exit()
            if self.coretemp is None:
                logger.warn('Unable to find coretemp directory in /sys, falling back on applesmc temps')

        self.fc = FanControl(self.applesmc)
        self.kb = BackLightControl(self.applesmc)

        self.sensors = {}
        self.__load_coretemp()
        self.__load_applesmc()
        self.load_config(config_file)

        self.light_log = []

    def load_config(self, config_file=None):
        errors = False
        if config_file is None:
            config_file = self.config_file

        cfg = config.FanConfig(config_file)
        if cfg is None:
            logger.error('Unable to parse config file "%s" ' % config_file)
            return False

        sensors = cfg.get_required_sensors()
        # Make sure all the required sensors exist before starting
        for sensor in sensors:
            if self.sensors.get(sensor, None) is None:
                logger.error('Unable to find sensor data for sensor : "%s" ' % sensor)
                errors = True

        fans = cfg.get_required_fans()

        for fan in fans:
            if not self.fc.has_fan(fan):
                logger.error('Unable to find fan data for fan : "%d" ' % fan)
                errors = True

        if errors:
            self.cfg = None
            return False

        self.cfg = cfg

    def run_sensors(self):
        sensors = self.cfg.get_required_sensors()

        for sensor in sensors:
            s = self.sensors.get(sensor)
            if s.get('current_log', None) is None:
                s['current_log'] = []

            s['current_log'].append(int(self.__read_temp(s)) / 1000)

            while len(s['current_log']) > self.cfg.sliding_window:
                s['current_log'].pop(0)

            s['current'] = sum(s['current_log']) / len(s['current_log'])

        fans = self.cfg.get_fan_speed(self.sensors)

        for fan in fans:
            self.fc.set_speed(fan, fans[fan])

    def run_light(self):
        light = self.kb.get_light()

        self.light_log.append(light)
        while len(self.light_log) > self.cfg.sliding_window:
            self.light_log.pop(0)

        light_avg = sum(self.light_log) / len(self.light_log)

        brightness = self.cfg.get_keyboard_brightness(light_avg)
        self.kb.set_brightness(brightness)

    def run(self):
        while 1:
            if self.cfg is None:
                break

            # Check lighting and adjust keyboard backlight
            self.run_light()

            # Check the CPU temp and adjust fan speed
            self.run_sensors()

            time.sleep(self.cfg.sleep_time)

    def __find_sys_dirs(self):
        base_dir = '/sys/devices'

        for root, dirnames, filenames in os.walk(base_dir):
            for dirname in fnmatch.filter(dirnames, 'applesmc*'):
                self.applesmc = os.path.join(root, dirname)
                logger.debug('found applesmc in "%s"' % self.applesmc)

            for dirname in fnmatch.filter(dirnames, 'coretemp.*'):
                self.coretemp = os.path.join(root, dirname)
                logger.debug('found coretemp in "%s"' % self.coretemp)

            if not self.coretemp is None and not self.applesmc is None:
                return True

        return False

    def __load_coretemp(self):

        if self.coretemp is None:
            return

        for temp in glob.glob(os.path.join(self.coretemp, 'temp*_label')):
            temp_id = os.path.basename(temp)[4:]
            temp_id = int(temp_id[:temp_id.find('_')])

            temp_info = {'id': temp_id}
            temp_info['label'] = self.__read_file(temp)
            temp_info['path'] = os.path.join(self.coretemp, 'temp%d_input' % temp_id)

            logger.info('Found sensor: "%s"' % temp_info['label'])
            self.sensors[temp_info['label']] = temp_info

    def __load_applesmc(self):
        for label in glob.glob(os.path.join(self.applesmc, 'temp*_label')):
            sensor = {}
            sensor_id = os.path.basename(label)[4:]
            sensor_id = int(sensor_id[:sensor_id.find('_')])

            sensor['id'] = sensor_id
            sensor['path'] = os.path.join(self.applesmc, 'temp%d_input' % sensor_id)
            sensor['label'] = self.__read_file(label)

            logger.info('Found sensor: %s' % sensor['label'])
            self.sensors[sensor['label']] = sensor

        self.light = os.path.join(self.applesmc, 'light')
        if not os.path.isfile(self.light):
            self.light = None

    def __read_temp(self, sensor):
        return self.__read_file(sensor['path'])

    def __read_file(self, filename):
        try:
            with open(filename, 'r') as f:
                return f.read().strip()
        except IOError, e:
            logger.error('Unable to read property from %s because %s' % (filename, e))
