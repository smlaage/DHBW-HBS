""" Hochregal-Lager - hbs_main.py

This is the main script starting the operation of the higb bay storage system.

SLW 03/2025
"""

import os
import logging
import time
import json
from subprocess import check_call

from hbs_collections import SysStatus
from hbs_collections import Msg
from hbs_collections import YPos
from hbs_user_terminal import UserTerminal
from hbs_controller import HBSController
from hbs_mqtt_client import MQTTClient

HOME_DIR = os.path.join("/home", os.getlogin(), "iot", "high_bay_storage")
DEBUG = False


class HBS:
    
    def __init__(self):
        logname = "HBS:__init__"
        
        os.chdir(HOME_DIR)
        now = time.localtime()
        log_filename = os.path.join("logfiles",
                                    "hbs_{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}.log".format(
                                    now[0], now[1], now[2], now[3], now[4], now[5]))
        logging.basicConfig(filename = log_filename,
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            level=logging.INFO,
                            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info(logname + "HBS program start")
                
        self.ut = UserTerminal()
        self.ut.wait_for_any_key(1)
        self.hbs_ctr = HBSController(self.ut)
        self.mqttc = MQTTClient(server_ip=self.ut.get_ip())
        self._status = SysStatus.busy
        self._prog_end = False
        self._manual_axis = -1   		# -1 -> off, 0 -> X, 1 -> y, 2 -> z
        self._sys_shutdown = False
        self._cmd_buffer = []
        self._cmd_functions = {
            "store"     : 		(self.hbs_ctr.store_box, 2),
            "destore"   : 		(self.hbs_ctr.destore_box, 2),
            "rearrange" : 		(self.hbs_ctr.rearrange_box, 4),
            "store_random": 	(self.hbs_ctr.store_box_random, 0),
            "destore_random": 	(self.hbs_ctr.destore_box_random, 0),
            "init_x"    : 		(self.hbs_ctr.op.init_xpos, 0),
            "init_y"    : 		(self.hbs_ctr.op.init_ypos, 0),
            "init_z"    : 		(self.hbs_ctr.op.init_zpos, 0),
            "show_occupancy":   (self.show_occupancy, 0),
            "shutdown"  :   	(self.init_shutdown, 0)
        }


    def load_storage(self):
        """ Loads the controller storage file from the drive.
            Return: True -> success, False -> failure """
        result = self.hbs_ctr.load_storage_file()
        self.ut.print_msg(result.name)
        if result is Msg.err_storage_io:
            return False
        else:
            return True
        
        
    def show_occupancy(self):
        """ Shows the occupancy on the LCD display.
            Returns a string of the current occupancy via MQTT.
            String format: 'occupancy:_**_**_*______*______**_**__*_********___***_*_*__' """
        logname = "HBS:show:_occupancy"
        self.ut.show_occupancy(self.hbs_ctr.occupancy)
        # generate occupancy string for return message
        ocp = 'occupancy:'
        for key in range(1, 51):
            if self.hbs_ctr.occupancy[key]['taken']:
                ocp += '*'
            else:
                ocp += '_'
        logging.info(logname + ": " + ocp)
        return ocp
        
    
    def start_mqtt(self):
        if not self.mqttc.connect(self._mqtt_message_handler):
            self.ut.print_msg("err_mqtt")
            return False
        # Wait for the MQTT client to be up and running
        for idx in range(10):
            if self.mqttc.is_connected:
                break
            time.sleep(1)
        # Check whether we are online
        if idx >= 10:
            self.ut.print_msg("err_mqtt")
            return False
        # All okay
        self.ut.print_msg("mqtt_connected")
        return True    
    

    def _mqtt_message_handler(self, client, userdata, json_msg):
        """ Callback-Funktion für die MQTT Messages """
        logname = "HBS._mqtt_message_handler"
        
        payload = json_msg.payload.decode().casefold()
        logging.info(logname + ": Message received: " + payload)
        print(logname + ": Message received: " + payload)
        self._cmd_buffer.append(payload)
        

    def start_operator(self):
        logname = "HBS.start_operator"
        logging.info(logname)
        self.set_status(SysStatus.busy)

        for ax in ('y', 'z', 'x'):
            self.ut.print_msg("init_" + ax)
            if ax == 'y':
                result = success = self.hbs_ctr.op.init_ypos()
            elif ax == 'z':
                result = self.hbs_ctr.op.init_zpos()
            else:
                result = self.hbs_ctr.op.init_xpos()
            self.ut.print_msg(result.name)
            if result is not Msg.okay:
                self.set_status(SysStatus.error)
                return False
        
        self.set_status(SysStatus.ready)
        return True

    
    def run_manual(self):
        """ Checks teh keyboard for any input, and takes action if needed. """
        bts = self.ut.get_buttons()
        
        # Check green and yellow button -> program end
        if bts[1] and bts[2]:
            self._prog_end = True
            
        # Check green and red button -> system shutdown
        if bts[1] and bts[3]:
            self._prog_end = True
            self._sys_shutdown = True
        
        # Check blue button
        if bts[0] == True:
            if self._manual_axis < 0:
                self._manual_axis = 0
            else:
                self._manual_axis += 1
                if self._manual_axis >= 3:
                    self._manual_axis = 0
            
            self.ut.show_axis(self._manual_axis, self.hbs_ctr)
            # Wait for the button to be released
            while self.ut.get_buttons()[0]:
                time.sleep(0.05)
                
        if self._manual_axis >= 0:
            # check green button
            if bts[1] == True:
                if self._manual_axis == 0:
                    if self.hbs_ctr.x > 1:
                        self.hbs_ctr.op.move_ypos(YPos.DEFAULT)
                        self.hbs_ctr.op.move_xpos(self.hbs_ctr.x - 1)
                elif self._manual_axis == 1:
                    if self.hbs_ctr.y.value >= 1:
                        self.hbs_ctr.op.move_ypos(YPos(self.hbs_ctr.y.value - 1))
                else:
                    if self.hbs_ctr.z > 0:
                        self.hbs_ctr.op.move_ypos(YPos.DEFAULT)
                        self.hbs_ctr.op.move_zpos(self.hbs_ctr.z - 1)
                        
                self.ut.show_axis(self._manual_axis, self.hbs_ctr)
                while self.ut.get_buttons()[1]:
                    time.sleep(0.05)
            # check yellow button        
            elif bts[2] == True:
                if self._manual_axis == 0:
                    if self.hbs_ctr.x < 10:
                        self.hbs_ctr.op.move_ypos(YPos.DEFAULT)
                        self.hbs_ctr.op.move_xpos(self.hbs_ctr.x + 1)
                elif self._manual_axis == 1:
                    if self.hbs_ctr.y.value < 2:
                        self.hbs_ctr.op.move_ypos(YPos(self.hbs_ctr.y.value + 1))
                else:
                    if self.hbs_ctr.z < 10:
                        self.hbs_ctr.op.move_ypos(YPos.DEFAULT)
                        self.hbs_ctr.op.move_zpos(self.hbs_ctr.z + 1)
                        
                self.ut.show_axis(self._manual_axis, self.hbs_ctr)
                while self.ut.get_buttons()[2]:
                    time.sleep(0.05)
                
                
    def decode_json(self, payload):
        """ Decords the received message. Checks fpr the right syntax. Extracts command and arguments.
            Returns: message, command, arguments. """
        logname = "HBS:decode_json"
        if DEBUG:
            print(logname + ": " + payload)
            
        # Convert json format to Python dictionary
        json_format_okay = True
        try:
            json_dict = json.loads(payload)
        except json.JSONDecodeError:
            json_format_okay = False
        if not json_format_okay:
            msg = logname + ": JSON format error"
            logging.error(msg)
            print(msg)
            return Msg.err_json_format, "", []
        # Extract the requested action
        if "operation" not in json_dict.keys():
            msg = logname + ": keyword 'operation' missing"
            logging.error(msg)
            print(msg)
            return Msg.err_json_noop, "", []
        # Check if the command is available
        cmd = json_dict["operation"]
        if DEBUG:
            print(logname + " command: '" + cmd + "'")
        if cmd not in self._cmd_functions:
            msg = logname + ": command not recognized: '" + cmd + "'"
            logging.error(msg)
            print(msg)
            return Msg.err_cmd_unknown, "", []
        # Find arguments
        arg_cnt = self._cmd_functions[cmd][1]
        if DEBUG:
            print(logname + ": number of arguments: " + str(arg_cnt))
        args = []
        arg_error = False
        for idx, arg in enumerate(("x", "z", "x_new", "z_new")):
            if idx >= arg_cnt:
                break
            if arg in json_dict.keys():
                args.append(json_dict[arg])
            else:
                arg_error = True
        if arg_error:
            msg = logname + ": wrong arguments"
            logging.error(msg)
            print(msg)
            return Msg.err_wrong_args, "", []
        # Success!
        if DEBUG:
            print("Okay! Command:", cmd, "Arguments:", args)
        return Msg.okay, cmd, args
                    
    
    def run(self):
        """ Main loop waiting for MQTT commands and/or manual input from the keyboard """
        logname = "HBS.run"
        if not self.mqttc.is_connected:
            self.ut.print_msg("err_mqtt")
            msg = logname + ": MQTT connection failed!"
            logging.info(msg)
            print(msg)
            return
            
        msg = "Waiting for MQTT messages. Cancel with ctrl-C!"
        logging.info(logname + ": " + msg)
        print()
        print(logname + ": " + msg)
        self.ut.print_msg("mqtt_ready")
        
        try:
            while not self._prog_end:
                
                if len(self._cmd_buffer) > 0:
                    self.set_status(SysStatus.busy)
                    result, cmd, args = self.decode_json(self._cmd_buffer[0])
                    del(self._cmd_buffer[0])
                    # If the decoding was okay, then let's run the command
                    if result is Msg.okay:
                        if len(args) == 0:
                            self.ut.print_msg(cmd)
                            result = self._cmd_functions[cmd][0]()
                        elif len(args) == 2:
                            self.ut.print_msg(cmd, str(args[0]) + '/' + str(args[1]))
                            result = self._cmd_functions[cmd][0](args[0], args[1])
                        elif len(args) == 4:
                            self.ut.print_msg(cmd, str(args[0]) + '/' + str(args[1]) +
                                                   ' ' + str(args[2]) + '/' + str(args[3]))
                            result = self._cmd_functions[cmd][0](args[0], args[1], args[2], args[3])
                        else:
                            result = Msg.err_wrong_arg_cnt
                            logging.error(logname + ": internal error! " + result.name)
                    # Check and handle the result
                    if isinstance(result, Msg):
                        # If the result is a Msg, let's deal with it
                        if result.name[0:4] == "err_":
                            self.set_status(SysStatus.error)                        
                        self.mqttc.send_result(result.name)
                        self.ut.print_msg(result.name)
                    elif isinstance(result, str):
                        # If the result is no message, just return the string via MQTT
                        self.mqttc.send_result(result)
                    else:
                        # Internal error
                        result = Msg.err_internal
                        self.mqttc.send_result(result.name)
                        logging.error(logname + ": " + result.name)
                        self.ut.print_msg(result.name)
                        
                    print(logname + ": Done!")
                    
                else:
                    # no pending command, set status to "ready"
                    if self._status is not SysStatus.error:
                        self.set_status(SysStatus.ready)
                    self.run_manual()
                    time.sleep(0.1)

        except KeyboardInterrupt:
            pass
            
        
    def set_status(self, status):
        """ Sets and publishes system status. """
        if status != self._status:
            self._status = status
            self.mqttc.send_status(SysStatus(status).name)

    
    def init_shutdown(self):
        self._prog_end = True
        self._sys_shutdown = True
        return Msg.shutdown


    @property
    def sys_shutdown(self):
        return self._sys_shutdown
        
        
#==============================================================================
        
hbs = HBS()

if hbs.start_mqtt():
    if hbs.start_operator():
        if hbs.load_storage():
            hbs.run()            

hbs.mqttc.send_status(Msg.sys_exit.name)
hbs.ut.print_msg("mqtt_disconnect")
hbs.mqttc.disconnect()
print("MQTT disocnnected!")

msg = "Program ended"
logging.info(msg)
print(msg)
hbs.ut.print_msg("sys_exit")

if hbs.sys_shutdown:
    msg = "System shutdown"
    logging.info(msg)
    print(msg)
    hbs.ut.print_msg("poweroff")
    if not DEBUG:
        check_call(['sudo', 'poweroff'])
        
