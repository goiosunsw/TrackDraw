#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import TrackDrawData as TDD
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import sounddevice as sd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy import signal
from scipy.io import wavfile
import synth

class Slots:
    
    def __init__(self, master):
        self.master = master
        
    @pyqtSlot()
    def audioOpen(self, *arg, parent=None, **kwarg):
        fname = QFileDialog.getOpenFileName(parent, "Open a wave file", "",
                "Wav files (*.wav)")
        if fname[0]:
            old_fs, x = wavfile.read(fname[0])
            new_fs = TDD.DEFAULT_PARAMS.resample_fs
            new_n  = round(new_fs/old_fs*len(x))
            new_x  = signal.resample(x, new_n)
            TDD.LOADED_SOUND.waveform = new_x
            TDD.LOADED_SOUND.fs = new_fs
    
    
    @pyqtSlot()
    def audioSave(self, *arg, parent=None, **kwarg):
        fname = QFileDialog.getSaveFileName(parent, "Save the synthesized sound",
                "", "Wav files (*.wav)")
        if fname[0]:
            print(fname)
    
    
    @pyqtSlot()
    def helpAbout(self, *arg, parent=None, **kwarg):
        aboutText = """
                    <b>TrackDraw v0.2.0</b>\n
                    Copyright (c) 2016
                    """
        QMessageBox.about(parent, "About", aboutText)
    
    
    @pyqtSlot()
    def clearPlots(self, *arg, **kwarg):
        print(TDD.F0_TRACK.points)
    
    
    @pyqtSlot()
    def applyAnalysis(self, *arg, **kwarg):
        print(0)
    
    
    @pyqtSlot()
    def synthesize(self, *arg, **kwarg):
        TDD.CURRENT_PARAMS.F0 = TDD.F0_TRACK.points
        TDD.CURRENT_PARAMS.FF = np.zeros([TDD.CURRENT_PARAMS.track_npoints,
                                          TDD.CURRENT_PARAMS.n_form])
        for i in range(TDD.CURRENT_PARAMS.n_form):
            TDD.CURRENT_PARAMS.FF[:,i] = TDD.TRACKS[i].points
        TDD.SYNTH_SOUND.waveform = synth.klatt.klatt_make(TDD.CURRENT_PARAMS)
        if self.master.displayDock.synthedRadioButton.isChecked():
            self.master.cw.spec_cv.plot_specgram(TDD.SYNTH_SOUND.waveform, TDD.SYNTH_SOUND.fs, 512, "type", TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(TDD.SYNTH_SOUND.waveform)
        
        
    @pyqtSlot()
    def mouse(self, *arg, **kwarg):
        event = list(arg)[0]
        if event.button:
            try:
                plot = kwarg["plot"]
                target = kwarg["target"]
                wasClick = kwarg["wasClick"]
                x_loc, y_loc = plot.mouse(event)
                dist_to_x_pts = np.abs(np.linspace(0,TDD.DEFAULT_PARAMS.track_npoints-1,TDD.DEFAULT_PARAMS.track_npoints) - x_loc)
                nearest_x_idx = dist_to_x_pts.argmin()
                if target == "F0":
                    TDD.F0_TRACK.points[nearest_x_idx] = y_loc
                    plot.update_track(TDD.F0_TRACK.points)
                elif target == "FF":
                    if wasClick == True:
                        y_coords_at_nearest_x = np.array([track.points[nearest_x_idx] for track in TDD.TRACKS])
                        dist_to_y_pts = np.abs(y_coords_at_nearest_x - y_loc)
                        trackNo = dist_to_y_pts.argmin()
                        TDD.TRACKS[trackNo].points[nearest_x_idx] = y_loc
                        plot.update_track(TDD.TRACKS[trackNo].points, trackNo)
                        plot.locked_track = trackNo
                    elif wasClick == False:
                        TDD.TRACKS[plot.locked_track].points[nearest_x_idx] = y_loc
                        plot.update_track(TDD.TRACKS[plot.locked_track].points, plot.locked_track)
            except TypeError:
                pass
            
            
    @pyqtSlot()
    def regrabPlots(self, *arg, **kwarg):
        self.master.cw.spec_cv.start()
        self.master.cw.f0_cv.start()
        
        
    @pyqtSlot()
    def switchPlots(self, *arg, **kwarg):
        if self.master.displayDock.synthedRadioButton.isChecked():
            waveform = TDD.SYNTH_SOUND.waveform
            fs = TDD.SYNTH_SOUND.fs
        elif self.master.displayDock.loadedRadioButton.isChecked():
            waveform = TDD.LOADED_SOUND.waveform
            fs = TDD.LOADED_SOUND.fs
        if len(waveform) == 1:
            self.master.cw.spec_cv.start(TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(waveform)
            self.master.cw.wave_cv.clear()
        else:
            self.master.cw.spec_cv.plot_specgram(waveform, fs, 512, "type", TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(waveform)
    
    @pyqtSlot()
    def enableWave(self, *arg, **kwarg):
        if self.master.displayDock.waveCheckBox.checkState() == 0:
            self.master.cw.wave_cv.locked = True
        else:
            self.master.cw.wave_cv.locked = False
        if self.master.cw.wave_cv.locked == True:
            self.master.cw.wave_cv.clear()
        else:
            self.master.cw.wave_cv.plot_waveform(self.master.cw.wave_cv.current_waveform)
            
    def drawSpec(x):
        return 0
    
