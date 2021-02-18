#!/usr/bin/python3
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, Qt
from PyQt5.QtWidgets import QWidget, QCheckBox, QApplication
import pyqtgraph as pg
import numpy as np
import sys
import time
import queue
import serial.tools.list_ports
import math
import os
# from pynput import keyboard
# from PyQt5.QtCore import pyqtRemoveInputHook

from airfoil import Airfoil

airfoil_data_folder = QtCore.QDir.homePath() + "/.airfoils"

class ConnectedAirfoilsModel(QtCore.QObject):
    data_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.af_left = Airfoil()
        self.af_right = Airfoil()
        self.it_point_list_right = []
        self.it_point_list_left = []

        self.af_left.data_changed.connect(self.connect_airfoils)
        self.af_right.data_changed.connect(self.connect_airfoils)

    def connect_airfoils(self):
        if(self.af_left.loaded and self.af_right.loaded):
            degrees = list(set(self.af_left.get_degree_list() +
                               self.af_right.get_degree_list()))
            degrees.sort()

            self.it_point_list_right = self.af_right.get_interpolated_point_list(
                degrees)
            self.it_point_list_left = self.af_left.get_interpolated_point_list(
                degrees)

            self.data_changed.emit()

    def generate_gcode(self, feedrate):
        gcode = list()
        if(self.af_left.loaded and self.af_right.loaded):
            # turn on the spindle (hotwire) at the given temp
            gcode.append("M3 S" + str(control_widget.temp_spbox.value()) + "\n")
            gcode.append("M7\n")
            gcode.append("F%.2f\n" % feedrate)

            # example coordinate for cutting block to size:
            # (x, y) -> x = x and u, y = y and z
            if (control_widget.cutBlockToSizeCheckbox.isChecked()):
                # (0, 0)
                gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                            (0, 0, 0, 0))

                # (0, block height)
                gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                            (0,
                            control_widget.block_height_spbox.value(),
                            0,
                            control_widget.block_height_spbox.value()))

                # (block length, block height)
                gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                            (control_widget.block_length_spbox.value(),
                            control_widget.block_height_spbox.value(),
                            control_widget.block_length_spbox.value(),
                            control_widget.block_height_spbox.value()))

                # (block length, 0)
                gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                            (control_widget.block_length_spbox.value(),
                            0,
                            control_widget.block_length_spbox.value(),
                            0))

                # (block length, block height)
                gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                            (control_widget.block_length_spbox.value(),
                            control_widget.block_height_spbox.value(),
                            control_widget.block_length_spbox.value(),
                            control_widget.block_height_spbox.value()))

                # (0, block height)
                gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                            (0,
                            control_widget.block_height_spbox.value(),
                            0,
                            control_widget.block_height_spbox.value()))

                # (0, 0)
                gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                            (0, 0, 0, 0))

            # Cut the wing profiles
            gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                         (self.af_right.start[0],
                          self.af_right.start[1],
                          self.af_left.start[0],
                          self.af_left.start[1]))

            for i in range(len(self.it_point_list_right[0])):
                gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                             (self.it_point_list_right[0][i],
                              self.it_point_list_right[1][i],
                              self.it_point_list_left[0][i],
                              self.it_point_list_left[1][i]))

            gcode.append("G01 X%.3f Y%.3f U%.3f Z%.3f\n" %
                         (self.af_right.end[0],
                          self.af_right.end[1],
                          self.af_left.end[0],
                          self.af_left.end[1]))

        return gcode


class MachineModel(QtCore.QObject):
    data_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._position = [0.0, 0.0, 0.0, 0.0]

    def set_position(self, position):
        self._position = position
        self.data_changed.emit()

    def get_position(self):
        return self._position

    def set_no_position(self):
        self._position = None
        self.data_changed.emit()


