#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@name:    sine.py
@author:  Daniel R Guest
@date:    07/20/2016
@version: 1.0
@purpose: Synthesize "sine wave" vowels.

@overview:
    Formant tracks provided by TrackDraw 2016 are used as frequency contours 
    for 5 sine waves. Output waveform is returned
"""
def sine_make(params):
    # Import
    import numpy as np
    from scipy.interpolate import interp1d
    import matplotlib.pyplot as plt
    
    # Extract necessary variables from TrackDraw 2016 Parameters object
    input_formants = params.FF
    input_envelope = params.ENV
    dur = params.dur
    Fs = params.synth_fs
    
    # Create necessary variables
    dt = 1/Fs
    n_formants = input_formants.shape[1]
    n_samples = round(dur*Fs)
    
    # Interpolate "formants"
    interpolated_formants = np.zeros([n_samples, n_formants])
    for i in range(n_formants):
        seq = np.arange(0, input_formants.shape[0])
        seq_new = np.linspace(0, input_formants.shape[0]-1, n_samples)
        temp = interp1d(seq, input_formants[:,i])(seq_new)
        interpolated_formants[:,i] = temp

    # Interpolate envelope
    seq = np.arange(0, input_envelope.shape[0])
    seq_new = np.linspace(0, input_envelope.shape[0]-1, n_samples)
    interpolated_envelope = interp1d(seq, input_envelope)(seq_new)
    
    # Generate sine waves
    waves = []
    for i in range(n_formants):
        phase = np.cumsum(2*np.pi*interpolated_formants[:,i]/Fs)
        waves.append(np.cos(phase))
    output_wave = np.zeros([n_samples])
    for i in range(n_formants):
        output_wave = output_wave + waves[i]
    output_wave = output_wave*interpolated_envelope
    return(output_wave)
        