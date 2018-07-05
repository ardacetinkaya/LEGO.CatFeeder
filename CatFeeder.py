import sys
import tty
import brickpi3
import time
import random
import datetime

import iothub_client
from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue

CONNECTION_STRING = ""
PROTOCOL = IoTHubTransportProvider.MQTT
BP = None


def catfood_client_init():
    client = IoTHubClient(CONNECTION_STRING, PROTOCOL)
    return client


def send_confirmation_callback(message, result, user_context):
    print ("LEGO.CatFeeder IoT Hub responded to message with status: %s" % (result))


def method_callback(method_name, payload, user_context):
    print ("\nCallback method is called: \nMethodName = %s\nPayload = %s" % (method_name, payload))
    method_return_value = DeviceMethodReturnValue()
    #Just check invoked operations and do necessary things
    if method_name == "open":
        manage_lid(method_name)
    elif method_name == "close":
        manage_lid(method_name)
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
        #print ("close")
        BP.set_motor_power(BP.PORT_B, 100)
        time.sleep(0.55)
        BP.set_motor_power(BP.PORT_B, 0)

    elif inkey == 'open':
        #print ("open")
        BP.set_motor_power(BP.PORT_B, -100)
        time.sleep(0.6)
        BP.set_motor_power(BP.PORT_B, 0)
    else:
        #print ("quit")
        BP.set_motor_power(BP.PORT_B, 0)
        BP.reset_all()
        return "quit"

    time.sleep(0.02)
    return inkey


def main():
    print("Hello...\nThis is LEGO.CatFeeder with IoT Hub device/server feature.\nAn IoT Hub can send some messages to invoke some operations")
    print("\nPress Ctrl-C to exit...")
    try:
        client = catfood_client_init()
        client.set_device_method_callback(method_callback, None)

        while True:
            lid_status = input("\nOpen or Close lid: ")
            result = manage_lid(lid_status)
            message = "{\"lid\": \"%s\",\"date\":\"%s\"}" % (lid_status, str(datetime.datetime.now()))
            message = IoTHubMessage(message)

            print("Sending message to IoT Hub: %s" % message.get_string())
            client.send_event_async(message, send_confirmation_callback, None)
            time.sleep(0.2)
            if result == 'quit':
                break

    except IoTHubError as iothub_error:
        print ("Unexpected error %s from IoTHub" % iothub_error)
        return
    except (KeyboardInterrupt, SystemExit):
        print ("\nLEGO.CatFeeder is stopped...")


if __name__ == '__main__':
    main()
