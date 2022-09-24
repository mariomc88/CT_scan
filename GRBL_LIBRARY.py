import serial
import serial.tools.list_ports
import pandas as pd
import os
import os.path
import yaml
import sys
import glob
import time
from pynput.mouse import Listener, Button
from pynput.mouse import Controller as Mouse_controller
from pynput.keyboard import Controller as Keyboard_controller
from pynput.keyboard import Key


class Grbl:

    settings = pd.read_csv("setting_codes_en_US.csv")  # Dataframe with description of available settings in GRBL
    alarms = pd.read_csv("alarm_codes_en_US.csv")  # Dataframe with description of alarm messages in GRBL
    errors = pd.read_csv("error_codes_en_US.csv")  # Dataframe with description of error messages in GRBL
    list_ports = None
    clicks_counter = 0
    click_position = []
    position = 0
    files_count = 0

    with open('config.yml') as f_read:  # Configuration file for parameters to be stored from session to session
        config = yaml.load(f_read, Loader=yaml.FullLoader)
    f_read.close()

    def __init__(self, port, grbl_bitrate, timeout, motor):

        self.port = port
        self.grbl_bitrate = grbl_bitrate
        self.timeout = timeout
        self.lock_state = False
        self.motor = motor
        self.lock_state = False
        try:
            print(self.port)
            self.connect = serial.Serial(self.port, self.grbl_bitrate, timeout=self.timeout)
        except serial.SerialException as e:
            if e.errno == 2:
                raise ValueError("Non existent serial port "+self.motor)
            elif e.errno == 16:
                raise ValueError("Device or resource busy "+self.motor)
        self.start_msg = (self.connect.read(100)).decode()
        if self.motor == "servo" and "servo" not in self.start_msg:
            raise ValueError("Servo stage connected at linear")
        if self.motor == "linear" and "servo" in self.start_msg:
            raise ValueError("Linear stage connected at servo")
        if "'$H'|'$X' to unlock" in self.start_msg:  # If a part of the locked message is found
            self.lock_state = True

    @staticmethod
    def serial_ports():  # Function posted by tfeldmann in the stackoverflow post:
        # https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
        # returns the name of available ports depending on the system OS
        """ Lists serial port names

            raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        Grbl.list_ports = result
        # return result

    @staticmethod
    def check_error(error_message):  # Check the description for the corresponding alarm or error code
        if "ALARM" in error_message:
            alarm_code = error_message.split("ALARM:")[-1][0]
            alarm_description = Grbl.alarms.loc[Grbl.alarms['Alarm Code in v1.1+'] ==
                                                int(alarm_code)][" Alarm Description"].values[0]
            return alarm_description
        if "error" in error_message:
            error_code = error_message.split(":")[-1]
            error_description = Grbl.errors.loc[Grbl.errors['Error Code in v1.1+ '] ==
                                                int(error_code)][" Error Description"].values[0]
            return error_description
        else:
            print("No response received from command")

    def command_sender(self, command, ack=""):  # The acknowledgment will be "ok" for linear movements
        # or "end" for rotational movements.
        # Function to send the Gcode commands to the board, the number of arguments passed to it
        command = command.encode()
        self.connect.write(command)
        if not ack:
            grbl_out = self.connect.read_until(b"ok").decode()
            print(grbl_out)
            if "ok" not in grbl_out:
                print(str(grbl_out)+"\n"+str(self.check_error(grbl_out)))

        elif ack:
            end_counter = 0
            while True:
                grbl_out = serial.Serial(self.port, self.grbl_bitrate, timeout=15).read_until(ack.encode()).decode()
                if ack in grbl_out:
                    end_counter += 1
                else:
                    print("No response from controller")
                    break
                if end_counter == 2:
                    print("Displacement completed")
                    break

    @staticmethod
    def check_new_file(file_path):  # Checks the number of files in the past path
        return len([name for name in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, name))])

    @staticmethod
    def read_config(*args):  # Reads and returns the value stored in the config file for a passed parameter
        key = args[-1]
        args_tup = tuple(args)
        output = Grbl.config[args_tup[0]][key]
        return output, Grbl.config, args_tup, key
        # print(read_config("file_path", "route")[0])

    @staticmethod
    def write_config(*args, new_value=""):  # Rewrite value for a passed parameter
        #  global config Check this
        old_value, Grbl.config, args_tup, key = Grbl.read_config(*args)
        if old_value != new_value:
            Grbl.config[args_tup[0]][key] = new_value
            with open("config.yml", 'w') as f_write:
                yaml.dump(Grbl.config, f_write)
            f_write.close()

    def trial_angle_rotate(self, sense, advance):  # Rotation steps for the trial menu
        Grbl.write_config("ct_config", "Trials angle", new_value=advance)
        if sense == "up":
            Grbl.position += advance/360
            self.command_sender(command="G0 Z"+str(Grbl.position), ack="end")

        else:
            Grbl.position -= advance/360
            self.command_sender(command="G0Z"+str(Grbl.position), ack="end")
        print(Grbl.position)
        # self.lable_current_angle.setText("Current angle: "+str(MainWindow.position))
        # self.show()

    def trigger_sender(self, step, detector_type):
        if detector_type == "Flatpanel":
            if Grbl.clicks_counter == 0:
                def on_click(x, y, button, pressed):
                    if str(button) == "Button.left" and pressed is False:
                        print("Click")
                        print(Grbl.clicks_counter)
                        if Grbl.clicks_counter == 1:
                            click_position = [x, y]
                            print(click_position)
                            listener.stop()
                            pass
                        Grbl.clicks_counter += 1
                with Listener(on_click=on_click) as listener:
                    listener.join()
            else:
                Mouse_controller.position = set(Grbl.click_position)
                Mouse_controller.click(Button.left, 1)
            time.sleep(2)
            c = Keyboard_controller()
            c.type("Scan"+str(step))
            time.sleep(0.5)
            c.press(Key.enter)
        elif detector_type == "Medipix":
            self.command_sender("M08")
            time.sleep(0.5)
            self.command_sender("M09")

    def rotation_control(self, num, dir_path, detector_type):

        for step in range(1, num + 1):
            angle = round(360/num, 3)
            Grbl.position += angle/360
            self.command_sender("G0 Z"+str(Grbl.position), "end")
            self.trigger_sender(step, detector_type)
            while True:
                print(dir_path)
                if Grbl.check_new_file(dir_path) >= Grbl.files_count + 1:
                    Grbl.files_count = Grbl.check_new_file(dir_path)
                    break
                time.sleep(0.5)
            progress = round(step/num*100)
            # self.progressBar.setValue(progress)
            print(progress, "%")
        time.sleep(2)
