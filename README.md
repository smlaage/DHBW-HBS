# Umstellung eines Fischertechnik Hochregallagers auf IoT

Das Hochregallager wird über den Raspberry Pi in Kombination mit einer Erweiterungsplatine gesteuert.
Auf dem Pi läuft ein MQTT-Broker über den das Hochregallager über das Topic "hochregallager/set" angesteuert werden kann. 
Weiter ist auf dem Pi ein Samba-Share "IoTHochregallager" eingerichtet. 

IP: 192.168.178.40
user: dhbw-iot
passwd: dagobert34

mqtt-topic: hochregallager/set
mqtt-user: dhbw-mqtt
mqtt-passwd: daisy56

# example usage in terminal

mosquitto_pub -h 192.168.178.40 -t "hochregallager/set" -m '{"operation": "STORE_RANDOM"}' -u "dhbw-mqtt" -P "daisy56"

# Mögliche Messages

Eine MQTT-Message muss als JSON-String formatiert sein.

{"operation": "\<operation>"}  
{"operation": "\<operation>", "x": \<insert-x>, "z": \<insert-z>}  
{"operation": "\<operation>", "x": \<insert-x>, "z": \<insert-z>, "x_new": \<insert-x_new>, "z_new": \<insert-z_new>}

Folgende Operationen und Parameter sind verfügbar:
- STORE
    - x
    - z
- STORE_RANDOM
- STORE_ASCENDING
- REARRANGE
    - x
    - z
    - x_new
    - z_new
- DESTORE
    - x
    - z
- DESTORE_RANDOM
- DESTORE_ASCENDING
- DESTORE_OLDEST

## Beispiel messages


    {"operation": "STORE", "x": 10, "z": 5}

    {"operation": "STORE_RANDOM"}

    {"operation": "STORE_ASCENDING"}

    {"operation": "REARRANGE", "x": 10, "z": 5, "x_new": 1, "z_new": 1}

    {"operation": "DESTORE", "x": 10, "z": 5}

    {"operation": "DESTORE_RANDOM"}

    {"operation": "DESTORE_ASCENDING"}

    {"operation": "DESTORE_OLDEST"}

# iot-logistikmodel