#!TDS/usr/bin/env python3
# -*- coding: utf-8 -*-

from TrackDrawData import DEFAULT_PARAMS
from functools import partial
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np
import matplotlib
matplotlib.use("QT5Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class CanvasGrid(QWidget):
    """ Stores canvases which display information about current waveform """
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)

        mainGrid = QGridLayout()
        self.setLayout(mainGrid)
        mainGrid.setRowMinimumHeight(0, 80)
        mainGrid.setRowMinimumHeight(1, 300)
        mainGrid.setRowMinimumHeight(2, 120)
        mainGrid.setColumnMinimumWidth(0, 100)
        mainGrid.setColumnMinimumWidth(1, 300)

        mainGrid.setRowStretch(0, 4)
        mainGrid.setRowStretch(1, 20)
        mainGrid.setRowStretch(2, 6)
        mainGrid.setColumnStretch(0, 1)
        mainGrid.setColumnStretch(1, 7)

        self.wave_cv = WaveCanvas(self)
        self.stft_cv = STFTCanvas(self)
        self.spec_cv = SpecCanvas(self)
        self.f0_cv = F0Canvas(self)
        mainGrid.addWidget(self.wave_cv, 0, 1)
        mainGrid.addWidget(self.stft_cv, 1, 0)
        mainGrid.addWidget(self.spec_cv, 1, 1)
        mainGrid.addWidget(self.f0_cv, 2, 1)
        
        self.current_waveform = None
        self.current_fs = None
        
class trackCanvas(FigureCanvas):
    """
    Canvas object for animated canvases in TrackDraw 2016.
    
    Arguments:
        parent (CanvasGrid object) -- refers to parent CanvasGrid object, which
            is a subclass of QWidget
    
    Attributes:
        enabled (boolean) -- if True, tracks will be drawn. If not, they will
            still be properly stored, but will not be drawn.
        background -- background stored from copy_from_bbox operation
        tracks (list) -- contains canvas' current Line2D objects, which
            represent tracks.
        x_low (float) -- lower limit of plot in x-dimension
        x_high (float) -- upper limit of plot in x-dimension
        y_low (float) -- lower limit of plot in y-dimension
        y_high (float) -- upper limit of plot in y-dimension
        track_npoints (int) -- number of points in tracks
        locked_track (int) -- current locked track
        
    trackCanvas is a subclass of FigureCanvas to be used for all TrackDraw
    animated plots which display tracks. This will allow for easy creation
    of other similar canvas objects to allow for animated graphical input of
    parameters. Currently, only F0Canvas and SpecCanvas use this as a parent
    class.
    """    
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.hold(False)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        self.enabled = True
        self.background = None
        self.tracks = []
        self.x_low = 0
        self.x_high = 0
        self.y_low = 0
        self.y_high = 0
        self.track_npoints = DEFAULT_PARAMS.track_npoints
        self.locked_track = 0
        
    def clear(self):
        self.ax.clear()
        self.fig.canvas.draw()
        
    def getBackground(self):
        """ Grabs current background. """
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        
    def start(self, tracks):
        """ 
        Starts tracks. 
        
        Arguments:
            tracks (list) -- list of TrackDrawData.Track objects.
            
        Used whenever canvas is initialized, or when one needs a fresh empty background.
        """
        self.ax.clear()
        self.tracks = []
        self.ax.set_xlim(0, self.track_npoints - 1)
        self.ax.set_ylim(self.y_low, self.y_high)
        self.fig.canvas.draw()
        self.getBackground()
        for i in range(len(tracks)):
            self.tracks.append(self.ax.plot(tracks[i].points, color="blue",
                                          marker="o"))
        self.ax.set_xlim(0, self.track_npoints - 1)
        self.ax.set_ylim(self.y_low, self.y_high)
        self.updateCanvas(redraw=True)
        
    def mouse(self, event):
        """ Converts mouse coordinates in pixels to data coordinates. """
        x_loc, y_loc = self.ax.transData.inverted().transform((event.x, event.y))
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        # Only return if within plot limits
        if x_min < x_loc < x_max and y_min < y_loc < y_max:
            return(x_loc, y_loc)
        
    def updateCanvas(self, new_tracks=0, trackNo=0, redraw=False):
        """
        Animates canvas.
        
        Arguments:
            new_tracks (list) -- list of Track objects.
            trackNo (int) -- index of track which has been updated.
            redraw (boolean) -- if True, does not use new_track and trackNo
                arguments to change a track.
        
        First, the current background is restored. Then, if redraw is False,
        the trackNo-th track's y_data is changed to match the data found in 
        new_track. If self.enabled is True, the tracks are drawn. Finally, 
        the axes' clipbox is blitted to animate changes. 
        """
        self.ax.set_xlim(0, self.track_npoints - 1)
        self.ax.set_ylim(self.y_low, self.y_high)
        self.fig.canvas.restore_region(self.background)
        if redraw == False:
            self.tracks[trackNo][0].set_ydata(new_tracks[trackNo].points)
        if self.enabled:
            for i in range(len(self.tracks)):
                self.ax.draw_artist(self.tracks[i][0])
        self.fig.canvas.blit(self.ax.clipbox)
        

