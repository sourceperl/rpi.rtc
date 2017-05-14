# rpi.rtc
Simple Python module to deal with DS1302 on Raspberry Pi

### Setup

    sudo python3 setup.py install
    sudo cp examples/* /usr/local/bin/

### Read RTC chip date and time

    rtc_get_time

### RPi date and time (UTC) to RTC chip

    rtc_set_utc

### Update Rpi system time from RTC chip

Typically call at RPi startup

    sudo update_sys_clock
