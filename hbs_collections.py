""" hbs_collections.py

This file comprises a number of enumerations for various usages in the context of the high bay storage system.

SLW 04-2025
"""

from enum import Enum

# I/O Pins
class IOPins:    
    x_up = (0, 0)   	# WH 7S1 X-Achse nach X+ / X-axis to X+
    x_down = (0, 1)		# GN 7S2 X-Achse nach X- / X-axis to X3
    x_slow = (0, 2)		# YE 11K2 X-Achse langsam / a-Axis slow
    y_in = (0, 3)		# GY 12A1 Y-Achse nach Y- / Y-axis to Y5
    y_out = (0, 4)   	# PK 12A1 Y-Achse nach Y+ / Y-axis to Y+
    z_up = (0, 5)		# VT 12A1 Z-Achse nach Z+ / EZ-axis to Z+
    z_down = (0, 6)		# GY-PK 12A1 Z-Achse nach Z- / Z-axis to Z8
    io1_out = (0, 7)	# RD-BU 12A2 E/A-Station 1 auslagern / I/O-station 1 release from stock
    io1_in = (1, 0)		# WH-GN 12A2 E/A-Station 1 einlagern / I/O-station 1 place into stock
    io2_out = (1, 1)	# BN-GN 12A2 E/A-Station 2 auslagern / I/O-station 2 release from stock
    io2_in = (1, 2)		# WH-YE 12A2 E/A-Station 2 einlagern / I/O-station 2 place into stock

# System status
class SysStatus(Enum):
    error = -1
    ready = 0
    busy = 1

# Y axis positions
class YPos(Enum):
    DESTORE = 0
    DEFAULT = 1
    STORE = 2
    UNDEFINED = -1

# Messages
class Msg(Enum):
    okay = 0
    # Storage file handling
    storage_loaded = 1
    storage_created = 2
    # Errors for operations store and destore
    err_storage_io = 3
    err_shelf_empty = 4
    err_shelf_occupied = 5
    err_wrong_x_target = 6
    err_wrong_y_target = 7
    err_wrong_z_target = 8
    err_wrong_z_level = 9
    err_storage_full = 10
    err_storage_empty = 11
    # Mechanical issues, e.g. sensors not responding
    err_input_belt = 19
    err_y_pos  = 20		# Axis not responding
    err_x_pos  = 21
    err_z_pos  = 22
    err_xz_pos = 23
    err_x_udf  = 24		# Actual position undefined
    err_y_udf  = 25    
    err_z_udf  = 26
    # Errors during the initialization of the axis
    err_x_init = 30
    err_y_init = 31
    err_z_init = 32
    # Errors during the encoding of MQTT/JSON commands
    err_json_format 	= 40
    err_json_noop 		= 41
    err_cmd_unknown 	= 42
    err_wrong_args      = 43
    err_wrong_arg_cnt	= 44
    # Internal error - this should not happen
    err_internal	   = 90
    # System messages
    sys_exit = 97
    shutdown = 98
    err_emrg_stop  = 99