class WaveCanvas(FigureCanvas):
    """
    Contains waveform reflecting current analyzed/plotted waveform.
    
    Arguments:
        parent (CanvasGrid object) -- refers to parent CanvasGrid object, which
            is a subclass of QWidget.
        
    Attributes: 
        enabled (boolean) -- if True, wave is plotted.
        current_waveform (np.array) -- stores most recently plotted waveform.
        
    WaveCanvas stores the most recently plotted waveform and displays it if
    displayDock.waveCheckBox is checked. Whenever the current display option is
    changed (i.e. whenever displayDock's radio buttons to switch between synth
    and loaded are pressed) the new waveform is plotted on wavecanvas using the 
    plot_waveform method even if the waveform is empty or not to be displayed.
    This way, if the user checks waveCheckBox it will display the correct
    waveform even if the waveCheckBox was unchecked when the display option was
    switched.
    
    TODO -- replace with more generic subclass of figure canvas, like a generic
        subclass for non-animated plots? If it's worth it...
    """
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax  = self.fig.add_subplot(111)
        self.ax.hold(False)
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        self.fig.subplots_adjust(left=0.08, right=0.95) 
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        self.enabled = True
        self.current_waveform = None
        
    def clear(self):
        self.ax.clear()
        self.fig.canvas.draw()
        
    def plot_waveform(self, waveform):
        self.current_waveform = waveform
        try:
            if self.enabled == False:
                self.clear()
            else:
                self.ax.plot(waveform)
                self.fig.canvas.draw()
        except ValueError:
            return

            
class STFTCanvas(FigureCanvas):
    """
    Contains mag. spec. of small snippet of waveform around mouse cursor.
    
    Arguments:
        parent (CanvasGrid object) -- refers to parent CanvasGrid object, which
            is a subclass of QWidget.
    
    Attributes:
        background -- background stored from copy_from_bbox operation
        enabled (boolean) -- if True, STFT is plotted.
        stft (np.array) -- contains most recently plotted STFT
        stft_size (int) -- size of STFT frame in samples
        
    STFTCanvas is updated by the mouse() slot in Slots. A small chunk of the 
    current displayed/analyzed waveform is grabbed, centered on the current 
    x_loc of the mouse cursor and the magnitude spectrum of the chunk is 
    calculated and displayed (if the STFT checkbox is checked). Uses blitting
    to animate the plot efficiently.
    
    TODO -- consider ways to use trackCanvas as parent class, might make things
        easier and reduce code repetition? 
    """
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax  = self.fig.add_subplot(111)
        self.ax.hold(False)
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        self.fig.subplots_adjust(top=0.95, bottom=0.1)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        self.background = None
        self.enabled = True
        self.stft = None
        self.stft_size = DEFAULT_PARAMS.stft_size
        
    def start(self, restart=False):
        self.ax.clear()
        self.ax.set_xlim(-20, 40)
        self.ax.set_ylim(0, self.stft_size)
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        self.stft, = self.ax.plot(np.ones([self.stft_size])*-20, np.arange(self.stft_size))
        self.fig.canvas.draw()
        self.ax.set_xlim(-20, 40)
        self.ax.set_ylim(0, self.stft_size)
        if restart:
            self.update_stft(self.current_stft)
        
    def update_stft(self, new_stft=0):
        try:
            self.stft.set_xdata(new_stft[0:-1])
            self.current_stft = new_stft[0:-1]
            self.fig.canvas.restore_region(self.background)
            if self.enabled:
                self.ax.draw_artist(self.stft)
                self.fig.canvas.blit(self.ax.clipbox)
        except RuntimeError:
            pass

            
