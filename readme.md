## MacFanControl
Python daemon to control fan speeds of macbooks using the applemsc (and coretemp) modules.

## Requirements

  - applesmc
  - python-daemon - apt-get install python-daemon

## Config
This is a example config for a MacBookPro Retina, and should be located in /etc/macfancontrol.conf
The controller will find the highest speed based on the list of config options provided.

    [
            {
                "fans":[1, 2], // List of fans to use for a list of possible fans check the log file.
                "max_speed": 5900, // Max RPM of the fans
                "min_speed": 2000, // Min speed of the fans
                /*
                    Sensors to use for a full list of sensors check out the log file
                 */
                "sensors":["Core 1", "Core 2", "Core 3", "Core 0"],
                /*
                  What temperature to use from the sensors list
                   - average - the average temp found from all sensors listed.
                   - max - The highest temp found out of all sensors listed.
                 */
                "sensor_type":"average",

                /*
                 Speed of the fan in percentage above the minimum,
                    0.0 = min_speed
                    0.8 = 80% between min and max speeds
                    1.0 = max_speed
                 */
                "control":[
                    {"temp": 30, "speed":0.0},
                    {"temp": 45, "speed":0.15},
                    {"temp": 50, "speed":0.2},
                    {"temp": 55, "speed":0.25},
                    {"temp": 60, "speed":0.4},
                    {"temp": 65, "speed":0.6},
                    {"temp": 75, "speed":0.8},
                    {"temp": 80, "speed":1}
                ]
            }, {
                "fans":[1],
                "max_speed": 5900,
                "min_speed": 2000,
                "sensors":["TC0P"],
                "sensor_type":"average",
                "control":[
                    {"temp": 30, "speed":0.0},
                    {"temp": 45, "speed":0.15},
                    {"temp": 50, "speed":0.2},
                    {"temp": 55, "speed":0.25},
                    {"temp": 60, "speed":0.4},
                    {"temp": 65, "speed":0.6},
                    {"temp": 75, "speed":0.8},
                    {"temp": 80, "speed":1}
                ]
            }
    ]

## Errors
Everything is logged to /var/log/macfancontrol.log


