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
    The Sound class now automatically updates n_samples whenever the waveform
    attribute changes. n_samples should never be changed individually.
    """
    def __init__(self, waveform, fs, nchannels):
        self.fs = fs
        self.waveform = waveform
        self.nchannels = nchannels

    @property
    def waveform(self):
        return self._waveform
    # Automatically update n_samples and t whenever waveform changes
    @waveform.setter
    def waveform(self, val):
        self._waveform = val
        self.nsamples = len(self._waveform)
        self.dur = self.nsamples/self.fs


class Track:
    """
    Helpful docstring
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
#            self.points = np.concatenate(self.points, np.ones([track_npoints-len(self.points)])*final_value)

        
class Parameters:
    """
    Helpful docstring
    """
    def __init__(self, F0=100,
                       FF=[500, 1500, 2500, 3500, 4500],
                       BW=np.array([50, 100, 100, 200, 250]),
                       resample_fs=10000,
                       synth_fs=10000,
                       track_npoints=40,
                       voicing="Full Voicing",
                       window_len=256,
                       window_type=np.hamming,
                       noverlap=0.5,
                       dur=1,
                       inc_ms=5,
                       ENV=np.array([0, 1, 1, 1, 0]),
                       radiation=0,
                       synth_type="Klatt 1980",
                       nformant=5,
                       stft_size=64):
        self.F0 = F0
        self.FF = FF
        self.BW = BW
        self.resample_fs = resample_fs
        self.synth_fs = synth_fs
        self.track_npoints = track_npoints
        self.voicing = voicing
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
        
        
DEFAULT_PARAMS = Parameters()
CURRENT_PARAMS = Parameters()
LOADED_SOUND = Sound(np.zeros([1]), DEFAULT_PARAMS.resample_fs, 1)
SYNTH_SOUND  = Sound(np.zeros([1]), DEFAULT_PARAMS.resample_fs, 1)

npoints = DEFAULT_PARAMS.track_npoints
F0 = DEFAULT_PARAMS.F0
allFF = DEFAULT_PARAMS.FF
F0_TRACK =  [Track(F0*np.ones([npoints]))]
TRACKS   = [Track(FF*np.ones([npoints])) for FF in allFF]

