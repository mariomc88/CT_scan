"""
This module holds the class for interacting with an Aerotech XYZ.
Author R.Cole
"""

import socket
import logging

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
        if not self.connected:
            self.connect()
        self.write_read('ENABLE ' + axis)
        if axis == "X":
            self.x_enabled = True
        elif axis == "Y":
            self.y_enabled = True
        # self.write_read('ENABLE Y')
        #  self.write_read('ENABLE Z')
        logging.info('Enabled axis', axis)
        print('Enabled axis', axis)

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
        if EOS_CHAR not in command:
            command = ''.join((command, EOS_CHAR))

        self._socket.send(command.encode())
        read = self._socket.recv(4096).decode().strip()
        code, response = read[0], read[1:]
        if code != ACK_CHAR:
            logging.error("Error from write_read().")
        return response

    def home(self, axis):
        """This method homes the stage."""
        self.connect()
        if axis == "X" and self.x_enabled:
            self.write_read('HOME X')
            self.x_homed = True
            print("X axis homed")

        elif axis == "Y" and self.y_enabled:
            self.write_read('HOME Y')
            self.y_homed = True
            print("Y axis homed")

        # self.write_read('HOME Y')
        # self.write_read('HOME Z')
        logging.info('Homed', axis)

    def move(self, x_pos, y_pos):  # , z_pos):
        """Move to an X Y Z
        Parameters
        ----------
        x_pos : double
            The x position required
        y_pos : double
            The y position required
        """
        # command = "MOVEABS X%f XF10.0 Y%f YF10.0 Z%f ZF10.0" % (
        #     x_pos, y_pos, z_pos)
        command = "MOVEABS X%f XF10.0 Y%f YF10.0" % (
            x_pos, y_pos)
        self.write_read(command)
        logging.info('Command written: %s', command)

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

    def positions_reached(self):
        """Method to check if both axis are in position.
        Returns
        ----------
        True : position reached
        """
        command = "WAIT INPOS XY"
        self.write_read(command)
        logging.info('Position reached')

    def close(self):
        """Close the connection."""
        self._socket.shutdown(1)
        self._socket.close()
        self.connected = False
        logging.info("Connection closed")
