"""
@name:    klatt.py
@author:  Daniel R Guest
@date:    11/15/2016
@version: 0.4
@purpose: Klatt voice synthesizer and interface between TrackDraw 2016 and
          Klatt syntheiszer.

@overview: TODO
"""
import math
try:
    from numpy.random import normal
except ImportError:
    print("NumPy not available. Exiting now.")
    import sys
    sys.exit()

class KlattSynth(object):

    def __init__(self):
        # Create tags
        self.name = "Klatt 1990 Synthesizer"
        self.algorithm = "KLSYN90"

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
                      "FS", "DT"]                         # Sample rate
        self.params = {param: None for param in param_list}

        # Initialize data vectors
        self.output = np.zeros(self.params["N_INV"]*self.params["INV_SAMP"])

        # Initialize sections
        self.voice = KlattVoice(self)
        self.noise = KlattNoise(self)
        self.cascade = KlattCascade(self, [self.voice, self.noise])
        self.parallel = KlattParallel(self, [self.voice, self.noise])
        self.radiation = KlattRadiation(self, [self.cascade, self.parallel])
        self.output_module = KlattOutput(self, [self.radiation])

    def run(self):
        for i in range(self.params["N_INV"]):
            self.voice.run()
            self.noise.run()
            self.cascade.run()
            self.radiation.run()
            self.output_module.run()
        self.reset()

    def update_inv(self):
        self.curr_inv = self.curr_inv + 1
        self.next_inv = self.curr_inv + 1
        self.curr_ind = self.curr_inv * self.params["INV_SAMP"]
        self.next_inv = self.next_inv * self.params["INV_SAMP"]

    def reset(self):
        self.curr_inv = 0
        self.next_inv = 1
        self.curr_ind = self.curr_inv * self.params["INV_SAMP"]
        self.next_ind = self.next_inv * self.params["INV_SAMP"]

   
