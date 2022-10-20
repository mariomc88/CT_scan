from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import pyqtSlot, QObject, QRunnable, QThreadPool
from MainWindow import Ui_CT_controller
from locked import Ui_Unlocksystem
from progress_bar import Ui_Progress_window
from connection_parameters import Ui_Connection_parameters
import sys
from GRBL_LIBRARY import Grbl

Grbl.serial_ports()
print(Grbl.list_ports)


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    """
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(object)
    progress = QtCore.pyqtSignal(int)


class Worker(QRunnable):
    """   Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    type callback: function.
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        #  self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them

        """
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
        """
        result = self.fn(*self.args, **self.kwargs)
        self.signals.result.emit(result)  # Return the result of the processing
        self.signals.finished.emit()  # Done


class ConnectionWindow(QMainWindow, Ui_Connection_parameters, Grbl):

    def __init__(self):
        super().__init__()
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.pushButton_check.clicked.connect(self.connection_worker)
        self.threadpool = QThreadPool()
        self.linear_port = Grbl.read_config("linear_stage", "port")[0]
        self.servo_port = Grbl.read_config("servo_stage", "port")[0]
        self.ensemble_IP = Grbl.read_config("ensemble", "IP")[0]
        self.ensemble_port = Grbl.read_config("ensemble", "port")[0]
        self.linear = None
        self.servo = None
        self.servo_connected = False
        self.linear_connected = False
        self.combobox()

        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

    def combobox(self):
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
            self.servo = Grbl((self.comboBox_servo.currentText()).replace('"Saved"', ""), 115200, 2, "servo")
            self.label_error_servo.clear()
            self.label_error_servo.setText("Correct servo connection")
            self.servo_connected = True
        except ValueError as e:
            self.label_error_servo.setText(str(e))
        try:
            self.linear = Grbl((self.comboBox_linear.currentText()).replace('"Saved"', ""), 115200, 2, "linear")
            self.label_error_linear.clear()
            self.label_error_linear.setText("Correct linear connection")
            self.linear_connected = True
        except ValueError as e:
            self.label_error_linear.setText(str(e))
        if self.linear_connected or self.servo_connected:
            print("Correct connection")
            print("servo is in:", self.servo.port)
            self.close()

            controller = Controller(MainWindow(self.servo, self.linear))
            """
            if self.linear.lock_state:
                controller.show_unlock()

            else:
                controller.show_main()
            """
            controller.show_window()
            return True
        else:
            print("Incorrect connection")
            Grbl.serial_ports()
            self.combobox()
            return False

    def connection_worker(self):
        self.pushButton_check.setEnabled(False)
        worker = Worker(self.connection)
        worker.run()
        self.pushButton_check.setEnabled(True)

        #  worker.signals.result.connect(self.print_output)
        #  worker.signals.finished.connect(self.thread_complete)
        #  worker.signals.progress.connect(self.progress_fn)


