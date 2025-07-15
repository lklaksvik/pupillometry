import matplotlib.pyplot as plt
from pyplr import graphing
from pyplr import preproc
import numpy as np
import pandas as pd
from copy import deepcopy
import seaborn as sns
from pyplr.plr import PLR

def smooth_eyebrain_data(data):
    """
    IMPORTANT: CODE IS KEPT IN ITS ORIGINAL FORM WHERE ONLY ONE EYE IS PROCESSED.
    Processes the data_processed from the eyebrain stimulus administration.
    
    Args:
        data_processed (data_processedFrame): data_processed for the first eye.
        data_processed_eye1 (data_processedFrame): data_processed for the second eye.
        timestamp (datetime): Timestamp of the data_processed collection.
        subject_id (str): Subject ID for naming files.
        subject_folder_path (str): Path to the subject's folder.
    
    Returns:
        None
    """

    # create a copy of data_processed to avoid modifying the original
    data_processed = data.copy()

    # Sampling frequency
    SAMPLE_RATE = 120

    # Pupil columns to analyse
    pupil_cols = ['diameter_3d', 'diameter']

    # Make figure for processing
    #f, axs = graphing.pupil_preprocessing(nrows=4, subject='Example')
    fig, axs = plt.subplots(5, sharex=True, figsize=(10,10))
    fig.suptitle('Subject PLR')

    # Plot the raw data_processed
    data_processed[pupil_cols].plot(title='Raw', ax=axs[0], legend=True)
    axs[0].legend(loc='center right', labels=['mm', 'pixels'])

    # Mask first derivative
    data_processed = preproc.mask_pupil_first_derivative(
        data_processed, threshold=3.0, mask_cols=pupil_cols)
    data_processed[pupil_cols].plot(
        title='Masked 1st deriv (3*SD)', ax=axs[1], legend=False)

    # Mask confidence
    data_processed = preproc.mask_pupil_confidence(
        data_processed, threshold=0.8, mask_cols=pupil_cols)
    data_processed[pupil_cols].plot(
        title='Masked confidence (<0.8)', ax=axs[2], legend=False)

    # Interpolate
    data_processed = preproc.interpolate_pupil(
        data_processed, interp_cols=pupil_cols)
    data_processed[pupil_cols].plot(
        title='Linear interpolation', ax=axs[3], legend=False)

    # Smooth
    data_processed = preproc.butterworth_series(
        data_processed, fields=pupil_cols, filt_order=3,
        cutoff_freq=4/(SAMPLE_RATE/2))
    data_processed[pupil_cols].plot(
        title='3rd order Butterworth filter with 4 Hz cut-off',
        ax=axs[4], legend=False)
    
    return data_processed

def get_stamps(timestamps):
    stamp1 = np.where(timestamps <= 500548.684061)[0][-1]
    stamp2 = np.where(timestamps <= 500640.209426)[0][-1]
    stamp3 = np.where(timestamps <= 500731.603996)[0][-1]
    stamp4 = np.where(timestamps <= 500823.042564)[0][-1]
    stamp5 = np.where(timestamps <= 500914.477428)[0][-1]
    stamp6 = np.where(timestamps <= 501005.93432)[0][-1]
    stamps = [stamp1, stamp2, stamp3, stamp4, stamp5, stamp6]
    return stamps

