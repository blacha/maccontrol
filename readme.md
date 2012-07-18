## MacControl
Python daemon to control keyboard backlight and fan speeds of macbooks using the applemsc (and coretemp) modules.


## Requirements

  - applesmc
  - python-daemon - apt-get install python-daemon

## Config
This is a example config for a MacBookPro Retina, and should be located in /etc/maccontrol.conf
The controller will find the highest speed based on the list of config options provided.

    {
        /* Time to sleep between updates (must be > 0.5 seconds) */
        "sleep": 1,
        /* Sliding window size to use for moinitoring Temp/Brightness */
        "window": 3,
        /*
            Backlight controls, will use the highest brightness it can based on the light input sensor
            Sensor values decrease for the darker it is.
             20 + direct sunlight
             12 - Bright Room light
           */
        "backlight": [
            {"sensor": 10, "brightness": 50},
            {"sensor": 7, "brightness": 100},
            {"sensor": 6, "brightness": 150},
            {"sensor": 5, "brightness": 175},
            {"sensor": 4, "brightness": 200},
            {"sensor": 3, "brightness": 225}
        ],

        "fan":[
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
    }

## Errors
Everything is logged to /var/log/macfancontrol.log