class AirfoilItemManager:
    def __init__(self, airfoil, color):
        self.airfoil = airfoil
        self.airfoil.data_changed.connect(self.draw)

        self.curve = pg.PlotCurveItem(
            [], [], pen=pg.mkPen(color=color, width=2))
        self.lead_in = pg.PlotCurveItem([], [], pen=pg.mkPen(
            color=color, width=3, style=QtCore.Qt.DotLine))
        self.lead_out = pg.PlotCurveItem([], [], pen=pg.mkPen(
            color=color, width=3, style=QtCore.Qt.DotLine))

        # Load button
        self.load_btn = QtGui.QPushButton("Load")
        self.load_btn.clicked.connect(self.on_load)

        # Rotating spbox
        self.rot_spbox = QtGui.QDoubleSpinBox()
        self.rot_spbox.setRange(-90, 90)
        self.rot_spbox.setValue(self.airfoil.r)
        self.rot_spbox.setPrefix("R : ")
        self.rot_spbox.setSuffix("°")
        self.rot_spbox.valueChanged.connect(self.on_rot)

        # Wing Chord (or scale, of the profile)
        self.scale_spbox = QtGui.QDoubleSpinBox()
        self.scale_spbox.setRange(1, 10000)
        self.scale_spbox.setValue(self.airfoil.s)
        self.scale_spbox.setPrefix("C : ")
        self.scale_spbox.setSuffix("mm")
        self.scale_spbox.valueChanged.connect(self.on_scale)

        # Translate X
        self.tx_spbox = QtGui.QDoubleSpinBox()
        self.tx_spbox.setRange(-10000, 10000)
        self.tx_spbox.setValue(self.airfoil.t[0])
        self.tx_spbox.setPrefix("TX : ")
        self.tx_spbox.setSuffix("mm")
        self.tx_spbox.valueChanged.connect(self.on_tx)

        # Translate Y
        self.ty_spbox = QtGui.QDoubleSpinBox()
        self.ty_spbox.setRange(-10000, 10000)
        self.ty_spbox.setValue(self.airfoil.t[1])
        self.ty_spbox.setPrefix("TY : ")
        self.ty_spbox.setSuffix("mm")
        self.ty_spbox.valueChanged.connect(self.on_ty)

        # Dilate
        self.dilate_spbox = QtGui.QDoubleSpinBox()
        self.dilate_spbox.setRange(0, 100)
        self.airfoil.d = 1
        self.dilate_spbox.setValue(self.airfoil.d)
        self.dilate_spbox.setSingleStep(0.1)
        self.dilate_spbox.setPrefix("D : ")
        self.dilate_spbox.setSuffix("mm")
        self.dilate_spbox.valueChanged.connect(self.on_dilate)

        self.name = QtGui.QLabel(text="No airfoil loaded")
        self.name.setAlignment(Qt.Qt.AlignCenter)
        self.name.setMaximumSize(1000, 20)
        self.name.setStyleSheet("color: rgb" + str(color))

    def draw(self):
        self.curve.setData(
            self.airfoil.trans_data[0], self.airfoil.trans_data[1])
        self.lead_in.setData([self.airfoil.start[0], self.airfoil.trans_data[0][0]], [
                             self.airfoil.start[1], self.airfoil.trans_data[1][0]])
        self.lead_out.setData([self.airfoil.end[0], self.airfoil.trans_data[0][-1]], [
                              self.airfoil.end[1], self.airfoil.trans_data[1][-1]])

    def on_load(self):
        filename, _ = QtGui.QFileDialog.getOpenFileName(self.load_btn.parent(),
                                                        "Open File",
                                                        "",
                                                        "All Files (*)")
        if filename: #TODO: add conditional here
            self.airfoil.load(filename)
            self.name.setText(self.airfoil.name)

    def on_rot(self):
        self.airfoil.rotate(self.rot_spbox.value())

    def on_scale(self):
        self.airfoil.scale(self.scale_spbox.value())

    def scale_to_value(self, scale):
        self.airfoil.scale(scale)
        self.scale_spbox.setValue(scale)

    def on_tx(self):
        self.airfoil.translate_x(self.tx_spbox.value())

    def on_ty(self):
        self.airfoil.translate_y(self.ty_spbox.value())

    def on_dilate(self):
        self.airfoil.dilate(self.dilate_spbox.value())


