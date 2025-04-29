""" DHBW Hochregal-Lager - hbs_user_terminal.py

Driver fpr the user terminal, comprising a HD44780 text display (4 lines, 20 columns),
4 leds and 4 buttons

LEDS:
- green -> ready
- yellow -> busy
- red - error
- blue -> storage full

Buttons:
- blue -> manual mode, ax selection
- green -> manual down
- yellow -> manual up
- red -> emergency stop

- green + yellow -> program end
- green + red -> system shutdown

SLW 03/2025
"""

from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO
import time
import subprocess
import logging
import sys


MESSAGE_FILE = "hbs_messages_de.dat"

class UserTerminal:
    
    def __init__(self):
        self._led_green, self._led_yellow, self._led_red, self._led_blue = 16, 20, 26, 19
        self._bt_blue, self._bt_green, self._bt_yellow, self._bt_red = 8, 25, 24, 23
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._led_green, GPIO.OUT)
        GPIO.setup(self._led_yellow, GPIO.OUT)
        GPIO.setup(self._led_red, GPIO.OUT)
        GPIO.setup(self._led_blue, GPIO.OUT)
        GPIO.setup(self._bt_blue, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self._bt_green, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self._bt_yellow, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(self._bt_red, GPIO.IN, GPIO.PUD_UP)
        self.ae, self.oe, self.ue,  = 225, 239, 245
        self._chr_shelf_0 = bytearray([0x00, 0x00, 0x00, 0xff, 0x00, 0x00, 0x00, 0xff])
        self._chr_shelf_1 = bytearray([0x00, 0x00, 0x00, 0xff, 0x00, 0x0e, 0x0e, 0xff])
        self._chr_shelf_2 = bytearray([0x00, 0x0e, 0x0e, 0xff, 0x00, 0x00, 0x00, 0xff])
        self._chr_shelf_3 = bytearray([0x00, 0x0e, 0x0e, 0xff, 0x00, 0x0e, 0x0e, 0xff])
        self._chr_shelf_4 = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff])
        self._chr_shelf_5 = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x0e, 0x0e, 0xff])
        self._chr_shelf_6 = bytearray([0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02])
        self._chr_shelf_7 = bytearray([0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08])
        self.ip = ""
        
        # Show LEDs
        self._show_leds()

        # Initialize display
        self._n_rows, self._n_columns = 4, 20
        self._frame_buf = ['', '', '', '']
        self._lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
                            cols=self._n_columns, rows=self._n_rows, dotsize=8,
                            charmap='A02',
                            auto_linebreaks=True,
                            backlight_enabled=True)
        self._row, self._display_row = 0, 0
        self._lcd.create_char(0, self._chr_shelf_0)
        self._lcd.create_char(1, self._chr_shelf_1)
        self._lcd.create_char(2, self._chr_shelf_2)
        self._lcd.create_char(3, self._chr_shelf_3)
        self._lcd.create_char(4, self._chr_shelf_4)
        self._lcd.create_char(5, self._chr_shelf_5)
        self._lcd.create_char(6, self._chr_shelf_6)
        self._lcd.create_char(7, self._chr_shelf_7)
        time.sleep(0.1)
        self.clear()
        
        # Read message file
        try:
            with open(MESSAGE_FILE, "r", encoding="UTF-8") as f:
                lines = f.readlines()
        except IOError:
            msg = "Messages file error"
            self.print_str(msg)
            logging.error(msg)
            self.set_error()
            sys.exit()
            
        self.msg = {}
        for l in lines:
            l = l.strip(' ')
            if l[0] == '#':
                continue
            if l.find(':') > 0:
                key, value = l.split(':')
                self.msg[key.strip()] = value.strip()
                
        # Show welcome message
        self.print_line(self.msg["wlc_01"])
        self.print_line(self.msg["wlc_02"])
        
        # Show SSID and IP address
        for idx in range(10):
            ip_address = subprocess.check_output(['hostname', '-I'])
            if len(ip_address) > 5:
                break
            else:
                self.print_str('.')
                time.sleep(1)
        self.carret()

        if idx < 9:
            ip_address = ip_address.decode("UTF-8")
            self._ip_address = ip_address.split(' ')[0]
            self.print_line("IP: " + self._ip_address)
            ssid = subprocess.check_output(["iwgetid -r"], shell=True).decode("UTF-8")
            ssid = ssid.strip('\n')
            self.print_line("SSID: " + ssid)
        else:
            logging.error("No network connection")
            self.print_msg("err_nonet")
            self.print_msg("sys_exit")
            self.set_error()


    def get_ip(self):
        return self._ip_address
        

    # display --------------------------------------------------------------------------        
    def print_str(self, s):
        if self._display_row > 3:
            self.scroll_up()
            self._display_row = 3
        s = s.replace('ä', chr(self.ae))
        s = s.replace('ö', chr(self.oe))
        s = s.replace('ü', chr(self.ue))
        l = len(self._frame_buf[self._row])
        diff = self._n_columns - l
        if diff > 0:
            s = s[: diff]
            self._frame_buf[self._row] += s
            self._lcd.write_string(s)
    
    def print_line(self, s):
        """ Prints a line to the display. """
        self.print_str(s)
        self.newline()
        
    def scroll_up(self):
        self._lcd.clear()
        cursor = self._row + 1
        if cursor > 3:
            cursor = 0
        for idx in range(3):
            self._lcd.cursor_pos = (idx, 0)
            self._lcd.write_string(self._frame_buf[cursor])
            cursor += 1
            if cursor > 3:
                cursor = 0
        self._frame_buf[self._row] = ''
        self._lcd.cursor_pos = (3, 0)
        
    def print_msg(self, msg_key, add_on = ""):
        msg = self.msg[msg_key]
        if len(add_on) > 0:
            msg += ' ' + add_on
        self.print_line(msg)
        
                                        
    def clear(self):
        self._lcd.clear()
        self._frame_buf = ['', '', '', '']
        self._row, self._display_row = 0, 0

    def carret(self):
        """ carriage return """
        self._frame_buf[self._row] = ''
        self._lcd.cursor_pos = (self._display_row, 0)
       
    def newline(self):
        self._row += 1
        self._display_row += 1
        if self._row > 3:
            self._row = 0
        self._lcd.cursor_pos = (self._row, 0)
        
    
    def show_axis(self, ax, hbs_ctr):
        """ Shows the current value of the axis. 0 -> x, 1 -> y, 2 -> z """
        if ax == 0:
            self.print_str(self.msg["msg_x_man"] + ': ' + str(hbs_ctr.x) + '         ')
            self.carret()
        elif ax == 1:
            self.print_str(self.msg["msg_y_man"] + ': ' + hbs_ctr.y.name + '  ')
            self.carret()
        else:
            self.print_str(self.msg["msg_z_man"] + ': ' + str(hbs_ctr.z) + '         ')
            self.carret()
    
    
    def show_occupancy(self, storage_places):
        """ Shows the current occupancy of the system on the LCD display """
          
        # line 5
        display_str = '    \x06'
        for col in range(1, 11):
            place_up = storage_places[4 * 10 + col]['taken']
            if place_up:
                display_str += '\x05'
            else:
                display_str += '\x04'
        display_str += '\x07'
        self.print_line(display_str)
        # lines 4 to 1
        line = 2
        for row_up, row_down in ((3,2), (1,0)):
            display_str = '    \x06'
            for col in range(1, 11):
                place_up = storage_places[row_up * 10 + col]['taken']
                place_down = storage_places[row_down * 10 + col]['taken']
                if place_up and place_down:
                    display_str += '\x03'
                elif place_up and not place_down:
                    display_str += '\x02'
                elif not place_up and place_down:
                    display_str += '\x01'
                else:
                    display_str += '\x00'
            display_str += '\x07'
            self.print_line(display_str)
            line += 1
        
        
    # LEDs -------------------------------------------------------------------
    def _show_leds(self):
        for led in (self._led_green, self._led_yellow, self._led_red, self._led_blue):
            GPIO.output(led, True)
            time.sleep(0.1)
            GPIO.output(led, False)
    
    def set_ready(self):
        GPIO.output(self._led_green, True)
        GPIO.output(self._led_yellow, False)
        GPIO.output(self._led_red, False)
        
    def set_busy(self):
        GPIO.output(self._led_green, False)
        GPIO.output(self._led_yellow, True)
        GPIO.output(self._led_red, False)

    def set_error(self):
        GPIO.output(self._led_green, False)
        GPIO.output(self._led_yellow, False)
        GPIO.output(self._led_red, True)
        
    def set_full(self):
        GPIO.output(self._led_blue, True)
        
    def clear_full(self):
        GPIO.output(self._led_blue, False)
      
      
    # Buttons-------------------------------------------------------------------
    def get_buttons(self):
        return not GPIO.input(self._bt_blue), \
               not GPIO.input(self._bt_green),  \
               not GPIO.input(self._bt_yellow), \
               not GPIO.input(self._bt_red)
    
    def get_bt_red(self):
        return not GPIO.input(self._bt_red)
    
    def wait_for_any_key(self, timeout = -1):
        if timeout > 0:
            end_time = time.time() + timeout
            while time.time() < end_time:
                bts = self.get_buttons()
                if bts[0] or bts[1] or bts[2] or bts[3]:
                    break
                time.sleep(0.1)
        else:
            while True:
                bts = self.get_buttons()
                if bts[0] or bts[1] or bts[2] or bts[3]:
                    break
                time.sleep(0.1)

#==========================================
        
if __name__ == "__main__":
    
    ut = UserTerminal()
    ut.wait_for_any_key(1)
    ut._lcd.clear()
    ut._lcd.write_string("Hello there \x00\x01\x02\x03\x04\x05")
      
    
        