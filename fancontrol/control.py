import glob
import os
import fnmatch
import logging
import time
import fancontrol.config as config

logger = logging.getLogger('macfancontrol')


class FanControl():
    fan_properties = ['label', 'manual', 'max', 'min', 'output']
    coretemp_properties = ['label', 'crit', 'max']

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

        self.sensors = {}
        self.__load_coretemp()
        self.__load_applesmc()
        self.load_config(config_file)

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
            if self.fans.get(fan, None) is None:
                logger.error('Unable to find fan data for fan : "%d" ' % fan)
                errors = True

        if errors:
            self.cfg = None
            return False

        self.cfg = cfg

    def set_speed(self, fan_id, speed):
        fan = self.fans.get(fan_id, None)
        if fan is None:
            logger.error('Unable to set fanspeed for fan "%d" as it doesnt exist' % fan_id)
            return

        max_speed = int(fan['max'])
        if max_speed < speed:
            logger.warn('Trying to set fanspeed "%d" above the max "%d" for fan %d (rpm has been limited to %d)' % (speed, max_speed, fan_id, max_speed))
            speed = max_speed

        last_speed = fan.get('last_speed', -1)
        if last_speed == speed:
            return

        logger.info('setting fan "%d" to %d rpm' % (fan_id, speed))
        fan['last_speed'] = speed

        filename = os.path.join(self.applesmc, 'fan%d_min' % fan_id)
        with open(filename, 'w') as f:
            f.write('%d' % speed)

    def run(self):
        while 1:
            if self.cfg is None:
                break

            sensors = self.cfg.get_required_sensors()

            for sensor in sensors:
                s = self.sensors.get(sensor)
                s['current'] = int(self.__read_temp(s)) / 1000

            fans = self.cfg.get_fan_speed(self.sensors)

            for fan in fans:
                self.set_speed(fan, fans[fan])

            time.sleep(self.cfg.get_sleep_time())

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
        self.fans = {}

        for fan_min in glob.glob(os.path.join(self.applesmc, 'fan*_min')):
            fan = {}
            fan_id = os.path.basename(fan_min)[3:]
            fan_id = int(fan_id[:fan_id.find('_')])
            for prop in self.fan_properties:
                fan[prop] = self.__read_fan(fan_id, prop)

            if fan['min'] is None:
                logger.error('unable to read information for fan %d' % fan_id)
                continue

            logger.info('Found fan: "%s" max RPM : %s' % (fan['label'], fan['max']))

            self.fans[fan_id] = fan

        for label in glob.glob(os.path.join(self.applesmc, 'temp*_label')):
            sensor = {}
            sensor_id = os.path.basename(fan_min)[3:]
            sensor_id = int(sensor_id[:sensor_id.find('_')])

            sensor['id'] = sensor_id
            sensor['path'] = os.path.join(self.applesmc, 'temp%d_input' % sensor_id)
            sensor['label'] = self.__read_file(label)

            logger.info('Found sensor: %s' % sensor['label'])
            self.sensors[sensor['label']] = sensor

    def __read_temp(self, sensor):
        return self.__read_file(sensor['path'])

    def __read_fan(self, fan_id, config):
        filename = os.path.join(self.applesmc, 'fan%d_%s' % (fan_id, config))
        return self.__read_file(filename)

    def __read_file(self, filename):
        try:
            with open(filename, 'r') as f:
                return f.read().strip()
        except IOError, e:
            logger.error('Unable to read property from %s because %s' % (filename, e))
