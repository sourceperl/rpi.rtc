import time
import datetime
import RPi.GPIO as GPIO


class DS1302:
    CLK_DELAY = 0.00001

    def __init__(self, clk_pin=11, data_pin=13, ce_pin=15):
        # init GPIO
        # TODO no warnings
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
        GPIO.setup(self._data_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.output(self._clk_pin, GPIO.LOW)
        GPIO.output(self._data_pin, GPIO.LOW)
        time.sleep(self.CLK_DELAY)
        GPIO.output(self._ce_pin, GPIO.HIGH)

    def _end_tx(self):
        """
        End of transaction.
        """
        GPIO.setup(self._data_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.output(self._clk_pin, GPIO.LOW)
        GPIO.output(self._data_pin, GPIO.LOW)
        time.sleep(self.CLK_DELAY)
        GPIO.output(self._ce_pin, GPIO.LOW)

    def _r_byte(self):
        """
        Read byte from the chip.

        :return: byte value
        :rtype: int
        """
        # data pin is now input with pull-up resistor
        GPIO.setup(self._data_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # clock the byte from chip
        byte = 0
        for i in range(8):
            # make a pulse on CLK pin
            time.sleep(self.CLK_DELAY)
            GPIO.output(self._clk_pin, GPIO.HIGH)
            time.sleep(self.CLK_DELAY)
            GPIO.output(self._clk_pin, GPIO.LOW)
            # store current bit into byte
            time.sleep(self.CLK_DELAY)
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
        GPIO.setup(self._data_pin, GPIO.OUT, initial=GPIO.LOW)
        # clock the byte to chip
        for _ in range(8):
            GPIO.output(self._clk_pin, GPIO.LOW)
            time.sleep(self.CLK_DELAY)
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
        # Read data bytes.
        bytes = bytearray()
        for _ in range(31):
            bytes.append(self._r_byte())
        # end of message
        self._end_tx()
        return bytes

    def write_ram(self, bytes):
        """
        Write RAM with bytes

        :param bytes: bytes to write
        :type bytes: bytearray
        """
        # start message
        self._start_tx()
        # write ram burst
        self._w_byte(0xfe)
        # Write data bytes.
        for i in range(min(len(bytes), 31)):
            self._w_byte(ord(bytes[i:i + 1]))
        # for _ in range(31 - len(bytes)):
        #     self._w_byte(ord(' '))
        # end of message
        self._end_tx()

    def read_datetime(self):
        """
        Read current date and time from RTC chip.

        :return: date and time
        :rtype: datetime
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
        :type dt: datetime
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
        # Write all data
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
