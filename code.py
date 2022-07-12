import time
import board
import neopixel
from analogio import AnalogOut

import ipaddress
import wifi
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as MQTT


# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print("Connected to MQTT Broker!")
    print("Flags: {0}\n RC: {1}".format(flags, rc))

def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    print("Disconnected from MQTT Broker!")
    wifi_connected = False

def subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))

def unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))

def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    print("Published to {0} with PID {1}".format(topic, pid))

def message(client, topic, message):
    # Method called when a client's subscribed feed has a new value.
    print("New message on topic {0}: {1}".format(topic, message))
    if len(message.split(":")) == 2:
      Key = message.split(":")[0]
      KeyValue = message.split(":")[1]
      if Key == "router":
        if KeyValue == "reboot":
          try:
            led.fill(BLUE) 
            analog_out.value = 65535
            mqtt_client.publish(secrets["mqtt_topic"], "status:power_off")

            time.sleep(5)

            analog_out.value = 0
            mqtt_client.publish(secrets["mqtt_topic"], "status:reboot_done")
            led.fill(GREEN)
            print ("Reboot complete") 
          except:
            print ("Failed to complete reboot")
            analog_out.value = 0
            led.fill(ORANGE) 
      

def connect_wifi():
  try:
    print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

    print("Connecting to %s"%secrets["ssid"])
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    print("Connected to %s!"%secrets["ssid"])
    print("My IP address is", wifi.radio.ipv4_address)
  except:
    print ("Failed to connect to wifi")
    led.fill(ORANGE) 
    return False, None

  # Create a socket pool
  pool = socketpool.SocketPool(wifi.radio)

  # Set up a MiniMQTT Client
  mqtt_client = MQTT.MQTT(
      broker=secrets["mqtt_broker"],
      port=secrets["mqtt_port"],
      socket_pool=pool,
  )

  # Connect callback handlers to mqtt_client
  mqtt_client.on_connect = connect
  mqtt_client.on_disconnect = disconnect
  mqtt_client.on_subscribe = subscribe
  mqtt_client.on_unsubscribe = unsubscribe
  mqtt_client.on_publish = publish
  mqtt_client.on_message = message

  try:
    print("Attempting to connect to %s" % mqtt_client.broker)
    mqtt_client.connect()
  except:
    print ("Failed to connect to MQTT broker")
    led.fill(ORANGE) 
    return False, None
    

  print("Subscribing to %s" % secrets["mqtt_topic"])
  mqtt_client.subscribe(secrets["mqtt_topic"])

  led.fill(GREEN) 
  return True, mqtt_client


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

#Onboard neopixel is used as a status indicator
BLACK = (0,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
ORANGE = (255,127,0)
led = neopixel.NeoPixel(board.NEOPIXEL, 1)
led.fill(BLACK) 

#Pin A0 is connected to IoT Relay switch
analog_out = AnalogOut(board.A0)
analog_out.value = 0

wifi_connected = False


while True:
  if not wifi_connected:
    wifi_connected, mqtt_client = connect_wifi()
 
  if wifi_connected:
    if not mqtt_client.is_connected():
      wifi_connected = False
      led.fill(ORANGE) 

  if wifi_connected:
    try:
      mqtt_client.loop()
    except:
      print ("Lost connection to MQTT broker")
      wifi_connected = False
      led.fill(ORANGE) 

  time.sleep(0.5)