class SideViewWidget(QtGui.QWidget):

    def __init__(self, connected_airfoils, machine):
        super().__init__()
        plot = pg.PlotWidget()

        self._connected_airfoils = connected_airfoils
        self._machine = machine

        self.aim_left = AirfoilItemManager(
            self._connected_airfoils.af_left, (46, 134, 171))
        self.aim_right = AirfoilItemManager(
            self._connected_airfoils.af_right, (233, 79, 55))
        self.connection_lines_item = pg.QtGui.QGraphicsPathItem()
        self.connection_lines_item.setPen(pg.mkPen(0.7))
        self.machine_item = pg.PlotCurveItem(
            [], [], pen=pg.mkPen(color=(84, 209, 35), width=4))

        self._connected_airfoils.data_changed.connect(self.draw_connected)
        self._machine.data_changed.connect(self.draw_machine)

        plot.addItem(self.connection_lines_item)
        plot.addItem(self.aim_left.curve)
        plot.addItem(self.aim_right.curve)
        plot.addItem(self.aim_left.lead_in)
        plot.addItem(self.aim_right.lead_in)
        plot.addItem(self.aim_left.lead_out)
        plot.addItem(self.aim_right.lead_out)
        plot.addItem(self.machine_item)

        grid_alpha = 50
        grid_levels = [(10, 0), (5, 0), (1, 0)]
        x = plot.getAxis("bottom")
        y = plot.getAxis("left")
        x.setGrid(grid_alpha)
        y.setGrid(grid_alpha)
        x.setTickSpacing(levels=grid_levels)
        y.setTickSpacing(levels=grid_levels)

        plot.setRange(xRange=(0, 100), padding=0, disableAutoRange=False)
        plot.setAspectLocked()

        layout = QtGui.QGridLayout()
        layout.addWidget(self.aim_left.name, 0, 0)
        layout.addWidget(self.aim_left.load_btn, 1, 0)
        layout.addWidget(self.aim_left.rot_spbox, 2, 0)
        layout.addWidget(self.aim_left.scale_spbox, 3, 0)
        layout.addWidget(self.aim_left.tx_spbox, 4, 0)
        layout.addWidget(self.aim_left.ty_spbox, 5, 0)
        layout.addWidget(self.aim_left.dilate_spbox, 6, 0)
        layout.addWidget(plot, 0, 1, 8, 1)
        layout.addWidget(self.aim_right.name, 0, 2)
        layout.addWidget(self.aim_right.load_btn, 1, 2)
        layout.addWidget(self.aim_right.rot_spbox, 2, 2)
        layout.addWidget(self.aim_right.scale_spbox, 3, 2)
        layout.addWidget(self.aim_right.tx_spbox, 4, 2)
        layout.addWidget(self.aim_right.ty_spbox, 5, 2)
        layout.addWidget(self.aim_right.dilate_spbox, 6, 2)
        self.setLayout(layout)

    def draw_machine(self):
        mpos = self._machine.get_position()
        if(mpos is not None):
            self.machine_item.setData([mpos[0], mpos[2]], [mpos[1], mpos[3]])
        else:
            self.machine_item.setData([])

    def draw_connected(self):
        right_points = self._connected_airfoils.it_point_list_right
        left_points = self._connected_airfoils.it_point_list_left
        nb_points = len(left_points[0])

        x = np.dstack((right_points[0], left_points[0]))
        y = np.dstack((right_points[1], left_points[1]))
        connected = np.dstack((np.ones(nb_points), np.zeros(nb_points)))

        path = pg.arrayToQPath(x.flatten(), y.flatten(), connected.flatten())
        self.connection_lines_item.setPath(path)


class SerialThread(QtCore.QThread):
    connection_changed = QtCore.pyqtSignal()
    port_list_changed = QtCore.pyqtSignal()

    def __init__(self, machine):
        super().__init__()
        self._machine = machine
        self.port = ""
        self.port_list = []

        self.connected = False
        self.connecting = False
        self.running = False
        self.stop_request = False
        self.connect_request = False
        self.disconnect_request = False
        self.gcode = []
        self.last_status_request = time.time()

        self.on_board_buf = 128
        self.past_cmd_len = queue.Queue()

    def __del__(self):
        self.wait()

    def connect(self, port):
        if(not self.connected):
            self.port = port
            self.connect_request = True
        else:
            print("already connected")
            pass

    def disconnect(self):
        if(self.connected):
            if(not self.running):
                self.disconnect_request = True
            else:
                print("running")
                pass
        else:
            print("\n+----------------+")
            print("| Not connected. |")
            print("+----------------+\n")
            pass

    def play(self, gcode):
        if(self.connected):
            if(not self.running):
                self.gcode = list(gcode)
                self.running = True
            else:
                print("already running")
                pass
        else:
            print("\n+----------------+")
            print("| Not connected. |")
            print("+----------------+\n")
            pass

    def jog(self, gcode):
        if(self.connected):
            if(not self.running):
                self.gcode = list(gcode)
                self.running = True
            else:
                print("already running")
                pass
        else:
            print("\n+----------------+")
            print("| Not connected. |")
            print("+----------------+\n")
            pass

    def stop(self):
        if(self.connected):
            if(self.running):
                self.stop_request = True
            else:
                print("not running")
                pass
        else:
            print("\n+----------------+")
            print("| Not connected. |")
            print("+----------------+\n")
            pass

    def run(self):
        while(True):
            if(self.connected):
                if(self.disconnect_request):
                    self._reset()

                try:
                    if(self.stop_request):
                        self.serial.write(("!").encode("ascii"))
                        self.running = False
                        self.stop_request = False
                except serial.SerialException:
                    self._reset()
                    continue

                try:
                    if(self.running):
                        if(self.gcode):
                            if(len(self.gcode[0]) <= self.on_board_buf):
                                cmd = self.gcode.pop(0)
                                self.serial.write(cmd.encode("ascii"))
                                self.on_board_buf -= len(cmd)
                                self.past_cmd_len.put(len(cmd))
                        else:
                            self.running = False
                except serial.SerialException:
                    self._reset()
                    continue

                try:
                    now = time.time()
                    if(self.last_status_request + 0.2 < now):
                        self.serial.write(("?").encode("ascii"))
                        self.last_status_request = now
                except serial.SerialException:
                    self._reset()
                    continue

                try:
                    read_data = self.serial.readline().decode("ascii")
                    self._process_read_data(read_data)
                except serial.SerialException:
                    self._reset()
                    continue

            else:
                if(self.connect_request):
                    self._attempt_connection(self.port)
                    self.connect_request = False
                else:
                    self.port_list = [
                        port.device for port in serial.tools.list_ports.comports()]
                    self.port_list.sort()
                    self.port_list_changed.emit()
                    time.sleep(0.2)

    def _reset(self):
        self.serial.close()
        self.running = False
        self.stop_request = False
        self.connect_request = False
        self.disconnect_request = False
        self.on_board_buf = 128
        self.past_cmd_len = queue.Queue()

        self.connected = False
        self._machine.set_no_position()
        self.connection_changed.emit()

    def _process_read_data(self, data):
        # print data for debugging purposes
        # print(data)
        if(data == 'ok\r\n'):
            self.on_board_buf += self.past_cmd_len.get()
        elif(data != ''):
            if(data[0] == "<"):
                self._parse_status(data)
            else:
                # handle grbl errors here
                pass

    def _parse_status(self, status):
        mpos_idx = status.find("WPos:")
        mpos_str = status[mpos_idx+5:].split("|")[0].split(",")
        mpos = [float(i) for i in mpos_str]
        if(mpos[0] == mpos[2] and mpos[1] == mpos[3]):
            mpos[3] += 0.001
        self._machine.set_position(mpos)

    def _attempt_connection(self, port):
        self.connecting = True
        self.connection_changed.emit()
        try:
            self.serial = serial.Serial(port, 115200, timeout=2.0)

            # consume initial CRLF
            self.serial.readline()

            # read in the initial firmware prompt
            prompt = self.serial.readline().decode("ascii")

            # printout prompt for debugging purposes
            # print("prompt: ", prompt.encode("ascii"))
            # print("prompt: (not ascii encoded) ->", prompt)

            # make sure this is Grbl firmware
            if(prompt[:4] == "Grbl"):
                self.serial.timeout = 0.1
                self.connected = True
            else:
                print("Prompt failed")
        except:
            pass
        self.connecting = False
        self.connection_changed.emit()


