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
                       DUR=1,
                       VER="1980"):
        self.FS = FS
        self.DUR = DUR
        self.N_FORM = N_FORM
        self.N_SAMP = round(FS*DUR)
        self.VER = VER


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
                       BGS=200,
                       A1=0,
                       A2=0,
                       A3=0,
                       A4=0,
                       A5=0,
                       AN=0,
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
        self.BGS = BGS
        self.A1 = A1
        self.A2 = A2
        self.A3 = A3
        self.A4 = A4
        self.A5 = A5
        self.AN = AN


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


def klatt_fake():
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
    if tvparams is None or ntvparams is None:
        tvparams, ntvparams = klatt_fake()

    # Initialize synth
    synth = KlattSynth()

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
        synth.params[param] = getattr(ntvparams,param)
    synth.setup()
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
    def __init__(self):
        """
        Initializes KlattSynth object.

        Creates name and tag which can be used by TrackDraw to display current
        synthesis type. Also creates the parameter list, but leaves it blank.
        """
        # Create tags
        self.name = "Klatt 1988 Synthesizer"
        self.algorithm = "KLSYN88+"

        # Initialize empty attributes
        self.output = None
        self.sections = None

        # Initialize synthesis parameters dictionary
        param_list = ["F0", "AV", "OQ", "SQ", "TL", "FL", # Source
                      "DI", "AVS", "AV", "AF", "AH",      # Source
                      "FF", "BW",                         # Formants
                      "FGP", "BGP", "FGZ", "BGZ", "BGS",  # Glottal pole/zero
                      "FNP", "BNP", "FNZ", "BNZ",         # Nasal pole/zero
                      "FTP", "BTP", "FTZ", "BTZ",         # Tracheal pole/zero
                      "A2F", "A3F", "A4F", "A5F", "A6F",  # Frication parallel
                      "B2F", "B3F", "B4F", "B5F", "B6F",  # Frication parallel
                      "A1V", "A2V", "A3V", "A4V", "ATV",  # Voicing parallel
                      "A1", "A2", "A3", "A4", "A5", "AN", # 1980 parallel
                      "ANV",                              # Voicing parallel
                      "SW", "INV_SAMP", "N_INV", "N_FORM",# Synth settings
                      "N_SAMP", "FS", "DT", "VER"]        # Synth settings
        self.params = {param: None for param in param_list}

    def setup(self):
        """
        Sets up Klatt synthesizer.

        Run after parameter values are set, creates output vector, derives
        necessary variables from input parameters, initializes sections.
        """
        # Initialize data vectors
        self.output = np.zeros(self.params["N_SAMP"])

        # Derive dt
        self.params["DT"] = 1/self.params["FS"]

        # Differential functiontioning based on version...
        if self.params["VER"] == "1980":
            # Initialize sections
            self.voice = KlattVoice1980(self)
            self.noise = KlattNoise1980(self)
            self.cascade = KlattCascade1980(self, [self.voice, self.noise])
            self.parallel = KlattParallel1980(self, [self.voice, self.noise])
            self.radiation = KlattRadiation(self, [self.cascade, self.parallel])
            self.output_module = KlattOutput(self, [self.radiation])
            self.sections = [self.voice, self.noise, self.cascade,
                             self.parallel, self.radiation, self.output_module]
        else:
            print("Sorry, versions other than Klatt 1980 are not supported.")

    def run(self):
        self.output[:] = np.zeros(self.params["N_SAMP"])
        for section in self.sections:
            section.run()
        self.output[:] = self.output_module.output[:]


##### BEGIN SECTIONS #####
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
        self.rgp = Resonator(master=self.master,
                             input_connect=[self.impulse])
        self.rgz = Resonator(master=self.master,
                             input_connect=[self.rgp], anti=True)
        self.rgs = Resonator(master=self.master,
                             input_connect=[self.rgp])
        self.av = Amplifier(master=self.master,
                            input_connect=[self.rgz])
        self.avs = Amplifier(master=self.master,
                             input_connect=[self.rgs])
        self.mixer = Mixer(master=self.master,
                           input_connect=[self.av, self.avs])

    def run(self):
        self.impulse.impulse_gen()
        self.rgp.resonate(ff=self.master.params["FGP"],
                          bw=self.master.params["BGP"])
        self.rgz.resonate(ff=self.master.params["FGZ"],
                          bw=self.master.params["BGZ"])
        self.rgs.resonate(ff=self.master.params["FGP"],
                          bw=self.master.params["BGS"])
        self.av.amplify(dB=self.master.params["AV"])
        self.avs.amplify(dB=self.master.params["AVS"])
        self.mixer.mix()
        self.output[:] = self.mixer.output[:]