class SpecCanvas(trackCanvas):
    """
    Contains tracks reflecting formant frequencies and plots spectrograms.
    
    Arguments:
        See trackCanvas's doc string.
        
    Attributes:
        See trackCanvas's doc string.
        current_waveform (np.array) -- waveform corresponding to the most
            recently plotted waveform.
        current_fs (int) -- sampling rate in Hz corresponding to the most
            recently plotted waveform.
        y_high (int) -- modified from trackCanvas defaults, set as f/2 since
            spectrogram is to be plotted.
        nformant (int) -- just keeps track of current number of formants to be
            reflected in tracks. May be best to replace its functionality, need
            to change references to it in Slots. 
            
    SpecCanvas adds a number of attributes (and changes one default attribute)
    from its parent class, trackCanvas. It also adds a new method,
    plot_specgram(), which accepts data from TrackDraw about how to plot the
    spectrogram and then plots it and calls the right methods to make sure
    tracks are also still plotted. 
    
    TODO -- figure out why it's only plotting the first track on startup
    """
    def __init__(self, parent=None):
        trackCanvas.__init__(self, parent=parent)
        
        # Set SpecCanvas unique plot settings
        self.ax.set_xlabel("Time [s]")
        self.ax.set_ylabel("Frequency [Hz]")
        self.fig.subplots_adjust(left=0.08, top=0.95, right=0.95, bottom=0.1)
        
        # Initialize SpecCanvas unique attributes, or adjust defaults
        self.current_waveform = None
        self.current_fs = None
        self.y_high = DEFAULT_PARAMS.synth_fs/2
        self.nformant = DEFAULT_PARAMS.nformant
        
    def plot_specgram(self, x_right=1.0, waveform=0, fs=0, window_len=256, 
                      noverlap=0.5, window_type=np.hanning, tracks=0, 
                      restart=False):
        """
        Plots spectrogram on spec_cv
        
        Arguments:
            x_right (float) -- right limit in x-dimension, usually set to
                analyzed waveform's duration
            waveform (np.array) -- waveform to be analyzed in spectrogram
            fs (int) -- sampling rate in Hz
            window_len (int) -- length of window to be used in samples
            noverlap (int) -- proportion overlap to be used for windows
            window_type (window function) -- some type of window function from
                numpy.
            tracks (list) -- list of TrackDrawData.Track objects, used to
                redraw tracks after spectrogram is plotted.
            restart (boolean) -- if False, creates spectrogram based on input
                waveform/fs/duration/etc., if True, creates spectrogram based
                on previously used waveform/fs/duration/etc. cached from last
                call in current_waveform, current_fs
        
        plot_specgram() handles the task of plotting a spectrogram to the
        specCanvas based on input waveform/fs data or based on cached 
        waveform/fs data from the most recent call to plot_specgram(). The axes
        are temporarily set to values appropriate for the spectrogram, then the
        new background (containing the plotted spectrogram) is grabbed and axes
        are restored to a scale appropriate for all Track related features.
        
        TODO -- look into automatic zero-padding to fix scaling issues?
        TODO -- condense restart branches into one set of code
        TODO -- implement more clear system for setting limits and duration...
        """
        if restart == False:
            self.current_waveform = waveform
            self.current_fs = fs
            self.y_high = fs/2
            self.ax.clear()
            self.tracks = []
            self.ax.specgram(self.current_waveform, NFFT=window_len, Fs=self.current_fs,\
                             noverlap=int(window_len*noverlap), window=window_type(window_len), 
                             cmap=plt.cm.gist_heat)
            self.fig.canvas.draw()
            self.getBackground()
            for i in range(len(tracks)):
                self.tracks.append(self.ax.plot(tracks[i].points, color="blue", marker="o"))
            self.updateCanvas(redraw=True)
        elif restart == True:
            self.ax.clear()
            self.ax.specgram(self.current_waveform, NFFT=window_len, Fs=self.current_fs,\
                             noverlap=int(window_len*noverlap), window=window_type(window_len), 
                             cmap=plt.cm.gist_heat)
            self.fig.canvas.draw()
            self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
            self.updateCanvas(redraw=True)            
        

