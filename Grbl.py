import serial
import pandas as pd
import os
import os.path
import yaml
import glob
import sys
import time


class Grbl:

    """
    Description: Creates an object with the needed functionality for both
    servo and stepper stages, using serial communication for the communication.

        Args:
            -port (string): serial communication port
            -grbl_bitrate (string): serial bitrate
            -timeout (string): timeout for serial communication (Does not apply
            to all commands, see command_sender())
            -motor (string): servo or linear
    """

    settings = pd.read_csv("setting_codes_en_US.csv")  # Dataframe with description of available settings in GRBL
    alarms = pd.read_csv("alarm_codes_en_US.csv")  # Dataframe with description of alarm messages in GRBL
    errors = pd.read_csv("error_codes_en_US.csv")  # Dataframe with description of error messages in GRBL
    # Initialization of various class variables
    list_serial_ports = None
    files_count = 0  # In selected directory for image recording

    with open('config.yml') as f_read:  # Configuration file for parameters to be stored from session to session
        config = yaml.load(f_read, Loader=yaml.FullLoader)
    f_read.close()

    def __init__(self, port, grbl_bitrate, timeout, motor):

        self.port = port
        self.grbl_bitrate = grbl_bitrate
        self.timeout = timeout
        self.lock_state = False
        self.motor = motor
        self.stop_reading = False
        self.linear_homed = False

        # Position initialization for motor type
        if self.motor == "servo":
            self.servo_position = 0
        elif self.motor == "linear":
            self.linear_position = {"X": 0, "Y": 0, "Z": 0}
            self.linear_wco = {"X_co": 0, "Y_co": 0, "Z_co": 0}
        try:
            print(self.port)
            self.connect = serial.Serial(self.port, self.grbl_bitrate, timeout=self.timeout)
        # Code to catch possible reasons for not successful connection
        except serial.SerialException as e:
            error = int(e.args[0].split("(")[1].split(",")[0])
            print(error)
            if error == 2:
                raise ValueError("Port nicht gefunden: "+self.motor)
            elif error == 13:
                raise ValueError("Zugriff verweigert: "+self.motor)
        self.start_msg = (self.connect.read(100)).decode()
        if self.motor == "servo" and "servo" not in self.start_msg:
            if not self.start_msg:
                raise ValueError("No response from the servo connected port")
            else:
                raise ValueError("Servo stage connected at linear")
            # as servo stage connected at linear
        elif self.motor == "linear":
            if not self.start_msg:
                raise ValueError("No response from the linear connected port")
            elif "servo" in self.start_msg:
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
            ports = ['COM%s' % (i + 1) for i in range(25)]
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
        Grbl.list_serial_ports = result

    def command_sender(self, command, ack=""):
        """
        Description: send the Gcode command to the desired Grbl board, servo or linear

            Args:
                -command (string): Gcode command to be sent
                -ack (string): response to expect from the board confirming the
                success of the operation. When sending commands non needing
                confirmation, this field is left empty.
            Returns:
                - True for a successful execution
                - grbl_out for an empty ack command, representing the error from
                the board
                - False for an unsuccessful execution
        """
        command = (command + "\n").encode()
        self.connect.reset_input_buffer()
        self.connect.write(command)
        print("Command sent:", command)
        if not ack:
            grbl_out = self.read_non_blocking(self.connect, "ok")
            print(grbl_out)
            if "ok" not in grbl_out:
                print(str(grbl_out)+"\n"+str(self.check_error(grbl_out)))
            elif "G" in command.decode():
                return True
            return grbl_out

        else:
            #  self.connect.timeout = 120  # To account for long homing or displacements
            ack_counter = 0
            while True:
                grbl_out = self.read_non_blocking(self.connect, ack)
                print(grbl_out)
                if ack in grbl_out:
                    if ack == "end" and ack_counter == 0:
                        ack_counter += 1
                        continue
                    else:
                        print("Displacement completed")
                        #  self.connect.timeout = 2  # Restore default timeout, check later
                        return True
                else:
                    print("No terminating character received")
                    return False  # Check_later, should grbl_out also be returned?

    def read_non_blocking(self, connection, read_until=""):
        """
        Description: thread friendly serial message sender, allows the
        termination of the execution thread when Grbl.stop_reading == True

            Args:
                -connection (pyserial connection object): pyserial object already initialized
                -read_until (string): what acknowledgment message to expect
        """
        data_str = ""
        counter = 0
        timeout = connection.timeout / 0.01
        if read_until:
            timeout = 300/0.01
        while connection.is_open:
            if self.stop_reading:  # Variable state changes to True when an
                # "emergency_stop" is issued by the user, see ProgressWindow.stop_reading
                print("Emergency cancel")
                connection.write(b"!")  # Stop executing commands
                #  connection.close()
                raise NotImplementedError("Stop reading")
            if connection.in_waiting > 0:  # Message received to buffer
                data_str += connection.read(connection.in_waiting).decode('ascii')
                if read_until and read_until in data_str:
                    return data_str
            else:
                counter += 1
                if timeout and counter > timeout:
                    return data_str
                time.sleep(0.01)

    @staticmethod
    def check_error(error_message):
        """
        Description: Retrieve the complete description of the error or alarm code

            Args:
                -error_message(string): unexpected response from the grbl board
            Returns:
                -alarm_description (string)
                -error_description (string)
        """
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

    def check_position(self):
        """
        Description: Retrieve position and wco (work coordinates offset) of the setup

            Returns:
                -pos_dict(dict): containing the machine position corrected with the wco values.
        """
        position_report = self.command_sender("?")
        wco = position_report.split("WCO")[1].strip("WCO:").split(">")[0].split(",")
        wco_dict = {"X_co": float(wco[0]), "Y_co": float(wco[1]), "Z_co": float(wco[2])}
        if wco_dict:
            self.linear_wco = wco_dict  # Save wco value
        position = position_report.split("MPos")[1].split("|")[0].strip("MPos:").split(">")[0].split(",")
        # If MPos: is given, use WPos = MPos - WCO
        pos_dict = {"X": float(position[0]) - self.linear_wco["X_co"], "Y": float(position[1]) -
                    self.linear_wco["Y_co"], "Z": float(position[2]) - self.linear_wco["Z_co"]}

        return pos_dict

    @staticmethod
    def check_new_file(file_path):
        """
        Description: checks the number of files in the past path

            Returns: number of files in the folder
        """
        return len([name for name in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, name))])

    @staticmethod
    def read_config(*args):
        """
        Description: reads and returns the value stored in the config file for a passed parameter

            Args: Field to check in .yaml configuration file, with the last value
            being the key

            Returns:
                -output: value of specified field
                -Grbl.config: complete configuration file
                -args_tup: tuple with the specified fields
                -key
        """
        key = args[-1]
        args_tup = tuple(args)
        output = Grbl.config[args_tup[0]][key]
        return output, Grbl.config, args_tup, key

    @staticmethod
    def write_config(*args, new_value=""):
        """
        Description: rewrite value for a passed parameter
        """
        #  global config Check this
        old_value, Grbl.config, args_tup, key = Grbl.read_config(*args)
        if old_value != new_value:
            Grbl.config[args_tup[0]][key] = new_value
            with open("config.yml", 'w') as f_write:
                yaml.dump(Grbl.config, f_write)
            f_write.close()
