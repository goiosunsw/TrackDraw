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
        """
        Clears plots.
        
        TODO -- what is the point of this slot/button? If there is no replot
            button, why is there a clear button? 
        """
        self.master.cw.wave_cv.clear()
        self.master.cw.spec_cv.start(TDD.TRACKS)
        
    @pyqtSlot()
    def enableTracks(self, *arg, **kwarg):
        if self.master.displayDock.showFTCheckBox.checkState() == 0:
            self.master.cw.spec_cv.enabled = False
        else:
            self.master.cw.spec_cv.enabled = True
        self.master.cw.spec_cv.updateCanvas(redraw=1)        
        
    @pyqtSlot()
    def switchPlots(self, *arg, **kwarg):
        """
        Switches between displaying the loaded or synthed signal.
        
        TODO -- seems a little slow... look into profiling it... probably is
            just the amount of plotting that needs to be done, and
            matplotlib is really slow by default. maybe we can convert wave
            canvas to be animated as well if it would help.
        """
        waveform, fs, dur = self.getCurrentWaveform()
        self.pushDisplayUpdates(waveform, fs, dur)
            
    @pyqtSlot()
    def enableWave(self, *arg, **kwarg):
        """
        Enables or disables wave display when the wave checkbox is clicked.
        
        Simply sets the canvas' visibility status on detection of any change
        in the associated checkbox. 
        
        TODO -- figure out how to properly resize window on change
        TODO -- figure out how to best set some parameter in the canvas to 
            disable unnecessary calculations
        """
        if self.master.displayDock.waveCheckBox.checkState() == 0:
            self.master.cw.wave_cv.setHidden(True)
        else:
            self.master.cw.wave_cv.setHidden(False)
            
    @pyqtSlot()
    def enableSTFT(self, *arg, **kwarg):
        """
        Enables or disables STFT display when the STFT checkbox is clicked.

        TODO -- figure out how to properly resize window on change
        TODO -- figure out how to best set some parameter in the canvas to 
            disable unnecessary calculations        
        """
        if self.master.displayDock.STFTCheckBox.checkState() == 0:
            self.master.cw.stft_cv.setHidden(True)
            self.master.cw.stft_cv.enabled = False
        else:
            self.master.cw.stft_cv.setHidden(False)
            self.master.cw.stft_cv.enabled = True
            
    @pyqtSlot()
    def changeNoTracks(self, curr_index, *arg, **kwarg):
        """
        Changes the number of tracks when nformant combobox is activated.
        
        Arguments:
            curr_index (int) -- comes from combobox, indicates how many tracks
                are to be used. Number of tracks is curr_index + 1.
                
        changeNoTracks updates spec_cv's nformant and CURRENT_PARAMS's nformant
        and then properly removes or appends Track objects from/to TRACKS. Once
        the nformant variables and TRACKS are properly updated, the current
        waveform is grabbed and spec_cv/wave_cv are updated accordingly.
        """
        new_nformant = curr_index + 1
        if self.master.cw.spec_cv.nformant > new_nformant:
            TDD.TRACKS = TDD.TRACKS[0:new_nformant]
        elif self.master.cw.spec_cv.nformant < new_nformant:
            difference = abs(self.master.cw.spec_cv.nformant - new_nformant)
            if difference == 1:
                TDD.TRACKS.append(TDD.Track(np.ones([TDD.DEFAULT_PARAMS.track_npoints])*
                                                    TDD.DEFAULT_PARAMS.FF[curr_index]))          
            elif difference > 1:
                old_index = self.master.cw.spec_cv.nformant
                for i in range(difference):
                    TDD.TRACKS.append(TDD.Track(np.ones([TDD.DEFAULT_PARAMS.track_npoints])*
                                                        TDD.DEFAULT_PARAMS.FF[old_index+i]))
        # Need to update both spec_cv's nformant and current_param's nformant
        self.master.cw.spec_cv.nformant = new_nformant
        TDD.CURRENT_PARAMS.nformant = new_nformant
        waveform, fs, dur = self.getCurrentWaveform()     
        self.pushDisplayUpdates(waveform, fs, dur)
        
    @pyqtSlot()
    def enableBubble(self, *arg, **kwarg):
        if self.master.displayDock.trackBubbleCheckBox.isChecked():
            TDD.CURRENT_PARAMS.track_bubble = True
        elif self.master.displayDock.trackBubbleCheckBox.isChecked():
            TDD.CURRENT_PARAMS.track_bubble = False
        
    @pyqtSlot()
    def changeTracks(self, *arg, **kwarg):
        TDD.CURRENT_PARAMS.bubble_len = self.master.displayDock.trackGroup.sliders["Bubble size"].value()
        new_track_npoints = self.master.displayDock.trackGroup.sliders["Number of points"].value()
        if new_track_npoints != TDD.CURRENT_PARAMS.track_npoints:
            TDD.CURRENT_PARAMS.track_npoints = new_track_npoints
            self.master.cw.spec_cv.track_npoints = new_track_npoints
            self.master.cw.f0_cv.track_npoints = new_track_npoints
            for i in range(len(TDD.TRACKS)):
                TDD.TRACKS[i].changeNoPoints(new_track_npoints)
            TDD.F0_TRACK[0].changeNoPoints(new_track_npoints)
            waveform, fs, dur = self.getCurrentWaveform()  
            self.pushDisplayUpdates(waveform, fs, dur)
        
    @pyqtSlot()
    def onResize(self, *arg, **kwarg):
        """
        Called whenever a resize of the main window occurs, restarts all plots.
        
        On any resize of the main window, the current displayed waveform is
        grabbed and sent to the pushDisplayUpdates function, which restarts
        all animated plots so that their backgrounds are appropriately updated.
        """
        waveform, fs, dur = self.getCurrentWaveform()
        self.pushDisplayUpdates(waveform, fs, dur)
    ##### End display slots #####
    
    
    ##### Analysis slots #####
    @pyqtSlot()
    def applyAnalysis(self, *arg, **kwarg):
        """
        Updates spec_cv and stft_cv to reflect analysis parameter changes.
        """
        self.master.cw.spec_cv.plot_specgram(window_len=TDD.CURRENT_PARAMS.window_len,
                                             window_type=TDD.CURRENT_PARAMS.window_type,
                                             noverlap=TDD.CURRENT_PARAMS.noverlap,
                                             tracks=TDD.TRACKS, restart=True)   
        self.master.cw.stft_cv.start()
       
    @pyqtSlot()
    def changeWindow(self, curr_index, *arg, **kwarg):
        """
        Changes the window type to be used by the spectrogram.
        
        Arguments:
            curr_index (int) -- comes from the combobox, indicates which window
                is to be used. 
        
        Whenever the window type combobox is used, the window_type attribute of
        CURRENT_PARAMS is updated accordingly.
        
        TODO -- is there a better way to do this? Maybe we could use the text
            of the current index so that at least we can be sure we're 
            setting the right window? Or actually store the windows as data
            in the combobox?
        """
        if curr_index == 0:
            TDD.CURRENT_PARAMS.window_type = np.hamming
        if curr_index == 1:
            TDD.CURRENT_PARAMS.window_type = np.bartlett
        if curr_index == 2:
            TDD.CURRENT_PARAMS.window_type = np.blackman
                
    @pyqtSlot()
    def changeSpectrogram(self, *arg, **kwarg):
        TDD.CURRENT_PARAMS.window_len =\
            self.master.analysisDock.spectrogramGroup.sliders["Frame size"].value()
        TDD.CURRENT_PARAMS.noverlap =\
            self.master.analysisDock.spectrogramGroup.sliders["Frame overlap"].value()/100
        
    @pyqtSlot()
    def changeSTFTSize(self, *arg, **kwarg):
        """ Change size of frame for STFT display. """
        # Need to update both TDD and stft_cv's stftSize
        TDD.CURRENT_PARAMS.stft_size =\
                self.master.analysisDock.stftSizeGroup.currValue
        self.master.cw.stft_cv.stft_size =\
                self.master.analysisDock.stftSizeGroup.currValue
        self.master.cw.stft_cv.start(restart=True)
    ##### End analysis slots #####
    
    
    ##### Synthesis slots #####
    @pyqtSlot()
    def changeSynth(self, curr_index, *arg, **kwarg):
        """
        Change which synth is to be used by synthesize(). 
        
        Arguments:
            curr_index (int) -- comes from the combobox, indicates which synth
                is to be used.
                
        Whenever the synth type combobox is used, the synth_type attribute of
        CURRENT_PARAMS is updated accordingly.
        
        TODO -- is there a better way to do this? Maybe we could use the text
            of the current index so that at least we can be sure we're 
            setting the right synth? Or actually store the synths as data
            in the combobox?
        """
        if curr_index == 0:
            TDD.CURRENT_PARAMS.synth_type = "Klatt 1980"
        if curr_index == 1:
            TDD.CURRENT_PARAMS.synth_type = "Sine wave"
            
    @pyqtSlot()
    def changeBW(self, *arg, **kwarg):
        """
        Updates formant bandwidth values when sliders are used.
        
        TODO -- figure out where to store slider keys? 
        """
        keys = ["F1 bandwidth", "F2 bandwidth", "F3 bandwidth", "F4 bandwidth",
                "F5 bandwidth"]
        for i in range(5):
            TDD.CURRENT_PARAMS.BW[i] =\
                 self.master.synthesisDock.FFBandwidthGroup.sliders[keys[i]].value()
 
    @pyqtSlot()
    def changeAmplitude(self, *arg, **kwarg):
        keys = ["Amplitude of voicing", "Amplitude of QS voicing",
                "Amplitude of aspiration", "Amplitude of frication"]
        TDD.CURRENT_PARAMS.AV =\
            self.master.synthesisDock.amplitudeGroup.sliders[keys[0]].value()
        TDD.CURRENT_PARAMS.AVS =\
            self.master.synthesisDock.amplitudeGroup.sliders[keys[1]].value()
        TDD.CURRENT_PARAMS.AH =\
            self.master.synthesisDock.amplitudeGroup.sliders[keys[2]].value()
        TDD.CURRENT_PARAMS.AF =\
            self.master.synthesisDock.amplitudeGroup.sliders[keys[3]].value()
        
    @pyqtSlot()
    def synthesize(self, *arg, **kwarg):
        """
        Synthesizes waveform with current syntheis parameters.
        
        Synthesize updates CURRENT_PARAMS's F0 and FF information by extracting
        it from F0_TRACK and TRACKS, then synthesizes a waveform based on the
        current synthesis parameters and updates SYNTH_SOUND.waveform 
        accordingly. Then, if the synth radio button is checked, the changes
        to the waveform are reflected in the display.
        """
        TDD.CURRENT_PARAMS.F0 = TDD.F0_TRACK[0].points
        TDD.CURRENT_PARAMS.FF = np.zeros([TDD.CURRENT_PARAMS.track_npoints,
                                          TDD.CURRENT_PARAMS.nformant])
        for i in range(TDD.CURRENT_PARAMS.nformant):
            TDD.CURRENT_PARAMS.FF[:,i] = TDD.TRACKS[i].points
        if TDD.LOADED_SOUND.dur < 0.05: # random catch-all value
            TDD.CURRENT_PARAMS.dur = 1
        else:
            TDD.CURRENT_PARAMS.dur = TDD.LOADED_SOUND.dur
        
        if TDD.CURRENT_PARAMS.synth_type == "Klatt 1980":
            TDD.SYNTH_SOUND.waveform = synth.klatt.klatt_make(TDD.CURRENT_PARAMS)
        elif TDD.CURRENT_PARAMS.synth_type == "Sine wave":
            TDD.SYNTH_SOUND.waveform = synth.sine.sine_make(TDD.CURRENT_PARAMS)
        if self.master.displayDock.synthedRadioButton.isChecked():
            self.master.cw.spec_cv.plot_specgram(x_right=TDD.SYNTH_SOUND.dur,
                                                 waveform=TDD.SYNTH_SOUND.waveform,
                                                 fs=TDD.SYNTH_SOUND.fs,
                                                 window_len=TDD.CURRENT_PARAMS.window_len,
                                                 noverlap=TDD.CURRENT_PARAMS.noverlap,
                                                 window_type=TDD.CURRENT_PARAMS.window_type,
                                                 tracks=TDD.TRACKS)
            self.master.cw.wave_cv.plot_waveform(TDD.SYNTH_SOUND.waveform)
    ##### End synthesis slots #####    
    
    
    ##### Track slots #####
    @pyqtSlot()
    def mouse(self, *arg, **kwarg):
        """
        Performs TRACKS, F0_TRACK, or stft updates depending on canvas activity
        
        Arguments:
            event (PyQt Event) -- passed as default index 0 argument in *arg.
            plots (TrackDraw Canvas object) -- passed as "plot" in **kwarg,
                plot to be manipulated by mouse().
            target (string) -- passed as "target" in **kwarg, used to provide
                conditional functionality in mouse() based on whether one is
                manipulating the f0_cv or the spec_cv.
            wasClick (boolean) -- passed as "wasClick" in **kwarg, used to 
                provide different functionality based on whether current mouse
                action was a single click or a mouse drag movement.
            
        Whenever spec_cv or f0_cv record mouse activity, this slot handles that
        activity. If the mouse button is clicked on the spec_cv, the nearest
        vertex to the mouse is found and updated to the mouse's location in the
        y-dimension, and the index of the track to which the updated vertex 
        belongs is set as locked_track. If the mouse button is clicked on
        f0_cv, just the vertex update occurs. If the mouse is dragged on
        spec_cv, the same updating that occurs with a click occurs, except
        the track updated is always the locked_track from the most recent click.
        If the mouse is dragged on the f0_cv, the same thing happens as with a 
        click. Regardless of if the mouse button is down or not, the stft_cv is
        updated with an stft around the mouse's current location if possible. 
        
        The general pattern for track updates is that an x_loc and y_loc are
        received from the canvas if the mouse is within the bounds of the
        plotted area. The x_loc and y_loc received are in coordinates in terms
        of the tracks. Then, the nearest vertex is found, the track(s) data in
        TDD is updated, and the updated track data is sent back to the relevant
        canvas using the canvas' updateCanvas() method. 
        
        The general pattern for stft updates is that an x_loc and y_loc are
        received from the canvas if the mouse is within the bounds of the
        plotted area. The x_loc and y_loc received are in coordinates in terms
        of the tracks, so x_loc is converted to be in terms of the samples of 
        the displayed signal. Then, if an stft around that location is possible
        (i.e. if an stft has room to be calculated) it is calculated, converted
        to log scale, and passed to stft_cv via stft_cv's update_stft method.
        
        TODO -- add alternative functionality when SHIFT or CTRL keys are
            applied. See main.py for some helpful code to make those as well as
            the deprecated mouse_shift() slot below.
        TODO -- beautify the code, it's kinda ugly...
        TODO -- add track bubble features
        """
        event = list(arg)[0]
        x_loc = None
        y_loc = None
        plot=kwarg["plot"]
        target=kwarg["target"]
        wasClick=kwarg["wasClick"]
        try:
            x_loc, y_loc = plot.mouse(event)
        except TypeError:
            pass
        if event.button and x_loc != None:
            # Get correct tracks
            if target == "F0":
                tracks = TDD.F0_TRACK
            elif target == "FF":
                tracks = TDD.TRACKS
            # Find nearest x index
            dist_to_x_pts = np.abs(np.linspace(0,
                                   TDD.CURRENT_PARAMS.track_npoints-1,
                                   TDD.CURRENT_PARAMS.track_npoints)-x_loc)
            nearest_x_idx = dist_to_x_pts.argmin()
            # Grab y coordinates from all lines at that x index
            y_coords_at_nearest_x = np.array([track.points[nearest_x_idx]
                                              for track in tracks])
            # Find the nearest one
            dist_to_y_points = np.abs(y_coords_at_nearest_x - y_loc)
            trackNo = dist_to_y_points.argmin()
            # Update selected track if was a click
            if wasClick == True:
                plot.locked_track = trackNo
            # Check for track bubbles and handle that logic if necessary
            if TDD.CURRENT_PARAMS.track_bubble == True and len(tracks) > 1:
                if y_coords_at_nearest_x[plot.locked_track] < y_loc:
                    try:
                        val_above = y_coords_at_nearest_x[plot.locked_track + 1] 
                        difference = abs(val_above - y_loc)
                        if difference <= TDD.CURRENT_PARAMS.bubble_len:
                            tracks[plot.locked_track].points[nearest_x_idx] =\
                                    val_above - TDD.CURRENT_PARAMS.bubble_len
                        else:
                            tracks[plot.locked_track].points[nearest_x_idx] = y_loc
                    except IndexError:
                        tracks[plot.locked_track].points[nearest_x_idx] = y_loc
                if y_coords_at_nearest_x[plot.locked_track] > y_loc:
                    try:
                        val_below = y_coords_at_nearest_x[plot.locked_track - 1]
                        difference = abs(val_below - y_loc)
                        if difference <= TDD.CURRENT_PARAMS.bubble_len:
                            tracks[plot.locked_track].points[nearest_x_idx] =\
                                    val_below + TDD.CURRENT_PARAMS.bubble_len
                        else:
                            tracks[plot.locked_track].points[nearest_x_idx] = y_loc
                    except IndexError:
                        tracks[plot.locked_track].points[nearest_x_idx] = y_loc
            else:
                tracks[plot.locked_track].points[nearest_x_idx] = y_loc
            plot.updateCanvas(tracks, plot.locked_track)
        if self.master.cw.stft_cv.enabled == True:
            waveform, fs, dur = self.getCurrentWaveform()
            try:
                x_loc = x_loc/TDD.CURRENT_PARAMS.track_npoints
                x_loc = int(x_loc*dur*fs)
                if TDD.CURRENT_PARAMS.stft_size < x_loc < round(fs*dur)\
                        -TDD.CURRENT_PARAMS.stft_size:
                    waveform = waveform/np.max(np.abs(waveform))
                    magnitude = np.fft.rfft(waveform[x_loc-TDD.CURRENT_PARAMS.stft_size:x_loc
                                                     +TDD.CURRENT_PARAMS.stft_size])
                    magnitude = 20*np.log10(np.abs(magnitude))
                    self.master.cw.stft_cv.update_stft(magnitude)
            except TypeError:
                pass
        
    @pyqtSlot()
    def mouse_ctrl(self, *arg, **kwarg):
        """
        DEPRECATED -- to be integrated into mouse() above. Don't use!
        """
        event = list(arg)[0]
        x_loc = None
        y_loc = None
        # If mouse button is down, perform track updates
        if event.button:
            try:
                plot = kwarg["plot"]
                target = kwarg["target"]
                wasClick = kwarg["wasClick"]
                x_loc, y_loc = plot.mouse(event)
                dist_to_x_pts = np.abs(np.linspace(0,TDD.CURRENT_PARAMS.track_npoints-1,TDD.CURRENT_PARAMS.track_npoints) - x_loc)
                nearest_x_idx = dist_to_x_pts.argmin()
                if target == "F0":
                    if wasClick == True:
                        plot.locked_point = nearest_x_idx
                        TDD.F0_TRACK[0].points[nearest_x_idx] = y_loc
                        plot.update_track(TDD.F0_TRACK[0].points)
                    elif wasClick == False:
                        if plot.locked_point == nearest_x_idx:
                            TDD.F0_TRACK.points[nearest_x_idx] = y_loc
                            plot.update_track(TDD.F0_TRACK.points)
                        elif plot.locked_point != nearest_x_idx:
                            difference = abs(plot.locked_point - nearest_x_idx)
                            if plot.locked_point > nearest_x_idx:
                                TDD.F0_TRACK.points[nearest_x_idx:plot.locked_point] = np.linspace(y_loc, TDD.F0_TRACK.points[plot.locked_point], difference)
                            elif plot.locked_point < nearest_x_idx:
                                TDD.F0_TRACK.points[plot.locked_point:nearest_x_idx] = np.linspace(TDD.F0_TRACK.points[plot.locked_point], y_loc, difference)
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
        else:
            try:
                plot = kwarg["plot"]
                target = kwarg["target"]
                wasClick = kwarg["wasClick"]
                x_loc, y_loc = plot.mouse(event)
            except TypeError:
                pass
        # Regardless of if mouse button is down, perform stft update
        waveform, fs, dur = self.getCurrentWaveform()
        if x_loc == None:
            try:
                x_loc, y_loc = plot.mouse(event)
            except TypeError:
                pass
            # Meed to convert from track dimensions to regular dimensions
        try:
            x_loc = x_loc/TDD.CURRENT_PARAMS.track_npoints
            x_loc = int(x_loc*dur*fs)
            if TDD.CURRENT_PARAMS.stft_size < x_loc < round(fs*dur)-TDD.CURRENT_PARAMS.stft_size:
                waveform = waveform/np.max(np.abs(waveform))
                magnitude = np.fft.rfft(waveform[x_loc-TDD.CURRENT_PARAMS.stft_size:x_loc+TDD.CURRENT_PARAMS.stft_size])
                magnitude = 20*np.log10(np.abs(magnitude))
                self.master.cw.stft_cv.update_stft(magnitude)
        except TypeError:
            pass
    ##### End track slots #####
    
    
    ##### Playback slots #####
    @pyqtSlot()
    def play(self):
        """ Plays current displayed waveform after normalizing it. """
        waveform, fs, dur = self.getCurrentWaveform()
        waveform = waveform/np.max(np.abs(waveform))*0.9
        sd.play(waveform, fs)
        time.sleep(dur)
    ##### End playback slots #####
    
    
    ##### Non-slots #####
    def getCurrentWaveform(self):
        """
        Grabs currently displayed waveform data.
        
        Checks which display radio button (synth or loaded) is currently 
        checked. Then grabs the correct waveform, fs, and dur associated with
        the current displayed signal. 
        
        TODO -- replace with a better system. Right now, anytime changes occur
            to display/plotting parameters, the slot which handles that update
            calls this method to get the current waveform. In the long run,
            there needs to be some better way of doing this. 
        """
        if self.master.displayDock.synthedRadioButton.isChecked():
            waveform = TDD.SYNTH_SOUND.waveform
            fs = TDD.SYNTH_SOUND.fs
            dur = TDD.SYNTH_SOUND.dur
        elif self.master.displayDock.loadedRadioButton.isChecked():
            waveform = TDD.LOADED_SOUND.waveform
            fs = TDD.LOADED_SOUND.fs
            dur = TDD.LOADED_SOUND.dur
        return(waveform, fs, dur)
        
    def pushDisplayUpdates(self, waveform, fs, dur):
        """
        Updates all canvases to reflect any parameter changes.
        
        Arguments:
            waveform (np.array) -- current displayed waveform, usually grabbed
                by getCurrentWaveform() function.
            fs (int) -- sampling rate in Hz of current displayed waveform, 
                usually grabbed by getCurrentwavform() function.
            dur (float) -- duration in seconds of current displayed waveform, 
                usually grabbed in getCurrentWaveform() function. 
        
        This is a utility function called by various slots whenever they change
        elements pertaining to the canvases/display. It updates the display 
        in an appropriate way by calling the canvases' start() methods if the
        length of the waveform is 1 (i.e. the waveform is empty) or by calling
        the canvases' plot_***() methods if the waveform contains a sound.
        """
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
        
    ##### End non-slots #####  