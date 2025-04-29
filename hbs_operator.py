""" hbs_operator.py

Low level operation functions for the high bay storage

SLW 04/2025
"""

import logging
import time
import os
import io_extension

from hbs_collections import Msg
from hbs_collections import YPos
from hbs_collections import IOPins
from hbs_user_terminal import UserTerminal

DEBUG = False
SIMULATION = False


class HBSOperator:
    """ Operator for a high bay storage """

    def __init__(self, ut):  # Requires the user terminal as argument. 
        logname = "HBSOperator.__init__: "
        if DEBUG: print(logname)
        
        self._break_time = 0.1
        self._x_timeout, self._y_timeout, self._z_timeout = 2.0, 2.5, 1.5  # Timeout in seconds
        self.io = io_extension.IOExtension()
        self.pins = IOPins()
        self.ut = ut
        self._sim_x, self._sim_y, self._sim_z = -1, YPos.UNDEFINED, -1
        
        
    def s(self):
        """ Wrapper to call stop_motion faster in the terminal """
        self.stop_motion()
        
    # Check-Functions --------------------------------------------------------------------------------------------    
    
    def check_xtarget(self, x):
        """ Checks the valid range of the x target position.
            Returns True or False. """
        logname = "HBSOperator.check_xtarget"
        if DEBUG: print(logname)             
               
        if not 1 <= x <= 10:
            msg = logname + "X-target of " + str(x) + " is out of range. The valid range is 1 to 10."
            logging.error(logname + ": " + msg)
            print(logname + ": " + msg)
            self.ut.set_error()
            return False
        else:
            if DEBUG: print(logname + " Okay")
            return True
        
        
    def check_ztarget(self, z):
        """ Checks the valid range of the z target position.
            Returns True or False. """
        logname = "HBSOperator.check_ztarget"
        if DEBUG: print(logname)

        if not 1 <= z <= 10:
            msg = "Z-target of " + str(z) + " is out of range. The valid range is 1 to 10."
            logging.error(logname + ": " + msg)
            print(logname + ": " + msg)
            self.ut.set_error()
            return False
        else:
            if DEBUG: print(logname + " Okay")
            return True
        
        
    def check_zlevel(self, z_level):
        """ Checks the valid range of the z level.
            Returns True or False. """ 
        logname = "HBSOperator.check_zlevel"
        if DEBUG: print(logname)
        
        if not 1 <= z_level <= 5:
            msg = "Z-level of " + str(z_level) + " is out of range. The valid range is 1 to 5."
            logging.error(logname + ": " + msg)
            print(logname + ": " + msg)
            self.ut.set_error()
            return False
        else:
            if DEBUG: print(logname + " Okay")
            return True
        
    
    def check_xdf(self):
        """ Checks whether the x axis is at an defined position.
            If not, this function raises an error message """
        logname = "HBSOperator:check_xdf"
        if DEBUG: print(logname)
        if (SIMULATION and self._sim_x < 0) or (self.get_xpos() < 0):
            msg = logname + ": X position is undefined"
            logging.error(msg)
            print(msg)
            self.ut.set_error()
            return Msg.err_x_udf
        else:
            return Msg.okay


    def check_ydf(self):
        """ Checks whether the y axis is at an defined position.
            If not, this function raises an error message """
        logname = "HBSOperator:check_ydf"
        if DEBUG: print(logname)
        if (SIMULATION and (self._sim_y is YPos.UNDEFINED)) or (self.get_zpos() is YPos.UNDEFINED):
            msg = logname + ": Y position is undefined"
            logging.error(msg)
            print(msg)
            self.ut.set_error()
            return Msg.err_y_udf
        else:
            return Msg.okay
        
        
    def check_zdf(self):
        """ Checks whether the z axis is at an defined position.
            If not, this function raises an error message """
        logname = "HBSOperator:check_zdf"
        if DEBUG: print(logname)
        if (SIMULATION and self._sim_z < 0) or (self.get_zpos() < 0):
            msg = logname + ": Z position is undefined"
            logging.error(msg)
            print(msg)
            self.ut.set_error()
            return Msg.err_z_udf
        else:
            return Msg.okay

    
    def check_ydefault(self):
        """ Checks whether the y position is at default, so that x and/or z can start moving """
        logname = "HBSOperator.check_ydefault: "
        if DEBUG: print(logname)
        if SIMULATION:
            if self._sim_y is YPos.UNDEFINED:
                return False
            else:
                return True
        
        if not self.get_ypos() is YPos.DEFAULT:
            msg = "Can't move in x-direction while ypos is not YPos.DEFAULT"
            logging.error(logname + ": " + msg)
            print(logname + ": " + msg)
            self.ut.set_error()
            return False
        else:
            return True
        
        
    def stop_motion(self):
        """ Stop any motion of the operator """
        logname = "HBSOperator.stop_motion"
        if DEBUG: print(logname)

        for idx in range(8):
            # port 2 == True does not cause motion
            if idx == 2:
                continue
            self.io.set_port(0, idx, False)
        for idx in range(3):
            self.io.set_port(1, idx, False)
            
    # Get functions ----------------------------------------------------------------------------------

    def get_xpos(self) -> int:
        """ Get the x-axis position of the operator.
            Returns -1 for undefined positions """
        
        if SIMULATION:
            return self._sim_x
        
        cnt = 0
        for port in self.io.read_port(0):
            cnt += 1
            if port:
                return cnt
        for port in self.io.read_port(1):
            cnt += 1
            if not cnt <= 10:
                break
            if port:
                return cnt
        return -1
    

    def get_ypos(self) -> YPos:
        """ Get the y-axis position of the operator.
            Returns YPos.UNDEFINED for undefined positions """

        if SIMULATION:
            return self._sim_y
        
        cnt = 0
        for port in self.io.read_port(1)[2:5]:
            if port:
                return YPos(cnt)
            cnt += 1
        return YPos.UNDEFINED


    def get_zpos(self) -> int:
        """ Return the z-axis position of the operator.
            Returns -1 for undefined positions """
        
        if SIMULATION:
            return self._sim_z
        
        ports = self.io.read_port(1)[5:8] + self.io.read_port(2)[0:7]
        ports.reverse()
        cnt = 1
        for port in ports:
            if port:
                return cnt
            cnt += 1
        return -1
        
    # Move axis --------------------------------------------------------------------------------------------------
    """ The following operators are moving the axis.
        The functions are managing the LEDs (ready, busy, error).
        Each operator function returns the result of the action as a message.
    """
    
    def move_xpos(self, target_pos: int):
        """ Move the X operator to a target_pos. """
        logname = "HBSOperator.move_xpos"
        if DEBUG: print(logname)
        
        if not self.check_xtarget(target_pos):
            return Msg.err_wrong_x_target        
        if not self.check_ydefault():
            return Msg.err_y_udf
        # Check whether we are done already
        current_pos = self.get_xpos()        
        if current_pos == target_pos:
            return Msg.okay
        # Check whether the current position is valid
        result = self.check_xdf()
        if result is not Msg.okay: return result

        # simulation
        if SIMULATION:
            print(logname, "moving to x_pos:", target_pos)
            self.ut.set_busy()
            for _ in range(20):
                if self.ut.get_bt_red():
                    self._sim_x = -1
                    return self.emergency_stop()
                time.sleep(0.1)
            self.ut.set_ready()
            time.sleep(self._break_time)
            self._sim_x = target_pos
            return Msg.okay      
            
        # Start moving ...
        self.ut.set_busy()
        self.io.set_port(self.pins.x_slow, abs(target_pos - current_pos) <= 1)
        if current_pos < target_pos:
            self.io.set_port(self.pins.x_up, True)
        else:
            self.io.set_port(self.pins.x_down, True)
        
        # Run the motors, watch for timeout
        t_end = time.time() + self._x_timeout
        time_reset = False
        while time.time() < t_end:
            # Check for emergency stop
            if self.ut.get_bt_red():
                return self.emergency_stop()
            # Check the current position
            current_pos = self.get_xpos()
            if current_pos == target_pos:
                break
            if current_pos >= 0:
                self.io.set_port(self.pins.x_slow, abs(target_pos - current_pos) <= 1)
                if time_reset:
                    t_end = time.time() + self._x_timeout
                    time_reset = False
            else:
                time_reset = True
        
        # Arrived
        self.io.set_port(self.pins.x_up, False)
        self.io.set_port(self.pins.x_down, False)
        self.ut.set_ready()
        time.sleep(self._break_time)
        
        # All okay?
        if self.get_xpos() == target_pos:
            return Msg.okay
        else:
            self.log_error(logname, "X positioning unsuccessful!")
            return Msg.err_x_pos
        
        
    def move_ypos(self, target_pos: YPos):
        """ Move the operator to the y-axis position a_ypos. """
        logname = "HBSOperator.move_ypos" 
        if DEBUG: print(logname)
        
        if target_pos == YPos.UNDEFINED:
            msg = "Can't move Y to undefined position"
            logging.error(logname + ": " + msg)
            print(logname + ": " + msg)
            self.ut.set_error()
            return Msg.err_wrong_y_target
        
        # Check whether we done already
        current_pos = self.get_ypos()
        if current_pos is target_pos:
            return Msg.okay
        # Check whether the current position is valid
        result = self.check_ydf()
        if result is not Msg.okay: return result

        # simulation
        if SIMULATION:
            print(logname, "moving to y_pos:", target_pos)
            self.ut.set_busy()
            for _ in range(20):
                if self.ut.get_bt_red():
                    self._sim_y = YPos.UNDEFINED
                    return self.emergency_stop()
                time.sleep(0.1)
            self.ut.set_ready()
            time.sleep(self._break_time)
            self._sim_y = target_pos
            return Msg.okay     
            
        # Start moving ...
        self.ut.set_busy()
        if current_pos.value < target_pos.value:
            self.io.set_port(self.pins.y_in, True)
        elif current_pos.value > target_pos.value:
            self.io.set_port(self.pins.y_out, True)

        # Run the motors, watch for timeout
        t_end = time.time() + self._y_timeout
        time_reset = False
        while time.time() < t_end:
            # Check for emergency stop
            if self.ut.get_bt_red():
                return self.emergency_stop()
            # Check the current position
            current_pos = self.get_ypos()
            if current_pos is target_pos:
                break
            if current_pos != YPos.UNDEFINED:
                if time_reset:
                    t_end = time.time() + self._y_timeout
                    time_reset = False
            else:
                time_reset = True

        # Arrived
        self.io.set_port(self.pins.y_out, False)
        self.io.set_port(self.pins.y_in, False)
        self.ut.set_ready()
        time.sleep(self._break_time)
        
        # All okay?
        if self.get_ypos() is target_pos:
            return Msg.okay
        else:
            self.log_error(logname, "Y positioning unsuccessful!")
            return Msg.err_y_pos
        

    def move_zpos(self, target_pos: int):
        """ Move theZ  operator to a target position. """
        logname = "HBSOperator.move_zpos" 
        if DEBUG: print(logname)
  
        # Validate target
        if not self.check_ztarget(target_pos):
            return Msg.err_wrong_z_target                
        # Check whether we are done already
        current_pos = self.get_zpos()        
        if current_pos == target_pos:
            return Msg.okay
        # Check whether we are at a valid position
        result = self.check_zdf()
        if result is not Msg.okay: return result
        
        # simulation
        if SIMULATION:
            print(logname, "moving to z_pos:", target_pos)
            self.ut.set_busy()
            for _ in range(20):
                if self.ut.get_bt_red():
                    self._sim_z = -1
                    return self.emergency_stop()
                time.sleep(0.1)
            self.ut.set_ready()
            time.sleep(self._break_time)
            self._sim_z = target_pos
            return Msg.okay      
            
        # Start moving ...
        self.ut.set_busy()
        if current_pos < target_pos:
            self.io.set_port(self.pins.z_up, True)
        else:
            self.io.set_port(self.pins.z_down, True)

        # Run the motors, watch for timeout
        t_end = time.time() + self._z_timeout
        time_reset = False
        while time.time() < t_end:
            # Check for emergency stop
            if self.ut.get_bt_red():
                return self.emergency_stop()
            # Check the current position
            current_pos = self.get_zpos()
            if current_pos == target_pos:
                break
            if current_pos >= 0:
                if time_reset:
                    t_end = time.time() + self._z_timeout
                    time_reset = False
                else:
                    time_reset = True
            
        # Arrived    
        self.io.set_port(self.pins.z_up, False)
        self.io.set_port(self.pins.z_down, False)
        time.sleep(self._break_time)
        
        # All okay?
        if self.get_zpos() == target_pos:
            return Msg.okay
        else:
            self.log_error(logname, "Z positioning unsuccessful!")
            return Msg.err_z_pos


    def move_xzpos(self, target_xpos: int, target_zpos: int):
        """ Move the operator to the z-axis position a_xpos"""
        logname = "HBSOperator.move_xzpos"
        if DEBUG: print(logname)
        
        # Check validity of targets
        if not self.check_xtarget(target_xpos):
            return Msg.err_wrong_x_target
        if not self.check_ztarget(target_zpos):
            return Msg.err_wrong_z_target
        # Check the current status of the sensors
        result = self.check_xdf()
        if result is not Msg.okay: return result
        result = self.check_zdf()
        if result is not Msg.okay: return result
        # Get current positions
        current_zpos = self.get_zpos()
        current_xpos = self.get_xpos()
        # Check whether Y is in the right position for horizontal moves
        if current_xpos != target_xpos:
            if not self.check_ydefault():
                return Msg.err_y_udf
        # Anything to do?
        if current_xpos == target_xpos and current_zpos == target_zpos:
            return Msg.okay

        # simulation
        if SIMULATION:
            print(logname, "moving to x_pos: " + str(target_xpos) + ", z_pos: " + str(target_zpos))
            self.ut.set_busy()
            for _ in range(20):
                if self.ut.get_bt_red():
                    self._sim_x = -1
                    self._sim_z = -1
                    return self.emergency_stop()
                time.sleep(0.1)
            self.ut.set_ready()
            time.sleep(self._break_time)
            self._sim_x = target_xpos
            self._sim_z = target_zpos
            return Msg.okay      

        # Start moving
        self.ut.set_busy()
        # Start x motor
        if current_xpos == target_xpos:
            x_okay = True
        else:
            self.io.set_port(self.pins.x_slow, abs(target_xpos - current_xpos) <= 1)
            if current_xpos < target_xpos:
                self.io.set_port(self.pins.x_up, True)
            else:
                self.io.set_port(self.pins.x_down, True)
            x_okay = False
        # Start z motor
        if current_zpos == target_zpos:
            z_okay = True
        else:
            if target_zpos < current_zpos:
                self.io.set_port(self.pins.z_down, True)
            else:
                self.io.set_port(self.pins.z_up, True)
            z_okay = False

        # Run the motors, watch for timeout
        t_end_x = time.time() + self._x_timeout
        t_end_z = time.time() + self._z_timeout
        x_time_reset, z_time_reset = False, False
        while True:
            # Check for timeout
            now = time.time()
            if (not x_okay and now > t_end_x) or (not z_okay and now > t_end_z):
                break
            # Check for emergency stop
            if self.ut.get_bt_red():
                return self.emergency_stop()
            # X axis
            current_xpos = self.get_xpos()
            if current_xpos >= 0:
                if not x_okay and x_time_reset:
                    t_end_x = time.time() + self._x_timeout
                    x_time_reset = False
                self.io.set_port(self.pins.x_slow, abs(target_xpos - current_xpos) <= 1)
                if current_xpos == target_xpos:
                    self.io.set_port(self.pins.x_up, False)
                    self.io.set_port(self.pins.x_down, False)
                    x_okay = True
            else:
                x_time_reset = True
            # Z axis
            current_zpos = self.get_zpos()
            if current_zpos >= 0:
                if not z_okay and z_time_reset:
                    t_end_z = time.time() + self._z_timeout
                    z_time_reset = False
                if current_zpos == target_zpos:
                    self.io.set_port(self.pins.z_down, False)
                    self.io.set_port(self.pins.z_up, False)
                    z_okay = True
            else:
                z_time_reset = True
            # Target reached ?
            if x_okay and z_okay:
                break
  
        # We have arrived
        self.stop_motion()
        self.ut.set_ready()
        time.sleep(self._break_time)

        # Check the result
        if not self.get_xpos() == target_xpos:
            self.log_error(logname, "X positioning unsuccessful!")
            return Msg.err_x_pos                       
        if not self.get_zpos() == target_zpos:
            self.log_error(logname, "Z positioning unsuccessful!")
            return Msg.err_z_pos
        
        return Msg.okay
    
        
    def move_home(self):
        """ Moves all axes to the home position: x: 10, y: DEFAULT, z: 1 """
        logname = "HBSOperator.move_home"
        logging.info(logname)
        if DEBUG or SIMULATION:
            print(logname)
            
        result = self.move_ypos(YPos.DEFAULT)
        if result is not Msg.okay: return result
        result = self.move_zpos(1)
        if result is not Msg.okay: return result
        result = self.move_xpos(10)
        if result is not Msg.okay: return result
            
        return Msg.okay
    
 
    #- Box-Functions -------------------------------------------------------------------------------------------------------------
    """ The following functions are storing or destoring boxes to and from the shelf """
        
    def put_box(self, xpos, z_level):
        """ Put box into a storage place.
            Arguments: 1 <= xpos <= 10, 1 <= z_level <= 5
            Returns: Message of the result (e.g. Msg.okay) """
        logname = "HBSOperator.put_box"
        if DEBUG: print(logname)
        logging.info(logname + ": X: " + str(xpos) + " Z-Level: " + str(z_level))

        if not self.check_xtarget(xpos):
            return Msg.err_wrong_x_target
        if not self.check_zlevel(z_level):
            return Msg.err_wrong_z_level

        # Manage the movements
        if not self.move_ypos(YPos.DEFAULT):
            return Msg.err_y_pos
        if not self.move_xzpos(xpos, z_level * 2):
            return Msg.err_xz_pos
        if not self.move_ypos(YPos.STORE):
            return Msg.err_y_pos
        if not self.move_zpos(z_level * 2 - 1):
            return Msg.err_z_pos
        if not self.move_ypos(YPos.DEFAULT):
            return Msg.err_y_pos
        
        # Done
        return Msg.okay


    def get_box(self, xpos, z_level):
        """ Get a box from a storage place.
            Returns: Message of the result (e.g. Msg.okay) """
        logname = "HBSOperator.get_box"
        if DEBUG: print(logname)
        logging.info(logname + ": X: " + str(xpos) + " Z-Level: " + str(z_level))
        
        if not self.check_xtarget(xpos):
            return Msg.err_wrong_x_target
        if not self.check_zlevel(z_level):
            return Msg.err_wrong_z_level
 
        # Manage the movements
        result = self.move_ypos(YPos.DEFAULT)
        if result is not Msg.okay: return result
        result = self.move_xzpos(xpos, z_level * 2 - 1)
        if result is not Msg.okay: return result
        result = self.move_ypos(YPos.STORE)
        if result is not Msg.okay: return result
        result = self.move_zpos(z_level * 2)
        if result is not Msg.okay: return result
        result = self.move_ypos(YPos.DEFAULT)
        if result is not Msg.okay: return result        
        
        return Msg.okay


    def fetch_box(self):
        """ Fetch a a box from the input-station.
            Returns: Message of the result (e.g. Msg.okay) """
        logname = "HBSOperator.fetch_box"
        logging.info(logname)
        if DEBUG: print(logname)
        
        # Move to the gripper to the input station
        result = self.move_ypos(YPos.DEFAULT)
        if result is not Msg.okay: return result         
        result = self.move_xzpos(10, 1)
        if result is not Msg.okay: return result
           
        # Start the input-station
        self.ut.set_busy()
        self.io.set_port(self.pins.io1_in, True)
        self.io.set_port(self.pins.io2_in, True)        
        # Polling für 5s
        t_end = time.time() + 5
        while time.time() < t_end:
            # Check for emergency stop
            if self.ut.get_bt_red():
                self.emergency_stop()
            if not self.io.read_port(3)[1]:
                time.sleep(0.3)
                break
        # Stop the input-station
        self.io.set_port(self.pins.io1_in, False)
        self.io.set_port(self.pins.io2_in, False)       
        time.sleep(self._break_time)
        
        # Check the light barrier whether the box is in the right position
        if self.io.read_port(3)[1]:
            self.ut.set_error()
            msg = "Error in belt"
            logging.error(logname + ": " + msg)
            print(logname + ": " + msg)
            return Msg.err_input_belt
        
        self.ut.set_ready()
        result = self.move_ypos(YPos.DESTORE)
        if result is not Msg.okay: return result        
        result = self.move_zpos(2)
        if result is not Msg.okay: return result
        result = self.move_ypos(YPos.DEFAULT)
        if result is not Msg.okay: return result
        
        # Done
        return Msg.okay


    def drop_box(self):
        """ Drop a box to the output-station.
            Returns: Message of the result (e.g. Msg.okay) """
        logname = "HBSOperator.drop_box"
        logging.info(logname)
        if DEBUG: print(logname)
        
        # Move the gripper to the output station
        result = self.move_ypos(YPos.DEFAULT)
        if result is not Msg.okay: return result
        result = self.move_xzpos(1, 2)
        if result is not Msg.okay: return result
        result = self.move_ypos(YPos.DESTORE)
        if result is not Msg.okay: return result
        result = self.move_zpos(1)
        if result is not Msg.okay: return result
        result = self.move_ypos(YPos.DEFAULT)
        if result is not Msg.okay: return result
        
        # Start the output-station
        self.ut.set_busy()
        self.io.set_port(self.pins.io1_out, True)
        self.io.set_port(self.pins.io2_out, True)
        end_t = time.time() + 6
        while time.time() < end_t:
            # Check for emergency stop
            if self.ut.get_bt_red():
                return Msg.err_emrg_stop
 
        # Stop the output-station
        self.io.set_port(self.pins.io1_out, False)
        self.io.set_port(self.pins.io2_out, False)
        time.sleep(self._break_time)

        # Done
        self.ut.set_ready()
        return Msg.okay
    
               
    # Utility Functions --------------------------------------------------------------------------------
    
    def log_error(self, logname, msg):
        logging.error(logname + ": " + msg)
        print(logname + ": " + msg)
        self.ut.set_error()


    def emergency_stop(self):
        logname = "HBSOperator.emergency_stop"
        self.stop_motion()
        self.ut.set_error()
        logging.error(logname + ": system halted")
        print(logname + ": system halted")
        return Msg.err_emrg_stop
    

    def debug_sensors(self):
        """Zeigt den Status aller Sensoren kontinuierlich an"""
        while True:
            port_0 = self.io.read_port(0)
            port_1 = self.io.read_port(1)
            port_2 = self.io.read_port(2)
            port_3 = self.io.read_port(3)

            os.system('clear')

            print("##################")
            for index, pin in enumerate(port_0):
                print(f"Port 0|{index}: {pin}")
            for index, pin in enumerate(port_1):
                print(f"Port 1|{index}: {pin}")
            for index, pin in enumerate(port_2):
                print(f"Port 2|{index}: {pin}")
            for index, pin in enumerate(port_3):
                print(f"Port 3|{index}: {pin}")
            print("##################")

            time.sleep(1)
    
    # Initialization functions -----------------------------------------------------------------------------
                          
    def init_ypos(self):
        """ Initializes the y-axis by finding the next valid position and moving to YPos:DEFAULT. """
        logname = "HBSOperator.init_ypos"
        logging.info(logname + ": Initializing Y ...")
        if DEBUG: print(logname + ": Initializing Y ...")
        
        if SIMULATION:
            print(logname)
            self.ut.set_busy()
            time.sleep(1)
            self.ut.set_ready()
            time.sleep(self._break_time)
            self._sim_y = YPos.DEFAULT
            return Msg.okay        

        # Find a valid position by moving left and right
        wait_time = self._y_timeout / 2
        for pin in (self.pins.y_out, self.pins.y_in):       
            if self.get_ypos() != YPos.UNDEFINED:
                break
            self.ut.set_busy()
            end_time = time.time() + wait_time
            wait_time = self._y_timeout 
            self.io.set_port(pin, True)
            while time.time() < end_time:
                # Check for emergency stop
                if self.ut.get_bt_red():
                    return self.emergency_stop()
                if self.get_ypos() != YPos.UNDEFINED:
                    break
            self.io.set_port(pin, False)
            self.ut.set_ready()
            time.sleep(self._break_time)

        # Result okay?
        if self.get_ypos() is YPos.UNDEFINED:
            # Initialization unsuccessful
            self.log_error(logname, "Y initialization unsuccessful")
            self.ut.set_error()
            return Msg.err_y_init
        else:
            # Move to default position
            return self.move_ypos(YPos.DEFAULT)
            

    def init_xpos(self):
        """ Initializes the x-axis by fnding the next valid position """
        logname = "HBSOperator.init_xpos"
        logging.info(logname + ": Initializing X ...")
        if DEBUG: print(logname + ": Initializing X ...")        
        
        if SIMULATION:
            print(logname)
            self.ut.set_busy()
            time.sleep(1)
            self.ut.set_ready()
            time.sleep(self._break_time)
            self._sim_x = 1
            return Msg.okay     
        
        # In case of an undefined position, move to the next sensor
        wait_time = self._x_timeout / 2
        for pin in (self.pins.x_down, self.pins.x_up):
            if self.get_xpos() >= 0:
                break
            self.ut.set_busy()
            self.io.set_port(self.pins.x_slow, True)
            self.io.set_port(pin, True)
            end_time = time.time() + wait_time
            wait_time = self._x_timeout
            while time.time() < end_time:
                # Check for emergency stop
                if self.ut.get_bt_red():
                    return self.emergency_stop()
                if self.get_xpos() >= 0:
                    break
            self.io.set_port(pin, False)
            self.ut.set_ready()
            time.sleep(self._break_time)
            
        # Result okay?            
        if self.get_xpos() >= 0:
            return Msg.okay
        else:
            # Initialization unsuccessful
            self.log_error(logname, "X initialization unsuccessful")
            self.ut.set_error()
            return Msg.err_x_init
            

    def init_zpos(self):
        """ Initializes the z-axis by finding the next valid position """
        logname = "HBSOperator.init_zpos"
        logging.info(logname + ": Initializing Z ...")
        if DEBUG: print(logname + ": Initializing Z ...")

        if SIMULATION:
            print(logname)
            self.ut.set_busy()
            time.sleep(1)
            self.ut.set_ready()
            time.sleep(self._break_time)
            self._sim_z = 1
            return Msg.okay     

        # In case of an undefined position, move to the next sensor
        wait_time = self._z_timeout / 2
        for pin in (self.pins.z_down, self.pins.z_up):
            if self.get_zpos() >= 0:
                break
            self.ut.set_busy()
            self.io.set_port(pin, True)
            end_time = time.time() + wait_time
            wait_time = self._z_timeout
            while time.time() < end_time:
                # Check for emergency stop
                if self.ut.get_bt_red():
                    return self.emergency_stop()
                if self.get_zpos() >= 0:
                    break
            self.io.set_port(pin, False)
            self.ut.set_ready()
            time.sleep(self._break_time)
    
        # Result okay?            
        if self.get_zpos() >= 0:
            return Msg.okay
        else:
            # Initialization unsuccessful
            self.log_error(logname, "Z initialization unsuccessful")
            self.ut.set_error()
            return Msg.err_z_init
            
#============================================================================================

if __name__ == "__main__":
    
    ut = UserTerminal()
    op = HBSOperator(ut)
    op.init_xpos()
    op.init_ypos()
    op.init_zpos()
    
 