class F0Canvas(trackCanvas):
    """
    Contains track representing an F0 contour.
    
    Attributes:
        See trackCanvas' doc string.
        y_low (int) -- modified from trackCanvas, set to 90 as the lower margin
            for possible F0.
        y_high (int) -- modified from trackCavnas, set to 150 as the upper
            margin for possible F0. 
            
    F0Canvas simply changes a handful fo default values from trackCanvas, and
    otherwise functions as a typical trackCanvas. 
    """
    def __init__(self, parent=None):
        trackCanvas.__init__(self, parent=parent)
        
        # Set F0Canvas unique plot settings
        self.ax.xaxis.set_visible(False)
        self.fig.subplots_adjust(left=0.08, right=0.95) 
        
        # Initialize F0Canvas unique attributes, or adjust defaults
        self.y_low = 90
        self.y_high = 150
        
        
class DisplayDock(QDockWidget):
    """
    Contains interface/controls for all main window display parameters.
    
    Arguments:
        parent (?) -- ?

    Attributes:
        loadedRadioButton (QRadioButton) -- if checked, results in loaded
            waveform being the one displayed/analyzed/played.
        synthRadioButton (QRadioButton) -- if checked, results in synthed
            waveform being the one displayed/analyzed/played.
        waveCheckBox (QCheckBox) -- if checked, wave_cv is shown.
        STFTCheckBox (QCheckBox) -- if checked, stft_cv is shown.
        showFTCheckBox (QCheckBox) -- if checked, formant tracks are shown.
        clearButton (QButton) -- if pressed, all plots are cleared.
        track_npointsGroup (SliderGroup) -- slider which allows the number of
            points in the tracks to vary.
        trackBubbleSlider (SliderGroup) -- slider which allows the length of
            track bubbles to vary.
        trackBubbleCheckBox (QCheckBox) -- checkbox which allows track bubbles
            to be enabled or disabled.
        
            
    DisplayDock stores all user intefaces mechanisms that allow for changing
    display-related parameters. Most widgets here which are attributes are 
    attributes so they can be referred to/accessed in main or in 
    TrackDrawSlots.
    """
    def __init__(self, parent=None):
        super(DisplayDock, self).__init__(parent)
        self.setWindowTitle("Display settings")

        ### Select display group
        dispGroupBox = QGroupBox("Display")
        dispGroupVBox = QVBoxLayout()
        dispGroupBox.setLayout(dispGroupVBox)
        self.loadedRadioButton  = QRadioButton("Loaded sound")
        self.loadedRadioButton.setChecked(True)
        self.synthedRadioButton = QRadioButton("Synthesized sound")
        dispGroupVBox.addWidget(self.loadedRadioButton)
        dispGroupVBox.addWidget(self.synthedRadioButton)
        ###
        self.waveCheckBox = QCheckBox("Show waveform")
        self.waveCheckBox.setChecked(True)

        self.STFTCheckBox = QCheckBox("Show STFT")
        self.STFTCheckBox.setChecked(True)

        self.showFTCheckBox = QCheckBox("Show formant tracks")
        self.showFTCheckBox.setChecked(True)
        ### Clear plots button
        self.clearButton = QPushButton("Clear plots (Ctrl+L)")
        self.clearButton.setToolTip("Clear all plots")
        self.clearButton.setStatusTip("Clear all plots")
        ###
        
        ### track_npoints slider
        self.track_npointsGroup = SliderGroup(label="Number of track points:",
                units="points", minimum=20, maximum=80, stepDouble=False, 
                value=40)
        ###
        self.trackBubbleSlider = SliderGroup(label="Length of track bubbles:",
                units="Hz", minimum=50, maximum=500, stepDouble=False,
                value=DEFAULT_PARAMS.bubble_len)
        self.trackBubbleSlider.slider.setValue(DEFAULT_PARAMS.bubble_len)
        self.trackBubbleCheckBox = QCheckBox("Use track bubbles")
        self.trackBubbleCheckBox.setChecked(False)

        ### Set up main widget
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        mainVBox.addWidget(dispGroupBox)
        mainVBox.addWidget(self.waveCheckBox)
        mainVBox.addWidget(self.STFTCheckBox)
        mainVBox.addWidget(self.showFTCheckBox)
        mainVBox.addWidget(self.clearButton)
        mainVBox.addWidget(self.track_npointsGroup)
        mainVBox.addWidget(self.trackBubbleSlider)
        mainVBox.addWidget(self.trackBubbleCheckBox)
        mainVBox.addStretch()
        self.setWidget(mainWidget)


