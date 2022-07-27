from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from basic_3 import Ui_CT_controller
from locked import Ui_Unlocksystem
from progress_bar import Ui_Progress_window
import serial
import serial.tools.list_ports
import time
import sys
import glob
import pandas as pd
import os
import os.path
import yaml

position = 0  # Position of rotation
files_count = 0


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
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
    return result
# Import the csv files with configuration, alarms and erros info.


settings = pd.read_csv("setting_codes_en_US.csv")
errors = pd.read_csv("error_codes_en_US.csv")
alarms = pd.read_csv("alarm_codes_en_US.csv")

print(serial_ports())
"""
s = serial.Serial('COM19', 115200, timeout=2)
X = (s.read(100)).decode()
print(X)
if "Grbl 1.1" and "['$' for help]" not in X:
    print("Incorrect connection")
    #time.sleep(5)
    sys.exit()
"""
lock_state = False
"""
if "'$H'|'$X' to unlock" in X:
    lock_state = True
"""


def check_error(error_message):
    if "ALARM" in error_message:
        alarm_code = error_message.split("ALARM:")[-1][0]
        alarm_description = alarms.loc[alarms['Alarm Code in v1.1+'] == int(alarm_code)][" Alarm Description"].values[0]
        return alarm_description
    if "error" in error_message:
        error_code = error_message.split(":")[-1]
        error_description = errors.loc[errors['Error Code in v1.1+ '] ==
                                       int(error_code)][" Error Description"].values[0]
        return error_description
    else:
        print("No response received from command")


def command_sender(*arg):
    if len(arg) == 2:
        command = "G0 " + str(arg[0]) + str(arg[1]) + "\n"
    elif len(arg) == 3:
        command = "G0 " + str(arg[0]) + str(arg[1]) + "\n"
        print(command)
        s.write(command.encode())
        if arg[2] == "end":
            end_counter = 0
            while True:
                grbl_out = s.read_until(b"end").decode()
                if "end" in grbl_out:
                    end_counter += 1
                if end_counter == 2:
                    break
                print("loop")
            time.sleep(1)
    else:
        command = str(arg[0]) + "\n"
    if len(arg) != 3:
        print(command)
        # start_time = time.time()
        s.write(command.encode())

        grbl_out = s.read_until(b"ok").decode()  # Wait for grbl response with carriage return
        print(grbl_out)
        # end_time = time.time()
        # print("Elapsed time: ", end_time - start_time)
        if "ok" not in grbl_out:
            print(str(grbl_out)+"\n"+str(check_error(grbl_out)))


def check_new_file(file_path):
    return len([name for name in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, name))])


with open('config.yml') as f_read:
    config = yaml.load(f_read, Loader=yaml.FullLoader)
f_read.close()


def read_config(*args):
    key = args[-1]
    args_tup = tuple(args)
    output = config[args_tup[0]][key]
    return output, config, args_tup, key

# print(read_config("file_path", "route")[0])


def write_config(*args, new_value=""):
    global config
    old_value, config, args_tup, key = read_config(*args)
    if old_value != new_value:
        config[args_tup[0]][key] = new_value
        with open("config.yml", 'w') as f_write:
            yaml.dump(config, f_write)
        f_write.close()

# write_config("file_path", "route")
# Class with the main window used to control the CT scan


