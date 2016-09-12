#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
authors: A. Y. Cho and Daniel R Guest
date:    07/17/2016
version: 0.1.0
"""


import numpy as np
import matplotlib.mlab as mlab

class Sound:
    """
    Any loaded or synthesized sound.
    
    Arguments:
        fs (int) -- sample rate in Hz.
        waveform (np.array) -- signal of the sound.
        nchannels (int) -- number of channels in the sound file.

    Attributes:
        fs -- see above
        waveform -- see above
        nchannels -- see above
        nsamples (int) -- number of samples in signal.
        dur (float) -- length of signal in seconds.
        
    Used to store all the necessary elements to analyze or play back a sound. 
    Only the sound's waveform and fs need to be provided, everything else
    is derived or has default values.
    """
    def __init__(self, waveform, fs, nchannels=1):
        self.fs = fs
        self.waveform = waveform
        self.nchannels = nchannels

    @property
    def waveform(self):
        return self._waveform
    # Automatically update nsamples and dur whenever waveform changes
    @waveform.setter
    def waveform(self, val):
        self._waveform = val
        self.nsamples = len(self._waveform)
        self.dur = self.nsamples/self.fs


class Track:
    """
    Class for organizing sequences of y coordinates.
    
    TODO -- flesh out this doc string.
    """
    def __init__(self, points):
        self.points = points
        
    def changeNoPoints(self, track_npoints):
        if len(self.points) == track_npoints:
            return
        elif len(self.points) > track_npoints:
            self.points = self.points[0:track_npoints]
        elif len(self.points) < track_npoints:
            final_value = self.points[-1]
            vector_to_be_appended = np.ones([track_npoints-len(self.points)])*final_value
            self.points = np.concatenate((self.points, vector_to_be_appended))

        
class Parameters:
    """
    Contains parameters for TrackDraw 2016.
    
    TODO -- flesh out this doc string.
    """
    def __init__(self, F0=100,
                       FF=[500, 1500, 2500, 3500, 4500],
                       BW=np.array([50, 100, 100, 200, 250]),
                       AV=0,
                       AVS=0,
                       AH=0,
                       AF=0,
                       resample_fs=10000,
                       synth_fs=10000,
                       track_npoints=80,
                       window_len=256,
                       window_type=np.hamming,
                       noverlap=0.5,
                       dur=1,
                       inc_ms=5,
                       ENV=np.array([0, 1, 1, 1, 0]),
                       radiation=0,
                       synth_type="Klatt 1980",
                       nformant=5,
                       stft_size=64,
                       track_bubble=False,
                       bubble_len=250,
                       threshold=0):
        self.F0 = F0
        self.FF = FF
        self.BW = BW
        self.AV = AV
        self.AVS = AVS
        self.AH = AH
        self.AF = AF
        self.resample_fs = resample_fs
        self.synth_fs = synth_fs
        self.track_npoints = track_npoints
        self.window_len = window_len
        self.window_type = window_type
        self.noverlap = noverlap
        self.dur = dur
        self.inc_ms = inc_ms
        self.ENV = ENV
        self.radiation = radiation
        self.synth_type = synth_type
        self.nformant = nformant
        self.stft_size = stft_size
        self.track_bubble = track_bubble
        self.bubble_len = bubble_len
        self.threshold = threshold
        
        
DEFAULT_PARAMS = Parameters()
CURRENT_PARAMS = Parameters()
LOADED_SOUND = Sound(np.zeros([1]), DEFAULT_PARAMS.resample_fs, 1)
SYNTH_SOUND  = Sound(np.zeros([1]), DEFAULT_PARAMS.resample_fs, 1)

npoints = DEFAULT_PARAMS.track_npoints
F0 = DEFAULT_PARAMS.F0
allFF = DEFAULT_PARAMS.FF
F0_TRACK =  [Track(F0*np.ones([npoints]))]
TRACKS   = [Track(FF*np.ones([npoints])) for FF in allFF]