class KlattNoise1980(KlattSection):
    """
    Generates noise ala Klatt 1980.
    """
    def __init__(self, master):
        KlattSection.__init__(self, master)
        self.noisegen = Noisegen(master=self.master)
        self.lowpass = Lowpass(master=self.master,
                               input_connect=[self.noisegen])
        self.amp = Amplifier(master=self.master,
                             input_connect=[self.lowpass])

    def run(self):
        self.noisegen.generate()
        self.lowpass.filter()
        self.amp.amplify(dB=-100)
        self.output[:] = self.amp.output[:]

class KlattCascade1980(KlattSection):
    """
    Simulates a vocal tract with a cascade of resonators.
    """
    def __init__(self, master, input_connect):
        KlattSection.__init__(self, master)
        self.ah = Amplifier(master=self.master,
                            input_connect=[input_connect[1]])
        self.mixer = Mixer(master=self.master,
                           input_connect=[input_connect[0], self.ah])
        self.rnp = Resonator(master=self.master,
                             input_connect=[self.mixer])
        self.rnz = Resonator(master=self.master,
                             input_connect=[self.rnp], anti=True)
        self.formants = []
        self.formants.append(Resonator(master=self.master, input_connect=[self.rnz]))
        previous_formant = self.formants[0]
        for form in range(1, self.master.params["N_FORM"]):
            self.formants.append(Resonator(master=self.master, input_connect=[previous_formant]))
            previous_formant = self.formants[form]

    def run(self):
        self.ah.amplify(dB=self.master.params["AH"])
        self.mixer.mix()
        self.rnp.resonate(ff=self.master.params["FNP"],
                          bw=self.master.params["BNP"])
        self.rnz.resonate(ff=self.master.params["FNZ"],
                          bw=self.master.params["BNZ"])
        for form in range(len(self.formants)):
            self.formants[form].resonate(ff=self.master.params["FF"][form],
                                         bw=self.master.params["BW"][form])
        self.output[:] = self.formants[-1].output[:]


class KlattParallel1980(KlattSection):
    """
    Simulates a vocal tract with a bank of parallel resonators.
    """
    def __init__(self, master, input_connect):
        KlattSection.__init__(self, master)
        self.af = Amplifier(master=self.master, input_connect=[input_connect[1]])
        self.a1 = Amplifier(master=self.master, input_connect=[input_connect[0]])
        self.r1 = Resonator(master=self.master, input_connect=[self.a1])
        self.first_diff = Firstdiff(master=self.master,
                                    input_connect=[input_connect[0]])
        self.mixer = Mixer(master=self.master,
                           input_connect=[self.first_diff, self.af])
        self.an = Amplifier(master=self.master, input_connect=[self.mixer])
        self.rnp = Resonator(master=self.master, input_connect=[self.an])
        self.a2 = Amplifier(master=self.master, input_connect=[self.mixer])
        self.r2 = Resonator(master=self.master, input_connect=[self.a2])
        self.a3 = Amplifier(master=self.master, input_connect=[self.mixer])
        self.r3 = Resonator(master=self.master, input_connect=[self.a3])
        self.a4 = Amplifier(master=self.master, input_connect=[self.mixer])
        self.r4 = Resonator(master=self.master, input_connect=[self.a4])
        self.a5 = Amplifier(master=self.master, input_connect=[input_connect[1]])
        self.r5 = Resonator(master=self.master, input_connect=[self.a5])
        # 6th formant currently not part of run routine! Not sure what values
        # to give to it... need to keep reading Klatt 1980.
        self.a6 = Amplifier(master=self.master, input_connect=[input_connect[1]])
        self.r6 = Resonator(master=self.master, input_connect=[self.a6])
        self.output_mixer = Mixer(master=self.master,
                                  input_connect=[self.r1, self.rnp, self.r2,
                                                 self.r3, self.r4, self.r5,
                                                 self.r6])

    def run(self):
        self.af.amplify(dB=self.master.params["AF"])
        self.a1.amplify(dB=self.master.params["A1"])
        self.r1.resonate(ff=self.master.params["FF"][0],
                         bw=self.master.params["BW"][0])
        self.first_diff.differentiate()
        self.mixer.mix()
        self.an.amplify(dB=self.master.params["AN"])
        self.rnp.resonate(ff=self.master.params["FNP"],
                          bw=self.master.params["BNP"])
        self.a2.amplify(dB=self.master.params["A2"])
        self.r2.resonate(ff=self.master.params["FF"][1],
                         bw=self.master.params["BW"][1])
        self.a3.amplify(dB=self.master.params["A3"])
        self.r3.resonate(ff=self.master.params["FF"][2],
                         bw=self.master.params["BW"][2])
        self.a4.amplify(dB=self.master.params["A4"])
        self.r4.resonate(ff=self.master.params["FF"][3],
                         bw=self.master.params["BW"][3])
        self.a5.amplify(dB=self.master.params["A5"])
        self.r5.resonate(ff=self.master.params["FF"][4],
                         bw=self.master.params["BW"][4])
        self.output_mixer.mix()
        self.output[:] = self.output_mixer.output[:]


