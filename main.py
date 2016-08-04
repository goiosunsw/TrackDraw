#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import TrackDrawWidgets as TDW
import TrackDrawSlots as TDS
import TrackDrawData as TDD
import sys
from functools import partial
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


__version__ = "0.2.0"


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.cw = TDW.CanvasGrid(self)
        self.setCentralWidget(self.cw)
        slots = TDS.Slots(master=self)

        ##### Callbacks #####
        # Callbacks created using functools.partial
        audioOpen = partial(slots.audioOpen, parent=self)
        audioSave = partial(slots.audioSave, parent=self)
        
        helpAbout = partial(slots.helpAbout, parent=self)
        
        clearPlots = partial(slots.clearPlots)
        switchPlots = partial(slots.switchPlots)
        enableWave = partial(slots.enableWave)
        enableTracks = partial(slots.enableTracks)
        enableSTFT = partial(slots.enableSTFT)
        changeNoTracks = partial(slots.changeNoTracks)
        self.onResize = partial(slots.onResize)
        changeNoPoints = partial(slots.changeNoPoints)
        
        applyAnalysis = partial(slots.applyAnalysis)
        changeWindow = partial(slots.changeWindow)
        changeFrameSize = partial(slots.changeFrameSize)
        changeOverlap = partial(slots.changeOverlap)
        changeSTFTSize = partial(slots.changeSTFTSize)
        
        synthesize = partial(slots.synthesize)
        changeBW = partial(slots.changeBW)
        changeSynth = partial(slots.changeSynth)
        changeAV = partial(slots.changeAV)
        changeAVS = partial(slots.changeAVS)
        changeAH = partial(slots.changeAH)
        
        play = partial(slots.play)
        ##### End callbacks setup #####
        
        ##### Menus #####
        # File menu
        fileMenuActions = [\
                self.createMenuAction("&Open a sound file...", 
                    audioOpen, QKeySequence.Open, None,
                    "Open a sound file"),
                self.createMenuAction("&Save synthesis...", audioSave,
                    QKeySequence.Save, None, "Save the synthesized sound file"),
                "|",
                self.createMenuAction("&Quit", self.close, "Ctrl+Q", None,
                    "Close TrackDraw")]
        self.fileMenu = self.menuBar().addMenu("&File")
        for action in fileMenuActions:
            if action == "|":
                self.fileMenu.addSeparator()
            else:
                self.fileMenu.addAction(action)
        # Analysis/Synthesis menu
        ASMenuActions = [\
                self.createMenuAction("C&lear plots", clearPlots, "Ctrl+L",
                    None, "Clear all plots"),
                self.createMenuAction("Apply analysis settings", applyAnalysis,
                    "Ctrl+R", None, "Apply analysis settings and refresh"),
                self.createMenuAction("S&ynthesize", synthesize,
                    "Ctrl+Y", None, "Synthesize using current settings"),
                self.createMenuAction("Play", play, "Ctrl+P", None,
                    "Play current displayed waveform")]
        self.ASMenu = self.menuBar().addMenu("A&nalysis/Synthesis")
        for action in ASMenuActions:
            self.ASMenu.addAction(action)
        # Help menu
        helpMenuActions = [\
                self.createMenuAction("&About", helpAbout,
                    tip="About TrackDraw")]
        self.helpMenu = self.menuBar().addMenu("&Help")
        for action in helpMenuActions:
            self.helpMenu.addAction(action)
        ##### End menu setup #####

        ##### Docks on the right hand side #####
        self.displayDock = TDW.DisplayDock(parent=self)
        self.displayDock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.displayDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.analysisDock = TDW.AnalysisDock(parent=self)
        self.analysisDock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.analysisDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.synthesisDock = TDW.SynthesisDock(parent=self)
        self.synthesisDock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.synthesisDock.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.addDockWidget(Qt.RightDockWidgetArea, self.displayDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.analysisDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.synthesisDock)
        self.tabifyDockWidget(self.displayDock, self.analysisDock)
        self.tabifyDockWidget(self.analysisDock, self.synthesisDock)

        self.setTabPosition(Qt.RightDockWidgetArea, 3)
        ##### End dock setup #####

        ##### Status bar #####
        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.sizeLabel)
        status.showMessage("Welcome to TrackDraw!", 5000)
        ##### End status bar setup #####
        
        ##### Combo boxes #####
        self.analysisDock.windowComboBox.activated.connect(changeWindow)
        self.synthesisDock.methodComboBox.activated.connect(changeSynth)
        self.synthesisDock.nformantComboBox.activated.connect(changeNoTracks)
        #### End Combo Boxes Setup #####
        
        ##### Sliders #####
        self.analysisDock.frameSizeGroup.slider.valueChanged.connect(changeFrameSize)
        self.analysisDock.overlapGroup.slider.valueChanged.connect(changeOverlap)
        for i in range(5):
            self.synthesisDock.FFBandwidthGroup.sliders[i].valueChanged.connect(changeBW)
        self.displayDock.track_npointsGroup.slider.valueChanged.connect(changeNoPoints)
        self.analysisDock.stftSizeGroup.slider.valueChanged.connect(changeSTFTSize)
        self.synthesisDock.avSlider.slider.valueChanged.connect(changeAV)
        self.synthesisDock.avsSlider.slider.valueChanged.connect(changeAVS)
        self.synthesisDock.ahSlider.slider.valueChanged.connect(changeAH)
        ##### End sliders setup #####
        
        ##### Buttons #####
        self.synthesisDock.synthButton.clicked.connect(synthesize)
        self.displayDock.clearButton.clicked.connect(clearPlots)
        self.analysisDock.applyButton.clicked.connect(applyAnalysis)
        self.displayDock.synthedRadioButton.toggled.connect(switchPlots)
        self.displayDock.waveCheckBox.stateChanged.connect(enableWave)
        self.displayDock.showFTCheckBox.stateChanged.connect(enableTracks)
        self.displayDock.STFTCheckBox.stateChanged.connect(enableSTFT)
        ##### End buttons setup #####
        
        ##### Canvases #####
        click_f0 = partial(slots.mouse, wasClick=True, plot=self.cw.f0_cv, target="F0")
        drag_f0 = partial(slots.mouse, wasClick=False, plot=self.cw.f0_cv, target="F0")
#        modifiers = QApplication.keyboardModifiers()
#        if modifiers == Qt.ShiftModifier:
        self.cw.f0_cv.fig.canvas.mpl_connect('button_press_event', click_f0)
        self.cw.f0_cv.fig.canvas.mpl_connect('motion_notify_event', drag_f0)
        
        click_ff = partial(slots.mouse, wasClick=True, plot=self.cw.spec_cv, target="FF")
        drag_ff = partial(slots.mouse, wasClick=False, plot=self.cw.spec_cv, target="FF")
        self.cw.spec_cv.fig.canvas.mpl_connect('button_press_event', click_ff)
        self.cw.spec_cv.fig.canvas.mpl_connect('motion_notify_event', drag_ff)
        ##### End canvases setup #####
    
    def createMenuAction(self, text, slot=None, shortcut=None, icon=None,
            tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action
        
    def resizeEvent(self, event):
        self.onResize()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TrackDraw")
    mainWindow = MainWindow()
    mainWindow.show()
    # Have to start canvasses here, otherwise they're the wrong size!!
    mainWindow.cw.spec_cv.start(TDD.TRACKS)
    mainWindow.cw.f0_cv.start(TDD.F0_TRACK)
    mainWindow.cw.stft_cv.start()
    app.exec_()


main()

