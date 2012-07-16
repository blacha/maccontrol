
import logging
import os
import glob
logger = logging.getLogger('maccontrol')


class FanControl:

    def __init__(self, applesmc):
        self.applesmc = applesmc
        self.fans = {}
        self.__read_fans()

    def has_fan(self, fan_id):
        return not self.fans.get(fan_id, None) is None

    def set_speed(self, fan_id, speed):
        fan = self.fans.get(fan_id, None)
        if fan is None:
            logger.error('Unable to set fanspeed for fan "%d" as it doesnt exist' % fan_id)
            return

        max_speed = int(fan['max'])
        if max_speed < speed:
            #logger.warn('Trying to set fanspeed "%d" above the max "%d" for fan %d (rpm has been limited to %d)' % (speed, max_speed, fan_id, max_speed))
            speed = max_speed

        last_speed = fan.get('last_speed', -1)
        if last_speed == speed:
            return

        logger.info('setting fan "%d" to %d rpm' % (fan_id, speed))
        fan['last_speed'] = speed

        filename = os.path.join(self.applesmc, 'fan%d_min' % fan_id)
        with open(filename, 'w') as f:
            f.write('%d' % speed)

    def __read_fans(self):
        self.fans = {}

        for fan_min in glob.glob(os.path.join(self.applesmc, 'fan*_min')):
            fan = {}
            fan_id = os.path.basename(fan_min)[3:]
            fan_id = int(fan_id[:fan_id.find('_')])
            for prop in ['label', 'max', 'min']:
                fan[prop] = self.__read_fan(fan_id, prop)

            if fan.get('min', None) is None:
                logger.error('unable to read information for fan %d' % fan_id)
                continue

            logger.info('Found fan: "%s" max RPM : %s' % (fan['label'], fan['max']))

            self.fans[fan_id] = fan

    def __read_fan(self, fan_id, prop=None):
        if prop is None:
            prop = 'min'

        with open(os.path.join(self.applesmc, 'fan%d_%s' % (fan_id, prop)), 'r') as f:
            return f.read().strip()
