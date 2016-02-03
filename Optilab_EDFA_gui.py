# -*- coding: utf-8 -*-

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.console
import numpy as np

import Optilab_EDFA as edfa

from pyqtgraph.dockarea import *
from functools import partial
import serial.tools.list_ports

app = QtGui.QApplication([])
win = QtGui.QMainWindow()
area = DockArea()
win.setCentralWidget(area)
win.resize(1000,600)
win.setWindowTitle(r'Optilab EDFA control')

## Create docks, place them into the window one at a time.
## Note that size arguments are only a suggestion; docks will still have to
## fill the entire dock area and obey the limits of their internal widgets.
d1 = Dock("EDFA control", size=(300, 100))     ## give this dock the minimum possible size
d2 = Dock("Console", size=(100,300), closable=True)
d3 = Dock("COM", size=(100,20))
d4 = Dock("Plot of the last 100 read values", size=(100,100))

area.addDock(d1, 'left')      ## place d1 at left edge of dock area (it will fill the whole space since there are no other docks yet)
area.addDock(d2, 'right')     ## place d2 at right edge of dock area
area.addDock(d3, 'bottom', d1)## place d3 at bottom edge of d1
area.addDock(d4, 'bottom', d1)

# Instance of EDFA connection
com = None

def EDFA_disconnect():
    if com is None:
        w2.append("<font color='red'><strong>Not connected</strong></font>")
        return
    w2.append("<font color='black'><strong>Disconnecting EDFA</strong></font>")
    com.disconnect()

def EDFA_connect():
    global com, port_list, w2
    port = str(port_list.currentText().split(" ")[-1][1:-1])
    baudrate=9600
    com = edfa.OptiLabEDFA(port=port, baudrate=baudrate)
    if com is not None:
        w2.append("<font color='blue'><strong>Established connection at port {0} with a baudrate of {1}</strong></font>".format(port, baudrate))
    else:
        w2.append("<font color='red'><strong>Failed to establish connection at port {0} with a baudrate of {1}</strong></font>".format(port, baudrate))
    # Update bias value at startup:
    sctl.setSliderPosition(com.current_set_bias_mA)
        
out_pow = []
out_gain = []

def update_values():
    global com, out_pow, out_gain
    if com is None or not com.edfa.isOpen():
        return
    # Issue a read
    com.read()
    # Update GUI
    edfa_output.setText("Output [dBm]: {:.2f}".format(com.output_power_dBm))    
    edfa_input.setText("Input [dBm]: {:.2f}".format(com.input_power_dBm))   
    edfa_gain.setText("Gain [dBm]: {:.2f}".format(com.output_power_dBm - com.input_power_dBm))   
    edfa_bias.setText("Bias [mA]: {:.2f}".format(com.current_bias_mA))   
    edfa_set_bias.setText("Set Bias [mA]: {:.2f}".format(com.current_set_bias_mA))  
    edfa_temperature.setText("Temperature [deg C]: {}".format(com.unit_temp_deg))  
    
    # Plot acquired values, pick last 100.
    if len(out_pow) > 100:
        out_pow = out_pow[1:]
        out_gain = out_gain[1:]
        
    out_pow.append(com.output_power_dBm)
    out_gain.append(com.output_power_dBm - com.input_power_dBm)
    
    p1.plot(np.array(out_pow), clear=True)
    p_gain.plot(np.array(out_gain), clear=True)

def turn_on():
    global com
    if com is None:
        w2.append("<font color='red'><strong>Connect to the EDFA first!</strong></font>")
        return
    com.turn_on()
    w2.append("<font color='green'><strong>EDFA pump is ON</strong></font>")
    
def turn_off():
    global com
    if com is None:
        w2.append("<font color='red'><strong>Connect to the EDFA first!</strong></font>")
        return
    com.turn_off()
    w2.append("<font color='green'><strong>EDFA pump is OFF</strong></font>")