def create_multi_index_df(data, stamps, eye):
    onset_time = 1
    duration_time = 60
    offset = -60*onset_time # 60 sample rate, start 1s before light to get baseline
    duration = 60*duration_time  # 60 sample rate

    if eye == 0:
        side = 'left'
    elif eye == 1:
        side = 'right'

    # find the indexes of the event starts, and offset by sample count
    range_idxs = (
        np.searchsorted(data.index, stamps, side) + offset
    )
    range_duration = duration

    # make a hierarchical index for eye 0
    data["orig_idx"] = stamps.index
    midx = pd.MultiIndex.from_product(
        [list(range(len(stamps))), list(range(range_duration))],
        names=["event", "onset"],
    )

    # get the samples
    df = pd.DataFrame()
    idx = 0

    for start_idx in range_idxs:
        # get the start time and add the required number of indices
        end_idx = start_idx + range_duration - 1  # .loc indexing is inclusive
        if end_idx >= len(data):
            end_idx = len(data) - 1
        new_df = deepcopy(
            data.loc[data.index[start_idx] : data[end_idx]]
        )
        df = pd.concat([df, new_df])
        idx += 1
        
    # if there is an error that doesn't allow the new indices to be set (size mismatch), use the if loop below
    if (len(df)!= len(midx)):
        df_test = df
        temp_df = deepcopy(df.loc[df.index[-1] : df.index[-1]])
        while len(df) != len(midx):
            df= pd.concat([df, temp_df])

    df.index = midx
    print("Extracted ranges for {} events".format(len(stamps)))

    # Calculate baselines
    baselines = df.loc[:, range(0, -offset), :].mean(level=0)

    # New columns for percent signal change
    df = preproc.percent_signal_change(df, baselines, ['diameter_3d', 'diameter'])

    # convert index to time and add colour column
    df = _convert_index_to_time(df)

    return df

# to be used in create_multi_index_df
def _convert_index_to_time(df):
    ONSET_IDX = 60
    SAMPLE_RATE = 60
    new_onset = (df.index.get_level_values('onset').unique() - ONSET_IDX) / SAMPLE_RATE
    df.index = df.index.set_levels(levels=new_onset, level='onset')
    df["colour"] = ""
    for (event, onset) in df.index:
        if event%2==1:
            df["colour"][event,onset] = "red"
        else:
            df["colour"][event,onset] = "blue"
    return df


# function to compute PIPR
def compute_and_plot_PIPR(df, eye):
    # plot 
    fig, ax = plt.subplots(figsize=(6,4))
    for r in range(5):
        if (r==0 or r%2==0):
            c = 'blue'
        else:
            c = 'red'
        df.loc[r, 'diameter_pc'].plot(
            color=c, lw='.1', ax=ax, legend=False)

    # Now show the means
    avgs_df = (df.reset_index()
                    .groupby(['colour','onset'], as_index=False)
                    .mean())
    sns.lineplot(data=avgs_df, x='onset', y='diameter_pc', hue='colour',
                    palette={'blue':'b','red':'r'}, legend=False)

    # Tweak figures
    ax.axvspan(0, 1, color='k', alpha=.1)
    ax.axhline(0, 0, 1, color='k', ls='--')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Pupil diameter \n(%-change from baseline)')
    ax.set_title('Subject = {}'.format(df['id'][0][0]))
    plt.show()

    # now code to compute PIPR (?)
    pipr_time = 7 # measure PIPR at t=7s (6s after stimulus turned off)
    print("Onset:", avgs_df.loc[avgs_df["onset"] == pipr_time])
    blue_d_pipr = avgs_df["diameter_3d"][480]
    red_d_pipr = avgs_df["diameter_3d"][4080]
    blue_d_pipr_pc = avgs_df["diameter_3d_pc"][480]
    red_d_pipr_pc = avgs_df["diameter_3d_pc"][4080]
    pipr_diff = red_d_pipr - blue_d_pipr
    pipr_pc_diff = red_d_pipr_pc - blue_d_pipr_pc
    print(f"PIPR (Absolute Difference) {eye}: ", pipr_diff)
    print(f"PIPR (Percent Change) {eye}:", pipr_pc_diff)

    # this information is not saved anywhere though? 

    return avgs_df, fig

# absolutely no idea what this is for, but it was in the original code: says it's optional but will include anyhow
def plr(df):
    onset_time = 1
    duration_time = 60
    offset = -60*onset_time # 60 sample rate, start 1s before light to get baseline

    average_plr = df.mean(level=1)['diameter_3d'].to_numpy()
    plr = PLR(average_plr,
          sample_rate=60,
          onset_idx=-offset,
          stim_duration=1)
    fig = plr.plot(vel=True, acc=True, print_params=True)
    params = plr.parameters()
    return params, fig