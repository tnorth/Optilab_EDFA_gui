#!/usr/bin/python

import serial
import sys
import time
import numpy as np
import pylab
import re

class OptiLabEDFA:
    rate = 9600
    port = None
    baudrate = None
    cmds = {"READ":"READ", "ON":"SETKEYON", "OFF":"SETKEYOFF", "BIAS":"SETBIAS:"}
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.connect()


    def connect(self):
        sys.stderr.write("Connecting OptiLab EDFA at %s with a baudrate of %d\n" % 
                            (self.port, self.baudrate)
                        )
        self.edfa = serial.Serial(self.port, self.baudrate, timeout=0.1)
        
        # initiate a READ
        self.read()
    
    def disconnect(self):
        if self.edfa:
            sys.stderr.write("Closing EDFA connection.\n")
            self.edfa.close()
        else:
            sys.stderr.write("No EDFA is currently connected.\n")
    

    def turn_on(self):
        self.edfa.write((self.cmds["ON"] + '\n').encode())
        # Replies: \r\nKEYON\r\nOK\r\n
        resp = self.edfa.readlines()
        if 'KEYON' in resp[1].decode(errors='ignore') and 'OK' in resp[2].decode(errors='ignore'):
            print("Pump laser turned ON")
        return True
    
    def turn_off(self):
        self.edfa.write((self.cmds["OFF"] + '\n').encode())
        # Replies: \r\nKEYON\r\nOK\r\n
        resp = self.edfa.readlines()
        if 'KEYOFF' in resp[1].decode(errors='ignore') and 'OK' in resp[2].decode(errors='ignore'):
            print("Pump laser turned OFF")
        return True    
    
    def set_bias(self, value):
        if value > 250 or value < 0 :
            print("Value must be in the range 0 - 255 mA")
            return False
        self.edfa.write((self.cmds["BIAS"] + str(value) + '\n').encode())
        resp = self.edfa.readlines()
        if 'OK' in resp[1].decode(errors='ignore'):
            return True
        return False
        
    def read(self):
        self.edfa.write((self.cmds["READ"] + '\n').encode())
        while 1:
            resp = self.edfa.readlines()
            if resp != []: break
        #print(resp)
        #for line in resp:
        #    print line
        
        def parse_read(msg):
            msg = [mm.decode(errors='ignore') for mm in msg]
            #print("msg: {}".format(msg))
            name = re.search("(EDFA.*?)\r\n", msg[1])
            #print(name.group(1))
            serialnumber = re.search("(S\/N.*?)\r\n", msg[2])
            #print(serialnumber.group(1))
            state = re.search("(INPUT LOW)", msg[3])
            
            # If there is no input:
            if state is None:
                # [00] five times
                input_power_dBm = re.search("INPUT\s+(.*?)dBm", msg[3])
                #print("Input Power [dBm] :", input_power_dBm.group(1))
                self.input_power_dBm = float(input_power_dBm.group(1))
                pos = 4
                
            else:
                self.input_power_dBm = -float('inf')
                #print(state.group(1))
                pos = 4
            
            # Get output power:
            output = re.search("OUTPUT\s+(.*?)dBm", msg[pos])
            if output is None:
                # No output ?
                output = re.search("(NO OUTPUT!)", msg[pos])
                self.output_power_dBm = -float('inf')
                print("No output power!")
            else:
                #print("Output power [dBm]: ", output.group(1))
                self.output_power_dBm = float(output.group(1))
            # Get Bias
            current_bias = re.search("BIAS1\s+(.*?)mA", msg[pos+1])
            #print("Current Bias [mA]: ", current_bias.group(1))
            self.current_bias_mA = float(current_bias.group(1))
            # Get set Bias
            current_set_bias = re.search("BIAS1\s+SET\s+(.*?)mA", msg[pos+2])
            #print("Current set Bias [mA]: ", current_set_bias.group(1))
            self.current_set_bias_mA = float(current_set_bias.group(1))
            # Get temperature
            unit_temp = re.search("UNITTEMP\s+(\d+).*?", msg[pos+3])
            #print("Unit temperature [deg]: ", unit_temp.group(1))
            self.unit_temp_deg = float(unit_temp.group(1))
            
        parse_read(resp)
	
    
    

if __name__ == "__main__":
    # TEST
    edfa = OptiLabEDFA()
    edfa.set_bias(250)
    edfa.turn_on()
    edfa.turn_off()
    edfa.read()
    edfa.disconnect()
     
