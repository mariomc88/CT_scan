from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import pyqtSlot, QObject, QRunnable, QThreadPool
from MainWindow_2 import Ui_CT_controller
from locked import Ui_Unlocksystem
from progress_bar import Ui_Progress_window
from connection_parameters import Ui_Connection_parameters
from Grbl import Grbl
import sys
import time
from pynput.mouse import Listener, Button
from pynput.mouse import Controller as Mouse_controller
from pynput.keyboard import Controller as Keyboard_controller
from pynput.keyboard import Key


class WorkerSignals(QObject):
    """
    Description: Class defining the pyqtsignals and it's type
    """

    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)
    result = QtCore.pyqtSignal(bool)
    progress = QtCore.pyqtSignal(int)


class Worker(QRunnable):
    """
    Description: Class which initializes the QThread worker
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        if "rotation_control" in str(self.fn):  # As the progress signal is only needed for this thread
            self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)  # Return the result of the processing
            self.signals.finished.emit()  # Done
        except NotImplementedError:  # Captures the termination process for the command_sender()
            self.signals.finished.emit()
            self.signals.error.emit("Close all")


class ConnectionWindow(QMainWindow, Ui_Connection_parameters, Grbl):
    """
    Definition: This class executes the GUI window that prompts the user to
    choose the connection details for the different stages, had the saved ones
    not worked
    """
    controller_MainWindow = None

    def __init__(self):
        super().__init__()
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
        self.worker = None
        self.threadpool = QThreadPool()

    def combobox(self):
        """
        Description: drop down menus for each stage connection parameters selection
        """
        print("Serial ports available:", len(Grbl.list_serial_ports))
        self.comboBox_linear.clear()
        self.comboBox_servo.clear()
        if self.linear_port:
            self.comboBox_linear.addItem('"Saved"' + self.linear_port)  # Add predetermined port
        if self.servo_port:
            self.comboBox_servo.addItem('"Saved"' + self.servo_port)  # Add predetermined port
        if Grbl.list_serial_ports:
            self.comboBox_linear.addItems(Grbl.list_serial_ports)
            self.comboBox_servo.addItems(Grbl.list_serial_ports)
        if self.ensemble_IP:  # Check_later, shouldn't this also include a predetermined IP?
            self.lineEdit_ens_IP.setText(self.ensemble_IP)
        if self.ensemble_port:
            self.lineEdit_ens_port.setText(self.ensemble_port)

    def connection(self):
        """
        Description: establish connection with the serial stages and capture and
        return the possible errors during the process.

            Returns True if both the connections were correct.
        """
        try:
            selected_servo_port = self.comboBox_servo.currentText().replace('"Saved"', "")
            self.servo = Grbl(selected_servo_port, 115200, 2, "servo")
            if self.servo_port != selected_servo_port:
                Grbl.write_config("servo_stage", "port", new_value=selected_servo_port)  # Save new successful port
            self.label_error_servo.clear()
            self.label_error_servo.setText("Correct servo connection")
            self.servo_connected = True
        except ValueError as e:
            self.label_error_servo.setText(str(e))
        try:
            selected_linear_port = self.comboBox_linear.currentText().replace('"Saved"', "")
            self.linear = Grbl(selected_linear_port, 115200, 2, "linear")
            if self.linear_port != selected_linear_port:
                Grbl.write_config("linear_stage", "port", new_value=selected_linear_port)  # Save new successful port
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
            Grbl.serial_ports()  # Refresh available ports
            self.combobox()
            return False

    def switch_window(self, connection):
        """
        Description: switches to next window, UnlockWindow if the Grbl board
        is in lock state or directly to the main window if not.
        """
        if connection:

            if self.linear.lock_state:
                controller = Controller(UnlockWindow(self.servo, self.linear))
                controller.show_window()
            else:
                ConnectionWindow.controller_MainWindow = Controller(MainWindow(self.servo, self.linear))
                ConnectionWindow.controller_MainWindow.show_window()
            self.close()

    def connection_worker(self):
        """
        Description: starts a thread to execute the connection() function
        """
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
    """
    Description: Includes the GUI and functions for the main GUI, which allows
    for setting the different parameters prior to the scan.

        Args:
            - servo(Grbl object): Grbl object with the connection parameters and
            methods of the servo motor
            - linear(Grbl object): Grbl object with the connection parameters and
            methods of the linear motor
    """
    def __init__(self, servo, linear):
        super().__init__()
        self.linear = linear
        self.linear.linear_position = dict(self.linear.check_position())
        # Read predefined parameters
        self.n_steps = int(Grbl.read_config("ct_config", "Angles per rotation")[0])
        self.trial_rot = float(Grbl.read_config("ct_config", "Trials angle")[0])
        self.dir_path = str(Grbl.read_config("file_path", "route")[0])
        self.detector = self.linear.linear_position["X"]
        self.sample = self.linear.linear_position["Y"]
        self.vertical = self.linear.linear_position["Z"]
        self.detector_type = str(Grbl.read_config("ct_config", "Detector type")[0])
        self.mm_per_rot = 360  # Conversion from degrees to mm
        self.files_count = 0
        self.setupUi(self)
        self.servo = servo
        self.update_linear_position()  # Check for linear stage working position and wco
        self.lineEdit_steps.editingFinished.connect(self.check_even)  # Once the value of steps is introduced, check if
        # it is an even number
        self.up_pushButton.clicked.connect(
            lambda: (self.trial_rot_worker(float("+"+self.lineEdit_angle_trial.text().replace("-", "")))))
        self.down_pushButton.clicked.connect(
            lambda: (self.trial_rot_worker(float("-"+self.lineEdit_angle_trial.text().replace("-", "")))))
        self.vert_up_pushButton.clicked.connect(
            lambda: (self.linear_motion(float("+"+self.lineEdit_vert_disp.text().replace("-", "")))))
        self.vert_down_pushButton.clicked.connect(
            lambda: (self.linear_motion(float("-"+self.lineEdit_vert_disp.text().replace("-", "")))))
        self.pushButton_set.clicked.connect(self.read_linedit)
        self.pushButton_next.clicked.connect(self.switch_window)
        self.pushButton_cancel.clicked.connect(self.stop_reading)
        self.actionReset_GRBL.triggered.connect(lambda: (self.linear.command_sender(chr(24))))
        self.actionChoose_file_path.triggered.connect(self.get_path)
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
        elif self.detector_type == "Trial":  # Do not assume trial mode will be preferred again
            self.radioButton_Flatpanel.setChecked(False)
            self.radioButton_Medipix.setChecked(False)
            self.radioButton_Trial_Mode.setChecked(False)
        if not linear.linear_homed:
            self.pushButton_set.setEnabled(False)
            self.pushButton_next.setEnabled(False)
            self.vert_down_pushButton.setEnabled(False)
            self.vert_up_pushButton.setEnabled(False)
            self.lineEdit_vert_disp.setEnabled(False)
        #  self.thread = None
        #  self.worker = None
        self.worker = None
        self.threadpool = QThreadPool()

    def update_linear_position(self):
        """

        Description: Fills the position label with the linear position from the "?" command

        """
        self.label_detector_position.setText(str(self.linear.linear_position["X"]))
        self.label_sample_position.setText(str(self.linear.linear_position["Y"]))
        self.label_vertical_position.setText(str(self.linear.linear_position["Z"]))

    def check_even(self):
        """

        Description: check the number of steps for each rotation, if not even increase it by one

        """
        self.n_steps = int(self.lineEdit_steps.text())
        if self.n_steps % 2 != 0:
            self.n_steps += 1
            self.lineEdit_steps.setText(str(self.n_steps))

    def read_linedit(self):
        """

        Description: Read each QLineEdit field which and call the appropriate G0 command for the initial, and saves the
        values for future predefined parameters

        """
        self.n_steps = int(self.lineEdit_steps.text())
        Grbl.write_config("ct_config", "Angles per rotation", new_value=str(self.n_steps))
        self.detector = float(self.lineEdit_detector.text())
        if float(self.detector):
            Grbl.write_config("ct_config", "Distance source detector", new_value=str(self.detector))
            self.linear.linear_position["X"] = self.detector
        self.sample = float(self.lineEdit_sample.text())
        if float(self.sample):
            Grbl.write_config("ct_config", "Distance Source object", new_value=str(self.sample))
            self.linear.linear_position["Y"] = self.sample
        self.linear_motion_worker()

    def get_path(self):  # Choose the path from the dropdown menu
        """
        Description: set the path for the recorded images to be saved
        """
        self.dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", self.dir_path)
        self.file_path_label.setText("File path: " + str(self.dir_path))
        Grbl.write_config("file_path", "route", new_value=str(self.dir_path))
        Grbl.files_count = Grbl.check_new_file(self.dir_path)
        print(self.dir_path)

    def linear_motion_worker(self):
        """

        Description: Start the thread for the linear movement and deactivate the related buttons meanwhile

        """
        self.pushButton_set.setEnabled(False)
        self.pushButton_next.setEnabled(False)
        self.vert_down_pushButton.setEnabled(False)
        self.vert_up_pushButton.setEnabled(False)
        self.lineEdit_vert_disp.setEnabled(False)
        self.worker = Worker(self.linear_motion)
        self.worker.signals.finished.connect(self.reactivate_linear_buttons)
        self.worker.signals.error.connect(self.stop)
        self.threadpool.start(self.worker)

    def linear_motion(self, advance=None):

        """
        Description: Commands the linear movements Gcode
        Returns:
            -True: if the reached position corresponds to the desired one
            -Advance: the increment to advance in the Z axis, need to recalculate Z position based on it
            -False: if not

        """
        if advance:
            self.linear.linear_position["Z"] += advance
        self.linear.command_sender("G0 " + "X" + str(self.linear.linear_position["X"])
                                   + "Y" + str(self.linear.linear_position["Y"])
                                   + "Z" + str(self.linear.linear_position["Z"]))
        self.linear.command_sender("G4 P0", "ok")
        self.update_linear_position()
        if self.linear.linear_position == self.linear.check_position:
            return True
        else:
            return False

    def reactivate_linear_buttons(self):
        self.pushButton_set.setEnabled(True)
        self.pushButton_next.setEnabled(True)
        self.vert_down_pushButton.setEnabled(True)
        self.vert_up_pushButton.setEnabled(True)
        self.lineEdit_vert_disp.setEnabled(True)

    def trial_rot_worker(self, advance):  # Analogue to linear movement worker
        self.up_pushButton.setEnabled(False)
        self.down_pushButton.setEnabled(False)
        self.lineEdit_angle_trial.setEnabled(False)
        self.worker = Worker(self.trial_angle_rotate, advance, self.mm_per_rot, self.servo)
        self.worker.signals.finished.connect(self.reactivate_trial_buttons)
        self.worker.signals.error.connect(self.stop)
        self.threadpool.start(self.worker)

    def trial_angle_rotate(self, advance, mm_per_rot, servo):
        # class
        """
        Description: send appropriate Gcode message to the grbl servo board

                    Args:
                        -advance (float): degrees to rotate
                        -mm_per_rot (float): conversion constant from degrees to mm
        """
        Grbl.write_config("ct_config", "Trials angle", new_value=advance)
        self.servo.servo_position += advance/360*mm_per_rot
        self.servo.command_sender(command="G0 Z" + str(servo.servo_position))
        self.servo.command_sender("G4 P0", "ok")
        return True

    def reactivate_trial_buttons(self):
        self.lable_current_angle.setText("Current angle: "+str(round(self.servo.servo_position/self.mm_per_rot*360, 3)))
        # Show the current position of the rotation axis
        self.up_pushButton.setEnabled(True)
        self.down_pushButton.setEnabled(True)
        self.lineEdit_angle_trial.setEnabled(True)

    def stop_reading(self):
        self.servo.stop_reading = True  # Grbl variable accessible during the command sending process
        self.linear.stop_reading = True  # Grbl variable accessible during the command sending process

    @staticmethod
    def stop():
        sys.exit()

    def switch_window(self):  # Switch to next window
        self.linear.linear_position = self.linear.check_position
        controller = Controller(ProgressWindow(self.n_steps, self.dir_path, self.detector, self.sample, self.vertical,
                                               self.detector_type, self.servo, self.mm_per_rot))
        controller.show_window()

    def detector_choice(self, state):
        """
        Description: Radio button for detector choice
        Args:
            state (string) detector choice

        Returns:

        """
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
    """
    Description: in charge of the progress window GUI and relative processes
    """
    def __init__(self, n_steps, dir_path, detector, sample, vertical, detector_type, servo, mm_per_rot):
        super().__init__()
        self.setupUi(self)
        self.clicks_counter = 0
        self.click_position = []
        self.trigger_delay = 1  # Delay after clicking the save button and then inputting the name
        self.prefix_name = "scan"
        self.n_steps, self.dir_path, self.detector, self.sample, self.vertical, self.detector_type, self.servo, \
            self.mm_per_rot = n_steps, dir_path, detector, sample, vertical, detector_type, servo, mm_per_rot
        self.pushButton_start_scan.clicked.connect(self.rotation_control_worker)
        self.pushButton_cancel.clicked.connect(lambda: (self.stop_reading()))
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
        self.worker = Worker(self.rotation_control, self.n_steps, self.servo)
        self.worker.signals.progress.connect(self.progress_update_bar)
        self.worker.signals.finished.connect(self.switch_window)
        self.worker.signals.error.connect(self.stop)
        self.threadpool.start(self.worker)

    def rotation_control(self, num, servo, progress_callback):
        """
        Description: Controls the process during the rotation, commanding the movements and the X-Ray scanning
        Args:
            num: (int) number of steps per rotation
            servo: (Grbl object)
            progress_callback: (pyqt.signal) it embeds the progress to update the progress bar

        Returns:
            True: once the process is completed

        """
        if self.lineEdit_prefix.text():  # Change the default prefix_name
            self.prefix_name = str(self.lineEdit_prefix.text())
        if self.lineEdit_delay.text():  # Change the default delay time
            self.trigger_delay = float(self.lineEdit_delay.text())
        n_zeros = len(str(num))  # Ensures the scan number has the same length, ex: 0001, 5165, 0100
        for step in range(1, num + 1):
            print('num = ', num)
            angle = round(1/num*self.mm_per_rot, 3)  # Check_urgent, why multiply by 360 to later divide by 360
            servo.servo_position += angle
            print('servo.servo_position ', servo.servo_position)
            self.servo.command_sender("G0 Z" + str(servo.servo_position))
            self.servo.command_sender("G4 P0", "ok")
            if self.detector_type != "Trial":  # Skip trigger sender and new file check for trial mode
                self.trigger_sender(step, n_zeros)
                while True:
                    print(self.dir_path)
                    if Grbl.check_new_file(self.dir_path) >= Grbl.files_count + 1:
                        Grbl.files_count = Grbl.check_new_file(self.dir_path)
                        break
                    time.sleep(0.1)  # Check for a new file every 0.1 seconds
            else:
                time.sleep(2)  # Time to wait for trial mode in between steps
            progress = int(round(step/num*100))
            # self.progressBar.setValue(progress)
            progress_callback.emit(progress)
        time.sleep(2)  # 2 seconds wait time at the end of the process
        return True

    def progress_update_bar(self, n):
        self.progressBar.setValue(n)

    def switch_window(self):
        self.close()

    def stop_reading(self):
        self.servo.stop_reading = True  # Grbl class variable accessible during the command sending process

    @staticmethod
    def stop():
        sys.exit()

    def trigger_sender(self, step, n_zeros):
        """
        Description: commands the X-ray scan for a given type of detector
        Args:
            step:
            n_zeros:
        """

        print("Start scan")
        if self.detector_type == "Flatpanel":
            file_name = str(step).zfill(
                n_zeros) + "_" + self.prefix_name + ".tif"
            if self.clicks_counter < 2:
                def on_click(x, y, button, pressed):
                    if str(button) == "Button.left" and not pressed:  # The click is already ended
                        print("Click")
                        if self.clicks_counter == 1:  # The second click saves location
                            self.click_position = [x, y]
                            listener.stop()
                        self.clicks_counter += 1
                with Listener(on_click=on_click) as listener:  # Wait for clicks
                    listener.join()
                print(self.click_position)
            else:
                time.sleep(self.trigger_delay)  # delay until next scan start, click on to scan button
                mouse = Mouse_controller()
                mouse.position = tuple(self.click_position)
                mouse.press(Button.left)
                mouse.release(Button.left)
            time.sleep(self.trigger_delay)  # Delay after the image capture is clicked, to let the scan time to process
            keyboard = Keyboard_controller()
            with keyboard.pressed(Key.ctrl):
                keyboard.press("s")
                keyboard.release("s")
            keyboard.release(Key.ctrl)  # Ctrl + s
            time.sleep(1.5)  # Wait time for the saving window to appear and then submit the name
            keyboard.type(file_name)  # "Scan"+str(step))
            time.sleep(1)  # Delay before pressing start to save the file
            keyboard.press(Key.enter)
            time.sleep(0.1)  # Duration of the ke press (probably not needed)
            keyboard.release(Key.enter)
        elif self.detector_type == "Medipix":  # Just send a high pulse
            self.servo.command_sender("M08")
            time.sleep(0.5)
            self.servo.command_sender("M09")


class UnlockWindow(QMainWindow, Ui_Unlocksystem):
    """
    Description: prompts user to either home or override the grbl board if it's in lock state
    """

    def __init__(self, servo, linear):
        super().__init__()
        #  QtWidgets.QApplication.__init__(self)
        self.setupUi(self)
        self.servo = servo
        self.linear = linear
        self.pushButton_homing.pressed.connect(self.homing)
        self.pushButton_homing.released.connect(self.switch_window)
        self.pushButton_override.pressed.connect(lambda: (self.linear.command_sender("$X")))
        self.pushButton_override.released.connect(self.switch_window)

    def homing(self):
        self.linear.command_sender("$H", "ok")
        self.linear.linear_homed = True

    def switch_window(self):
        controller = Controller(MainWindow(self.servo, self.linear))
        controller.show_window()
        self.close()


class Controller:
    """
    Description: class in charge of launching the next window inputted as window.
    """
    def __init__(self, window):
        self.showing_window = window

    def show_window(self):
        self.showing_window.show()

    def close_window(self):
        self.showing_window.close()


def main():
    Grbl.serial_ports()
    print(Grbl.list_serial_ports)
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller(ConnectionWindow())  # Start Connection window class
    if not (Grbl.read_config("linear_stage", "port")[0] and Grbl.read_config("servo_stage", "port")[0] and
            Grbl.read_config("ensemble", "IP")[0] and Grbl.read_config("ensemble", "port")[0]):  # If there is not saved
        # config for the different stages connections show the connection window
        controller.show_window()
    else:
        connection_trial = ConnectionWindow()
        if not connection_trial.connection():  # If the connection was unsuccessful show the connection window
            controller.show_window()
        else:  # If the connection was successful show the main window
            connection_trial.switch_window(True)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