class KlattRadiation(KlattSection):
    """
    Simulates the effect of radiation characteristic in the vocal tract.
    """
    def __init__(self, master, input_connect):
        KlattSection.__init__(self, master)
        self.mixer = Mixer(master=self.master,
                           input_connect=input_connect)
        self.radiation = Firstdiff(master=self.master,
                                   input_connect=[self.mixer])

    def run(self):
        self.mixer.mix()
        self.radiation.differentiate()
        self.output[:] = self.radiation.output[:]


class KlattOutput(KlattSection):
    def __init__(self, master, input_connect):
        KlattSection.__init__(self, master)
        self.normalizer = Normalizer(master=self.master,
                                     input_connect=input_connect)

    def run(self):
        self.normalizer.normalize()
        self.output[:] = self.normalizer.output[:]
##### END SECTIONS #####


##### START COMPONENTS #####
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


class Resonator(KlattComponent):
    """
    Klatt resonator.
    """
    def __init__(self, master, input_connect=None, anti=False):
        KlattComponent.__init__(self, master, input_connect)
        self.anti = anti

    def calc_coef(self, ff, bw):
        c = -np.exp(-2*np.pi*bw*self.master.params["DT"])
        b = (2*np.exp(-np.pi*bw*self.master.params["DT"])\
             *np.cos(2*np.pi*ff*self.master.params["DT"]))
        a = 1-b-c
        if self.anti:
            a_prime = 1/a
            b_prime = -b/a
            c_prime = -c/a
            return(a_prime, b_prime, c_prime)
        else:
            return(a, b, c)

    def resonate(self, ff, bw):
        self.pull()
        a, b, c = self.calc_coef(ff, bw)
        self.output[0] = a[0]*self.input[0]
        if self.anti:
            self.output[1] = a[1]*self.input[1] + b[1]*self.input[0]
            for n in range(2, self.master.params["N_SAMP"]):
                self.output[n] = a[n]*self.input[n] + b[n]*self.input[n-1] \
                                + c[n]*self.input[n-2]
        else:
            self.output[1] = a[1]*self.input[1] + b[1]*self.output[0]
            for n in range(2,self.master.params["N_SAMP"]):
                self.output[n] = a[n]*self.input[n] + b[n]*self.output[n-1] \
                                + c[n]*self.output[n-2]


class Impulse(KlattComponent):
    """
    Time-varying impulse generator.
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


class Amplifier(KlattComponent):
    """
    Simple amplifier, scales amplitude of signal by dB value.
    """
    def __init__(self, master, input_connect):
        KlattComponent.__init__(self, master, input_connect)

    def amplify(self, dB):
        self.pull()
        dB = np.sqrt(10)**(dB/10)
        self.output[:] = self.input[:]*dB


class Mixer(KlattComponent):
    """
    Simple mixer. Supports an arbitrary number of channels.
    """
    def __init__(self, master, input_connect):
        KlattComponent.__init__(self, master, input_connect)

    def mix(self):
        for i in range(len(self.input_connect)):
            self.output[:] = self.output[:] + self.input_connect[i].output[:]


class Firstdiff(KlattComponent):
    """
    Simple first difference operator.
    """
    def __init__(self, master, input_connect):
        KlattComponent.__init__(self, master, input_connect)

    def differentiate(self):
        self.pull()
        self.output[0] = self.input[0]
        for n in range(1, self.master.params["N_SAMP"]):
            self.output[n] = self.input[n] - self.input[n-1]


class Lowpass(KlattComponent):
    """
    Simple one-zero 6 dB/oct lowpass filter.
    """
    def __init__(self, master, input_connect):
        KlattComponent.__init__(self, master, input_connect)

    def filter(self):
        self.pull()
        self.output[0] = self.input[0]
        for n in range(1, self.master.params["N_SAMP"]):
            self.output[n] = self.input[n] + self.output[n-1]


class Normalizer(KlattComponent):
    """
    Normalizes signal so that abs(max value) is 1.
    """
    def __init__(self, master, input_connect):
        KlattComponent.__init__(self, master, input_connect)

    def normalize(self):
        self.pull()
        self.output[:] = self.input[:]/np.max(np.abs(self.input[:]))


class Noisegen(KlattComponent):
    """
    Generates noise from a Gaussian distribution.
    """
    def __init__(self, master, input_connect=None):
        KlattComponent.__init__(self, master, input_connect)

    def generate(self):
        self.output[:] = np.random.normal(loc=0.0, scale=1.0,
                                          size=self.master.params["N_SAMP"])
##### END COMPONENTS #####
