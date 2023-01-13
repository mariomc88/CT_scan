from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import pyqtSlot, QObject, QRunnable, QThreadPool
from MainWindow_2 import Ui_CT_controller
from locked import Ui_Unlocksystem
from progress_bar import Ui_Progress_window
from connection_parameters import Ui_Connection_parameters
import serial
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
    servo_position = 0
    files_count = 0
    stop_reading = False

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
        if self.motor == "servo":
            self.servo_position = 0
        elif self.motor == "linear":
            self.linear_position = {"X": 0, "Y": 0, "Z": 0}
            self.linear_wco = {"X_co": 0, "Y_co": 0, "Z_co": 0}
        try:
            print(self.port)
            self.connect = serial.Serial(self.port, self.grbl_bitrate, timeout=self.timeout)
        except serial.SerialException as e:
            error = int(e.args[0].split("(")[1].split(",")[0])
            print(error)
            if error == 2:
                raise ValueError("Port nicht gefunden: "+self.motor)
            elif error == 13:
                raise ValueError("Zugriff verweigert: "+self.motor)
        self.start_msg = (self.connect.read(100)).decode()
        if self.motor == "servo" and "servo" not in self.start_msg:
            print("servo_fault: ", self.start_msg)
            raise ValueError("Servo stage connected at linear")
        elif self.motor == "linear" and "servo" in self.start_msg:
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
        Grbl.list_ports = result
        # return result

    @staticmethod
    def read_non_blocking(connection, read_until=""):
        data_str = ""
        counter = 0
        if connection.timeout:
            timeout = connection.timeout / 0.01
        else:
            timeout = 0
        while connection.is_open:
            if Grbl.stop_reading:
                connection.write(b"!")
                #  connection.close()
                raise NotImplementedError("Stop reading")
            if connection.in_waiting > 0:
                data_str += connection.read(connection.in_waiting).decode('ascii')
            else:
                counter += 1
                if (timeout and counter > timeout) or (read_until and read_until in data_str):
                    return data_str
                time.sleep(0.01)

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
        # Function to send the GCode commands to the board, the number of arguments passed to it
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
            self.connect.timeout = 120
            while True:
                #  grbl_out = self.connect.read_until(ack.encode()).decode()
                grbl_out = self.read_non_blocking(self.connect, ack)
                print(grbl_out)
                if ack in grbl_out:
                    print("Displacement completed")
                    self.connect.timeout = 2
                    return True
                else:
                    print("No terminating character received")
                    return False

    def check_position(self):
        position_report = self.command_sender("?")
        wco = position_report.split("WCO")[1].strip("WCO:").split(">")[0].split(",")
        wco_dict = {"X_co": float(wco[0]), "Y_co": float(wco[1]), "Z_co": float(wco[2])}
        self.linear_wco = wco_dict
        position = position_report.split("MPos")[1].split("|")[0].strip("MPos:").split(">")[0].split(",")
        pos_dict = {"X": float(position[0]) - wco_dict["X_co"], "Y": float(position[1]) - wco_dict["Y_co"],
                    "Z": float(position[2]) - wco_dict["Z_co"]}

        return pos_dict

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

    def trial_angle_rotate(self, sense, advance, mm_per_rot, servo):  # Rotation steps for the trial menu
        Grbl.write_config("ct_config", "Trials angle", new_value=advance)
        if sense == "up":
            servo.servo_position += advance/360*mm_per_rot
            #  successful = self.command_sender(command="G0 Z"+str(servo.servo_position), ack="end") No end
            self.command_sender(command="G0 Z" + str(servo.servo_position))
        else:
            servo.servo_position -= advance/360*mm_per_rot
            #  successful = self.command_sender(command="G0 Z"+str(servo.servo_position), ack="end")  No end
            self.command_sender(command="G0 Z" + str(servo.servo_position))
        #  print("Command successful: ", successful) No end
        #  return successful No end

        # self.label_current_angle.setText("Current angle: "+str(MainWindow.servo_position))
        # self.show()


Grbl.serial_ports()
print(Grbl.list_ports)


