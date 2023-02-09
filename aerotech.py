"""
This module holds the class for interacting with an Aerotech XYZ.
Author R.Cole
"""

import socket
import logging
import select
import time

EOS_CHAR = '\n'   # End of string character
ACK_CHAR = '%'  # indicate success.
NAK_CHAR = '!'  # command error.
FAULT_CHAR = '#'  # task error.
TIMEOUT_CHAR = '$'


class Ensemble:
    """Class providing control over a single Aerotech XYZ stage."""
    def __init__(self, ip, port):
        """
        Parameters
        ----------
        ip : str
            The ip of the Ensemble, e.g. 'localhost'
        port : int
            The port, default 8000
        """
        self._ip = ip
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setblocking(True)
        self.connected = False
        self.x_enabled = False
        self.y_enabled = False
        self.x_homed = False
        self.y_homed = False
        self.pos_dict = None
        self.stop_reading = False
        logging.info('Ensemble instantiated.')

    def connect(self):
        """Open the connection."""
        try:
            if not self.connected:
                self._socket.connect((self._ip, self._port))
                self.connected = True
                print("Ensemble connected")
                logging.info('Connected')
                return True
        except ConnectionRefusedError:
            logging.error("Unable to connect.")
            raise ValueError("Unable to connect")

    def enable(self, axis):
        """Enable the axis"""
        axis = axis[0]
        command = ""
        if not self.connected:
            self.connect()
        if axis == "X":
            if not self.x_enabled:
                command = 'ENABLE ' + axis
            else:
                command = 'DISABLE ' + axis
            self.x_enabled = not self.x_enabled
        if axis == "Y":
            if not self.y_enabled:
                command = 'ENABLE ' + axis
            else:
                command = 'DISABLE ' + axis
            self.y_enabled = not self.y_enabled
        # self.write_read('ENABLE Y')
        #  self.write_read('ENABLE Z')
        self.write_read(command)
        if "ENABLE" in command:
            logging.info('Enabled axis', axis)
            print('Enabled axis', axis)
        else:
            logging.info('Disabled axis', axis)
            print('Disabled axis', axis)
        return True

    def write_read(self, command):
        """This method writes a command and returns the response,
        checking for an error code.
        Parameters
        ----------
        command : str
            The command to be sent, e.g. HOME X
        Returns
        ----------
        response : str
            The response to a command
        """
        print("Command sent: ", command)
        if EOS_CHAR not in command:
            command = ''.join((command, EOS_CHAR))
        self._socket.send(command.encode())
        self._socket.setblocking(True)
        ready = select.select([self._socket], [], [], None)
        while not ready:
            if self.stop_reading:
                self.abort_motion()
            print("checking")
            time.sleep(0.1)
        read = self._socket.recv(1024).decode().strip()
        code, response = read[0], read[1:]
        print("code", code)
        print("response", response)
        if code != ACK_CHAR:
            logging.error("Error from write_read().")
        return response

    def home(self, axis):
        """This method homes the stage."""
        axis = axis[0]
        if axis == "X" and self.x_enabled:
            self.write_read('HOME X')
            self.x_homed = True
            print("X axis homed")

        elif axis == "Y" and self.y_enabled:
            self.write_read('HOME Y')
            self.y_homed = True
            print("Y axis homed")
        else:
            print("Enable the axis first")
            return False
        # self.write_read('HOME Y')
        # self.write_read('HOME Z')
        logging.info('Homed', axis)
        print('Homed', axis)
        return True

    def move(self, x_pos="", y_pos=""):  # , z_pos):
        """Move to an X Y Z
        Parameters
        ----------
        x_pos : string
            The x position required with or without feed rate
        y_pos : string
            The y position required with or without feed rate
        """
        # command = "MOVEABS X%f XF10.0 Y%f YF10.0 Z%f ZF10.0" % (
        #     x_pos, y_pos, z_pos)
        command = "MOVEABS "
        if x_pos:
            command += str(x_pos)
            if "XF" not in x_pos:
                command += " XF10.0"
            if not self.x_enabled:
                print("Enable the X axis first")
                return False
        if y_pos:
            command += " " + str(y_pos)
            if "XF" not in y_pos:
                command += " YF10.0"
            if not self.y_enabled:
                print("Enable the Y axis first")
                return False
        print("Command sending is: ", command)
        self.write_read(command)
        logging.info('Command written: %s', command)
        return True

    def get_positions(self):
        """Method to get the latest positions.
        Returns
        ----------
        positions : dict
            The X,Y,Z positions.
        """
        x_pos = float(self.write_read('PFBK X'))
        y_pos = float(self.write_read('PFBK Y'))
        # z_pos = float(self.write_read('PFBK Z'))
        positions = {'X': x_pos, 'Y': y_pos}  # , 'Z':z_pos}
        logging.info('positions: %s', str(positions))
        return positions

    def position_reached(self, axis):
        """Method to check if both axis are in position.
        Returns
        ----------
        True: position reached
        """
        command = "WAIT INPOS " + axis
        self.write_read(command)
        logging.info("Position in axis %s reached" % axis)
        print("Position in axis %s reached" % axis)

    def abort_motion(self):
        """Method to abort motion on both axis"""
        command = "ABORT X Y"
        self.write_read(command)
        logging.info("Abort motion on both axis")
        print("Abort motion on both axis")

    def close(self):
        """Close the connection."""
        self._socket.shutdown(1)
        self._socket.close()
        self.connected = False
        logging.info("Connection closed")
