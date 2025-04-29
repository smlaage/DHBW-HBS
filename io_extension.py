#!/usr/bin/env python3
from smbus2 import SMBus


class IOExtension:
    """ IO extension board for Raspberry Pi """

    def __init__(self, out_a=0, out_b=0):
        self._mcp23017 = (0x20, 0x24, 0x22)
        self._address_map = {
            'IODIRA': 0x00, 'IODIRB': 0x01, 'GPPUA': 0x0c, 'GPPUB': 0x0d,
            'GPIOA': 0x12, 'GPIOB': 0x13, 'GPINTENA': 0x04, 'GPINTENB': 0x05
        }
        self._in_port_map = ((0, 'GPIOA'), (0, 'GPIOB'), (1, 'GPIOA'), (1, 'GPIOB'))
        self._bus = SMBus(1)
        # enable pullup resistors for input ports for device 0 and 1
        self._bus.write_byte_data(self._mcp23017[0], self._address_map['GPPUA'], 0xff)
        self._bus.write_byte_data(self._mcp23017[0], self._address_map['GPPUB'], 0xff)
        self._bus.write_byte_data(self._mcp23017[1], self._address_map['GPPUA'], 0xff)
        self._bus.write_byte_data(self._mcp23017[1], self._address_map['GPPUB'], 0xff)
        # set port direction to output for device 2
        self._bus.write_byte_data(self._mcp23017[2], self._address_map['IODIRA'], 0x00)
        self._bus.write_byte_data(self._mcp23017[2], self._address_map['IODIRB'], 0x00)
        # initialize output port status
        self._out_a, self._out_b = out_a, out_b
        self._bus.write_byte_data(self._mcp23017[2], self._address_map['GPIOA'], self._out_a)
        self._bus.write_byte_data(self._mcp23017[2], self._address_map['GPIOB'], self._out_b)

        # interrupts
        self._bus.write_byte_data(self._mcp23017[0], self._address_map['GPINTENA'], 0xFF)
        self._bus.write_byte_data(self._mcp23017[0], self._address_map['GPINTENB'], 0xFF)
        self._bus.write_byte_data(self._mcp23017[1], self._address_map['GPINTENA'], 0xFF)
        self._bus.write_byte_data(self._mcp23017[1], self._address_map['GPINTENB'], 0xFF)


    def read_port(self, port: int) -> list:
        """ Returns a list of booleans showing the current setting of the input port.
            Select port with an integer range 0 ... 3 """
        if port < 4:
            result = self._bus.read_byte_data(self._mcp23017[self._in_port_map[port][0]],
                                              self._address_map[self._in_port_map[port][1]])
            return [result & (1 << mask) == 0 for mask in range(8)]
        else:
            print("Input port", port, "undefined")
            return []
        

    def set_port(self, parm0, parm1, parm2=False):
        """ Sets a pin at the output port.
            port: 0 ... 1
            port_pin: 0 ... 7
            value: True for high, False for low
            Usage: set_port(tuple(port, pin), bool) or set_port(port, pin, bool) """
        if isinstance(parm0, tuple):
            port = parm0[0]
            port_pin = parm0[1]
            value = parm1
        else:
            port = parm0
            port_pin = parm1
            value = parm2
        if port_pin < 8:
            if port == 0:
                if value:
                    self._out_a |= (1 << port_pin)
                else:
                    self._out_a &= ~(1 << port_pin)
                self._bus.write_byte_data(self._mcp23017[2], self._address_map['GPIOA'], self._out_a)
            elif port == 1:
                if value:
                    self._out_b |= (1 << port_pin)
                else:
                    self._out_b &= ~(1 << port_pin)
                self._bus.write_byte_data(self._mcp23017[2], self._address_map['GPIOB'], self._out_b)
            else:
                print("Output port", port, "undefined")
        else:
            print("Output pin", port_pin, "undefined")

    def get_output_port(self) -> tuple:
        """ Returns a tuple with two bytes showing the current setting of the output port. """
        return self._out_a, self._out_b << 8

#=============================================================================================

if __name__ == "__main__":
    io = IOExtension()
    
    io.set_port(0, 1, True)
    io.set_port((1, 1), False)
