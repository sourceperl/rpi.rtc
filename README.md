# rpi.rtc
Simple Python module to deal with DS1302 RTC on Raspberry Pi

![](img/pi_rtc.jpg)

### Wire map (default conf.)

| Chip        | Rpi pin       |
| ----------- |:-------------:|
| VCC         | 3.3v pin      |
| GND         | GND pin       |
| CLK         | pin 11        |
| DATA        | pin 13        |
| CE (RST)    | pin 15        |

### Setup

    sudo apt-get -y install python3-rpi.gpio
    sudo python3 setup.py install

### Read RTC chip date and time

    ds1302_get_utc

### RPi date and time (UTC) to RTC chip

    ds1302_set_utc

### Update Rpi system time from RTC chip

Typically call at RPi startup

    sudo date -s `./ds1302_get_utc`

### One line to check RTC chip time vs system time

Since RTC store only second and not millisecond a 1s delta can occur (or more after a few days)

    # drift in second
    echo $(($(date -u -d`ds1302_get_utc` +%s) - $(date -u +%s)))
    # human readable
    echo "RTC `ds1302_get_utc`"; echo "SYS `date --utc +%FT%TZ`";