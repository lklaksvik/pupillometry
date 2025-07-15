# this is copied exactly from the pupilLabsDebug.ipynb notebook, but turned function

from pyplr import stlab
from time import sleep
from pyplr.pupil import PupilCore
import matplotlib.pyplot as plt
from pyplr.utils import unpack_data_pandas
import pyplr.calibrate as calb
import pandas as pd
from importlib import reload


def calibrate_pupilcapture():
    """ Calibrate the PupilCapture for the eye capture.
    
    This function sets up the PupilCore, starts recording, and checks the 3D model.
    
    """
    # Set up stlab
    
    # not sure if this is needed, but it was in the original code. Will test and see
    # d = stlab.SpectraTuneLab(password='2294b16eea08a15a')
    # d.turn_off()

    p = PupilCore()

    p.command('R our_recording')

    sleep(1)

    p.command('r')

    p.check_3d_model()

    p = PupilCore()
    pgr_future = p.pupil_grabber(topic='pupil.1.3d', seconds=5)

    data = pgr_future.result()
    data[0]

    data = unpack_data_pandas(data, cols=['timestamp','diameter_3d'])
    ax = data['diameter_3d'].plot(figsize=(14,4))
    ax.set_ylabel('Pupil diameter (mm)')
    ax.set_xlabel('Pupil timestamp (s)')

    return p

def calibrate_spectral_sensitivity(d):
    """ Calibrate spectral sensitivity of the eye capture.

    Input csv (S2_corected_oo_spectra.csv) must be in format of:
    led | intensity | wavelength 1 (380) | wavelength 2 | ... | wavelength
    
    """
    # not sure if passing d object works, but it should. 

    # Reload calb to ensure the latest version is used
    reload(calb)

    # Create a calibration context with the provided CSV file
    cc = calb.CalibrationContext('S2_corrected_oo_spectra.csv', binwidth=1)

    # plot calibrated spectra
    _ = cc.plot_calibrated_spectra()

    # calculate the peak spectral sensitivity for each LED at its maximum intensity setting
    cc.lkp.xs(key=4095, level=1).idxmax(axis=1)

    blue_led = (3,) #blue_led = 3. Had to change because of object type
    red_led = (9,) #red_led = 9
    target_lux = 800

    # Find the required intensity setting of the blue led for 800 lux
    blue_intensity = (cc.lux.loc[blue_led].sub(target_lux)
                                        .abs()
                                        .idxmin())
    #                                     .values[0])

    # Find the intensity setting of the red led for 800 lux
    red_intensity = cc.match(match_led=blue_led,
                            match_led_intensity=blue_intensity,
                            target_led=red_led,
                            match_type='irrad')[1]
    
    # sets the blue and red light specifications
    blue_spec, red_spec = [0]*10, [0]*10
    blue_spec[pd.to_numeric(blue_led)[0]] = blue_intensity
    red_spec[pd.to_numeric(red_led)[0]] = red_intensity
    d.turn_off()

    return blue_intensity, red_intensity