class MainWindow(QMainWindow, Ui_CT_controller):
    switch_window = QtCore.pyqtSignal(int, str, float, float, float, str)
    n_steps = int(read_config("ct_config", "Angles per rotation")[0])
    trial_rot = float(read_config("ct_config", "Trials angle")[0])
    dir_path = str(read_config("file_path", "route")[0])
    detector = float(read_config("ct_config", "Distance source detector")[0])
    sample = float(read_config("ct_config", "Distance Source object")[0])
    vertical = float(read_config("ct_config", "Object vertical position")[0])
    detector_type = str(read_config("ct_config", "Detector type")[0])

    def __init__(self):
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.pushButton_set.clicked.connect(self.read_linedit)
        self.lineEdit_steps.editingFinished.connect(self.check_even)
        self.up_pushButton.clicked.connect(lambda: (self.trial_angle_rotate("up")))
        self.down_pushButton.clicked.connect(lambda: (self.trial_angle_rotate("down")))
        self.actionReset_GRBL.triggered.connect(lambda: (command_sender(chr(24))))
        self.actionChoose_file_path.triggered.connect(self.get_path)
        self.lineEdit_vertical.setText(str(MainWindow.vertical))
        self.lineEdit_sample.setText(str(MainWindow.sample))
        self.lineEdit_detector.setText(str(MainWindow.detector))
        self.lineEdit_steps.setText(str(MainWindow.n_steps))
        self.lineEdit_angle_trial.setText(str(MainWindow.trial_rot))
        self.file_path_label.setText("File path: " + str(MainWindow.dir_path))
        self.radioButton_Flatpanel.clicked.connect(lambda: (self.detector_choice("Flatpanel")))
        self.radioButton_Medipix.clicked.connect(lambda: (self.detector_choice("Medipix")))
        if MainWindow.detector_type == "Flatpanel":
            self.radioButton_Flatpanel.setChecked(True)
            self.radioButton_Medipix.setChecked(False)
        elif MainWindow.detector_type == "Medipix":
            self.radioButton_Flatpanel.setChecked(False)
            self.radioButton_Medipix.setChecked(True)

        # self.lineEdit_steps.setText(str(MainWindow.n_steps))
        # self.lineEdit_steps.setText(str(MainWindow.n_steps))
        # self.lineEdit_steps.setText(str(MainWindow.n_steps))
        # self.lineEdit_steps.setText(str(MainWindow.n_steps))

    def check_even(self):  # Check the number of steps for each rotation is even, or increase it by one
        MainWindow.n_steps = int(self.lineEdit_steps.text())
        if MainWindow.n_steps % 2 != 0:
            MainWindow.n_steps += 1
            self.lineEdit_steps.setText(str(MainWindow.n_steps))

    def read_linedit(self):  # Read each QLineEdit field and call the appropiate G0 command
        MainWindow.detector = float(self.lineEdit_detector.text())
        write_config("ct_config", "Distance source detector", new_value=MainWindow.detector)
        # if float(detector):
        # command_sender("X", detector)
        MainWindow.sample = float(self.lineEdit_sample.text())
        write_config("ct_config", "Distance source detector", new_value=float(MainWindow.sample))
        # if float(sample):
        # command_sender("Y", sample)
        MainWindow.vertical = float(self.lineEdit_vertical.text())
        write_config("ct_config", "Distance source detector", new_value=float(MainWindow.vertical))
        # if float(vertical):
        # command_sender("Z", vertical)
        MainWindow.n_steps = int(self.lineEdit_steps.text())
        write_config("ct_config", "Angles per rotation", new_value=int(MainWindow.n_steps))

        self.switch()

    def trial_angle_rotate(self, sense):
        global position
        MainWindow.trial_rot = float(self.lineEdit_angle_trial.text())
        advance = MainWindow.trial_rot
        write_config("ct_config", "Trials angle", new_value=MainWindow.trial_rot)
        print("advance: "+str(advance))
        if sense == "up":
            position += advance/360
            command_sender("Z", str(position), "end")

        else:
            position -= advance/360
            command_sender("Z", str(position), "end")
        print(position)
        self.lable_current_angle.setText("Current angle: "+str(position))
        # self.show()

    def get_path(self):
        global files_count
        MainWindow.dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", "C:\\")
        self.file_path_label.setText("File path: " + str(MainWindow.dir_path))
        files_count = check_new_file(MainWindow.dir_path)
        print(files_count)
        print(MainWindow.dir_path)

    def switch(self):
        self.switch_window.emit(MainWindow.n_steps, MainWindow.dir_path, MainWindow.detector, MainWindow.sample,
                                MainWindow.vertical, MainWindow.detector_type)

    def detector_choice(self, state):
        MainWindow.detector_type = state
        if state == "Flatpanel":
            self.label_Flatpanel.setText("Instructions")
            write_config("ct_config", "Detector type", new_value=str(MainWindow.detector_type))
        elif state == "Medipix":
            self.label_Flatpanel.setText("")
            write_config("ct_config", "Detector type", new_value=str(MainWindow.detector_type))

class Progress_window(QMainWindow, Ui_Progress_window):
    switch_window = QtCore.pyqtSignal()
    detector_type = ""
    def __init__(self, num, dir_path, detector, sample, vertical, detector_type):
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.pushButton_start_scan.clicked.connect(lambda: (self.rotation_control(num, dir_path)))
        self.pushButton_cancel.pressed.connect(lambda: (command_sender("!")))
        self.pushButton_cancel.released.connect(self.close)
        self.label_file_path.setText("File path: " + str(dir_path))
        self.label_angles_rotation.setText("Angles per rotation: " + str(num))
        self.label_detector_position.setText("Detector position: " + str(detector))
        self.label_object_position.setText("Object position: " + str(sample))
        self.label_vertical_position.setText("Vertical position: " + str(vertical))
        self.label_magnification_ratio.setText("Magnification ratio: " + str(detector/sample))
        Progress_window.detector_type = detector_type
    """def switch(self):
        self.switch_window.emit()"""

    def rotation_control(self, num, dir_path):
        global position
        global files_count
        for step in range(1, num + 1):
            angle = round(360/num, 3)
            position += angle/360
            command_sender("Z", position, "end")
            self.trigger_sender(Progress_window.detector_type)
            while True:
                print(dir_path)
                if check_new_file(dir_path) >= files_count + 1:
                    files_count = check_new_file(dir_path)
                    break
                time.sleep(0.5)
            progress = round(step/num*100)
            self.progressBar.setValue(progress)
            print(progress, "%")
        time.sleep(2)
        self.close()
    def trigger_sender(self, detector_type):
        if detector_type == "Flatpanel":
            print("ueeee")
        elif detector_type == "Medipix":
            command_sender("M08")
            time.sleep(1)
            command_sender("M09")

class Unlock_window(QMainWindow, Ui_Unlocksystem):

    switch_window = QtCore.pyqtSignal()

    def __init__(self):
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.pushButton_homing.pressed.connect(lambda: (command_sender("$H")))
        self.pushButton_homing.released.connect(self.switch)
        self.pushButton_override.pressed.connect(lambda: (command_sender("$X")))
        self.pushButton_override.released.connect(self.switch)

    def switch(self):
        self.switch_window.emit()


class Controller:

    def __init__(self):
        pass

    def show_unlock(self):
        self.unlock = Unlock_window()
        self.unlock.switch_window.connect(self.show_main)
        self.unlock.show()

    def show_main(self):
        self.window = MainWindow()
        self.window.switch_window.connect(self.show_progress_window)
        if lock_state:
            self.unlock.close()
        self.window.show()

    def show_progress_window(self, num, dir_path, detector, sample, vertical, detector_type):
        # self.window.close()
        self.progress_window = Progress_window(num, dir_path, detector, sample, vertical, detector_type)
        # self.unlock.switch_window.connect(self.progress_window.close())
        self.progress_window.show()


def main():
    # position = 0
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    if lock_state:
        controller.show_unlock()
    else:
        controller.show_main()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
