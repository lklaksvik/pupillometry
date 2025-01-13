# this is copied exactly from the pupilLabsDebug.ipynb notebook, but turned function

from pyplr import stlab
from time import sleep
from pyplr.pupil import PupilCore
import matplotlib.pyplot as plt
from pyplr.utils import unpack_data_pandas


def execute_debug():
    # Set up stlab
    
    d = stlab.SpectraTuneLab(password='2294b16eea08a15a')
    d.turn_off()

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