from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from basic_3 import Ui_CT_controller
from locked import Ui_Unlocksystem
from progress_bar import Ui_Progress_window
from connection_parameters import Ui_Connection_parameters
import sys
from GRBL_LIBRARY import Grbl

Grbl.serial_ports()
print(Grbl.list_ports)


class MainWindow(QMainWindow, Ui_CT_controller):  # Class with the main window
    #  definition of needed variables in the class
    n_steps = int(Grbl.read_config("ct_config", "Angles per rotation")[0])
    trial_rot = float(Grbl.read_config("ct_config", "Trials angle")[0])
    dir_path = str(Grbl.read_config("file_path", "route")[0])
    detector = float(Grbl.read_config("ct_config", "Distance source detector")[0])
    sample = float(Grbl.read_config("ct_config", "Distance Source object")[0])
    vertical = float(Grbl.read_config("ct_config", "Object vertical position")[0])
    detector_type = str(Grbl.read_config("ct_config", "Detector type")[0])
    position = 0
    files_count = 0

    def __init__(self):
        super().__init__()
        QtWidgets.QApplication.__init__(self)
        # Set up window widgets

        self.setupUi(self)
        self.pushButton_set.released.connect(MainWindow.switch_window)
        self.lineEdit_steps.editingFinished.connect(self.check_even)
        self.up_pushButton.clicked.connect(lambda: (ConnectionWindow.servo.trial_angle_rotate("up",
                                                                                              float(
                                                                                                  self.lineEdit_angle_trial.text()))))
        self.down_pushButton.clicked.connect(lambda: (ConnectionWindow.servo.trial_angle_rotate("down",
                                                                                                float(
                                                                                                    self.lineEdit_angle_trial.text()))))
        self.actionReset_GRBL.triggered.connect(lambda: (ConnectionWindow.servo.command_sender(chr(24))))
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

    def check_even(self):  # Check the number of steps for each rotation, if not even increase it by one
        MainWindow.n_steps = int(self.lineEdit_steps.text())
        if MainWindow.n_steps % 2 != 0:
            MainWindow.n_steps += 1
            self.lineEdit_steps.setText(str(MainWindow.n_steps))

    def read_linedit(self):  # Read each QLineEdit field which and call the appropriate G0 command for the initial
        #  position parameters
        MainWindow.detector = float(self.lineEdit_detector.text())
        Grbl.write_config("ct_config", "Distance source detector", new_value=MainWindow.detector)
        # if float(detector):
        # command_sender("X", detector)
        MainWindow.sample = float(self.lineEdit_sample.text())
        Grbl.write_config("ct_config", "Distance source detector", new_value=float(MainWindow.sample))
        # if float(sample):
        # command_sender("Y", sample)
        MainWindow.vertical = float(self.lineEdit_vertical.text())
        Grbl.write_config("ct_config", "Distance source detector", new_value=float(MainWindow.vertical))
        # if float(vertical):
        # command_sender("Z", vertical)
        MainWindow.n_steps = int(self.lineEdit_steps.text())
        Grbl.write_config("ct_config", "Angles per rotation", new_value=int(MainWindow.n_steps))

    def get_path(self):  # Choose the path from the dropdown menu
        MainWindow.dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", MainWindow.dir_path)
        self.file_path_label.setText("File path: " + str(MainWindow.dir_path))
        Grbl.write_config("file_path", "route", new_value=str(MainWindow.dir_path))
        Grbl.files_count = Grbl.check_new_file(MainWindow.dir_path)
        print(MainWindow.dir_path)

    @staticmethod
    def switch_window():  # Switch to next window
        controller = Controller()
        controller.show_progress_window()

    def detector_choice(self, state):  # Radio button for detector choice
        MainWindow.detector_type = state
        if state == "Flatpanel":
            self.label_Flatpanel.setText("")
            Grbl.write_config("ct_config", "Detector type", new_value=str(MainWindow.detector_type))
        elif state == "Medipix":
            self.label_Flatpanel.setText("")
            Grbl.write_config("ct_config", "Detector type", new_value=str(MainWindow.detector_type))


