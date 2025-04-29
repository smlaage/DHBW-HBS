""" Hochregal-Lager - hbs_mqtt_client.py

MQTT client for the high bay storage system

SLW 03/2025
"""


import time
import paho.mqtt.client as mqtt
import logging

"""
Example:
$ mosquitto_pub -u dhbw-mqtt -P daisy56 -t hochregallager/set -m "{\"operation\": \"STORE_RANDOM\"}"
"""

# from typing import Callable, Dict, Any, Optional

SERVER_IP = '192.168.1.94'
SERVER_PORT = 1883
TOPIC_SUB = "hochregallager/set"
TOPIC_STATUS = "hochregallager/status"
TOPIC_RESULT = "hochregallager/result"
MQTT_USERNAME = 'dhbw-mqtt'
MQTT_PASSWORD = 'daisy56'


class MQTTClient:
    """ Class for mqtt connection """
    ut = object
    hbs_ctr = object
    
    def __init__(self, 
                 server_ip: str = SERVER_IP,
                 server_port: int = SERVER_PORT,
                 mqtt_username: str = MQTT_USERNAME,
                 mqtt_password: str = MQTT_PASSWORD):
        """Initialisiert den MQTT-Client mit den angegebenen Verbindungsdaten"""
   
        self.server_ip = server_ip
        self.server_port = server_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        
        self.client = mqtt.Client()
        self.client.username_pw_set(mqtt_username, mqtt_password)
        self.client.on_connect = self._on_connect

        self._connected = False


    def connect(self, message_handler):
        """Verbindet sich mit dem MQTT-Broker und startet die Subscription """
        logname = "MQTTClient.connect"
        
        success = True
        if self._connected:
            logging.info(logname + "MQTT Client connected already")
            return success
            
        logging.info(logname + ": Connect to MQTT-Broker " + self.server_ip + ':' + str(self.server_port))
        try:
            self.client.connect(self.server_ip, self.server_port, 60)
        except ConnectionRefusedError as err:
            msg = logname + ": " + str(err)
            logging.error(msg)
            print(msg)
            return False

        self.client.subscribe(TOPIC_SUB)
        logging.info(logname + ": Subscription started on: " + TOPIC_SUB)
        self.client.on_message = message_handler 	# callback function for messages
        self.client.loop_start()
        
        print()
        print("MQTT connected and subscription started!")
        start_msg =  "\nUse: 'mosquitto_pub -h " + self.server_ip
        start_msg += ' -t "' + TOPIC_SUB + '"'
        start_msg += ' -u "' + MQTT_USERNAME + '"'
        start_msg += ' -P "' + MQTT_PASSWORD + '"'
        start_msg += ' -m \"{\"operation\": \"STORE_RANDOM\"}\" '
        print(start_msg)
        print()
        
        return True
        

    def disconnect(self) -> None:
        """Trennt die Verbindung zum MQTT-Broker"""
        if self._connected:
            self.client.loop_stop()
            self.client.disconnect()
            self._connected = False
            
                    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        """ Callback-Funktion, die bei erfolgreicher Verbindung aufgerufen wird """
        logname = "MQTTClient._on_connect: "
        
        if rc == 0:
            self._connected = True
            logging.info(logname + "connected!")
            print(logname + "connected!")
            
        else:
            self._connected = False
            logging.error(logname + "connection failed with code " + str(rc))
            print("connection failed with code " + str(rc))

    
    def send_status(self, status):
        """ Publishes the system status via MQTT """
        self.client.publish(TOPIC_STATUS, status)
        
        
    def send_result(self, result):
        """ Publishes the result of an operation via MQTT """
        self.client.publish(TOPIC_RESULT, result)        

    
    @property
    def is_connected(self):
        return self._connected

            
#=================================================================================
            
if __name__ == "__main__":
    
    def message_handler(client, userdata, msg):
        payload = msg.payload.decode()
        print(payload)         
         
    mqttc = MQTTClient()
    success = True
    mqttc.connect(message_handler)
    
    if success:
        for idx in range(10):
            mqttc.send_status("Hallo " + str(idx))
            time.sleep(0.25)
        
        mqttc.disconnect()
    