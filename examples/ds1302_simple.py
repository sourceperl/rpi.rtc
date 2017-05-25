#!/usr/bin/env python3

import binascii
import datetime
import pyRPiRTC

rtc = pyRPiRTC.DS1302()

try:
    # read date and time from RTC chip
    print(rtc.read_datetime())

    # write current UTC date and time to chip
    rtc.write_datetime(datetime.datetime.utcnow())

    # read RAM and print dump
    print(binascii.hexlify(rtc.read_ram()))

    # write ram
    rtc.write_ram(b'\xDE\xAD\xBE\xEF')
finally:
    # clean close
    rtc.close()