class MainWindow(QMainWindow, Ui_CT_controller):  # Class with the main window


    def __init__(self, servo, linear):
        super().__init__()
        QtWidgets.QApplication.__init__(self)
        # Set up window widgets
        #  definition of needed variables in the class
        self.n_steps = int(Grbl.read_config("ct_config", "Angles per rotation")[0])
        self.trial_rot = float(Grbl.read_config("ct_config", "Trials angle")[0])
        self.dir_path = str(Grbl.read_config("file_path", "route")[0])
        self.detector = float(Grbl.read_config("ct_config", "Distance source detector")[0])
        self.sample = float(Grbl.read_config("ct_config", "Distance Source object")[0])
        self.vertical = float(Grbl.read_config("ct_config", "Object vertical position")[0])
        self.detector_type = str(Grbl.read_config("ct_config", "Detector type")[0])
        self.position = 0
        self.files_count = 0
        self.setupUi(self)
        self.servo = servo
        self.linear = linear
        self.lineEdit_steps.editingFinished.connect(self.check_even)
        self.up_pushButton.clicked.connect(lambda: (self.trial_rot_worker("up", float(self.lineEdit_angle_trial.text()))))
        self.down_pushButton.clicked.connect(lambda: (self.trial_rot_worker("down", float(self.lineEdit_angle_trial.text()))))
        self.pushButton_set.clicked.connect(self.linear_motion)
        self.pushButton_next.clicked.connect(self.switch_window)
        self.actionReset_GRBL.triggered.connect(lambda: (self.servo.command_sender(chr(24))))
        self.actionChoose_file_path.triggered.connect(self.get_path)
        self.lineEdit_vertical.setText(str(self.vertical))
        self.lineEdit_sample.setText(str(self.sample))
        self.lineEdit_detector.setText(str(self.detector))
        self.lineEdit_steps.setText(str(self.n_steps))
        self.lineEdit_angle_trial.setText(str(self.trial_rot))
        self.file_path_label.setText("File path: " + str(self.dir_path))
        self.radioButton_Flatpanel.clicked.connect(lambda: (self.detector_choice("Flatpanel")))
        self.radioButton_Medipix.clicked.connect(lambda: (self.detector_choice("Medipix")))
        if self.detector_type == "Flatpanel":
            self.radioButton_Flatpanel.setChecked(True)
            self.radioButton_Medipix.setChecked(False)
        elif self.detector_type == "Medipix":
            self.radioButton_Flatpanel.setChecked(False)
            self.radioButton_Medipix.setChecked(True)

    def check_even(self):  # Check the number of steps for each rotation, if not even increase it by one
        self.n_steps = int(self.lineEdit_steps.text())
        if self.n_steps % 2 != 0:
            self.n_steps += 1
            self.lineEdit_steps.setText(str(self.n_steps))

    def read_linedit(self):  # Read each QLineEdit field which and call the appropriate G0 command for the initial
        #  position parameters
        self.detector = float(self.lineEdit_detector.text())
        Grbl.write_config("ct_config", "Distance source detector", new_value=self.detector)
        # if float(detector):
        # command_sender("X", detector)
        self.sample = float(self.lineEdit_sample.text())
        Grbl.write_config("ct_config", "Distance source detector", new_value=float(self.sample))
        # if float(sample):
        # command_sender("Y", sample)
        self.vertical = float(self.lineEdit_vertical.text())
        Grbl.write_config("ct_config", "Distance source detector", new_value=float(self.vertical))
        # if float(vertical):
        # command_sender("Z", vertical)
        self.n_steps = int(self.lineEdit_steps.text())
        Grbl.write_config("ct_config", "Angles per rotation", new_value=int(self.n_steps))

    def get_path(self):  # Choose the path from the dropdown menu
        self.dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", self.dir_path)
        self.file_path_label.setText("File path: " + str(self.dir_path))
        Grbl.write_config("file_path", "route", new_value=str(self.dir_path))
        Grbl.files_count = Grbl.check_new_file(self.dir_path)
        print(self.dir_path)

    def trial_rot_worker(self, sense, advance):
        self.up_pushButton.setEnabled(False)
        self.down_pushButton.setEnabled(False)
        self.lineEdit_angle_trial.setEnabled(False)
        worker = Worker(self.servo.trial_angle_rotate(sense, advance))
        worker.run()
        self.up_pushButton.setEnabled(True)
        self.down_pushButton.setEnabled(True)
        self.lineEdit_angle_trial.setEnabled(True)

    def linear_motion(self):
        pass

    def switch_window(self):  # Switch to next window
        controller = Controller(ProgressWindow(self.n_steps, self.dir_path, self.detector, self.sample, self.vertical,
                                               self.detector_type, self.servo))
        controller.show_window()

    def detector_choice(self, state):  # Radio button for detector choice
        self.detector_type = state
        if state == "Flatpanel":
            self.label_Flatpanel.setText("")
            Grbl.write_config("ct_config", "Detector type", new_value=str(self.detector_type))
        elif state == "Medipix":
            self.label_Flatpanel.setText("")
            Grbl.write_config("ct_config", "Detector type", new_value=str(self.detector_type))


class ProgressWindow(Ui_Progress_window, MainWindow):
    detector_type = ""

    def __init__(self, n_steps, dir_path, detector, sample, vertical, detector_type, servo):
        #  super().__init__()
        QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.n_steps, self.dir_path, self.detector, self.sample, self.vertical, self.detector_type, self.servo = \
            n_steps, dir_path, detector, sample, vertical, detector_type, servo
        self.pushButton_start_scan.clicked.connect(self.rotation_control_worker)
        self.pushButton_cancel.pressed.connect(lambda: (self.servo.command_sender("!")))  # Linear also!!
        self.pushButton_cancel.released.connect(self.close)
        self.label_file_path.setText("File path: " + str(self.dir_path))
        self.label_angles_rotation.setText("Angles per rotation: " + str(self.n_steps))
        self.label_detector_position.setText("Detector position: " + str(self.detector))
        self.label_object_position.setText("Object position: " + str(self.sample))
        self.label_vertical_position.setText("Vertical position: " + str(self.vertical))
        self.label_magnification_ratio.setText("Magnification ratio: " + str(self.detector / self.sample))

    def rotation_control_worker(self):
        self.pushButton_start_scan.setEnabled(False)
        worker = Worker(self.servo.rotation_control(self.n_steps, self.dir_path, self.detector_type))
        worker.run()
        self.pushButton_start_scan.setEnabled(True)


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


class Controller:
    def __init__(self, window):
        self.showing_window = window

    def show_window(self):
        self.showing_window.show()


"""
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
"""


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

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