def valCh( num, val):
    global w2
    edfa_label.setText("Bias: {} [mA]".format(val))

    if com is None:
        return
        
    w2.append("<font color='black'><strong>Setting EDFA to a bias of {0} mA</strong></font>".format(val))
    ret = com.set_bias(val)
    if ret is False:
        w2.append("<font color='red'><strong>FAILED</strong></font>".format(val))
    # Expect: servo_number,pwm_value,mapped_servo_number
    
    #w2.append("<font color='red'>%f</font>\n" % val)
    

## Stuff that belongs to Dock d1 inside a Layout
edfa_layout = pg.LayoutWidget()
sctl = QtGui.QSlider(QtCore.Qt.Horizontal)

sctl.setMinimum(0)
sctl.setMaximum(250)
sctl.setPageStep(50)
sctl.setSliderPosition(0)

sctl.setTickInterval(10)
sctl.setSingleStep(1)
sctl.setTickPosition(2)

sctl.valueChanged.connect(partial(valCh, 0))
edfa_layout.addWidget(sctl,row=0, col=1)
edfa_label = QtGui.QLabel("Bias")

edfa_output = QtGui.QLabel("Output [dBm]:")
edfa_input = QtGui.QLabel("Input [dBm]:")
edfa_gain = QtGui.QLabel("Gain:")
edfa_bias = QtGui.QLabel("Bias [mA]:")
edfa_set_bias = QtGui.QLabel("Set Bias [mA]:")
edfa_temperature = QtGui.QLabel("Temperature [deg C]:")

edfa_off = QtGui.QPushButton()
edfa_off.setText("Turn pump OFF")

edfa_on = QtGui.QPushButton()
edfa_on.setText("Turn pump ON")

edfa_layout.addWidget(edfa_label, row=0, col=0)

edfa_layout.addWidget(edfa_output, row=1, col=1)
edfa_layout.addWidget(edfa_input, row=1, col=0)
edfa_layout.addWidget(edfa_gain, row=1, col=2)

edfa_layout.addWidget(edfa_bias, row=2, col=0)
edfa_layout.addWidget(edfa_set_bias, row=2, col=1)
edfa_layout.addWidget(edfa_temperature, row=3, col=0)

edfa_layout.addWidget(edfa_on, row=4, col=0)
edfa_layout.addWidget(edfa_off, row=4, col=2)

w1 = pg.LayoutWidget()

w1.addWidget(edfa_layout)

edfa_on.clicked.connect(turn_on)
edfa_off.clicked.connect(turn_off)

# Push to d1
d1.addWidget(w1)

## Stuff that belongs to Dock d4 (Plots)
p1 = pg.PlotWidget(title="Output power [dBm]")
p_gain = pg.PlotWidget(title="Gain [dBm]")

p1.enableAutoRange()
p_gain.enableAutoRange()

d4.addWidget(p1)
d4.addWidget(p_gain)


## Stuff that belong to Dock d2 (Console)
w2 = QtGui.QTextEdit()
d2.addWidget(w2)

## Stuff that belongs to Dock d3 (Port connection)
port_label = QtGui.QLabel("Port:")
port_list = QtGui.QComboBox()
port_connect = QtGui.QPushButton()
port_connect.setText("Connect")

port_disconnect = QtGui.QPushButton()
port_disconnect.setText("Disconnect")

port_layout = pg.LayoutWidget()
port_layout.addWidget(port_label, row=0, col=0)
port_layout.addWidget(port_list, row=0, col=1)
port_layout.addWidget(port_connect, row=0, col=2)
port_layout.addWidget(port_disconnect, row=0, col=3)

port_connect.clicked.connect(EDFA_connect)
port_disconnect.clicked.connect(EDFA_disconnect)

# Populate port list:
for port_address, port_name, _ in list(serial.tools.list_ports.comports())[::-1]:
    port_list.addItem("{0} ({1})".format(port_name, port_address))
d3.addWidget(port_layout)

win.show()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    
    refresh_timer = QtCore.QTimer()
    refresh_timer.timeout.connect(update_values)
    refresh_timer.start(1500)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
 