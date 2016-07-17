#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The model is initialized here. Put general description here.

authors: A. Y. Cho and Daniel R Guest
date:    07/15/2016
version: 0.1.0
"""

import numpy as np


class Model:
    """
    Contains:
        default_parms - Default parameters
        current_parms - Current parameters; expect this to change at runtime
        tracks - Container for the Track class instances
        loaded_sound - Sound object for holding the loaded sound file
        synth_sound  - Sound object for holding the synthesized sound
    """
    def __init__(self):
        self.default_parms = Parameters()
        self.current_parms = Parameters()

        # Create the default formant tracks
        default_FFs = self.default_parms.FF
        track_npoints = self.default_parms.track_npoints
        ones = np.ones(track_npoints)
        self.tracks = [Track(formant*ones) for formant in default_FFs]

        # Define the two sounds: load and synth
        default_fs = self.default_parms.fs
        self.loaded_sound = Sound(np.array([]), default_fs, 1)
        self.synth_sound  = Sound(np.array([]), default_fs, 1)


class Sound:
    """
    The Sound class now automatically updates n_samples whenever the waveform
    attribute changes. n_samples should never be changed individually.
    - Cho, 07/16
    """
    def __init__(self, waveform, fs, nchannels):
        self.waveform = waveform
        self.fs = fs
        self.nchannels = nchannels

    @property
    def waveform(self):
        return self._waveform
    # Automatically update n_samples and t whenever waveform changes
    @waveform.setter
    def waveform(self, val):
        self._waveform = val
        self.nsamples = len(self._waveform)


class Track:
    """
    Helpful docstring
    """
    def __init__(self, points):
        self.points = points


class Parameters:
    """
    Helpful docstring
    """
    def __init__(self, F0=100,\
                       FF=[800, 1600, 2400, 3200, 4000],\
                       BW=[20, 20, 20, 20, 20],\
                       fs=10000,\
                       track_npoints=40,\
                       voicing=0):
        self.F0 = F0
        self.FF = FF
        self.BW = BW
        self.fs = fs
        self.track_npoints = track_npoints
        self.voicing = voicing