class ProgressWindow(QMainWindow, Ui_Progress_window):
    detector_type = ""

    def __init__(self):
        super().__init__()
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.num, self.dir_path, self.detector, self.sample, self.vertical, self.detector_type = \
            MainWindow.n_steps, MainWindow.dir_path, MainWindow.detector, MainWindow.sample, MainWindow.vertical, \
            MainWindow.detector_type
        self.pushButton_start_scan.clicked.connect(lambda: (ConnectionWindow.servo.rotation_control(
            self.num, self.dir_path, self.detector_type)))
        self.pushButton_cancel.pressed.connect(lambda: (ConnectionWindow.servo.command_sender("!")))  # Linear also!!
        self.pushButton_cancel.released.connect(self.close)
        self.label_file_path.setText("File path: " + str(self.dir_path))
        self.label_angles_rotation.setText("Angles per rotation: " + str(self.num))
        self.label_detector_position.setText("Detector position: " + str(self.detector))
        self.label_object_position.setText("Object position: " + str(self.sample))
        self.label_vertical_position.setText("Vertical position: " + str(self.vertical))
        self.label_magnification_ratio.setText("Magnification ratio: " + str(self.detector / self.sample))

        #  ProgressWindow.detector_type = detector_type


class UnlockWindow(QMainWindow, Ui_Unlocksystem):

    def __init__(self):
        super().__init__()
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.pushButton_homing.pressed.connect(lambda: (ConnectionWindow.linear.command_sender("$H")))
        self.pushButton_homing.released.connect(self.switch)
        self.pushButton_override.pressed.connect(lambda: (ConnectionWindow.linear.command_sender("$X")))
        self.pushButton_override.released.connect(self.switch)

    def switch(self):
        self.switch_window.emit()


class ConnectionWindow(QMainWindow, Ui_Connection_parameters, Grbl):
    linear_port = Grbl.read_config("linear_stage", "port")[0]
    servo_port = Grbl.read_config("servo_stage", "port")[0]
    ensemble_IP = Grbl.read_config("ensemble", "IP")[0]
    ensemble_port = Grbl.read_config("ensemble", "port")[0]
    servo = None
    linear = None
    servo_connected = False
    linear_connected = False

    def __init__(self):
        super().__init__()
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.combobox()

    def combobox(self):
        self.comboBox_linear.clear()
        self.comboBox_servo.clear()
        if ConnectionWindow.linear_port:
            self.comboBox_linear.addItem('"Saved"' + ConnectionWindow.linear_port)
        if ConnectionWindow.servo_port:
            self.comboBox_servo.addItem('"Saved"' + ConnectionWindow.servo_port)
        if Grbl.list_ports:
            self.comboBox_linear.addItems(Grbl.list_ports)
            self.comboBox_servo.addItems(Grbl.list_ports)
        if ConnectionWindow.ensemble_IP:
            self.lineEdit_ens_IP.setText(ConnectionWindow.ensemble_IP)
        if ConnectionWindow.ensemble_port:
            self.lineEdit_ens_port.setText(ConnectionWindow.ensemble_port)
        self.pushButton_check.clicked.connect(self.connection)

    def connection(self):
        try:
            ConnectionWindow.servo = Grbl((self.comboBox_servo.currentText()).
                                          replace('"Saved"', ""), 115200, 2, "servo")
            self.label_error_servo.clear()
            self.label_error_servo.setText("Correct servo connection")
            ConnectionWindow.servo_connected = True
        except ValueError as e:
            self.label_error_servo.setText(str(e))
        try:
            ConnectionWindow.linear = Grbl((self.comboBox_linear.currentText()).
                                           replace('"Saved"', ""), 115200, 2, "linear")
            self.label_error_linear.clear()
            self.label_error_linear.setText("Correct linear connection")
            ConnectionWindow.linear_connected = True
        except ValueError as e:
            self.label_error_linear.setText(str(e))
        if ConnectionWindow.linear_connected or ConnectionWindow.servo_connected:
            controller = Controller()
            """
            if ConnectionWindow.linear.lock_state:
                controller.show_unlock()

            else:
                controller.show_main()
            """
            controller.show_main()
            self.close()
            return True
        else:
            print("Incorrect connection")
            Grbl.serial_ports()
            self.combobox()
            return False


class Controller:

    def __init__(self):
        self.connection = ConnectionWindow()
        self.unlock = UnlockWindow()
        self.window = MainWindow()
        self.progress_window = ProgressWindow()

    def show_connection(self):
        self.connection.show()

    def show_unlock(self):
        self.unlock.show()

    def show_main(self):
        self.window.show()

    def show_progress_window(self):
        self.progress_window.show()


def main():
    # position = 0
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    if not (Grbl.read_config("linear_stage", "port")[0] and Grbl.read_config("servo_stage", "port")[0] and
            Grbl.read_config("ensemble", "IP")[0] and Grbl.read_config("ensemble", "port")[0]):
        controller.show_connection()
    else:
        connection_trial = ConnectionWindow()
        if not connection_trial.connection():
            controller.show_connection()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
