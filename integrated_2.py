import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QFileDialog
from basic_3 import Ui_CT_controller
from locked import Ui_Unlocksystem
from progress_bar import Ui_Progress_window
import serial
import serial.tools.list_ports
import time
import sys
import glob
import pandas as pd
import os, os.path

position = 0 #Position of rotation
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
#Import the csv files with configuration, alarms and erros info.
settings = pd.read_csv("setting_codes_en_US.csv")
errors = pd.read_csv("error_codes_en_US.csv")
alarms = pd.read_csv("alarm_codes_en_US.csv")

print(serial_ports())

s = serial.Serial('COM19', 115200, timeout=2)
X = (s.read(100)).decode()
print(X)
if "Grbl 1.1" and "['$' for help]" not in X:
    print("Incorrect connection")
    #time.sleep(5)
    sys.exit()

lock_state = False

if "'$H'|'$X' to unlock" in X:
    lock_state = True

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
        #start_time = time.time()
        s.write(command.encode())

        grbl_out = s.read_until(b"ok").decode()  # Wait for grbl response with carriage return
        print(grbl_out)
        #end_time = time.time()
        #print("Elapsed time: ", end_time - start_time)
        if "ok" not in grbl_out:
            print(str(grbl_out)+"\n"+str(check_error(grbl_out)))

def check_new_file(file_path):
    return len([name for name in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, name))])

def mierda():
    return files_count

#Class with the main window used to control the CT scan
class MainWindow(QMainWindow, Ui_CT_controller):
    switch_window = QtCore.pyqtSignal(int, str)
    n_steps = 0
    trial_rot = 0
    def __init__(self):
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.pushButton_set.clicked.connect(self.read_linedit)
        self.lineEdit_steps.editingFinished.connect(self.check_even)
        self.up_pushButton.clicked.connect(lambda:(self.trial_angle_rotate("up")))
        self.down_pushButton.clicked.connect(lambda:(self.trial_angle_rotate("down")))
        self.actionReset_GRBL.triggered.connect(lambda:(command_sender(chr(24))))
        self.actionChoose_file_path.triggered.connect(self.get_path)
    def check_even(self): #Check the number of steps for each rotation is even, or increase it by one
        MainWindow.n_steps =  int(self.lineEdit_steps.text())
        if MainWindow.n_steps % 2 != 0:
            MainWindow.n_steps += 1
            self.lineEdit_steps.setText(str(MainWindow.n_steps))
    def read_linedit(self): #Read each QLineEdit field and call the appropiate G0 command
        detector = self.lineEdit_detector.text()
        if detector:
            command_sender("X", detector)
        sample = self.lineEdit_sample.text()
        if sample:
            command_sender("Y", sample)
        vertical = self.lineEdit_vertical.text()
        if vertical:
            command_sender("Z", vertical)

        self.switch()
    def trial_angle_rotate(self, sense):
        global position
        advance = float(self.lineEdit_angle_trial.text())
        print("advance: "+str(advance))
        if sense == "up":
            position += advance/360
            command_sender("Z", str(position), "end")

        else:
            position -= advance/360
            command_sender("Z", str(position), "end")
        print(position)
        self.lable_current_angle.setText("Current angle: "+str(position))
        #self.show()
    def get_path(self):
        global files_count
        MainWindow.dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", "C:\\")
        self.file_path_label.setText("File path: " + str(MainWindow.dir_path))
        files_count = check_new_file(MainWindow.dir_path)
        print(files_count)
        print(mierda())
        print(MainWindow.dir_path)

    def switch(self):
        self.switch_window.emit(MainWindow.n_steps, MainWindow.dir_path)


class Progress_window(QMainWindow, Ui_Progress_window):
    switch_window = QtCore.pyqtSignal()

    def __init__(self, num, dir_path):
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.pushButton_start_scan.clicked.connect(lambda:(self.rotation_control(num, dir_path)))
        self.pushButton_cancel.pressed.connect(lambda:(command_sender("!")))
        self.pushButton_cancel.released.connect(self.close)


    """def switch(self):
        self.switch_window.emit()"""

    def rotation_control(self, num, dir_path):
        global position
        global files_count
        for step in range(1,num + 1):
            angle = round(360/num, 3)
            position += angle/360
            command_sender("Z", position, "end")
            command_sender("M08")
            time.sleep(1)
            command_sender("M09")
            while (True):
                print(dir_path)
                if check_new_file(dir_path) >= files_count + 1:
                    files_count = check_new_file(dir_path)
                    break
                time.sleep(0.5)
            progress = round((step)/num*100)
            self.progressBar.setValue(progress)
            print(progress, "%")
        time.sleep(2)
        self.close()


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

    def show_progress_window(self, num, dir_path):
        #self.window.close()
        self.progress_window = Progress_window(num, dir_path)
        #self.unlock.switch_window.connect(self.progress_window.close())
        self.progress_window.show()



def main():
    position = 0
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    if lock_state:
        controller.show_unlock()
    else:
        controller.show_main()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()