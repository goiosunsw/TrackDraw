#!TDS/usr/bin/env python3
# -*- coding: utf-8 -*-

from TrackDrawData import DEFAULT_PARAMS
from functools import partial
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import matplotlib
matplotlib.use("QT5Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class CanvasGrid(QWidget):
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


class WaveCanvas(FigureCanvas):
    """
    WaveCanvas stores the most recently plotted waveform and displays it if
    displayDock.waveCheckBox is checked. Whenever the current display option is
    changed (i.e. whenever displayDock's radio buttons to switch between synth
    and loaded are pressed) the new waveform is plotted on wavecanvas using the 
    plot_waveform method even if the waveform is empty or not to be displayed.
    This way, if the user checks waveCheckBox it will display the correct
    waveform even if the waveCheckBox was unchecked when the display option was
    switched.
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
        
        self.locked = False
        self.current_waveform = None
        
    def clear(self):
        self.ax.clear()
        self.fig.canvas.draw()
        
    def plot_waveform(self, waveform):
        self.current_waveform = waveform
        if self.locked:
            self.clear()
        else:
            self.ax.plot(waveform)
            self.ax.set_xlim(0, len(waveform))
            self.fig.canvas.draw()

class STFTCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax  = self.fig.add_subplot(111)
        self.ax.hold(False)
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        self.fig.subplots_adjust(top=0.95, bottom=0.1)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)


class SpecCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax  = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time [s]")
        self.ax.set_ylabel("Frequency [Hz]")
        self.fig.subplots_adjust(left=0.08, top=0.95, right=0.95, bottom=0.1)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        self.tracks = []
        self.background = None
        self.n_form = 5
        self.locked_track = 0
        
    def start(self, tracks):
        self.ax.clear()
        self.tracks = []
        self.ax.set_xlim(0, DEFAULT_PARAMS.track_npoints-1)
        self.ax.set_ylim(0, 5000)
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        for i in range(self.n_form):
            self.tracks.append(self.ax.plot(tracks[i].points, color="blue", marker="o"))
        self.ax.set_xlim(0, DEFAULT_PARAMS.track_npoints-1)
        self.ax.set_ylim(0, 5000)
        self.fig.canvas.draw()
        
    def mouse(self, event):
        x_loc, y_loc = self.ax.transData.inverted().transform((event.x, event.y))
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()
        if xmin < x_loc < xmax and ymin < y_loc < ymax:
            return(x_loc, y_loc)
        
    def update_track(self, new_track=0, trackNo=0, redraw=0):
        if redraw == 0:
            self.fig.canvas.restore_region(self.background)
            self.tracks[trackNo][0].set_ydata(new_track)
            for i in range(self.n_form):
                self.ax.draw_artist(self.tracks[i][0])
            self.fig.canvas.blit(self.ax.clipbox)
        else:
            self.fig.canvas.restore_region(self.background)
            for i in range(self.n_form):
                self.ax.draw_artist(self.tracks[i][0])
            self.fig.canvas.blit(self.ax.clipbox)
        
    def plot_specgram(self, waveform, fs, window_len, window_type, tracks):
        self.ax.clear()
        self.tracks = []
        self.ax.specgram(waveform, NFFT=window_len, Fs=fs,\
                         noverlap=window_len*0.75, cmap=plt.cm.gist_heat)
        xmin, xmax = self.ax.get_xlim()
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        for i in range(self.n_form):
            self.tracks.append(self.ax.plot(tracks[i].points, color="blue", marker="o"))
        self.update_track(redraw=1)
        return(xmin, xmax)
        

class F0Canvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax  = self.fig.add_subplot(111)
        self.ax.hold(False)
        self.ax.xaxis.set_visible(False)
        self.fig.subplots_adjust(left=0.08, right=0.95) 
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        
        self.f0_track = None
        self.background = None
        
    def start(self, track):
        self.ax.clear()
        self.tracks = []
        self.ax.set_xlim(0, DEFAULT_PARAMS.track_npoints-1)
        self.ax.set_ylim(90, 150)
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)
        self.f0_track = self.ax.plot(track.points, color="blue", marker="o")
        self.ax.set_xlim(0, DEFAULT_PARAMS.track_npoints-1)
        self.ax.set_ylim(90, 150)
        self.fig.canvas.draw()
        
    def mouse(self, event):
        x_loc, y_loc = self.ax.transData.inverted().transform((event.x, event.y))
        xmin, xmax = self.ax.get_xlim()
        ymin, ymax = self.ax.get_ylim()
        if xmin < x_loc < xmax and ymin < y_loc < ymax:
            return(x_loc, y_loc)
        
    def update_track(self, new_track):
        self.fig.canvas.restore_region(self.background)
        self.f0_track[0].set_ydata(new_track)
        self.ax.draw_artist(self.f0_track[0])
        self.fig.canvas.blit(self.ax.clipbox)
        
        
class DisplayDock(QDockWidget):
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

        STFTCheckBox = QCheckBox("Show STFT")
        STFTCheckBox.setChecked(True)

        showFTCheckBox = QCheckBox("Show formant tracks")
        showFTCheckBox.setChecked(True)
        ### Clear plots button
        self.clearButton = QPushButton("Clear plots (Ctrl+L)")
        self.clearButton.setToolTip("Clear all plots")
        self.clearButton.setStatusTip("Clear all plots")
        ###
        
        ### Regrab Plots Button
        self.regrabButton = QPushButton("Regrab plots")
        ###

        ### Set up main widget
        mainWidget = QWidget()
        mainVBox = QVBoxLayout()
        mainWidget.setLayout(mainVBox)

        mainVBox.addWidget(dispGroupBox)
        mainVBox.addWidget(self.waveCheckBox)
        mainVBox.addWidget(STFTCheckBox)
        mainVBox.addWidget(showFTCheckBox)
        mainVBox.addWidget(self.clearButton)
        mainVBox.addWidget(self.regrabButton)
        mainVBox.addStretch()
        self.setWidget(mainWidget)


class AnalysisDock(QDockWidget):
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
        windowComboBox = QComboBox()
        windowComboBox.addItems(["Hanning", "Rectangular"])
        windowComboBox.setCurrentIndex(0)
        windowVBox.addWidget(windowLabel)
        windowVBox.addWidget(windowComboBox)


        frameSizeGroup = SliderGroup(label="Frame size:", units="samples",
                minimum=5, maximum=10, stepDouble=True, value=8)

        overlapGroup = SliderGroup(label="Frame overlap:", units="%",
                minimum=5, maximum=15, stepSize=5, value=10)

        thresholdGroup = SliderGroup(label="Threshold:", units="dB",
                minimum=0, maximum=10, stepSize=1, value=3)

        reassignCheckBox = QCheckBox("T-F reassignment")

        specVBox.addWidget(windowGroup)
        specVBox.addWidget(frameSizeGroup)
        specVBox.addWidget(overlapGroup)
        specVBox.addWidget(thresholdGroup)
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
        nformantComboBox = QComboBox()
        nformantComboBox.addItems(["1", "2", "3", "4", "5"])
        nformantComboBox.setCurrentIndex(4)
        nformantVBox.addWidget(nformantLabel)
        nformantVBox.addWidget(nformantComboBox)

        ### Klatt synthesis settings group box
        self.klattGroup = QGroupBox("Klatt synthesizer settings")
        klattVBox = QVBoxLayout()
        self.klattGroup.setLayout(klattVBox)

        voicingGroup = QWidget()
        voicingVBox = QVBoxLayout()
        voicingGroup.setLayout(voicingVBox)
        voicingLabel = QLabel("Voicing source:")
        self.voicingComboBox = QComboBox()
        self.voicingComboBox.addItems(\
                ["Pulse train", "Sinusoidal", "White noise",
                 "Liljencrants-Fant", "Rosenberg++"])
        self.voicingComboBox.setCurrentIndex(0)
        voicingVBox.addWidget(voicingLabel)
        voicingVBox.addWidget(self.voicingComboBox)

        F1BandwidthGroup = SliderGroup(label="F1 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)
        F2BandwidthGroup = SliderGroup(label="F2 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)
        F3BandwidthGroup = SliderGroup(label="F3 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)
        F4BandwidthGroup = SliderGroup(label="F4 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)
        F5BandwidthGroup = SliderGroup(label="F5 bandwidth:", units="Hz",
                minimum=5, maximum=20, value=10)

        FFBandwidthGroup = SliderGroup2(\
                labels=["F1 bandwidth:", "F2 bandwidth:", "F3 bandwidth:",
                       "F4 bandwidth:", "F5 bandwidth:"],
                units=["Hz", "Hz", "Hz", "Hz", "Hz"],
                mins=[5, 5, 5, 5, 5],
                maxs=[20, 20, 20, 20, 20],
                values=[10, 10, 10, 10, 10],
                stepSizes=[1, 1, 1, 1, 1],
                stepDoubles=[False, False, False, False, False])

        klattVBox.addWidget(voicingLabel)
        klattVBox.addWidget(voicingGroup)
        #klattVBox.addWidget(F1BandwidthGroup)
        #klattVBox.addWidget(F2BandwidthGroup)
        #klattVBox.addWidget(F3BandwidthGroup)
        #klattVBox.addWidget(F4BandwidthGroup)
        #klattVBox.addWidget(F5BandwidthGroup)
        klattVBox.addWidget(FFBandwidthGroup)
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
    """
    A convenience widget for displaying slider information (minimum, maximum,
    and current value). Set stepDouble=True to create a slider that doubles
    its value each step.
    """
    def __init__(self, labels, units, mins, maxs, values, stepSizes,
            stepDoubles, parent=None, slots=None):
        super(SliderGroup2, self).__init__(parent)
        SliderGrid = QGridLayout()
        self.setLayout(SliderGrid)

        self.sliders = []

        for i in range(len(labels)):
            self.stepSize = stepSizes[i]
            self.stepDouble = stepDoubles[i]
            if stepDoubles[i]:
                self.currValue = 2**values[i]
                minLabel = QLabel(str(2**mins[i]))
                maxLabel = QLabel(str(2**maxs[i]))
            else:
                self.currValue = self.stepSize*values[i]
                minLabel = QLabel(str(self.stepSize*mins[i]))
                maxLabel = QLabel(str(self.stepSize*maxs[i]))

            self.labelTxt = labels[i]
            self.unitsTxt = units[i]
            self.topLabel = QLabel(self.labelTxt + "  " + str(self.currValue)\
                          + " " + self.unitsTxt)
            self.botSlider = QSlider(minimum=mins[i], maximum=maxs[i],
                    value=values[i], orientation=Qt.Horizontal)
            self.botSlider.valueChanged.connect(self.updateValueLabel)

            SliderGrid.addWidget(self.topLabel,  2*i, 0, 1, 3)
            SliderGrid.addWidget(minLabel,  2*i + 1, 0)
            SliderGrid.addWidget(self.botSlider, 2*i + 1, 1)
            SliderGrid.addWidget(maxLabel,  2*i + 1, 2)

    @pyqtSlot()
    def updateValueLabel(self):
        if self.stepDouble:
            self.currValue = 2**self.botSlider.value()
        else:
            currValue = self.stepSize*self.botSlider.value()
        newTopTxt = self.labelTxt + "  " + str(self.currValue)\
                  + " " + self.unitsTxt
        self.topLabel.setText(newTopTxt)

