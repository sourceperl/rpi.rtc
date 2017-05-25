import time
import datetime
import RPi.GPIO as GPIO


class DS1302:
    # 5us
    CLK_DELAY = 5E-6

    def __init__(self, clk_pin=11, data_pin=13, ce_pin=15):
        # init GPIO
        # no warnings
        GPIO.setwarnings(False)
        # use safer pin number (avoid GPIO renumber on each Pi release)
        GPIO.setmode(GPIO.BOARD)
        # set GPIO pins
        self._clk_pin = clk_pin
        self._data_pin = data_pin
        self._ce_pin = ce_pin
        # CLK and CE (sometime call RST) pin are always output
        GPIO.setup(self._clk_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self._ce_pin, GPIO.OUT, initial=GPIO.LOW)
        # turn off WP (write protect)
        self._start_tx()
        self._w_byte(0x8e)
        self._w_byte(0x00)
        self._end_tx()
        # charge mode is disabled
        self._start_tx()
        self._w_byte(0x90)
        self._w_byte(0x00)
        self._end_tx()

    def _start_tx(self):
        """
        Start of transaction.
        """
        GPIO.output(self._clk_pin, GPIO.LOW)
        GPIO.output(self._ce_pin, GPIO.HIGH)

    def _end_tx(self):
        """
        End of transaction.
        """
        GPIO.setup(self._data_pin, GPIO.IN)
        GPIO.output(self._clk_pin, GPIO.LOW)
        GPIO.output(self._ce_pin, GPIO.LOW)

    def _r_byte(self):
        """
        Read byte from the chip.

        :return: byte value
        :rtype: int
        """
        # data pin is now input (pull-down resistor embedded in chip)
        GPIO.setup(self._data_pin, GPIO.IN)
        # clock the byte from chip
        byte = 0
        for i in range(8):
            # make a high pulse on CLK pin
            GPIO.output(self._clk_pin, GPIO.HIGH)
            time.sleep(self.CLK_DELAY)
            GPIO.output(self._clk_pin, GPIO.LOW)
            time.sleep(self.CLK_DELAY)
            # chip out data on clk falling edge: store current bit into byte
            bit = GPIO.input(self._data_pin)
            byte |= ((2 ** i) * bit)
        # return byte value
        return byte

    def _w_byte(self, byte):
        """
        Write byte to the chip.

        :param byte: byte value
        :type byte: int
        """
        # data pin is now output
        GPIO.setup(self._data_pin, GPIO.OUT)
        # clock the byte to chip
        for _ in range(8):
            GPIO.output(self._clk_pin, GPIO.LOW)
            time.sleep(self.CLK_DELAY)
            # chip read data on clk rising edge
            GPIO.output(self._data_pin, byte & 0x01)
            byte >>= 1
            GPIO.output(self._clk_pin, GPIO.HIGH)
            time.sleep(self.CLK_DELAY)

    def read_ram(self):
        """
        Read RAM as bytes

        :return: RAM dumps
        :rtype: bytearray
        """
        # start of message
        self._start_tx()
        # read ram burst
        self._w_byte(0xff)
        # read data bytes
        byte_a = bytearray()
        for _ in range(31):
            byte_a.append(self._r_byte())
        # end of message
        self._end_tx()
        return byte_a

    def write_ram(self, byte_a):
        """
        Write RAM with bytes

        :param byte_a: bytes to write
        :type byte_a: bytearray
        """
        # start message
        self._start_tx()
        # write ram burst
        self._w_byte(0xfe)
        # write data bytes
        for i in range(min(len(byte_a), 31)):
            self._w_byte(ord(byte_a[i:i + 1]))
        # end of message
        self._end_tx()

    def read_datetime(self):
        """
        Read current date and time from RTC chip.

        :return: date and time
        :rtype: datetime.datetime
        """
        # start message
        self._start_tx()
        # read clock burst
        self._w_byte(0xbf)
        byte_l = []
        for _ in range(7):
            byte_l.append(self._r_byte())
        # end of message
        self._end_tx()
        # decode bytes
        second = ((byte_l[0] & 0x70) >> 4) * 10 + (byte_l[0] & 0x0f)
        minute = ((byte_l[1] & 0x70) >> 4) * 10 + (byte_l[1] & 0x0f)
        hour = ((byte_l[2] & 0x30) >> 4) * 10 + (byte_l[2] & 0x0f)
        day = ((byte_l[3] & 0x30) >> 4) * 10 + (byte_l[3] & 0x0f)
        month = ((byte_l[4] & 0x10) >> 4) * 10 + (byte_l[4] & 0x0f)
        year = ((byte_l[6] & 0xf0) >> 4) * 10 + (byte_l[6] & 0x0f) + 2000
        # return datetime value
        return datetime.datetime(year, month, day, hour, minute, second)

    def write_datetime(self, dt):
        """
        Write a python datetime to RTC chip.

        :param dt: datetime to write
        :type dt: datetime.datetime
        """
        # format message
        byte_l = [0] * 9
        byte_l[0] = (dt.second // 10) << 4 | dt.second % 10
        byte_l[1] = (dt.minute // 10) << 4 | dt.minute % 10
        byte_l[2] = (dt.hour // 10) << 4 | dt.hour % 10
        byte_l[3] = (dt.day // 10) << 4 | dt.day % 10
        byte_l[4] = (dt.month // 10) << 4 | dt.month % 10
        byte_l[5] = (dt.weekday() // 10) << 4 | dt.weekday() % 10
        byte_l[6] = ((dt.year-2000) // 10) << 4 | (dt.year-2000) % 10
        # start message
        self._start_tx()
        # write clock burst
        self._w_byte(0xbe)
        # write all data
        for byte in byte_l:
            self._w_byte(byte)
        # end of message
        self._end_tx()

    @staticmethod
    def close():
        """
        Clean all GPIOs.
        """
        GPIO.cleanup()