class AnalysisDock(QDockWidget):
    """
    Contains interface/controls for all analysis parameters.
    
    Arguments:
        parent (?) -- ?

    Attributes:
        methodComboBox (QComboBox) -- combobox which allows the user to select
            the type of analysis to be performed.
        specGroup (QGroupBox) -- groupbox containing the user interface for
            spectrogram parameters.
        windowComboBox (QComboBox) -- combobox which allows user to select the
            type of window to use in the spectrogram, part of specGroup.
        frameSizeGroup (SliderGroup) -- slider which allows user to select the
            length of the frame to use in the spectrogram, part of specGroup.
        overlapGroup (SliderGroup) -- slider which allows user to select the
            amount of overlap in the frames in the spectrogram, part of
            specGroup.
        thresholdGroup (SliderGroup) -- slider which allows user to select the
            amount of thresholding to perform on the magnitude spectra returned
            by the spectrogram function, part of specGroup.
        waveletGroup (QGroupBox) -- groupbox containing the user interface for
            wavelet analysis parameters.
        applyButton (QButton) -- button which applies any updated analysis.
            
    AnalysisDock stores all user intefaces mechanisms that allow for changing
    analysis-related parameters. Whenever the methodComboBox is changed, the
    dock displays the appropriate Group associated with the selected synthesis
    type (i.e. specGroup is displayed if Spectrogram is chosen as the analysis
    type). Most widgets here which are attributes are attributes so they can
    be referred to/accessed in main or in TrackDrawSlots.
    """
    def __init__(self, parent=None):
        super(AnalysisDock, self).__init__(parent)
        self.setWindowTitle("Analysis settings")

        ### Select analysis method group
        methodGroup = QWidget()
        methodVBox = QVBoxLayout()
        methodGroup.setLayout(methodVBox)
        resample_fs = DEFAULT_PARAMS.resample_fs
        resampleLabel = QLabel("Resample rate:  " + str(resample_fs) + " Hz")
        methodLabel = QLabel("Method:")
        self.methodComboBox = QComboBox()
        self.methodComboBox.addItems(["Spectrogram", "Wavelet"])
        self.methodComboBox.setCurrentIndex(0)
        self.methodComboBox.currentIndexChanged.connect(self.changeAnalysis)

        methodVBox.addWidget(resampleLabel)
        methodVBox.addSpacing(15)
        methodVBox.addWidget(methodLabel)
        methodVBox.addWidget(self.methodComboBox)
        ###

        ### Spectrogram settings group box
        self.specGroup = QGroupBox("Spectrogram settings")
        specVBox = QVBoxLayout()
        self.specGroup.setLayout(specVBox)

        windowGroup = QWidget()
        windowVBox = QVBoxLayout()
        windowGroup.setLayout(windowVBox)
        windowLabel = QLabel("Window function:")
        self.windowComboBox = QComboBox()
        self.windowComboBox.addItems(["Hamming", "Bartlett", "Blackman"])
        self.windowComboBox.setCurrentIndex(0)
        windowVBox.addWidget(windowLabel)
        windowVBox.addWidget(self.windowComboBox)
        
        self.frameSizeGroup = SliderGroup(label="Specgram Frame size:", units="samples",
                minimum=5, maximum=10, stepDouble=True, value=8)

        self.overlapGroup = SliderGroup(label="Specgram Frame overlap:", units="%",
                minimum=5, maximum=15, stepSize=5, value=10)

        self.thresholdGroup = SliderGroup(label="Specgram threshold:", units="dB",
                minimum=0, maximum=10, stepSize=1, value=3)
        
        self.stftSizeGroup = SliderGroup(label="STFT frame size:", units="samples",
                minimum=5, maximum=10, stepDouble=True, value=6)

        reassignCheckBox = QCheckBox("T-F reassignment")

        specVBox.addWidget(windowGroup)
        specVBox.addWidget(self.frameSizeGroup)
        specVBox.addWidget(self.overlapGroup)
        specVBox.addWidget(self.thresholdGroup)
        specVBox.addWidget(self.stftSizeGroup)
        specVBox.addWidget(reassignCheckBox)
        ###

        ### Wavelet settings group box
        self.waveletGroup = QGroupBox("Wavelet settings")
        waveletVBox = QVBoxLayout()
        self.waveletGroup.setLayout(waveletVBox)

        settingGroup = QWidget()
        settingVBox = QVBoxLayout(settingGroup)

        waveletVBox.addWidget(settingGroup)
        ###

        ### Apply button
        self.applyButton = QPushButton("Apply settings (Ctrl+R)")
        self.applyButton.setToolTip("Apply analysis settings")
        self.applyButton.setStatusTip("Apply analysis settings")
        ###

        ### Set up main widget
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        mainVBox.addWidget(methodGroup)
        mainVBox.addWidget(self.specGroup)
        mainVBox.addWidget(self.waveletGroup)
        self.waveletGroup.setHidden(True)
        mainVBox.addWidget(self.applyButton)
        mainVBox.addStretch()
        self.setWidget(mainWidget)
        ###

    @pyqtSlot()
    def changeAnalysis(self):
        currIdx = self.methodComboBox.currentIndex()
        if currIdx == 0:
            self.specGroup.setHidden(False)
            self.waveletGroup.setHidden(True)
        elif currIdx == 1:
            self.specGroup.setHidden(True)
            self.waveletGroup.setHidden(False)