class WorkerSignals(QObject):

    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)
    result = QtCore.pyqtSignal(bool)
    progress = QtCore.pyqtSignal(int)


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        if "rotation_control" in str(self.fn):
            self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)  # Return the result of the processing
            self.signals.finished.emit()  # Done
        except NotImplementedError:
            self.signals.finished.emit()
            self.signals.error.emit("Close all")


class ConnectionWindow(QMainWindow, Ui_Connection_parameters, Grbl):

    controller_MainWindow = None

    def __init__(self):
        super().__init__()
        #  QtWidgets.QApplication.__init__(self,)
        self.setupUi(self)
        self.pushButton_check.clicked.connect(self.connection_worker)
        self.linear_port = Grbl.read_config("linear_stage", "port")[0]
        self.servo_port = Grbl.read_config("servo_stage", "port")[0]
        self.ensemble_IP = Grbl.read_config("ensemble", "IP")[0]

        self.ensemble_port = Grbl.read_config("ensemble", "port")[0]
        self.linear = None
        self.servo = None
        self.servo_connected = False
        self.linear_connected = False
        self.combobox()
        #  self.thread = None
        self.worker = None
        self.threadpool = QThreadPool()
        #  print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def combobox(self):
        print("Serial ports available:", len(Grbl.list_ports))
        self.comboBox_linear.clear()
        self.comboBox_servo.clear()
        if self.linear_port:
            self.comboBox_linear.addItem('"Saved"' + self.linear_port)
        if self.servo_port:
            self.comboBox_servo.addItem('"Saved"' + self.servo_port)
        if Grbl.list_ports:
            self.comboBox_linear.addItems(Grbl.list_ports)
            self.comboBox_servo.addItems(Grbl.list_ports)
        if self.ensemble_IP:
            self.lineEdit_ens_IP.setText(self.ensemble_IP)
        if self.ensemble_port:
            self.lineEdit_ens_port.setText(self.ensemble_port)

    def connection(self):
        try:
            selected_servo_port = self.comboBox_servo.currentText().replace('"Saved"', "")
            self.servo = Grbl(selected_servo_port, 115200, 2, "servo")
            if self.servo_port != selected_servo_port:
                Grbl.write_config("servo_stage", "port", new_value=selected_servo_port)
            self.label_error_servo.clear()
            self.label_error_servo.setText("Correct servo connection")
            self.servo_connected = True
        except ValueError as e:
            self.label_error_servo.setText(str(e))
        try:
            selected_linear_port = self.comboBox_linear.currentText().replace('"Saved"', "")
            self.linear = Grbl(selected_linear_port, 115200, 2, "linear")
            if self.linear_port != selected_linear_port:
                Grbl.write_config("linear_stage", "port", new_value=selected_linear_port)
            self.label_error_linear.clear()
            self.label_error_linear.setText("Correct linear connection")
            self.linear_connected = True
        except ValueError as e:
            self.label_error_linear.setText(str(e))
        if self.linear_connected and self.servo_connected:
            print("Correct connection")
            return True
        else:
            if self.servo_connected:
                self.servo.connect.close()
            elif self.linear_connected:
                self.linear.connect.close()
            print("Incorrect connection")
            Grbl.serial_ports()
            self.combobox()
            return False

    def switch_window(self, connection):
        if connection:

            if self.linear.lock_state:
                controller = Controller(UnlockWindow(self.servo, self.linear))
                controller.show_window()
            else:
                ConnectionWindow.controller_MainWindow = Controller(MainWindow(self.servo, self.linear))
                ConnectionWindow.controller_MainWindow.show_window()
            self.close()

    def connection_worker(self):
        self.pushButton_check.setEnabled(False)
        self.worker = Worker(self.connection)
        self.worker.signals.result.connect(self.switch_window)
        self.worker.signals.finished.connect(lambda: (self.pushButton_check.setEnabled(True)))
        self.threadpool.start(self.worker)
        """
                self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.start()
        """


