#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
authors: A. Y. Cho and Daniel R Guest
date:    08/14/2017
version: 0.2.0
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

    Arguments:
        points (numpy array): y coordinates

    Attributes:
        points (numpy array): see Arguments

    Methods:
        change_no_points: changes number of points in Track
    """
    def __init__(self, points):
        self.points = points

    def change_no_points(self, track_npoints):
        """
        Changes number of points in Track.

        Arguments:
            track_npoints (int): new number of points for Track
        """
        if len(self.points) == track_npoints:
            return
        elif len(self.points) > track_npoints:
            self.points = self.points[0:track_npoints]
        elif len(self.points) < track_npoints:
            final_value = self.points[-1]
            vector_to_be_appended = np.ones([track_npoints-len(self.points)])*final_value
            self.points = np.concatenate((self.points, vector_to_be_appended))

    def interpolate(self, out_len):
        """
        Returns numpy array containing interpolated Track values.

        Arguments:
            out_len (int): length of output numpy array
        """
        x = np.linspace(0, 1, len(self))
        xvals = np.linspace(0, 1, out_len)
        return(np.interp(xvals, x, self.points))

class TrackDrawParameters:
    """
    Simple container class for TrackDraw parameters.

    Arguments:
        resample_fs (int): Resample rate in Hz for input sounds
        synth_fs (int): Synthesis sample rate in Hz
        track_npoints (int): Number of points to use in Tracks
        window_len (int): Length of spectrogram windows in samples
        window_type (function): Callable which takes integer argument and
            returns window
        noverlap (float): Proportion of overlap between analysis windows in
            spectrogram
        dur (float): Duration of synthesized waveform in seconds
        nformant (int): Number of formants to use in synthesis algorithm
        track_bubble (boolean): Whether or not to use track bubbles, which
            forces Tracks to be certain distance from one another
        bubble_len (int): If track_bubble is true, sets size of bubbles
        threshold (float): Amount of thresholding to use on spectrogram

    TODO --- figure out how thresholding works and change docstring to reflect
    """
    def __init__(self, resample_fs=10000,
                       synth_fs=10000,
                       track_npoints=80,
                       window_len=256,
                       window_type=np.hamming,
                       noverlap=0.5,
                       dur=1,
                       nformant=5,
                       track_bubble=False,
                       bubble_len=250,
                       threshold=0):
        self.resample_fs = resample_fs
        self.synth_fs = synth_fs
        self.track_npoints = track_npoints
        self.window_len = window_len
        self.window_type = window_type
        self.noverlap = noverlap
        self.dur = dur
        self.nformant = nformant
        self.track_bubble = track_bubble
        self.bubble_len = bubble_len
        self.threshold = threshold

# Depreciated below... need to fix!

#DEFAULT_PARAMS = TrackDrawParameters()
#CURRENT_PARAMS = TrackDrawParameters()
#LOADED_SOUND = Sound(np.zeros([1]), DEFAULT_PARAMS.resample_fs, 1)
#SYNTH_SOUND  = Sound(np.zeros([1]), DEFAULT_PARAMS.resample_fs, 1)

#npoints = DEFAULT_PARAMS.track_npoints

#F0 = DEFAULT_PARAMS.F0
#allFF = DEFAULT_PARAMS.FF
#F0_TRACK =  [Track(F0*np.ones([npoints]))]
#TRACKS   = [Track(FF*np.ones([npoints])) for FF in allFF]

