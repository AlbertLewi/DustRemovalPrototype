"""
Library/Module for taking LUX data and inputting it in a CSV file with other relevant measurable data
The goal is for this to be usable across many different project files
Arduino Mega is used for data collection, yes overkill for one sensor,
LUX is calibrated compared to a phone app detector
"""
import pyfirmata2 as arduino
from pyfirmata2 import Arduino, util
import csv
import threading
import os
import time

#Set analog pin for reading

#Load board by passing a string comport in format "COM#"
def set_com(com):
    board = arduino.Arduino(com)
    # Start an iterator thread to handle data from the board
    it = util.Iterator(board)
    it.start()
    time.sleep(1)
    return board.get_pin('a:0:o')

#Define function that takes in board param and returns an averaged lux value
#pyfirmata2 uses threading and call backs
#Here 10 sample are collected with a timeout of 3, predefined variables
def collect_lux(pin, samples=10, timeout=3.0):

    if pin is None:
        print("Cannot find pin")
        return None

    luxlist = []

    #start thread event
    done = threading.Event()

    def _cb(data):
        # pyfirmata2 sometimes sends (pin, value) or raw value
        if isinstance(data, tuple) and len(data) >= 2:
            val = data[1]
        else:
            val = data

        # ignore warm-up None samples
        if val is None:
            return

        # val usually in 0.0-1.0 normalized range; convert to ADC 0-1023 if needed
        try:
            v = float(val)
        except Exception:
            return

        if 0.0 <= v <= 1.1:
            adc_counts = v * 1023.0
        else:
            # if the library already passes ADC counts
            adc_counts = v

        # guard against invalid/zero readings
        if adc_counts <= 0.0:
            return

        # compute rsensor and lux using your original formulas (avoid ZeroDivision)
        try:
            rsensor = (1023.0 - adc_counts) * 10.0 / adc_counts
            if rsensor <= 0.0:
                return
            lux = (1225.0 / rsensor) ** 1.0
        except Exception:
            return

        luxlist.append(lux)

        if len(luxlist) >= samples:
            done.set()

    # register callback & enable reporting (best-effort)
    try:
        pin.register_callback(_cb)
    except Exception:
        # fallback name if register_callback isn't available
        try:
            pin.callback = _cb
        except Exception as e:
            print("Failed to register callback:", e)
            return None

    try:
        pin.enable_reporting()
    except Exception:
        # ignore if not available
        pass

    # wait until we collected samples or timed out
    got = done.wait(timeout)

    # try disabling reporting and removing callback (best-effort cleanup)
    try:
        pin.disable_reporting()
    except Exception:
        pass

    try:
        # some versions may expose an unregister
        if hasattr(pin, "unregister_callback"):
            pin.unregister_callback(_cb)
        else:
            # attempt to remove attribute fallback
            if getattr(pin, "callback", None) == _cb:
                delattr(pin, "callback")
    except Exception:
        pass

    if len(luxlist) == 0:
        if not got:
            print("Timed out waiting for sensor samples.")
        return None

    # return average lux (float)
    return sum(luxlist) / len(luxlist)


#Define function to take in various data params
#Take in params of choosing, add more if applicable use the ones here as example, params should be numerical
#CSV by default should go into program folder, add path param if required to store csv in another dir
def csv_data(lux, num_of_particles, ratio):
    file_exists = os.path.isfile('luxdata.csv')

    with open('luxdata.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write header only if file is new
        if not file_exists:
            writer.writerow(["Lux", "# of Pixels Containing Particles", "Dust containing pixels/Total pixels"])

        # Write a new line of data every time
        writer.writerow([lux, num_of_particles, ratio])