class MainWindow(QMainWindow, Ui_CT_controller):  # Class with the main window

    def __init__(self, servo, linear):
        super().__init__()
        #  QtWidgets.QApplication.__init__(self)
        # Set up window widgets
        #  definition of needed variables in the class
        self.n_steps = int(Grbl.read_config("ct_config", "Angles per rotation")[0])
        self.trial_rot = float(Grbl.read_config("ct_config", "Trials angle")[0])
        self.dir_path = str(Grbl.read_config("file_path", "route")[0])
        self.detector = float(Grbl.read_config("ct_config", "Distance source detector")[0])
        self.sample = float(Grbl.read_config("ct_config", "Distance Source object")[0])
        self.vertical = float(Grbl.read_config("ct_config", "Object vertical position")[0])
        self.detector_type = str(Grbl.read_config("ct_config", "Detector type")[0])
        self.mm_per_rot = 360
        self.files_count = 0
        self.setupUi(self)
        self.servo = servo
        self.linear = linear
        self.linear.linear_position = self.linear.check_position()
        self.update_linear_position()
        self.lineEdit_steps.editingFinished.connect(self.check_even)
        self.up_pushButton.clicked.connect(
            lambda: (self.trial_rot_worker("up", float(self.lineEdit_angle_trial.text()))))
        self.down_pushButton.clicked.connect(
            lambda: (self.trial_rot_worker("down", float(self.lineEdit_angle_trial.text()))))
        self.vert_up_pushButton.clicked.connect(
            lambda: (self.vert_axis_worker("+", float(self.lineEdit_vert_disp.text()))))
        self.vert_down_pushButton.clicked.connect(
            lambda: (self.vert_axis_worker("-", float(self.lineEdit_vert_disp.text()))))
        self.pushButton_set.clicked.connect(self.read_linedit)
        self.pushButton_next.clicked.connect(self.switch_window)
        self.actionReset_GRBL.triggered.connect(lambda: (self.linear.command_sender(chr(24))))
        self.actionChoose_file_path.triggered.connect(self.get_path)
        #  self.lineEdit_vertical.setText(str(self.vertical))
        self.lineEdit_vert_disp.setText(str(self.vertical))
        self.lineEdit_sample.setText(str(self.sample))
        self.lineEdit_detector.setText(str(self.detector))
        self.lineEdit_steps.setText(str(self.n_steps))
        self.lineEdit_angle_trial.setText(str(self.trial_rot))
        self.file_path_label.setText("File path: " + str(self.dir_path))
        self.radioButton_Flatpanel.clicked.connect(lambda: (self.detector_choice("Flatpanel")))
        self.radioButton_Medipix.clicked.connect(lambda: (self.detector_choice("Medipix")))
        self.radioButton_Trial_Mode.clicked.connect(lambda: (self.detector_choice("Trial")))
        if self.detector_type == "Flatpanel":
            self.radioButton_Flatpanel.setChecked(True)
            self.radioButton_Medipix.setChecked(False)
            self.radioButton_Trial_Mode.setChecked(False)
        elif self.detector_type == "Medipix":
            self.radioButton_Flatpanel.setChecked(False)
            self.radioButton_Medipix.setChecked(True)
            self.radioButton_Trial_Mode.setChecked(False)
        elif self.detector_type == "Trial":
            self.radioButton_Flatpanel.setChecked(False)
            self.radioButton_Medipix.setChecked(False)
            self.radioButton_Trial_Mode.setChecked(False)

        #  self.thread = None
        #  self.worker = None
        self.worker = None
        self.threadpool = QThreadPool()

    def update_linear_position(self):
        self.label_detector_position.setText(str(self.linear.linear_position["X"]))
        self.label_sample_position.setText(str(self.linear.linear_position["Y"]))
        self.label_vertical_position.setText(str(self.linear.linear_position["Z"]))

    def check_even(self):  # Check the number of steps for each rotation, if not even increase it by one
        self.n_steps = int(self.lineEdit_steps.text())
        if self.n_steps % 2 != 0:
            self.n_steps += 1
            self.lineEdit_steps.setText(str(self.n_steps))

    def read_linedit(self):  # Read each QLineEdit field which and call the appropriate G0 command for the initial
        #  position parameters
        self.n_steps = int(self.lineEdit_steps.text())
        Grbl.write_config("ct_config", "Angles per rotation", new_value=str(self.n_steps))
        self.detector = float(self.lineEdit_detector.text())
        Grbl.write_config("ct_config", "Distance source detector", new_value=str(self.detector))
        if float(self.detector):
            self.linear.linear_position["X"] = self.detector
        self.sample = float(self.lineEdit_sample.text())
        Grbl.write_config("ct_config", "Distance Source object", new_value=str(self.sample))
        if float(self.sample):
            self.linear.linear_position["Y"] = self.sample
        """self.vertical = float(self.lineEdit_vertical.text())
        
        Grbl.write_config("ct_config", "Object vertical position", new_value=str(self.vertical))
        if float(self.vertical):
            self.linear.linear_position["Z"] = self.vertical"""
        self.linear_motion_worker()
        self.update_linear_position()

    def get_path(self):  # Choose the path from the dropdown menu
        self.dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", self.dir_path)
        self.file_path_label.setText("File path: " + str(self.dir_path))
        Grbl.write_config("file_path", "route", new_value=str(self.dir_path))
        Grbl.files_count = Grbl.check_new_file(self.dir_path)
        print(self.dir_path)

    def linear_motion_worker(self):
        self.pushButton_set.setEnabled(False)
        self.pushButton_next.setEnabled(False)
        #  self.worker = Worker(self.linear.command_sender, "G0 " + "X" + str(self.linear.linear_position["X"])
        #                       + "Y" + str(self.linear.linear_position["Y"]) + "Z" +
        #                       str(self.linear.linear_position["Z"]))
        self.worker = Worker(self.linear_motion)
        self.worker.signals.finished.connect(self.reactivate_linear_buttons)
        self.threadpool.start(self.worker)

    def linear_motion(self):
        self.linear.command_sender("G0 " + "X" + str(self.linear.linear_position["X"])
                                   + "Y" + str(self.linear.linear_position["Y"]))
        #  + "Z" + str(self.linear.linear_position["Z"])) No vertical movement
        self.linear.command_sender("G4 P0", "ok")
        if self.linear.linear_position == self.linear.check_position:
            return True
        else:
            return False

    def reactivate_linear_buttons(self):
        self.pushButton_set.setEnabled(True)
        self.pushButton_next.setEnabled(True)

    def vert_axis_worker(self, sense, advance):
        self.vert_down_pushButton.setEnabled(False)
        self.vert_up_pushButton.setEnabled(False)
        self.lineEdit_vert_disp.setEnabled(False)
        self.worker = Worker(self.vert_axis_motion, sense, advance)
        self.worker.signals.finished.connect(self.reactivate_vert_buttons)
        self.threadpool.start(self.worker)

    def vert_axis_motion(self, sense, advance):
        self.linear.command_sender("G91 " + "Z" + sense + str(advance))
        self.linear.command_sender("G4 P0", "ok")
        return True

    def reactivate_vert_buttons(self):
        self.vert_down_pushButton.setEnabled(True)
        self.vert_up_pushButton.setEnabled(True)
        self.lineEdit_vert_disp.setEnabled(True)

    def trial_rot_worker(self, sense, advance):
        self.up_pushButton.setEnabled(False)
        self.down_pushButton.setEnabled(False)
        self.lineEdit_angle_trial.setEnabled(False)
        #  self.thread = QThread()
        #  self.worker = Worker(self.servo.trial_angle_rotate, sense, advance, self.mm_per_rot, self.servo)
        self.worker = Worker(self.trial_rot_movement, sense, advance)
        #  No end signal
        self.worker.signals.finished.connect(self.reactivate_trial_buttons)
        self.threadpool.start(self.worker)
        #  self.label_current_angle.setText("Current angle: "+str(Grbl.position + advance))
        #  self.worker.moveToThread(self.thread)
        #  self.thread.started.connect(self.worker.run)
        #  self.thread.start()

    def trial_rot_movement(self, sense, advance):
        self.servo.trial_angle_rotate(sense, advance, self.mm_per_rot, self.servo)
        self.servo.command_sender("G4 P0", "ok")
        return True

    def reactivate_trial_buttons(self):
        self.lable_current_angle.setText("Current angle: "+str(self.servo.servo_position/self.mm_per_rot*360))
        self.up_pushButton.setEnabled(True)
        self.down_pushButton.setEnabled(True)
        self.lineEdit_angle_trial.setEnabled(True)
        #  print(self.servo.check_position())

    def switch_window(self):  # Switch to next window
        controller = Controller(ProgressWindow(self.n_steps, self.dir_path, self.detector, self.sample, self.vertical,
                                               self.detector_type, self.servo, self.mm_per_rot))
        controller.show_window()

    def detector_choice(self, state):  # Radio button for detector choice
        self.detector_type = state
        if state == "Flatpanel":
            self.label_Flatpanel.setText("")
            Grbl.write_config("ct_config", "Detector type", new_value=str(self.detector_type))
        elif state == "Medipix":
            self.label_Flatpanel.setText("")
            Grbl.write_config("ct_config", "Detector type", new_value=str(self.detector_type))
        elif state == "Trial":
            self.label_Flatpanel.setText("")
            Grbl.write_config("ct_config", "Detector type", new_value=str(self.detector_type))