class SynthesisDock(QDockWidget):
    """
    Contains interface/controls for all synthesis parameters.
    
    Arguments:
        parent (?) -- ?

    Attributes:
        methodComboBox (QComboBox) -- combobox allowing for selection of
            type of synthesis to be used
        nformantComboBox (QComboBox) -- combobox allowing for selection of
            number of formants to be synthesized.
        klattGroup (QGroupBox) -- groupbox for Klatt synthesizer parameters
        sineGroup (QGroupBox) -- groupbox for Sine wave synthesizer parameters
        avSlider (SliderGroup) -- slider to control AV (amplitude of voicing)
        avsSlider (SliderGroup) -- slider to control AVS (amplitude of quasi-
            sinusoidal voicing)
        FFBandwidthGroup (SliderGroup2) -- group of sliders to allow for
            selection formant bandwidths to be synthesized.
        synthButton (QButton) -- button for initiating synthesis using current
            settings.
            
    SynthesisDock stores all user intefaces mechanisms that allow for changing
    synthesis-related parameters. Whenever the methodComboBox is changed, the
    dock displays the appropriate Group associated with the selected synthesis
    type (i.e. klattGroup is displayed if Klatt 1980 is chosen as the synthesis
    type). Most widgets here which are attributes are attributes so they can
    be referred to/accessed in main or in TrackDrawSlots.
    """
    def __init__(self, parent=None):
        super(SynthesisDock, self).__init__(parent)
        self.setWindowTitle("Synthesis settings")

        ### Select synthesis method group
        methodGroup = QWidget()
        methodVBox = QVBoxLayout()
        methodGroup.setLayout(methodVBox)
        synthesis_fs = DEFAULT_PARAMS.synth_fs
        synthesisLabel = QLabel("Synthesis rate:  " + str(synthesis_fs) + " Hz")
        methodLabel = QLabel("Method:")
        self.methodComboBox = QComboBox()
        self.methodComboBox.addItems(["Klatt 1980", "Sine wave"])
        self.methodComboBox.setCurrentIndex(0)
        self.methodComboBox.currentIndexChanged.connect(self.changeSynthesis)

        methodVBox.addWidget(synthesisLabel)
        methodVBox.addSpacing(15)
        methodVBox.addWidget(methodLabel)
        methodVBox.addWidget(self.methodComboBox)
        ###

        nformantGroup = QWidget()
        nformantVBox = QVBoxLayout()
        nformantGroup.setLayout(nformantVBox)
        nformantLabel = QLabel("Number of formant tracks:")
        self.nformantComboBox = QComboBox()
        self.nformantComboBox.addItems(["1", "2", "3", "4", "5"])
        self.nformantComboBox.setCurrentIndex(4)
        nformantVBox.addWidget(nformantLabel)
        nformantVBox.addWidget(self.nformantComboBox)

        ### Klatt synthesis settings group box
        self.klattGroup = QGroupBox("Klatt synthesizer settings")
        klattVBox = QVBoxLayout()
        self.klattGroup.setLayout(klattVBox)

        voicingGroup = QWidget()
        voicingVBox = QVBoxLayout()
        voicingGroup.setLayout(voicingVBox)        
        
        self.amplitudeGroup = SliderGroup2(\
                keys=["Amplitude of voicing", "Amplitude of QS voicing",
                      "Amplitude of aspiration", "Amplitude of frication"],
                units=["dB", "dB", "dB", "dB"],
                mins=[0, 0, 0, 0],
                maxs=[40, 40, 40, 40],
                values=[DEFAULT_PARAMS.AV, DEFAULT_PARAMS.AVS,
                        DEFAULT_PARAMS.AH, DEFAULT_PARAMS.AF])

        self.FFBandwidthGroup = SliderGroup2(\
                keys=["F1 bandwidth", "F2 bandwidth", "F3 bandwidth",
                       "F4 bandwidth", "F5 bandwidth"],
                units=["Hz", "Hz", "Hz", "Hz", "Hz"],
                mins=[50, 50, 10, 50, 50],
                maxs=[250, 250, 250, 250, 250],
                values=[DEFAULT_PARAMS.BW[0], DEFAULT_PARAMS.BW[1],
                        DEFAULT_PARAMS.BW[2], DEFAULT_PARAMS.BW[3],
                        DEFAULT_PARAMS.BW[4]])

        klattVBox.addWidget(voicingGroup)
        klattVBox.addWidget(self.amplitudeGroup)
        klattVBox.addWidget(self.FFBandwidthGroup)
        ###

        ### Sine wave synthesis settings group box
        self.sineGroup = QGroupBox("Sine wave synthesizer settings")
        sineVBox = QVBoxLayout()
        self.sineGroup.setLayout(sineVBox)
        ###

        ### Synthesize button
        self.synthButton = QPushButton("Synthesize (Ctrl+Y)")
        self.synthButton.setToolTip("Synthesize using current settings")
        self.synthButton.setStatusTip("Synthesize using current settings")
        ###

        ### Set up main widget
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        mainVBox.addWidget(methodGroup)
        mainVBox.addWidget(nformantGroup)
        mainVBox.addWidget(self.klattGroup)
        mainVBox.addWidget(self.sineGroup)
        self.sineGroup.setHidden(True)
        mainVBox.addWidget(self.synthButton)
        mainVBox.addStretch()
        self.setWidget(mainWidget)
        ###

    @pyqtSlot()
    def changeSynthesis(self):
        currIdx = self.methodComboBox.currentIndex()
        if currIdx == 0:
            self.klattGroup.setHidden(False)
            self.sineGroup.setHidden(True)
        elif currIdx == 1:
            self.klattGroup.setHidden(True)
            self.sineGroup.setHidden(False)