class ControlWidget(QtGui.QWidget):
    def __init__(self, connected_airfoils, machine):
        super().__init__()

        self._connected_airfoils = connected_airfoils
        self.serial_thread = SerialThread(machine)
        self.serial_thread.connection_changed.connect(
            self.on_connection_change)
        self.serial_thread.port_list_changed.connect(self.on_port_list_change)
        self.serial_thread.start()

        layout = QtGui.QGridLayout()
        play_btn = QtGui.QPushButton("play")
        play_btn.clicked.connect(self.on_play)
        stop_btn = QtGui.QPushButton("stop")
        stop_btn.clicked.connect(self.on_stop)
        self.connect_btn = QtGui.QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect)

        # Auto - Scale Checkbox
        self.autoScaleCheckbox = QCheckBox("Auto-scale")

        # Cut Block to Size Checkbox
        self.cutBlockToSizeCheckbox = QCheckBox("Cut Block to Size")

        # Generate Gcode File button
        saveFile_btn = QtGui.QPushButton("save")
        saveFile_btn.clicked.connect(self.on_save)

        # Styrofoam Profiles
        self.import_styrofoam_profile_label = QtGui.QLabel(text="Import profile:")
        self.save_styrofoam_profile_label = QtGui.QLabel(text="Save profile:")

        self.import_styrofoam_profile_button = QtGui.QPushButton("Import")
        self.import_styrofoam_profile_button.clicked.connect(self.import_styrofoam_profile)

        self.save_styrofoam_profile_button = QtGui.QPushButton("Save")
        self.save_styrofoam_profile_button.clicked.connect(self.save_styrofoam_profile)

        # Jogging buttons
        jog_btn_x_positive = QtGui.QPushButton("X+")
        jog_btn_x_positive.clicked.connect(self.on_jog_x_positive)

        jog_btn_x_negative = QtGui.QPushButton("X-")
        jog_btn_x_negative.clicked.connect(self.on_jog_x_negative)

        jog_btn_y_positive = QtGui.QPushButton("Y+")
        jog_btn_y_positive.clicked.connect(self.on_jog_y_positive)

        jog_btn_y_negative = QtGui.QPushButton("Y-")
        jog_btn_y_negative.clicked.connect(self.on_jog_y_negative)

        jog_btn_u_positive = QtGui.QPushButton("U+")
        jog_btn_u_positive.clicked.connect(self.on_jog_u_positive)

        jog_btn_u_negative = QtGui.QPushButton("U-")
        jog_btn_u_negative.clicked.connect(self.on_jog_u_negative)

        jog_btn_z_positive = QtGui.QPushButton("Z+")
        jog_btn_z_positive.clicked.connect(self.on_jog_z_positive)

        jog_btn_z_negative = QtGui.QPushButton("Z-")
        jog_btn_z_negative.clicked.connect(self.on_jog_z_negative)

        # Draw the rest of the controls here
        self.port_box = QtGui.QComboBox()
        self.port_box.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)
        self.port_box.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        # set zero button
        self.setZeroButton = QtGui.QPushButton("Set Zero")
        self.setZeroButton.clicked.connect(self.on_set_zero)

        # feedrate
        self.feed_spbox = QtGui.QDoubleSpinBox()
        self.feed_spbox.setRange(1, 1000)
        self.feed_spbox.setValue(500)
        self.feed_spbox.setSingleStep(10)
        self.feed_spbox.setPrefix("Feedrate: ")
        self.feed_spbox.setSuffix("mm/s")

        # milliamps (Amperes, temperature of the wire)
        self.temp_spbox = QtGui.QDoubleSpinBox()
        self.temp_spbox.setRange(0, 12000)
        self.temp_spbox.setValue(1000)
        self.temp_spbox.setSingleStep(100)
        self.temp_spbox.setPrefix("Temp: ")
        self.temp_spbox.setSuffix("mA")
        self.temp_spbox.valueChanged.connect(self.on_temperature_change)

        # wing span
        self.span_spbox = QtGui.QDoubleSpinBox()
        self.span_spbox.setRange(1, 1200)
        self.span_spbox.setValue(1000)
        self.span_spbox.setSingleStep(10)
        self.span_spbox.setPrefix("Wing span: ")
        self.span_spbox.setSuffix("mm")
        self.span_spbox.valueChanged.connect(self.on_wing_span_change)

        # block width
        self.block_width_spbox = QtGui.QDoubleSpinBox()
        self.block_width_spbox.setRange(1, 1200)
        self.block_width_spbox.setValue(1000)
        self.block_width_spbox.setSingleStep(1)
        self.block_width_spbox.setPrefix("Block width: ")
        self.block_width_spbox.setSuffix("mm")

        # block length
        self.block_length_spbox = QtGui.QDoubleSpinBox()
        self.block_length_spbox.setRange(1, 580)
        self.block_length_spbox.setValue(400)
        self.block_length_spbox.setSingleStep(1)
        self.block_length_spbox.setPrefix("Block length: ")
        self.block_length_spbox.setSuffix("mm")

        # block height
        self.block_height_spbox = QtGui.QDoubleSpinBox()
        self.block_height_spbox.setRange(1, 320)
        self.block_height_spbox.setValue(100)
        self.block_height_spbox.setSingleStep(1)
        self.block_height_spbox.setPrefix("Block height: ")
        self.block_height_spbox.setSuffix("mm")

        # block offset
        self.block_offset_spbox = QtGui.QDoubleSpinBox()
        self.block_offset_spbox.setRange(0, 1200)
        self.block_offset_spbox.setValue(100)
        self.block_offset_spbox.setSingleStep(1)
        self.block_offset_spbox.setPrefix("Block offset: ")
        self.block_offset_spbox.setSuffix("mm")

        self.serial_text_item = QtGui.QTextEdit()
        self.serial_data = ""

        # lead in/out
        self.lead_spbox = QtGui.QDoubleSpinBox()
        self.lead_spbox.setRange(1, 1000)
        self.lead_spbox.setValue(self._connected_airfoils.af_left.lead_in_out)
        self.lead_spbox.setPrefix("Lead in/out: ")
        self.lead_spbox.setSuffix("mm")
        self.lead_spbox.valueChanged.connect(self.on_lead_change)

        # add all of the widgets to the layout
        layout.addWidget(self.feed_spbox, 5, 0)
        layout.addWidget(self.lead_spbox, 1, 0)
        layout.addWidget(self.block_width_spbox, 2, 0)
        layout.addWidget(self.block_height_spbox, 3, 0)
        layout.addWidget(self.block_length_spbox, 4, 0)
        layout.addWidget(self.block_offset_spbox, 0, 0)
        layout.addWidget(self.span_spbox, 6, 0)
        layout.addWidget(self.temp_spbox, 7, 0)
        layout.addWidget(play_btn, 4, 5)
        layout.addWidget(stop_btn, 4, 6)
        layout.addWidget(saveFile_btn, 8, 0)
        layout.addWidget(self.import_styrofoam_profile_label, 1, 5)
        layout.addWidget(self.import_styrofoam_profile_button, 1, 6)
        layout.addWidget(self.save_styrofoam_profile_label, 2, 5)
        layout.addWidget(self.save_styrofoam_profile_button, 2, 6)
        layout.addWidget(self.autoScaleCheckbox, 3, 5)
        layout.addWidget(self.cutBlockToSizeCheckbox, 3, 6)
        layout.addWidget(self.setZeroButton, 5, 6)
        layout.addWidget(jog_btn_x_positive, 6, 5)
        layout.addWidget(jog_btn_x_negative, 6, 6)
        layout.addWidget(jog_btn_y_positive, 7, 5)
        layout.addWidget(jog_btn_y_negative, 7, 6)
        layout.addWidget(jog_btn_u_positive, 8, 5)
        layout.addWidget(jog_btn_u_negative, 8, 6)
        layout.addWidget(jog_btn_z_positive, 9, 5)
        layout.addWidget(jog_btn_z_negative, 9, 6)
        layout.addWidget(self.serial_text_item, 0, 1, 5, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 5)
        layout.addWidget(self.port_box, 0, 5)
        layout.addWidget(self.connect_btn, 0, 6)

        # finish and apply layout
        self.setLayout(layout)

    def on_set_zero(self):
        self.serial_thread.disconnect()
        time.sleep(1)
        self.serial_thread.connect(self.port_box.currentText())

    def on_connection_change(self):
        if(self.serial_thread.connecting):
            text = "Connecting..."
            self.connect_btn.setFlat(True)
        elif(self.serial_thread.connected):
            text = "Disconnect"
            self.connect_btn.setFlat(False)
        else:
            text = "Connect"
            self.connect_btn.setFlat(False)

        self.connect_btn.setText(text)

    def on_temperature_change(self):
        temperature = self.temp_spbox.value()
        gcode = self.get_jog_gcode_header()
        gcode.append("M3 S" + str(temperature) + "\n")
        print(gcode)
        self.serial_thread.play(gcode)

    def on_port_list_change(self):
        new_items = self.serial_thread.port_list
        prev_items = []
        for idx in range(self.port_box.count()):
            prev_items.append(self.port_box.itemText(idx))

        items_to_remove = list(set(prev_items) - set(new_items))
        items_to_insert = list(set(new_items) - set(prev_items))
        items_to_remove.sort()
        items_to_insert.sort()

        for item in items_to_remove:
            self.port_box.removeItem(self.port_box.findText(item))

        self.port_box.insertItems(0, items_to_insert)

    def on_stop(self):
        self.serial_thread.stop()

    def on_connect(self):
        if(self.serial_thread.connected):
            self.serial_thread.disconnect()
        else:
            self.serial_thread.connect(self.port_box.currentText())

    def dimensions_fit(self):
        # make sure dimensions of the wing profiles fit within the machine cutting area:
        # 1200mm (width) x 580mm (length) x 320mm (height)
        if ((self.block_offset_spbox.value() + self.block_width_spbox.value()) > 1200):
            print("Error: offset + block width is too large!")
            print("Need to decrease offset or block width by a minimum of " +
                  str(int(self.block_offset_spbox.value() + self.block_width_spbox.value() - 1200)) + "mm.")
            return False
        elif (self.block_length_spbox.value() > 580):
            print("Error: length of block is too long!")
            print("Need to decrease length by a minimum of " + str(int(self.block_length_spbox.value() - 580)) + "mm")
            return False
        elif (side_view_widget.aim_left.scale_spbox.value() > 580):
            print("Error: length of the left wing profile is too long!")
            print("Need to decrease the length of the left profile by a minimum of " +
                  str(int(side_view_widget.aim_left.scale_spbox.value() - 580)) + "mm")
            return False
        elif (side_view_widget.aim_right.scale_spbox.value() > 580):
            print("Error: length of the right wing profile is too long!")
            print("Need to decrease the length of the right profile by a minimum of " +
                  str(int(side_view_widget.aim_right.scale_spbox.value() - 580)) + "mm")
            return False
        elif (self.block_width_spbox.value() < self.span_spbox.value()):
            print("Error: wing span is greater than the block size!")
            print("Need to decrease the wing span (or increase the block size) by a minimum of " +
                  str(int(self.span_spbox.value() - self.block_width_spbox.value())) + "mm")
        return True

    def on_wing_span_change(self):
        # check that the change is valid/invalid
        if (self.dimensions_fit()):
            # update the scale accordingly
            if (control_widget.autoScaleCheckbox.isChecked()):
                side_view_widget.aim_left.scale_to_value(self.calculate_profile_scaling_percentage())
            return True
        return False

    def calculate_projected_coordinate(self, left_coord, right_coord):
        x_axis_length = 1200
        x_prime = left_coord
        y_prime = right_coord

        # delta_x = left_coord_x - right_coord_x
        delta_x = left_coord[0] - right_coord[0]

        # delta_y = left_coord_y - right_coord_y
        delta_y = left_coord[1] - right_coord[1]

        # delta_z = x_axis_length - offset
        delta_z = x_axis_length - self.block_offset_spbox.value()

        # find vector of length == 1 by dividing by length
        # length: sqrt(x^2 + y^2 + z^2)
        length = math.sqrt(pow(delta_x, 2) + pow(delta_y, 2) + pow(delta_z, 2))

        # divide each component by length, to get a vector of length 1
        delta_x_unit_vector = delta_x / length
        delta_y_unit_vector = delta_y / length
        delta_z_unit_vector = delta_z / length

        # multiply each component of the unit vector by x_axis_length to
        # get the new coordinates of the vector projecting all the way
        # to portal #1.
        x_prime = delta_x_unit_vector * x_axis_length
        y_prime = delta_y_unit_vector * x_axis_length

        return [x_prime, y_prime]

    def distance(self, first_coord, second_coord):
        return math.sqrt(pow((first_coord[0] - second_coord[0]), 2) + pow((first_coord[1] - second_coord[1]), 2))

    # Once wingspan and offset are defined, calculate the scale adjustment
    # necessary to make the wing fit in the styrofoam at the correct offset.
    # For example, if the wingspan is 100mm, and the offset is 100mm, then
    # scale profile #1 up/down accordingly so that the wing is cut at the correct
    # size within the piece of styrofoam.
    def calculate_profile_scaling_percentage(self):
        # set it to the current scale value
        old_scale = side_view_widget.aim_left.scale_spbox.value()
        new_scale = old_scale
        print("Current scale is: " + str(new_scale))

        # count the number of coordinates in the 1st *.dat file, and
        num_coordinates_1 = len(connect_airfoils.it_point_list_left[0])

        # store the first and middle coordinates in two arrays.
        first_coord_index_1 = 0
        middle_coord_index_1 = num_coordinates_1 // 2

        first_coord_1 = [connect_airfoils.it_point_list_left[0][first_coord_index_1],
                       connect_airfoils.it_point_list_left[1][first_coord_index_1]]

        middle_coord_1 = [connect_airfoils.it_point_list_left[0][middle_coord_index_1],
                        connect_airfoils.it_point_list_left[1][middle_coord_index_1]]

        # count the number of coordinates in the 2nd *.dat file, and
        num_coordinates_2 = len(connect_airfoils.it_point_list_right[0])

        # store the first and middle coordinates in two arrays.
        first_coord_index_2 = 0
        middle_coord_index_2 = num_coordinates_2 // 2

        first_coord_2 = [connect_airfoils.it_point_list_right[0][first_coord_index_2],
                         connect_airfoils.it_point_list_right[1][first_coord_index_2]]

        middle_coord_2 = [connect_airfoils.it_point_list_right[0][middle_coord_index_2],
                          connect_airfoils.it_point_list_right[1][middle_coord_index_2]]

        # Use the calculation routine to find out what first_coord'
        # and middle_coord' are.
        coordintates_prime_1 = self.calculate_projected_coordinate(first_coord_2, first_coord_1)
        coordintates_prime_2 = self.calculate_projected_coordinate(middle_coord_2, middle_coord_1)

        # Use the distance formula for each set of coordinates. Then
        # calculate the % of change (+/-), and make sure to convert
        # it to a negative or positive integer.
        length_original_coord = self.distance(first_coord_1, middle_coord_1)
        length_prime_coord = self.distance(coordintates_prime_1, coordintates_prime_2)

        # Return the integer for profile #1 to be scaled to
        new_scale = (length_prime_coord - length_original_coord) / (length_original_coord) * 100

        if (new_scale == 0):
            new_scale = old_scale
        elif (new_scale < 0):
            new_scale = new_scale * -1
        elif (new_scale > self.block_length_spbox.value()):
            new_scale = self.block_length_spbox.value()

        print("New adjusted scale is " + str(new_scale))

        return new_scale

    def on_play(self):
        # TODO: test this: scale the wing to fit inside of the block
        # new_scale = self.calculate_profile_scaling_percentage()

        # check that the dimensions fit
        if (not self.dimensions_fit()):
            print("\nDimensions of the machine are 1200mm x 580mm x 320mm\n")
            return
        gcode = self._connected_airfoils.generate_gcode(
            self.feed_spbox.value())

        self.serial_data = ""
        self.serial_data += ";Left  airfoil : " + self._connected_airfoils.af_left.name
        self.serial_data += (" | R:%.2f S%.2f TX%.2f TY%.2f D%.2f\n" %
                             (self._connected_airfoils.af_left.r,
                              self._connected_airfoils.af_left.s,
                              self._connected_airfoils.af_left.t[0],
                              self._connected_airfoils.af_left.t[1],
                              self._connected_airfoils.af_left.d))
        self.serial_data += ";Right airfoil : " + \
            self._connected_airfoils.af_right.name
        self.serial_data += (" | R:%.2f S%.2f TX%.2f TY%.2f D%.2f\n" %
                             (self._connected_airfoils.af_right.r,
                              self._connected_airfoils.af_right.s,
                              self._connected_airfoils.af_right.t[0],
                              self._connected_airfoils.af_right.t[1],
                              self._connected_airfoils.af_right.d))

        for command in gcode:
            self.serial_data += command
        self.serial_text_item.setText(self.serial_data)

        self.serial_thread.play(gcode)

    def get_jog_gcode_header(self):
        # turn on the fan and set feedrate
        gcode = list()
        gcode.append("M7\n")
        gcode.append("F" + str(self.feed_spbox.value()) + "\n")
        return gcode

    def import_styrofoam_profile(self):
        filename = QtGui.QFileDialog.getOpenFileName(self.import_styrofoam_profile_button.parent(),
                                                     "Open Temperature/Speed Profile",
                                                     "",
                                                     "All Files (*)")
        if filename:
            # Change font to bold, and show filename after importing
            myFont=QtGui.QFont()
            myFont.setBold(True)
            label_filename = str(os.path.splitext(os.path.basename(filename[0]))[0])
            print("Filename of imported profile is: " + filename[0])
            print("Trimmed filepath: " + label_filename)

            # update the label to show that the file was imported
            control_widget.import_styrofoam_profile_label.setText(label_filename)
            control_widget.import_styrofoam_profile_label.setFont(myFont)

            # read the file and import it
            with open(filename[0], 'r') as temp_profile_file:
                # read in the temperature
                new_temperature = temp_profile_file.readline()

                # make sure it exists in the file
                if (new_temperature != ""):
                    new_feedrate = temp_profile_file.readline()

                    # check that the feedrate value exists
                    if (new_feedrate != ""):
                        # set temperature and feedrate
                        self.temp_spbox.setValue(int(new_temperature))
                        self.feed_spbox.setValue(int(new_feedrate))

    def save_styrofoam_profile(self):
        name = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '.', "(*.txt)")
        file = open(name[0] + ".txt", 'w')
        text = str(int(self.temp_spbox.value())) + "\r\n" + str(int(self.feed_spbox.value())) + "\r\n"
        file.write(text)
        file.close()

    def on_jog_x_positive(self):
        gcode = self.get_jog_gcode_header()
        gcode.append("G91 X10 F" + str(self.feed_spbox.value()) + "\n")
        print(gcode)
        self.serial_thread.play(gcode)

    def on_jog_x_negative(self):
        gcode = self.get_jog_gcode_header()
        gcode.append("G91 X-10 F" + str(self.feed_spbox.value()) + "\n")
        print(gcode)
        self.serial_thread.play(gcode)

    def on_jog_y_positive(self):
        gcode = self.get_jog_gcode_header()
        gcode.append("G91 Y10 F" + str(self.feed_spbox.value()) + "\n")
        print(gcode)
        self.serial_thread.play(gcode)

    def on_jog_y_negative(self):
        gcode = self.get_jog_gcode_header()
        gcode.append("G91 Y-10 F" + str(self.feed_spbox.value()) + "\n")
        print(gcode)
        self.serial_thread.play(gcode)

    def on_jog_u_positive(self):
        gcode = self.get_jog_gcode_header()
        gcode.append("G91 U10 F" + str(self.feed_spbox.value()) + "\n")
        print(gcode)
        self.serial_thread.play(gcode)

    def on_jog_u_negative(self):
        gcode = self.get_jog_gcode_header()
        gcode.append("G91 U-10 F" + str(self.feed_spbox.value()) + "\n")
        print(gcode)
        self.serial_thread.play(gcode)

    def on_jog_z_positive(self):
        gcode = self.get_jog_gcode_header()
        gcode.append("G91 Z10 F" + str(self.feed_spbox.value()) + "\n")
        print(gcode)
        self.serial_thread.play(gcode)

    def on_jog_z_negative(self):
        gcode = self.get_jog_gcode_header()
        gcode.append("G91 Z-10 F" + str(self.feed_spbox.value()) + "\n")
        print(gcode)
        self.serial_thread.play(gcode)

    def on_save(self):
        name = QtGui.QFileDialog.getSaveFileName(
            self, 'Save File', '.', "(*.nc)")
        file = open(name[0] + ".nc", 'w')
        text = control_widget.serial_text_item.toPlainText()
        file.write(text)
        file.close()

    def on_lead_change(self):
        self._connected_airfoils.af_left.set_lead(self.lead_spbox.value())
        self._connected_airfoils.af_right.set_lead(self.lead_spbox.value())


class MainWidget(QtGui.QSplitter):
    def __init__(self, w1, w2):
        super().__init__(QtCore.Qt.Vertical)
        self.addWidget(w1)
        self.addWidget(w2)


if __name__ == '__main__':
    # pyqtRemoveInputHook()
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    pg.setConfigOption('antialias', True)
    app = QtGui.QApplication([])

    connect_airfoils = ConnectedAirfoilsModel()
    machine = MachineModel()

    side_view_widget = SideViewWidget(connect_airfoils, machine)
    control_widget = ControlWidget(connect_airfoils, machine)

    main_widget = MainWidget(side_view_widget, control_widget)
    main_widget.show()

    sys.exit(app.exec_())