class ProgressWindow(Ui_Progress_window, QMainWindow):
    def __init__(self, n_steps, dir_path, detector, sample, vertical, detector_type, servo, mm_per_rot):
        super().__init__()
        #  QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.clicks_counter = 0
        self.click_position = []
        self.trigger_delay = 1
        self.prefix_name = "scan"
        self.n_steps, self.dir_path, self.detector, self.sample, self.vertical, self.detector_type, self.servo, \
            self.mm_per_rot = n_steps, dir_path, detector, sample, vertical, detector_type, servo, mm_per_rot
        self.pushButton_start_scan.clicked.connect(self.rotation_control_worker)
        self.pushButton_cancel.clicked.connect(lambda: (self.stop_reading()))  # Linear also!!
        #  self.pushButton_cancel.pressed.connect(lambda: (self.servo.command_sender("!")))  # Linear also!!
        #  self.pushButton_cancel.released.connect(self.close)
        self.label_file_path.setText("File path: " + str(self.dir_path))
        self.label_angles_rotation.setText("Angles per rotation: " + str(self.n_steps))
        self.label_detector_position.setText("Detector position: " + str(self.detector))
        self.label_object_position.setText("Object position: " + str(self.sample))
        self.label_vertical_position.setText("Vertical position: " + str(self.vertical))
        self.label_magnification_ratio.setText("Magnification ratio: " + str(self.detector / self.sample))
        self.threadpool = QThreadPool()
        #  self.thread = None
        self.worker = None

    def rotation_control_worker(self):
        self.pushButton_start_scan.setEnabled(False)
        #  self.thread = QThread()
        #  self.worker = Worker(self.rotation_control, self.n_steps, self.dir_path, self.detector_type)
        self.worker = Worker(self.rotation_control, self.n_steps, self.servo)
        # progress_callback=self.worker.signals.progress)

        #  self.worker.moveToThread(self.thread)
        self.worker.signals.progress.connect(self.progress_update_bar)
        self.worker.signals.finished.connect(self.switch_window)
        self.worker.signals.error.connect(self.stop)
        #  self.worker.signals.error.connect(self.switch_window)
        self.threadpool.start(self.worker)
        #  self.thread.started.connect(self.worker.run)
        #  self.thread.start()
        #  self.pushButton_start_scan.setEnabled(True)

    def rotation_control(self, num, servo, progress_callback):
        if self.lineEdit_prefix.text():
            self.prefix_name = str(self.lineEdit_prefix.text())
        if self.lineEdit_delay.text():
            self.trigger_delay = float(self.lineEdit_delay.text())
        n_zeros = len(str(num))
        for step in range(1, num + 1):
            angle = round(360/num*self.mm_per_rot, 3)
            servo.servo_position += angle/360
            #  self.servo.command_sender("G0 Z"+str(servo.servo_position), "end") No end signal now
            self.servo.command_sender("G0 Z" + str(servo.servo_position))  # , "ok")
            self.servo.command_sender("G4 P0", "ok")
            if self.detector_type != "Trial":
                self.trigger_sender(step, n_zeros)
                while True:
                    print(self.dir_path)
                    if Grbl.check_new_file(self.dir_path) >= Grbl.files_count + 1:
                        Grbl.files_count = Grbl.check_new_file(self.dir_path)
                        break
                    time.sleep(0.5)
            else:
                time.sleep(2)
            progress = int(round(step/num*100))
            # self.progressBar.setValue(progress)
            progress_callback.emit(progress)
        time.sleep(2)
        return True

    def progress_update_bar(self, n):
        self.progressBar.setValue(n)

    def switch_window(self):
        self.close()

    @staticmethod
    def stop_reading():
        Grbl.stop_reading = True

    @staticmethod
    def stop():
        sys.exit()

    def trigger_sender(self, step, n_zeros):

        file_name = str(step).zfill(n_zeros)+"_"+self.prefix_name+".tif"
        print("Start scan")
        if self.detector_type == "Flatpanel":
            if self.clicks_counter < 2:
                def on_click(x, y, button, pressed):
                    if str(button) == "Button.left" and not pressed:
                        print("Click")
                        if self.clicks_counter == 1:
                            ProgressWindow.click_position = [x, y]
                            listener.stop()
                        self.clicks_counter += 1
                with Listener(on_click=on_click) as listener:
                    listener.join()
                print(self.click_position)
            else:
                time.sleep(2)  # delay after the end of rotation is received (was 2)
                mouse = Mouse_controller()
                mouse.position = tuple(self.click_position)
                mouse.press(Button.left)
                mouse.release(Button.left)
            time.sleep(self.trigger_delay)  # wait for the image measuring time
            time.sleep(5)  # wait for safety time (was at 5)
            keyboard = Keyboard_controller()
            with keyboard.pressed(Key.ctrl):
                keyboard.press("s")
                keyboard.release("s")
            keyboard.release(Key.ctrl)
            time.sleep(0.5)  # Wait time for the saving window to appear and then submit the name
            keyboard.type(file_name)  # "Scan"+str(step))
            time.sleep(0.5)  # Delay before pressing start to save the file
            keyboard.press(Key.enter)
            time.sleep(0.1)  # Duration of the ke press (probably not needed)
            keyboard.release(Key.enter)
        elif self.detector_type == "Medipix":
            self.servo.command_sender("M08")
            time.sleep(0.5)
            self.servo.command_sender("M09")


class UnlockWindow(QMainWindow, Ui_Unlocksystem):

    def __init__(self, servo, linear):
        super().__init__()
        #  QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.servo = servo
        self.linear = linear
        self.pushButton_homing.pressed.connect(lambda: (self.linear.command_sender("$H", "ok")))
        self.pushButton_homing.released.connect(self.switch_window)
        self.pushButton_override.pressed.connect(lambda: (self.linear.command_sender("$X")))
        self.pushButton_override.released.connect(self.switch_window)

    def switch_window(self):
        controller = Controller(MainWindow(self.servo, self.linear))
        controller.show_window()
        self.close()


class Controller:
    def __init__(self, window):
        self.showing_window = window

    def show_window(self):
        self.showing_window.show()

    def close_window(self):
        self.showing_window.close()


def main():
    # position = 0
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller(ConnectionWindow())
    if not (Grbl.read_config("linear_stage", "port")[0] and Grbl.read_config("servo_stage", "port")[0] and
            Grbl.read_config("ensemble", "IP")[0] and Grbl.read_config("ensemble", "port")[0]):
        controller.show_window()
    else:
        connection_trial = ConnectionWindow()
        if not connection_trial.connection():
            controller.show_window()
        else:
            connection_trial.switch_window(True)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