class SliderGroup(QWidget):
    """
    A convenience widget for displaying slider information (minimum, maximum,
    and current value). Set stepDouble=True to create a slider that doubles
    its value each step.
    """
    def __init__(self, parent=None, label="", units="", minimum=1, maximum=99,
            value=1, stepSize=1, stepDouble=False, orientation=Qt.Horizontal):
        super(SliderGroup, self).__init__(parent)
        self.labelTxt = label
        self.unitsTxt = units
        self.stepSize = stepSize
        self.stepDouble = stepDouble
        if self.stepDouble:
            self.currValue = 2**value
            minLabel = QLabel(str(2**minimum))
            maxLabel = QLabel(str(2**maximum))
        else:
            self.currValue = self.stepSize*value
            minLabel = QLabel(str(self.stepSize*minimum))
            maxLabel = QLabel(str(self.stepSize*maximum))

        topContainer = QWidget()
        topHBox = QHBoxLayout()
        topContainer.setLayout(topHBox)
        topTxt = self.labelTxt + "  " + str(self.currValue)\
               + " " + self.unitsTxt
        self.topLabel = QLabel(topTxt)
        topHBox.addWidget(self.topLabel)

        botContainer = QWidget()
        botHBox = QHBoxLayout()
        botContainer.setLayout(botHBox)
        self.slider = QSlider(minimum=minimum, maximum=maximum,
                value=value, orientation=orientation)
        self.slider.valueChanged.connect(self.updateValueLabel)
        botHBox.addWidget(minLabel)
        botHBox.addWidget(self.slider)
        botHBox.addWidget(maxLabel)

        vBox = QVBoxLayout()
        self.setLayout(vBox)
        vBox.addWidget(topContainer)
        vBox.addWidget(botContainer)

    @pyqtSlot()
    def updateValueLabel(self):
        if self.stepDouble:
            self.currValue = 2**self.slider.value()
        else:
            self.currValue = self.stepSize*self.slider.value()
        newTopTxt = self.labelTxt + "  " + str(self.currValue)\
                  + " " + self.unitsTxt
        self.topLabel.setText(newTopTxt)

        
