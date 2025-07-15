# This file contains the function for running the eyebrain stimulus administration.
from time import sleep
from pyplr.pupil import PupilCore
from pyplr.utils import unpack_data_pandas

# imporivements that could be made:
# - be able to only capture one eye

def run_eyebrain_stimulus_administration(d, p, blue_intensity, red_intensity):
    """"Run the eyebrain stimulus administration protocol.

    This function administers light stimuli to the subject and records the pupil response.

    Args:
        d (stlab.SpectraTuneLab): The SpectraTuneLab object for controlling the light stimuli.
        p (PupilCore): The PupilCore object for recording pupil data
        blue_intensity (int): The intensity of the blue light stimulus, found by previous calibration.
        red_intensity (int): The intensity of the red light stimulus, found by previous calibration.
    
    """

    d.turn_off()
    sleep(2)
    # interstimulus time (seconds) = this variable + 5s due to sleep + processing
    ISI = 85 
    # total number of trials
    num_trials = 6 
    # total run time in seconds with appropriate offset to account for stim duration + sleeps
    run_time = ISI*num_trials + 5*num_trials + 30 

    # set warning time in seconds for when to give warning that a stimulus is due. 
    warning_time = 10

    # Start a new recording called "my_recording"
    p.command('R my_recording')

    # Wait a few seconds
    sleep(2)

    # Make an annotation for when the light comes on
    annotation = p.new_annotation('LIGHT_ON')

    # Start the .light_stamper(...) and .pupil_grabber(...)
    pgr_future_eye1 = p.pupil_grabber(topic='pupil.1.3d', seconds=run_time) # time here is TOTAL run time
    pgr_future_eye0 = p.pupil_grabber(topic='pupil.0.3d', seconds=run_time) # time here is TOTAL run time

    sleep(2)

    ##################################

    # Administer light stimulus #
    led_list = [3,9]*3

    for trial_num, led in enumerate(led_list, 1):
        # Inter-stimulus interval with warning (except for first trial)
        if trial_num > 1:
            # Sleep for most of ISI, then give warning
            sleep(ISI - warning_time)
            print(f"Trial {trial_num}/{num_trials}: Warning - stimulus in {warning_time} seconds")
            sleep(warning_time)
        
        # Stimulus administration
        intensities = [0]*10
        if led == 3:
            intensities[led] = int(blue_intensity)
            print(f"Trial {trial_num}: Administering BLUE stimulus (LED {led})")
        else:
            intensities[led] = int(red_intensity)
            print(f"Trial {trial_num}: Administering RED stimulus (LED {led})")
        
        lst_future = p.light_stamper(annotation=annotation, timeout=10)
        d.set_spectrum_a(intensities)
        sleep(1.)
        d.turn_off()
        
        print(f"Trial {trial_num} complete.")
    
    sleep(5)  # make sure there is extra time so that trials do not overlap
    
    ##################################

    # Wait for the futures
    while lst_future.running() or pgr_future_eye0.running() or pgr_future_eye1.running():
        print('Waiting for futures...')
        sleep(1)

    # End recording
    p.command('r')

    # Get the timestamp and pupil data
    timestamp = lst_future.result()[1]
    data_eye0 = unpack_data_pandas(pgr_future_eye0.result())
    data_eye1 = unpack_data_pandas(pgr_future_eye1.result())

    # timestamps are displayed in the output as well
    # Plot the PLR
    ax_0 = data_eye0['diameter_3d'].plot()
    ax_0.axvline(x=timestamp, color='k')
    ax_1 = data_eye1['diameter_3d'].plot()
    ax_1.axvline(x=timestamp, color='k')

    return data_eye0, data_eye1, timestamp