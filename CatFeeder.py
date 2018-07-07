#import sys
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


class CatFeeder:
    with open('config.json') as configFie:
        config = json.load(configFie)
    CONNECTION_STRING = config['connection']
    TEXT = ""
    PROTOCOL = IoTHubTransportProvider.MQTT
    BP = None
    
    def catfood_client_init(self):
        client = IoTHubClient(self.CONNECTION_STRING, self.PROTOCOL)
        return client

    def send_confirmation_callback(self,message, result, user_context):
        global TEXT
        time.sleep(0.3)
        self.TEXT = "\nLEGO.CatFeeder IoT Hub responded to message with status: %s" % (result)

    def method_callback(method_name, payload, user_context):
        print ("\nCallback method is called: \nMethodName = %s\nPayload = %s" %
               (method_name, payload))
        method_return_value = DeviceMethodReturnValue()

        result = command_manager(method_name)

        method_return_value.response = "{ \"Response\": \" %s is executed\" }" % method_name
        method_return_value.status = 200
        return method_return_value

    def manage_lid(self,inkey):
        global BP

        if self.BP == None:
            self.BP = brickpi3.BrickPi3()
            try:
                self.BP.offset_motor_encoder(
                    self.BP.PORT_A, self.BP.get_motor_encoder(self.BP.PORT_A))
                self.BP.offset_motor_encoder(
                    self.BP.PORT_B, self.BP.get_motor_encoder(self.BP.PORT_B))
                self.BP.offset_motor_encoder(
                    self.BP.PORT_C, self.BP.get_motor_encoder(self.BP.PORT_C))
                self.BP.offset_motor_encoder(
                    self.BP.PORT_D, self.BP.get_motor_encoder(self.BP.PORT_D))
                print("BrickPi is set and ready to use...")
            except IOError as error:
                print("Unexpected BrickPi error: %s. Please re-try" % error)

        if inkey == 'close':
            self.BP.set_motor_power(self.BP.PORT_B, 100)
            time.sleep(0.55)
            self.BP.set_motor_power(self.BP.PORT_B, 0)

        elif inkey == 'open':
            self.BP.set_motor_power(self.BP.PORT_B, -100)
            time.sleep(0.6)
            self.BP.set_motor_power(self.BP.PORT_B, 0)
        else:
            self.BP.set_motor_power(self.BP.PORT_B, 0)
            self.BP.reset_all()
            return "quit"

        time.sleep(0.02)
        return inkey

    def take_photo(self):
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

    def command_manager(self,argument):
        argument = argument.lower()
        switcher = {
            "o": self._open,
            "c": self._close,
            "p": self._photo,
            "q": self._quit
        }
        func = switcher.get(argument, "Invalid command")
        return func()

    def _open(self):
        self.manage_lid("open")
        return "Opened"

    def _close(self):
        self.manage_lid("close")
        return "Closed"

    def _photo(self):
        return self.take_photo()

    def _quit(self):
        print("LEGO.CatFeeder is stopping...")
        return "Quit"

    def run(self):
        print("Hello...\nThis is LEGO.CatFeeder with IoT Hub device/server feature.\nAn IoT Hub can send some messages to invoke some operations")
        print("\nPress Ctrl-C to exit...")
        try:
            client = self.catfood_client_init()
            client.set_device_method_callback(self.method_callback, None)

            while True:
                print(self.TEXT, end=" ")
                print(
                    "\nPlease enter a command.([o]pen - [c]lose - [p]hoto - [q]uit) : ", end=" ")
                input_result = input()
                result = self.command_manager(input_result)

                message = "{\"result\": \"%s\",\"date\":\"%s\"}" % (
                    result, str(datetime.datetime.now()))

                message = IoTHubMessage(message)
                client.send_event_async(
                    message, self.send_confirmation_callback, None)

                time.sleep(0.1)

                if result == 'Quit':
                    break

        except IoTHubError as iothub_error:
            print ("Unexpected error %s from IoTHub" % iothub_error)
            return
        except (KeyboardInterrupt, SystemExit):
            print ("\nLEGO.CatFeeder is stopped...")


if __name__ == '__main__':
    feeder = CatFeeder()
    feeder.run()
