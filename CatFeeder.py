import sys
import tty
import brickpi3
import time
import random
import datetime
import json
import iothub_client
from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue

try:
    import picamera
except ImportError:
    pass


with open('config.json') as configFie:
    config = json.load(configFie)
CONNECTION_STRING = config['connection']

PROTOCOL = IoTHubTransportProvider.MQTT
BP = None


def catfood_client_init():
    client = IoTHubClient(CONNECTION_STRING, PROTOCOL)
    return client


def send_confirmation_callback(message, result, user_context):
    print ("\nLEGO.CatFeeder IoT Hub responded to message with status: %s" % (result))


def method_callback(method_name, payload, user_context):
    print ("\nCallback method is called: \nMethodName = %s\nPayload = %s" %
           (method_name, payload))
    method_return_value = DeviceMethodReturnValue()

    # Just check invoked operations and do necessary things
    if method_name == "open":
        manage_lid(method_name)
    elif method_name == "close":
        manage_lid(method_name)
    elif method_name =="photo":
        take_photo()
    else:
        manage_lid(method_name)
        method_return_value.response = "{ \"Response\": \"No method is not defined to invoke: %s\" }" % method_name
        method_return_value.status = 404
        return method_return_value

    method_return_value.response = "{ \"Response\": \" %s is executed\" }" % method_name
    method_return_value.status = 200
    return method_return_value


def manage_lid(inkey):
    global BP

    if BP == None:
        BP = brickpi3.BrickPi3()
        try:
            BP.offset_motor_encoder(BP.PORT_A, BP.get_motor_encoder(BP.PORT_A))
            BP.offset_motor_encoder(BP.PORT_B, BP.get_motor_encoder(BP.PORT_B))
            BP.offset_motor_encoder(BP.PORT_C, BP.get_motor_encoder(BP.PORT_C))
            BP.offset_motor_encoder(BP.PORT_D, BP.get_motor_encoder(BP.PORT_D))
            print("BrickPi is set and ready to use...")
        except IOError as error:
            print("Unexpected BrickPi error: %s" % error)

    if inkey == 'close':
        BP.set_motor_power(BP.PORT_B, 100)
        time.sleep(0.55)
        BP.set_motor_power(BP.PORT_B, 0)

    elif inkey == 'open':
        BP.set_motor_power(BP.PORT_B, -100)
        time.sleep(0.6)
        BP.set_motor_power(BP.PORT_B, 0)
    else:
        BP.set_motor_power(BP.PORT_B, 0)
        BP.reset_all()
        return "quit"

    time.sleep(0.02)
    return inkey


def take_photo():
    # Some custom path to save taken photo
    resultPath = '/home/pi/Documents/Project/CameraApp/catfood.jpg'
    try:
        with picamera.PiCamera() as camera:
            camera.start_preview()
            time.sleep(1)
            camera.capture(resultPath)
            camera.stop_preview()
    except Exception as e:
        print(str(e))

    return resultPath

def command_manager(argument):
    argument = argument.lower()
    switcher={
        "o":_open,
        "c":_close,
        "p":_photo,
        "q":_quit
    }
    func = switcher.get(argument, "no command")
    return func()

def _open():
    manage_lid("open")
    return "Opened"

def _close():
    manage_lid("close")
    return "Closed"

def _photo():
    return take_photo()

def _quit():
    print("LEGO.CatFeeder is stopping...")
    return "Quit"

def main():
    print("Hello...\nThis is LEGO.CatFeeder with IoT Hub device/server feature.\nAn IoT Hub can send some messages to invoke some operations")
    print("\nPress Ctrl-C to exit...")
    try:
        client = catfood_client_init()
        client.set_device_method_callback(method_callback, None)

        while True:
            input_result = input("\nPlease enter a command.([o]pen - [c]lose - [p]hoto - [q]uit) : ")
            result = command_manager(input_result)
            message = "{\"result\": \"%s\",\"date\":\"%s\"}" % (
                result, str(datetime.datetime.now()))
            time.sleep(0.1)
            message = IoTHubMessage(message)
            client.send_event_async(message, send_confirmation_callback, None)
            
            time.sleep(0.1)
            
            if result == 'Quit':
                break

    except IoTHubError as iothub_error:
        print ("Unexpected error %s from IoTHub" % iothub_error)
        return
    except (KeyboardInterrupt, SystemExit):
        print ("\nLEGO.CatFeeder is stopped...")


if __name__ == '__main__':
    main()
