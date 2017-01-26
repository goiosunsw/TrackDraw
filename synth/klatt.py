"""
@name:    klatt.py
@author:  Daniel R Guest
@date:    01/25/2017
@version: 0.5
@purpose: Klatt voice synthesizer and interface between TrackDraw 2016 and
          Klatt syntheiszer.

@overview:
    klatt.py is composed of three sections: klatt_make, klatt_interpolate,
    and KlattSynth.

    klatt_make is a function that accepts a Parameters object
    from the TrackDraw 2016 program and extracts necessary synthesis
    parameters. It then passes pre-processes certain parameters using
    the klatt_interpolate function before initializing a KlattSynth
    object. Once the KlattSynth object is initialized, klatt_make calls
    the necessary methods to verify proper operations and synthesize
    the speech waveform, which it then returns to TrackDraw 2016.

    klatt_interpolate is a function used by klatt_make to interpolate
    parameters as necessary to be more suitable for use by the KlattSynth
    object.

    klatt.py is based on Klatt (1980) and Klatt (1990), but with a number
    of extensions which increase its flexibility such as a swappable
    voicing source, variable sampling frequency, and swappable resonators.

    Klatt, D. (1980). Software for a cascade/parallel formant synthesizer.
    The Journal Of The Acoustical Society Of America, 67(3), 971.

    Klatt, D. and Klatt, L. (1990). Analysis, synthesis, and perception of
    voice quality variations among female and male talkers. The Journal of
    the Acoustical Society of America, 87(2), 820-857.
"""

import math
try:
    import numpy as np
except ImportError:
    print("NumPy not available. Please install NumPy and run TrackDraw again. Exiting now.")
    import sys
    sys.exit()


class NTVParameters:
    """
    Contains non-time-varying parameters for TrackDraw 2016.

    Just here for testing purposes!
    """
    def __init__(self, FS=10000,
                       N_FORM=5,
                       DUR=1):
        self.FS = FS
        self.DUR = DUR
        self.N_FORM = N_FORM
        self.N_SAMP = round(FS*DUR)


class TVParameters:
    """
    Contains time-varying parameters for TrackDraw 2016.

    Just here for testing purposes!
    """
    def __init__(self, F0=100,
                       FF=[500, 1500, 2500, 3500, 4500],
                       BW=np.array([50, 100, 100, 200, 250]),
                       AV=0,
                       AVS=0,
                       AH=0,
                       AF=0,
                       N_FORM=5,
                       FNZ=250,
                       SW=0,
                       FGP=0,
                       BGP=100,
                       FGZ=1500,
                       BGZ=6000,
                       FNP=250,
                       BNP=100,
                       BNZ=100,
                       track_npoints=80):
        self.F0 = F0
        self.FF = [Track(np.ones(track_npoints)*FF[i]) for i in range(N_FORM)]
        self.BW = [Track(np.ones(track_npoints)*BW[i]) for i in range(N_FORM)]
        self.AV = AV
        self.AVS = AVS
        self.AH = AH
        self.AF = AF
        self.FNZ = FNZ
        self.SW = SW
        self.FGP = FGP
        self.BGP = BGP
        self.FGZ = FGZ
        self.BGZ = BGZ
        self.FNP = FNP
        self.BNP = BNP
        self.BNZ = BNZ


class Track:
    """
    Class for organizing sequences of y coordinates.

    Just here for testing purposes
    """
    def __init__(self, points):
        self.points = points

    def __len__(self):
        return(len(self.points))

    def changeNoPoints(self, track_npoints):
        if len(self.points) == track_npoints:
            return
        elif len(self.points) > track_npoints:
            self.points = self.points[0:track_npoints]
        elif len(self.points) < track_npoints:
            final_value = self.points[-1]
            vector_to_be_appended = np.ones([track_npoints-len(self.points)])*final_value
            self.points = np.concatenate((self.points, vector_to_be_appended))


def fake_parms():
    """
    Temporary utility function to create fake set of parameters for testing.
    """
    tvp = TVParameters()
    ntvp = NTVParameters()
    return(tvp, ntvp)

def klatt_make(tvparams, ntvparams):
    """
    Extracts necessary parameters from TrackDraw 2016 Parameters object.

    Arguments:
        tvparams --- time-varying parameters object
        ntvparams --- non-time-varying parameters object
    """
    # Initialize synth
    synth = KlattSynth(ntvparams.N_SAMP)

    # Loop through all time-varying parameters, processing as needed
    for param in list(filter(lambda aname: not aname.startswith("_"),
                             dir(tvparams))):
        if param is "FF" or param is "BW":
            synth.params[param] = \
                [klatt_trackterpolate(getattr(tvparams, param)[i],
                                      ntvparams.N_SAMP)
                 for i in range(ntvparams.N_FORM)]
        else:
            synth.params[param] = klatt_trackterpolate(
                                getattr(tvparams,param), ntvparams.N_SAMP)
    # Loop through all non-time-varying parameters and load
    for param in list(filter(lambda aname: not aname.startswith("_"),
                             dir(ntvparams))):
        if param is "N_SAMP":
            continue
        else:
            synth.params[param] = getattr(ntvparams,param)
    return(synth)

