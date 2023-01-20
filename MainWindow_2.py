# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\MainWindow_2.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CT_controller(object):
    def setupUi(self, CT_controller):
        CT_controller.setObjectName("CT_controller")
        CT_controller.resize(891, 635)
        self.centralwidget = QtWidgets.QWidget(CT_controller)
        self.centralwidget.setObjectName("centralwidget")
        self.layoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.layoutWidget.setGeometry(QtCore.QRect(31, 41, 821, 521))
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.curr_pos_label = QtWidgets.QLabel(self.layoutWidget)
        self.curr_pos_label.setObjectName("curr_pos_label")
        self.gridLayout.addWidget(self.curr_pos_label, 0, 4, 1, 1)
        self.label_detector = QtWidgets.QLabel(self.layoutWidget)
        self.label_detector.setEnabled(True)
        self.label_detector.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_detector.setObjectName("label_detector")
        self.gridLayout.addWidget(self.label_detector, 1, 0, 1, 1)
        self.lineEdit_detector = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit_detector.setObjectName("lineEdit_detector")
        self.gridLayout.addWidget(self.lineEdit_detector, 1, 3, 1, 1)
        self.label_detector_position = QtWidgets.QLabel(self.layoutWidget)
        self.label_detector_position.setEnabled(True)
        self.label_detector_position.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_detector_position.setObjectName("label_detector_position")
        self.gridLayout.addWidget(self.label_detector_position, 1, 4, 1, 1)
        self.label_sample = QtWidgets.QLabel(self.layoutWidget)
        self.label_sample.setObjectName("label_sample")
        self.gridLayout.addWidget(self.label_sample, 2, 0, 1, 1)
        self.lineEdit_sample = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit_sample.setObjectName("lineEdit_sample")
        self.gridLayout.addWidget(self.lineEdit_sample, 2, 3, 1, 1)
        self.label_sample_position = QtWidgets.QLabel(self.layoutWidget)
        self.label_sample_position.setEnabled(True)
        self.label_sample_position.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_sample_position.setObjectName("label_sample_position")
        self.gridLayout.addWidget(self.label_sample_position, 2, 4, 1, 1)
        self.label_vertical = QtWidgets.QLabel(self.layoutWidget)
        self.label_vertical.setObjectName("label_vertical")
        self.gridLayout.addWidget(self.label_vertical, 3, 0, 1, 1)
        self.vert_up_pushButton = QtWidgets.QPushButton(self.layoutWidget)
        self.vert_up_pushButton.setObjectName("vert_up_pushButton")
        self.gridLayout.addWidget(self.vert_up_pushButton, 3, 1, 1, 1)
        self.vert_down_pushButton = QtWidgets.QPushButton(self.layoutWidget)
        self.vert_down_pushButton.setObjectName("vert_down_pushButton")
        self.gridLayout.addWidget(self.vert_down_pushButton, 3, 2, 1, 1)
        self.lineEdit_vert_disp = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit_vert_disp.setWhatsThis("")
        self.lineEdit_vert_disp.setText("")
        self.lineEdit_vert_disp.setObjectName("lineEdit_vert_disp")
        self.gridLayout.addWidget(self.lineEdit_vert_disp, 3, 3, 1, 1)
        self.label_vertical_position = QtWidgets.QLabel(self.layoutWidget)
        self.label_vertical_position.setEnabled(True)
        self.label_vertical_position.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_vertical_position.setObjectName("label_vertical_position")
        self.gridLayout.addWidget(self.label_vertical_position, 3, 4, 1, 1)
        self.label_steps_rotation = QtWidgets.QLabel(self.layoutWidget)
        self.label_steps_rotation.setObjectName("label_steps_rotation")
        self.gridLayout.addWidget(self.label_steps_rotation, 4, 0, 1, 1)
        self.lineEdit_steps = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit_steps.setObjectName("lineEdit_steps")
        self.gridLayout.addWidget(self.lineEdit_steps, 4, 3, 1, 1)
        self.label_rotation_position = QtWidgets.QLabel(self.layoutWidget)
        self.label_rotation_position.setEnabled(True)
        self.label_rotation_position.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_rotation_position.setObjectName("label_rotation_position")
        self.gridLayout.addWidget(self.label_rotation_position, 4, 4, 1, 1)
        self.label_X_detector = QtWidgets.QLabel(self.layoutWidget)
        self.label_X_detector.setObjectName("label_X_detector")
        self.gridLayout.addWidget(self.label_X_detector, 5, 0, 1, 1)
        self.Enable_X_pushButton = QtWidgets.QPushButton(self.layoutWidget)
        self.Enable_X_pushButton.setObjectName("Enable_X_pushButton")
        self.gridLayout.addWidget(self.Enable_X_pushButton, 5, 1, 1, 1)
        self.pushButton_Home_X = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_Home_X.setObjectName("pushButton_Home_X")
        self.gridLayout.addWidget(self.pushButton_Home_X, 5, 2, 1, 1)
        self.lineEdit_Detector_X = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit_Detector_X.setObjectName("lineEdit_Detector_X")
        self.gridLayout.addWidget(self.lineEdit_Detector_X, 5, 3, 1, 1)
        self.label_X_detector_position = QtWidgets.QLabel(self.layoutWidget)
        self.label_X_detector_position.setEnabled(True)
        self.label_X_detector_position.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_X_detector_position.setObjectName("label_X_detector_position")
        self.gridLayout.addWidget(self.label_X_detector_position, 5, 4, 1, 1)
        self.label_Y_detector = QtWidgets.QLabel(self.layoutWidget)
        self.label_Y_detector.setObjectName("label_Y_detector")
        self.gridLayout.addWidget(self.label_Y_detector, 6, 0, 1, 1)
        self.Enable_Y_pushButton = QtWidgets.QPushButton(self.layoutWidget)
        self.Enable_Y_pushButton.setObjectName("Enable_Y_pushButton")
        self.gridLayout.addWidget(self.Enable_Y_pushButton, 6, 1, 1, 1)
        self.pushButton_Home_Y = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_Home_Y.setObjectName("pushButton_Home_Y")
        self.gridLayout.addWidget(self.pushButton_Home_Y, 6, 2, 1, 1)
        self.lineEdit_Detector_Y = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit_Detector_Y.setObjectName("lineEdit_Detector_Y")
        self.gridLayout.addWidget(self.lineEdit_Detector_Y, 6, 3, 1, 1)
        self.label_Y_detector_position = QtWidgets.QLabel(self.layoutWidget)
        self.label_Y_detector_position.setEnabled(True)
        self.label_Y_detector_position.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_Y_detector_position.setObjectName("label_Y_detector_position")
        self.gridLayout.addWidget(self.label_Y_detector_position, 6, 4, 1, 1)
        self.lineEdit_angle_trial = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit_angle_trial.setWhatsThis("")
        self.lineEdit_angle_trial.setObjectName("lineEdit_angle_trial")
        self.gridLayout.addWidget(self.lineEdit_angle_trial, 7, 0, 1, 1)
        self.up_pushButton = QtWidgets.QPushButton(self.layoutWidget)
        self.up_pushButton.setObjectName("up_pushButton")
        self.gridLayout.addWidget(self.up_pushButton, 7, 1, 1, 1)
        self.down_pushButton = QtWidgets.QPushButton(self.layoutWidget)
        self.down_pushButton.setObjectName("down_pushButton")
        self.gridLayout.addWidget(self.down_pushButton, 8, 1, 1, 1)
        self.pushButton_set = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_set.setObjectName("pushButton_set")
        self.gridLayout.addWidget(self.pushButton_set, 8, 5, 1, 1)
        self.lable_current_angle = QtWidgets.QLabel(self.layoutWidget)
        self.lable_current_angle.setObjectName("lable_current_angle")
        self.gridLayout.addWidget(self.lable_current_angle, 9, 0, 1, 10)
        self.radioButton_Trial_Mode = QtWidgets.QRadioButton(self.layoutWidget)
        self.radioButton_Trial_Mode.setObjectName("radioButton_Trial_Mode")
        self.gridLayout.addWidget(self.radioButton_Trial_Mode, 9, 2, 1, 1)
        self.radioButton_Medipix = QtWidgets.QRadioButton(self.layoutWidget)
        self.radioButton_Medipix.setObjectName("radioButton_Medipix")
        self.gridLayout.addWidget(self.radioButton_Medipix, 9, 3, 1, 1)
        self.radioButton_Flatpanel = QtWidgets.QRadioButton(self.layoutWidget)
        self.radioButton_Flatpanel.setObjectName("radioButton_Flatpanel")
        self.gridLayout.addWidget(self.radioButton_Flatpanel, 9, 4, 1, 1)
        self.pushButton_next = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_next.setObjectName("pushButton_next")
        self.gridLayout.addWidget(self.pushButton_next, 9, 5, 1, 1)
        self.file_path_label = QtWidgets.QLabel(self.layoutWidget)
        font = QtGui.QFont()
        font.setItalic(True)
        self.file_path_label.setFont(font)
        self.file_path_label.setObjectName("file_path_label")
        self.gridLayout.addWidget(self.file_path_label, 10, 0, 1, 10)
        self.label_Flatpanel = QtWidgets.QLabel(self.layoutWidget)
        self.label_Flatpanel.setText("")
        self.label_Flatpanel.setObjectName("label_Flatpanel")
        self.gridLayout.addWidget(self.label_Flatpanel, 11, 0, 1, 1)
        self.pushButton_cancel = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.gridLayout.addWidget(self.pushButton_cancel, 7, 5, 1, 1)
        CT_controller.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(CT_controller)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 891, 22))
        self.menubar.setObjectName("menubar")
        self.menuSettings = QtWidgets.QMenu(self.menubar)
        self.menuSettings.setObjectName("menuSettings")
        CT_controller.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(CT_controller)
        self.statusbar.setObjectName("statusbar")
        CT_controller.setStatusBar(self.statusbar)
        self.actionGrbl_Settings = QtWidgets.QAction(CT_controller)
        self.actionGrbl_Settings.setCheckable(False)
        self.actionGrbl_Settings.setObjectName("actionGrbl_Settings")
        self.actionReset_GRBL = QtWidgets.QAction(CT_controller)
        self.actionReset_GRBL.setObjectName("actionReset_GRBL")
        self.actionChoose_file_path = QtWidgets.QAction(CT_controller)
        self.actionChoose_file_path.setObjectName("actionChoose_file_path")
        self.menuSettings.addAction(self.actionGrbl_Settings)
        self.menuSettings.addAction(self.actionReset_GRBL)
        self.menuSettings.addAction(self.actionChoose_file_path)
        self.menubar.addAction(self.menuSettings.menuAction())

        self.retranslateUi(CT_controller)
        QtCore.QMetaObject.connectSlotsByName(CT_controller)

    def retranslateUi(self, CT_controller):
        _translate = QtCore.QCoreApplication.translate
        CT_controller.setWindowTitle(_translate("CT_controller", "MainWindow"))
        self.curr_pos_label.setText(_translate("CT_controller", "Current position:"))
        self.label_detector.setText(_translate("CT_controller", "Detector position"))
        self.lineEdit_detector.setStatusTip(_translate("CT_controller", "Set detector position in mm"))
        self.lineEdit_detector.setPlaceholderText(_translate("CT_controller", "0"))
        self.label_detector_position.setText(_translate("CT_controller", "0"))
        self.label_sample.setText(_translate("CT_controller", "Sample position"))
        self.lineEdit_sample.setStatusTip(_translate("CT_controller", "Set sample position in mm"))
        self.lineEdit_sample.setPlaceholderText(_translate("CT_controller", "0"))
        self.label_sample_position.setText(_translate("CT_controller", "0"))
        self.label_vertical.setText(_translate("CT_controller", "Vertical position"))
        self.vert_up_pushButton.setText(_translate("CT_controller", "↑"))
        self.vert_down_pushButton.setText(_translate("CT_controller", "↓"))
        self.lineEdit_vert_disp.setStatusTip(_translate("CT_controller", "Angle to cover by servo in trial mode"))
        self.lineEdit_vert_disp.setPlaceholderText(_translate("CT_controller", "0"))
        self.label_vertical_position.setText(_translate("CT_controller", "0"))
        self.label_steps_rotation.setText(_translate("CT_controller", "Angles per rotation"))
        self.lineEdit_steps.setStatusTip(_translate("CT_controller", "Set the numbers of angles to cover per rotation"))
        self.lineEdit_steps.setPlaceholderText(_translate("CT_controller", "0"))
        self.label_rotation_position.setText(_translate("CT_controller", "0"))
        self.label_X_detector.setText(_translate("CT_controller", "X Detector stage"))
        self.Enable_X_pushButton.setText(_translate("CT_controller", "Enable X"))
        self.pushButton_Home_X.setText(_translate("CT_controller", "Home X"))
        self.lineEdit_Detector_X.setStatusTip(_translate("CT_controller", "Set the numbers of angles to cover per rotation"))
        self.lineEdit_Detector_X.setPlaceholderText(_translate("CT_controller", "0"))
        self.label_X_detector_position.setText(_translate("CT_controller", "0"))
        self.label_Y_detector.setText(_translate("CT_controller", "Y Detector stage"))
        self.Enable_Y_pushButton.setText(_translate("CT_controller", "Enable Y"))
        self.pushButton_Home_Y.setText(_translate("CT_controller", "Home Y"))
        self.lineEdit_Detector_Y.setStatusTip(_translate("CT_controller", "Set the numbers of angles to cover per rotation"))
        self.lineEdit_Detector_Y.setPlaceholderText(_translate("CT_controller", "0"))
        self.label_Y_detector_position.setText(_translate("CT_controller", "0"))
        self.lineEdit_angle_trial.setStatusTip(_translate("CT_controller", "Angle to cover by servo in trial mode"))
        self.lineEdit_angle_trial.setPlaceholderText(_translate("CT_controller", "Trials angle"))
        self.up_pushButton.setText(_translate("CT_controller", "↑"))
        self.down_pushButton.setText(_translate("CT_controller", "↓"))
        self.pushButton_set.setText(_translate("CT_controller", "Set"))
        self.lable_current_angle.setText(_translate("CT_controller", "Current angle:"))
        self.radioButton_Trial_Mode.setText(_translate("CT_controller", "Trial Mode"))
        self.radioButton_Medipix.setText(_translate("CT_controller", "Medipix Mode"))
        self.radioButton_Flatpanel.setText(_translate("CT_controller", "Flatpanel Mode"))
        self.pushButton_next.setText(_translate("CT_controller", "Next"))
        self.file_path_label.setText(_translate("CT_controller", "File path: "))
        self.pushButton_cancel.setText(_translate("CT_controller", "Cancel"))
        self.menuSettings.setTitle(_translate("CT_controller", "&Settings"))
        self.actionGrbl_Settings.setText(_translate("CT_controller", "&Grbl Settings"))
        self.actionGrbl_Settings.setToolTip(_translate("CT_controller", "Modifiy GRBL Presets"))
        self.actionReset_GRBL.setText(_translate("CT_controller", "Reset GRBL"))
        self.actionChoose_file_path.setText(_translate("CT_controller", "Choose file path"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CT_controller = QtWidgets.QMainWindow()
    ui = Ui_CT_controller()
    ui.setupUi(CT_controller)
    CT_controller.show()
    sys.exit(app.exec_())
