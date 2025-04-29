""" hbs_controller.py

High level functions to run the high bay storage

SLW 04/2025
"""

# from pathlib import Path
import random
import pickle
import time
import os
import logging

from hbs_collections import Msg
from hbs_user_terminal import UserTerminal
from hbs_operator import HBSOperator


# Location of the storage file
STORE_DIR = "obj"
STORE_FILE = "storage_places.pkl"

DEBUG = False


class HBSController:
    """class for storage-management of high-bay storage"""
 
    def __init__(self, ut):       			    # expects the user termianl as argument
        logname = "HBSController.__init__"
        logging.info(logname)
        self.op = HBSOperator(ut)  # create an operator instance
        
        
    def load_storage_file(self):
        """ Loads or creates the storage file """
        logname = "HBSController.load_storage_file"

        self._storage_file = os.path.join(STORE_DIR, STORE_FILE)  # define path to the storage file
        if os.path.isfile(self._storage_file):
            if not self.load_from_file():
                result = Msg.err_storage_io
            else:
                result = Msg.storage_loaded
        else:   # file does not exist (e.g. first start ) -> prepare storage_places dict and save to file
            x_pos = 1
            z_pos = 1
            for box_nr in range(1, 51):     # from 1 to 50
                if x_pos > 10:              # 10 places on x-axis
                    x_pos = 1
                    z_pos += 1
                self._storage_places[box_nr] = {'x': x_pos, 'z': z_pos, 'taken': False, 'timestamp': None}
                x_pos += 1
            self.save_to_file()             # save
            result = Msg.storage_created
        logging.info(logname + ": " + result.name)
        if DEBUG:
            print(logname + ": " + result.name)
            self.print_all()              # optional: print all file entries in terminal
        return result
    
    
    def occupy_place(self, x_pos, z_pos):
        """ change box-status taken on 'true' and save timestamp"""
        place_nr = (z_pos - 1) * 10 + x_pos
        self._storage_places[place_nr]['taken'] = True
        self._storage_places[place_nr]['timestamp'] = time.time()
        self.save_to_file()


    def clear_place(self, x_pos, z_pos):
        """ change box-status taken on 'false' and remove timestamp"""
        place_nr = (z_pos - 1) * 10 + x_pos
        self._storage_places[place_nr]['taken'] = False
        self._storage_places[place_nr]['timestamp'] = None
        self.save_to_file()
        
        
    def get_place(self, x_pos, z_pos):
        """ Checks whether a place is occupied.
            Returns True (occupied) or False (empty) """
        place_nr = (z_pos - 1) * 10 + x_pos
        return self._storage_places[place_nr]['taken']
        
        
    def store_box(self, xpos, zlevel):
        """get new box from io-station 1 & put box in storage place (x,z).
           Return: message of action """
        logname = "HBSController.store_box: "
        log_msg = logname + str(xpos) + ", " + str(zlevel)
        logging.info(log_msg)
        if DEBUG:
            print(log_msg)
        # Validate the input
        if not self.op.check_xtarget(xpos):
            return Msg.err_wrong_x_target
        if not self.op.check_zlevel(zlevel):
            return Msg.err_wrong_z_target
        # Check whether the shelf is empty
        if self.get_place(xpos, zlevel):
            logging.info(logname + "shelf occupied " + str(xpos) + '/' + str(zlevel))
            print(logname + "shelf occupied " + str(xpos) + '/' + str(zlevel))
            return Msg.err_shelf_occupied
        # Get the box from the input belt and store it in the shelf
        result = self.op.fetch_box()
        if result is not Msg.okay:
            return result
        result = self.op.put_box(xpos, zlevel)
        if result is not Msg.okay:
            return result
        # Done
        self.occupy_place(xpos, zlevel)
        if DEBUG:
            self.print_all()
        return Msg.okay              
                    

    def destore_box(self, xpos, zlevel):
        """get box from storage place (x,z) & put box io-station 2
           Return: message of action """
        logname = "HBSController.destore_box: "
        log_msg = logname + str(xpos) + ", " + str(zlevel)
        logging.info(log_msg)
        if DEBUG:
            print(log_msg)
            
        # Validate input
        if not self.op.check_xtarget(xpos):
            return Msg.err_wrong_x_target
        if not self.op.check_zlevel(zlevel):
            return Msg.err_wrong_z_target
        # Check whether there is a box in the shelf
        if not self.get_place(xpos, zlevel):
            logging.info(logname + "shelf empty " + str(xpos) + '/' + str(zlevel))
            print(logname + "shelf empty " + str(xpos) + '/' + str(zlevel))
            return Msg.err_shelf_empty
        # Get the box and drop it to the output belt
        result = self.op.get_box(xpos, zlevel)
        if result is not Msg.okay:
            return result
        result = self.op.drop_box()
        if result is not Msg.okay:
            return result
        # Done
        self.clear_place(xpos, zlevel)
        if DEBUG:
            self.print_all()
        return Msg.okay
    
    
    def store_box_random(self):
        """Puts box in random storage place"""
        logname = "HBSController.store_box_random"
        log_msg = logname
        logging.info(log_msg)
        if DEBUG:
            print(log_msg)
        
        if not self.hbs_is_full():    # check if at least one free place is available
            place_found = False
            while not place_found:
                box_nr_random = random.randrange(1, 51)
                if not self._storage_places[box_nr_random]['taken']:
                    x_pos, z_level = self._storage_places[box_nr_random]['x'], self._storage_places[box_nr_random]['z']
                    result = self.store_box(x_pos, z_level)
                    if result is not Msg.okay:
                        return result
                    place_found = True
            if DEBUG:
                self.print_all()
            return Msg.okay
        else:
            msg = logname + ": storage is full!"
            logging.error(msg)
            print(msg)
            return Msg.err_storage_full


    def destore_box_random(self):
        """Takes a box from a random storage place"""
        logname = "HBSController.destore_box_random"
        log_msg = logname
        logging.info(log_msg)
        if DEBUG:
            print(log_msg)
        
        if self.hbs_is_not_empty():    # check if there is at least one box available
            place_found = False
            while not place_found:
                box_nr_random = random.randrange(1, 51)
                if self._storage_places[box_nr_random]['taken']:
                    x_pos, z_level = self._storage_places[box_nr_random]['x'], self._storage_places[box_nr_random]['z']
                    result = self.destore_box(x_pos, z_level)
                    if result is not Msg.okay:
                        return result
                    place_found = True
            if DEBUG:
                self.print_all()
            return Msg.okay
        else:
            msg = logname + ": storage is empty!"
            logging.error(msg)
            print(msg)
            return Msg.err_storage_empty


    def rearrange_box(self, old_xpos, old_zlevel, new_xpos, new_zlevel):
        """get box from (old_xpos, old_zlevel) & put box in (new_xpos, new_zlevel)"""
        logname = "HBSController.rearrange_box: "
        log_msg = logname
        logging.info(log_msg)
        if DEBUG:
            print(logname + str(old_xpos) + '/' + str(old_zlevel) + " - " + str(new_xpos) + '/' + str(new_zlevel))
        
        # Validate old input
        if not self.op.check_xtarget(old_xpos):
            return Msg.err_wrong_x_target
        if not self.op.check_zlevel(old_zlevel):
            return Msg.err_wrong_z_target
        # Check whether there is a box in the shelf
        if not self.get_place(old_xpos, old_zlevel):
            msg = logname + ": shelf empty " + str(old_xpos) + '/' + str(old_zlevel)
            logging.info(msg)
            print(msg)
            return Msg.err_shelf_empty
        # Validate new input
        if not self.op.check_xtarget(new_xpos):
            return Msg.err_wrong_x_target
        if not self.op.check_zlevel(new_zlevel):
            return Msg.err_wrong_z_target
        # Check whether the target shelf is empty
        if self.get_place(new_xpos, new_zlevel):
            msg = logname + ": shelf occupied " + str(new_xpos) + '/' + str(new_zlevel)
            logging.info(msg)
            print(msg)
            return Msg.err_shelf_occupied
        
        # Get box
        result = self.op.get_box(old_xpos, old_zlevel)
        if result is not Msg.okay:
            return result
        self.clear_place(old_xpos, old_zlevel)

        # Put box
        result = self.op.put_box(new_xpos, new_zlevel)
        if result is not Msg.okay:
            return result
        self.occupy_place(new_xpos, new_zlevel)
        
        # Done!
        return Msg.okay


    def hbs_is_full(self) -> bool:
        """returns True if high-bay storage is completely full"""
        for x in self._storage_places:
            if not self._storage_places[x]['taken']:
                return False
        return True


    def hbs_is_not_empty(self) -> bool:
        """returns True if at least one box is stored in high-bay storage"""
        for x in self._storage_places:
            if self._storage_places[x]['taken']:
                return True
        return False


    def save_to_file(self):
        """writes storage_places dict into file"""
        with open(self._storage_file, 'wb') as f:
            pickle.dump(self._storage_places, f, pickle.HIGHEST_PROTOCOL)


    def load_from_file(self):
        """read storage_places dict from file"""
        okay = True
        try:
            with open(self._storage_file, 'rb') as f:
                self._storage_places = pickle.load(f)
        except IOError:
            okay = False
        return okay
            

    def print_all(self):
        logname = "HBSController.print_all: "
        
        try:
            with open(self._storage_file, 'rb') as f:
                self._storage_places = pickle.load(f)
        except IOError:
            err_msg = logname + "file i/o error for " + self._storage_file
            logging.error(logname + "file i/o error for " + self._storage_file)
            print(err_msg)
            return
        
        print()
        print("High Bay Storage")
        print()
        for row in range(4, -1, -1):
            row_str = " " + str(row+1) + "  | "
            for col in range(1, 11):
                key = row * 10 + col
                if self._storage_places[key]['taken']:
                    row_str += '* | '
                else:
                    row_str += '- | '
            print(row_str)
        print("    " + 41 * '=')
        row_str = "      "
        for col in range(1, 11):
            row_str += str(col) + "   "
        print(row_str)
        print()    
                
             
    @property
    def occupancy(self):
        return self._storage_places
             
    @property
    def x(self):
        return self.op.get_xpos()
    
    @property
    def y(self):
        return self.op.get_ypos()
    
    @property
    def z(self):
        return self.op.get_zpos()
    
    
#=======================================================================================================
            
if __name__ == "__main__":
    
    ut = UserTerminal()
    hbs_ctr = HBSController(ut)
    
    """
    if not hbs_ctr.op.init_ypos():
        print(Msg.err_y_pos)
    if not hbs_ctr.op.init_zpos():
        print(Msg.err_z_pos)
    if not hbs_ctr.op.init_xpos():
        print(Msg.err_x_pos)
    """
 
    hbs_ctr.load_storage_file()
    hbs_ctr.print_all()
    ut.show_occupancy(hbs_ctr.occupancy)
    