def klatt_trackterpolate(track, n_samp):
    """
    Converts Track formatted data to vector of length n_samp.

    Right now, just interpolates linearly, but need to
    upgrade to take into account that filter coefs
    should not change every sample......
    """
    try:
        x = np.linspace(0, 1, len(track))
    except TypeError:
        return(np.ones(n_samp)*track)
    xvals = np.linspace(0, 1, n_samp)
    try:
        return(np.interp(xvals, x, track.points))
    except AttributeError:
        return(np.interp(xvals, x, track))


class KlattSynth(object):
    """
    Synthesizes speech ala Klatt 1980 and Klatt 1990.

    KlattSynth contains all necessary synthesis parameters in an attribute
    called params. The synthesis routine is organized around the concept of
    sections and components. Sections are objects with represent organizational
    abstractions drawn from the Klatt 1980 paper. Each section is composed of
    muiltiple components, which are small signal processing units like
    individual filters, resonators, amplifiers, etc. Each section has a run()
    method with performs the operation that section is designed to do. For
    example, a KlattVoice section's run() method generates a voicing waveform.

    KlattSynth's param attribute will need to be provided with paramters, there
    are no built-in defaults! Currently the only way to do so is to generate a
    KlattSynth object through the klatt_make function or to do so manually.
    Eventually, I will add other options...

    KlattSynth is not designed for real-time operation in any way.
    """
    def __init__(self, N_SAMP):
        # Create tags
        self.name = "Klatt 1988 Synthesizer"
        self.algorithm = "KLSYN88+"

        # Initialize synthesis parameters dictionary
        param_list = ["F0", "AV", "OQ", "SQ", "TL", "FL", # Source
                      "DI", "AVS", "AV", "AF", "AH",      # Source
                      "FF", "BW",                         # Formants
                      "FGP", "BGP", "FGZ", "BGZ",         # Glottal pole/zero
                      "FNP", "BNP", "FNZ", "BNZ",         # Nasal pole/zero
                      "FTP", "BTP", "FTZ", "BTZ",         # Tracheal pole/zero
                      "A2F", "A3F", "A4F", "A5F", "A6F",  # Frication parallel
                      "B2F", "B3F", "B4F", "B5F", "B6F",  # Frication parallel
                      "A1V", "A2V", "A3V", "A4V", "ATV",  # Voicing parallel
                      "ANV",                              # Voicing parallel
                      "SW", "INV_SAMP", "N_INV", "N_FORM",# Synth settings
                      "N_SAMP", "FS", "DT"]               # Synth settings
        self.params = {param: None for param in param_list}
        self.params["N_SAMP"] = N_SAMP

        # Initialize data vectors
        self.output = np.zeros(self.params["N_SAMP"])

        # Initialize sections
        self.voice = KlattVoice1980(self)
        # self.noise = KlattNoise(self)
        # self.cascade = KlattCascade(self, [self.voice, self.noise])
        # self.parallel = KlattParallel(self, [self.voice, self.noise])
        # self.radiation = KlattRadiation(self, [self.cascade, self.parallel])
        # self.output_module = KlattOutput(self, [self.radiation])

    def run(self):
        self.voice.run()
            #self.noise.run()
            #self.cascade.run()
            #self.radiation.run()
            #self.output_module.run()
        self.output[:] = self.voice.output[:]


class KlattSection:
    """
    Parent class for section-level objects in the TrackDraw synthesizer.
    """
    def __init__(self, master):
       self.master = master
       self.output = np.zeros(self.master.params["N_SAMP"])


class KlattVoice1980(KlattSection):
    """
    Generates a voicing waveform ala Klatt 1980.
    """
    def __init__(self, master):
        KlattSection.__init__(self, master)
        self.impulse = Impulse(master=self.master)

    def run(self):
        self.impulse.impulse_gen()
        self.output[:] = self.impulse.output[:]


class KlattComponent:
    """
    Parent class for component-level objects in the TrackDraw synthesizer.
    """
    def __init__(self, master, input_connect=None):
        self.master = master
        self.input = np.zeros(self.master.params["N_SAMP"])
        self.output = np.zeros(self.master.params["N_SAMP"])
        self.input_connect = input_connect

    def pull(self):
        """ Perpetuates signal from previous component to this component """
        self.input = np.zeros(self.master.params["N_SAMP"])
        self.output = np.zeros(self.master.params["N_SAMP"])
        self.input[:] = self.input_connect[0].output[:]


class Impulse(KlattComponent):
    """
    Klatt time-varying impulse generator.

    Calculates the length of a glottal pulse period in samples based on the
    current interval's sampling rate and F0 value, stores this value in
    glot_period. Then goes through each sample of the current interval to
    determine if glot_period samples have passed since the last glottal pulse,
    whose index is stored in Klatt_Synth as an attribute called last_glot_pulse.
    """
    def __init__(self, master):
        KlattComponent.__init__(self, master)
        self.last_glot_pulse = 0

    def impulse_gen(self):
        self.output = np.zeros(self.master.params["N_SAMP"])
        glot_period = np.round(self.master.params["FS"]
                            /self.master.params["F0"])
        for n in range(self.master.params["N_SAMP"]):
            if n - self.last_glot_pulse >= glot_period[n]:
                self.output[n] = 1
                self.last_glot_pulse = n