class SliderGroup2(QWidget):
    
    def __init__(self, keys, units, mins, maxs, values,
                 parent=None, slots=None):
        super(SliderGroup2, self).__init__(parent)
        SliderGrid = QGridLayout()
        self.setLayout(SliderGrid)

        self.keys = []
        self.sliders = {}
        self.callbacks = {}
        self.values = {}
        self.labelTxt = {}
        self.unitTxt = {}
        self.unitsTxt = {}
        self.topLabel = {}
        self.minLabel = {}
        self.maxLabel = {}
            
        for i in range(len(keys)):
            self.keys.append(keys[i])
            self.labelTxt[self.keys[i]] = self.keys[i] + ":"
            self.unitTxt[self.keys[i]] = units[i]
            self.values[self.keys[i]] = values[i]
            self.topLabel[self.keys[i]] = QLabel(self.labelTxt[self.keys[i]]
                                                 + " "
                                                 + str(self.values[self.keys[i]])
                                                 + " "
                                                 + self.unitTxt[self.keys[i]])
            self.minLabel[self.keys[i]] = QLabel(str(mins[i]))
            self.maxLabel[self.keys[i]] = QLabel(str(maxs[i]))
            self.sliders[self.keys[i]] = QSlider(minimum=mins[i], maximum=maxs[i],
                                                 value=values[i],
                                                 orientation=Qt.Horizontal)
            self.callbacks[self.keys[i]] = partial(self.updateValueLabel,
                                                    sliderKey=self.keys[i])
            self.sliders[self.keys[i]].valueChanged.connect(self.callbacks[self.keys[i]])
            self.sliders[self.keys[i]].setValue(self.values[self.keys[i]])
            SliderGrid.addWidget(self.topLabel[self.keys[i]], 2*i, 0, 1, 3)
            SliderGrid.addWidget(self.minLabel[self.keys[i]], 2*i + 1, 0)
            SliderGrid.addWidget(self.sliders[self.keys[i]], 2*i + 1, 1)
            SliderGrid.addWidget(self.maxLabel[self.keys[i]], 2*i + 1, 2)
            
    @pyqtSlot()
    def updateValueLabel(self, sliderKey=None):
        newTopTxt = self.labelTxt[sliderKey] + " " + str(self.sliders[sliderKey].value()) + " " + self.unitTxt[sliderKey]
        self.topLabel[sliderKey].setText(newTopTxt)

