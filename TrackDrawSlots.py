#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import TrackDrawData as TDD
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import time
import sounddevice as sd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy import signal
from scipy.io import wavfile
import synth

class Slots:
    
    def __init__(self, master):
        self.master = master
    
    ##### File management slots ####
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
        if self.master.displayDock.loadedRadioButton.isChecked():
            self.master.cw.spec_cv.plot_specgram(TDD.LOADED_SOUND.dur,
                                                 TDD.LOADED_SOUND.waveform,
                                                 TDD.LOADED_SOUND.fs,
                                                 TDD.CURRENT_PARAMS.window_len,
                                                 TDD.CURRENT_PARAMS.noverlap,
                                                 TDD.CURRENT_PARAMS.window_type,
                                                 TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(TDD.LOADED_SOUND.waveform)
    
    @pyqtSlot()
    def audioSave(self, *arg, parent=None, **kwarg):
        fname = QFileDialog.getSaveFileName(parent, "Save the synthesized sound",
                "", "Wav files (*.wav)")
        if fname[0]:
            print(fname)
    ##### End file management slots #####
    
    
    ##### Misc slots #####
    @pyqtSlot()
    def helpAbout(self, *arg, parent=None, **kwarg):
        aboutText = """
                    <b>TrackDraw v0.2.0</b>\n
                    Copyright (c) 2016
                    """
        QMessageBox.about(parent, "About", aboutText)        
    ##### End misc slots #####
    
    
    ##### Display slots #####
    @pyqtSlot()
    def clearPlots(self, *arg, **kwarg):
        self.master.cw.wave_cv.clear()
        self.master.cw.spec_cv.start(TDD.TRACKS)
        
    @pyqtSlot()
    def enableTracks(self, *arg, **kwarg):
        if self.master.displayDock.showFTCheckBox.checkState() == 0:
            self.master.cw.spec_cv.enabled = False
        else:
            self.master.cw.spec_cv.enabled = True
        self.master.cw.spec_cv.update_track(redraw=1)        
        
    @pyqtSlot()
    def switchPlots(self, *arg, **kwarg):
        waveform, fs, dur = self.getCurrentWaveform()
        if len(waveform) == 1:
            self.master.cw.spec_cv.start(TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(waveform)
            self.master.cw.wave_cv.clear()
        else:
            self.master.cw.spec_cv.plot_specgram(dur, waveform, fs,
                    TDD.CURRENT_PARAMS.window_len,
                    TDD.CURRENT_PARAMS.noverlap,
                    TDD.CURRENT_PARAMS.window_type, TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(waveform)         
            
    @pyqtSlot()
    def enableWave(self, *arg, **kwarg):
        if self.master.displayDock.waveCheckBox.checkState() == 0:
            self.master.cw.wave_cv.enabled = False
        else:
            self.master.cw.wave_cv.enabled = True
        if self.master.cw.wave_cv.enabled == False:
            self.master.cw.wave_cv.clear()
        else:
            self.master.cw.wave_cv.plot_waveform(self.master.cw.wave_cv.current_waveform)
            
    @pyqtSlot()
    def changeNoTracks(self, curr_index, *arg, **kwarg):
        new_nformant = curr_index + 1
        if self.master.cw.spec_cv.nformant > new_nformant:
            TDD.TRACKS = TDD.TRACKS[0:new_nformant]
        elif self.master.cw.spec_cv.nformant < new_nformant:
            difference = abs(self.master.cw.spec_cv.nformant - new_nformant)
            if difference == 1:
                TDD.TRACKS.append(TDD.Track(np.ones([TDD.DEFAULT_PARAMS.track_npoints])*TDD.DEFAULT_PARAMS.FF[curr_index]))          
            elif difference > 1:
                old_index = self.master.cw.spec_cv.nformant
                for i in range(difference):
                    TDD.TRACKS.append(TDD.Track(np.ones([TDD.DEFAULT_PARAMS.track_npoints])*TDD.DEFAULT_PARAMS.FF[old_index+i]))
        # Need to update both spec_cv's nformant and current_param's nformant
        self.master.cw.spec_cv.nformant = new_nformant
        TDD.CURRENT_PARAMS.nformant = new_nformant
        waveform, fs, dur = self.getCurrentWaveform()     
        if len(waveform) == 1:
            self.master.cw.spec_cv.start(TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(waveform)
            self.master.cw.wave_cv.clear()
        else:
            self.master.cw.spec_cv.plot_specgram(dur, waveform, fs,
                    TDD.CURRENT_PARAMS.window_len,
                    TDD.CURRENT_PARAMS.noverlap,
                    TDD.CURRENT_PARAMS.window_type, TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(waveform)
            
    @pyqtSlot()
    def changeNoPoints(self, *arg, **kwarg):
        new_track_npoints = self.master.displayDock.track_npointsGroup.slider.value()
        # Need to update both spec_cv/f0_cv and current_param's nformant
        TDD.CURRENT_PARAMS.track_npoints = new_track_npoints
        self.master.cw.spec_cv.track_npoints = new_track_npoints
        self.master.cw.f0_cv.track_npoints = new_track_npoints
        for i in range(len(TDD.TRACKS)):
            TDD.TRACKS[i].changeNoPoints(new_track_npoints)
        TDD.F0_TRACK.changeNoPoints(new_track_npoints)
        waveform, fs, dur = self.getCurrentWaveform()  
        if len(waveform) == 1:
            self.master.cw.spec_cv.start(TDD.TRACKS)
            self.master.cw.f0_cv.start(TDD.F0_TRACK)
            self.master.cw.wave_cv.plot_waveform(waveform)
            self.master.cw.wave_cv.clear()
        else:
            self.master.cw.spec_cv.plot_specgram(dur, waveform, fs,
                    TDD.CURRENT_PARAMS.window_len,
                    TDD.CURRENT_PARAMS.noverlap,
                    TDD.CURRENT_PARAMS.window_type, TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(waveform)    
            self.master.cw.f0_cv.start(TDD.F0_TRACK)
            
    @pyqtSlot()
    def onResize(self, *arg, **kwarg):
        if self.master.displayDock.synthedRadioButton.isChecked():
            waveform = TDD.SYNTH_SOUND.waveform
        elif self.master.displayDock.loadedRadioButton.isChecked():
            waveform = TDD.LOADED_SOUND.waveform
        if len(waveform) > 1:
            self.master.cw.spec_cv.plot_specgram(TDD.TRACKS, restart=True)
            self.master.cw.f0_cv.start(TDD.F0_TRACK)
        else:
            self.master.cw.spec_cv.start(TDD.TRACKS)
            self.master.cw.f0_cv.start(TDD.F0_TRACK)
    ##### End display slots #####
    
    
    ##### Analysis slots #####
    @pyqtSlot()
    def applyAnalysis(self, *arg, **kwarg):
        self.master.cw.spec_cv.plot_specgram(window_len=TDD.CURRENT_PARAMS.window_len,
                                             window_type=TDD.CURRENT_PARAMS.window_type,
                                             noverlap=TDD.CURRENT_PARAMS.noverlap,
                                             tracks=TDD.TRACKS, restart=True)   
       
    @pyqtSlot()
    def changeWindow(self, curr_index, *arg, **kwarg):
        if curr_index == 0:
            TDD.CURRENT_PARAMS.window_type = np.hamming
        if curr_index == 1:
            TDD.CURRENT_PARAMS.window_type = np.bartlett
        if curr_index == 2:
            TDD.CURRENT_PARAMS.window_type = np.blackman
                        
    @pyqtSlot()
    def changeFrameSize(self, *arg, **kwarg):
        TDD.CURRENT_PARAMS.window_len = self.master.analysisDock.frameSizeGroup.currValue
               
    @pyqtSlot()
    def changeOverlap(self, *arg, **kwarg):
        TDD.CURRENT_PARAMS.noverlap = self.master.analysisDock.overlapGroup.currValue*0.01
    ##### End analysis slots #####
    
    
    ##### Synthesis slots #####
    @pyqtSlot()
    def changeSynth(self, curr_index, *arg, **kwarg):
        if curr_index == 0:
            TDD.CURRENT_PARAMS.synth_type = "Klatt 1980"
        if curr_index == 1:
            TDD.CURRENT_PARAMS.synth_type = "Sine wave"
            
    @pyqtSlot()
    def changeBW(self, *arg, **kwarg):
        for i in range(5):
            TDD.CURRENT_PARAMS.BW[i] = self.master.synthesisDock.FFBandwidthGroup.sliders[i].value()*5
        
    @pyqtSlot()
    def changeSource(self, curr_index, *arg, **kwarg):
        if curr_index == 0:
            TDD.CURRENT_PARAMS.voicing = "Full Voicing"
        if curr_index == 1:
            TDD.CURRENT_PARAMS.voicing = "QS Voicing"
        if curr_index == 2:
            TDD.CURRENT_PARAMS.voicing = "Noise"
            
    @pyqtSlot()
    def synthesize(self, *arg, **kwarg):
        TDD.CURRENT_PARAMS.F0 = TDD.F0_TRACK.points
        TDD.CURRENT_PARAMS.FF = np.zeros([TDD.CURRENT_PARAMS.track_npoints,
                                          TDD.CURRENT_PARAMS.nformant])
        for i in range(TDD.CURRENT_PARAMS.nformant):
            TDD.CURRENT_PARAMS.FF[:,i] = TDD.TRACKS[i].points
        if TDD.CURRENT_PARAMS.synth_type == "Klatt 1980":
            TDD.SYNTH_SOUND.waveform = synth.klatt.klatt_make(TDD.CURRENT_PARAMS)
        elif TDD.CURRENT_PARAMS.synth_type == "Sine wave":
            TDD.SYNTH_SOUND.waveform = synth.sine.sine_make(TDD.CURRENT_PARAMS)
        if self.master.displayDock.synthedRadioButton.isChecked():
            self.master.cw.spec_cv.plot_specgram(TDD.SYNTH_SOUND.dur,
                                                 TDD.SYNTH_SOUND.waveform,
                                                 TDD.SYNTH_SOUND.fs,
                                                 TDD.CURRENT_PARAMS.window_len,
                                                 TDD.CURRENT_PARAMS.noverlap,
                                                 TDD.CURRENT_PARAMS.window_type,
                                                 TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(TDD.SYNTH_SOUND.waveform)
    ##### End synthesis slots #####    
    
    
    ##### Track slots #####
    @pyqtSlot()
    def mouse(self, *arg, **kwarg):
        event = list(arg)[0]
        if event.button:
            try:
                plot = kwarg["plot"]
                target = kwarg["target"]
                wasClick = kwarg["wasClick"]
                x_loc, y_loc = plot.mouse(event)
                dist_to_x_pts = np.abs(np.linspace(0,TDD.CURRENT_PARAMS.track_npoints-1,TDD.CURRENT_PARAMS.track_npoints) - x_loc)
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
    ##### End track slots #####
    
    
    ##### Playback slots #####
    @pyqtSlot()
    def play(self):
        waveform, fs, dur = self.getCurrentWaveform()
        waveform = waveform/np.max(np.abs(waveform))*0.9
        sd.play(waveform, fs)
        time.sleep(dur)
    ##### End playback slots #####
    
    ##### Non-slots #####
    def getCurrentWaveform(self):
        if self.master.displayDock.synthedRadioButton.isChecked():
            waveform = TDD.SYNTH_SOUND.waveform
            fs = TDD.SYNTH_SOUND.fs
            dur = TDD.SYNTH_SOUND.dur
        elif self.master.displayDock.loadedRadioButton.isChecked():
            waveform = TDD.LOADED_SOUND.waveform
            fs = TDD.LOADED_SOUND.fs
            dur = TDD.SYNTH_SOUND.dur
        return(waveform, fs, dur)
    ##### End non-slots #####  