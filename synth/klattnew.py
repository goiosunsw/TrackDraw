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
            # Initialize section objects
            self.voice = KlattVoice1980(self)
            self.noise = KlattNoise1980(self)
            self.cascade = KlattCascade1980(self)
            self.parallel = KlattParallel1980(self)
            self.radiation = KlattRadiation1980(self)
            self.output_module = OutputModule(self)
            # Run wires
            self.voice.connect([self.cascade, self.parallel])
            self.noise.connect([self.cascade, self.parallel])
            self.cascade.connect([self.radiation])
            self.parallel.connect([self.radiation])
            self.radiation.connect([self.output_module])
            # Put all section objects into self.sections
            self.sections = [self.voice, self.noise, self.cascade,
                             self.parallel, self.radiation, self.output_module]
            # Patch all components together
            for section in self.sections:
                section.patch()
        else:
            print("Sorry, versions other than Klatt 1980 are not supported.")

    def run(self):
        self.output[:] = np.zeros(self.params["N_SAMP"])
        for section in self.sections:
            section.run()
        self.output[:] = self.output_module.output[:]


##### CLASS DEFINITIONS #####
class KlattSection:
    """
    Parent class for section-level objects in TrackDraw synth system.

    TODO - parcel out parameter setting, probably wasteful but potentially
    worthwile?.
    """
    def __init__(self, mast):
        self.mast = mast
        self.ins = []
        self.outs = []

    def connect(self, sections):
        for section in sections:
            section.ins.append(Buffer(mast=self.mast))
            self.outs.append(Buffer(mast=self.mast, dests=[section.ins[-1]]))

    def process_ins(self):
        for _in in self.ins:
            _in.process()

    def process_outs(self):
        for out in self.outs:
            out.process()


class KlattComponent:
    """
    Parent class for component-level objects in TrackDraw synth system.

    TODO - Write connect() method to remove item.dests = nonsense
    """
    def __init__(self, mast, dests=None):
        self.mast = mast
        if dests is None:
            self.dests = []
        else:
            self.dests = dests
        self.input = np.zeros(self.mast.params["N_SAMP"])
        self.output = np.zeros(self.mast.params["N_SAMP"])

    def receive(self, signal):
        """
        Updates current signal.
        """
        self.input[:] = signal[:]

    def send(self):
        """
        Perpetuates signal to components further down in the chain.
        """
        for dest in self.dests:
            dest.receive(signal=self.output[:])

    def connect(self, components):
        """
        Provides interface to change dests
        """
        for component in components:
            self.dests.append(component)


##### SECTION DEFINITIONS #####
class KlattVoice1980(KlattSection):
    """
    Generates a voicing waveform ala Klatt 1980.
    """
    def __init__(self, mast):
        KlattSection.__init__(self, mast)
        self.impulse = Impulse(mast=self.mast)
        self.rgp = Resonator(mast=self.mast)
        self.rgz = Resonator(mast=self.mast, anti=True)
        self.rgs = Resonator(mast=self.mast)
        self.av = Amplifier(mast=self.mast)
        self.avs = Amplifier(mast=self.mast)
        self.mixer = Mixer(mast=self.mast)
        self.switch = Switch(mast=self.mast)

    def patch(self):
        self.impulse.dests = [self.rgp]
        self.rgp.dests = [self.rgz, self.rgs]
        self.rgz.dests = [self.av]
        self.rgs.dests = [self.avs]
        self.av.dests = [self.mixer]
        self.avs.dests = [self.mixer]
        self.mixer.dests = [self.switch]
        self.switch.dests = [*self.outs]

    def run(self):
        self.impulse.impulse_gen()
        self.rgp.resonate(ff=self.mast.params["FGP"],
                          bw=self.mast.params["BGP"])
        self.rgz.resonate(ff=self.mast.params["FGZ"],
                          bw=self.mast.params["BGZ"])
        self.rgs.resonate(ff=self.mast.params["FGP"],
                          bw=self.mast.params["BGS"])
        self.av.amplify(dB=self.mast.params["AV"])
        self.avs.amplify(dB=self.mast.params["AVS"])
        self.mixer.mix()
        self.switch.operate(choice=self.mast.params["SW"])
        self.process_outs()


class KlattNoise1980(KlattSection):
    """
    Generates noise ala Klatt 1980.
    """
    def __init__(self, mast):
        KlattSection.__init__(self, mast)
        self.noisegen = Noisegen(mast=self.mast)
        self.lowpass = Lowpass(mast=self.mast)
        self.amp = Amplifier(mast=self.mast)

    def patch(self):
        self.noisegen.dests = [self.lowpass]
        self.lowpass.dests = [self.amp]
        self.amp.dests = [*self.outs]

    def run(self):
        self.noisegen.generate()
        self.lowpass.filter()
        self.amp.amplify(dB=-100)
        self.process_outs()


class KlattCascade1980(KlattSection):
    """
    Simulates a vocal tract with a cascade of resonators.
    """
    def __init__(self, mast):
        KlattSection.__init__(self, mast)
        self.ah = Amplifier(mast=self.mast)
        self.mixer = Mixer(mast=self.mast)
        self.rnp = Resonator(mast=self.mast)
        self.rnz = Resonator(mast=self.mast, anti=True)
        self.formants = []
        for form in range(self.mast.params["N_FORM"]):
            self.formants.append(Resonator(mast=self.mast))

    def patch(self):
        self.ins[0].dests = [self.mixer]
        self.ins[1].dests = [self.ah]
        self.ah.dests = [self.mixer]
        self.mixer.dests = [self.rnp]
        self.rnp.dests = [self.rnz]
        self.rnz.dests = [self.formants[0]]
        for i in range(0, self.mast.params["N_FORM"]-1):
            self.formants[i].dests = [self.formants[i+1]]
        self.formants[self.mast.params["N_FORM"]-1].dests = [*self.outs]

    def run(self):
        self.process_ins()
        self.ah.amplify(dB=self.mast.params["AH"])
        self.mixer.mix()
        self.rnp.resonate(ff=self.mast.params["FNP"],
                          bw=self.mast.params["BNP"])
        self.rnz.resonate(ff=self.mast.params["FNZ"],
                          bw=self.mast.params["BNZ"])
        for form in range(len(self.formants)):
            self.formants[form].resonate(ff=self.mast.params["FF"][form],
                                         bw=self.mast.params["BW"][form])
        self.process_outs()


class KlattParallel1980(KlattSection):
    """
    Simulates a vocal tract with a bank of parallel resonators.

    TODO - Finish putting together connections, test.
    """
    def __init__(self, mast):
        KlattSection.__init__(self, mast)
        self.af = Amplifier(mast=self.mast)
        self.a1 = Amplifier(mast=self.mast)
        self.r1 = Resonator(mast=self.mast)
        self.first_diff = Firstdiff(mast=self.mast)
        self.mixer = Mixer(mast=self.mast)
        self.an = Amplifier(mast=self.mast)
        self.rnp = Resonator(mast=self.mast)
        self.a2 = Amplifier(mast=self.mast)
        self.r2 = Resonator(mast=self.mast)
        self.a3 = Amplifier(mast=self.mast)
        self.r3 = Resonator(mast=self.mast)
        self.a4 = Amplifier(mast=self.mast)
        self.r4 = Resonator(mast=self.mast)
        self.a5 = Amplifier(mast=self.mast)
        self.r5 = Resonator(mast=self.mast)
        # 6th formant currently not part of run routine! Not sure what values
        # to give to it... need to keep reading Klatt 1980.
        self.a6 = Amplifier(mast=self.mast)
        self.r6 = Resonator(mast=self.mast)
        self.output_mixer = Mixer(mast=self.mast)

    def patch(self):
        self.ins[1].connect([self.af])
        self.ins[0].connect([self.a1, self.first_diff])
        self.af.connect([self.mixer, self.a5, self.a6])
        self.first_diff.connect([self.mixer])
        self.mixer.connect([self.an, self.a2, self.a3, self.a4])
        self.a1.connect([self.r1])
        self.an.connect([self.rnp])
        self.a2.connect([self.r2])
        self.a3.connect([self.r3])
        self.a4.connect([self.r4])
        self.a5.connect([self.r5])
        self.r6.connect([self.r6])
        for item in [self.a1, self.an, self.a2, self.a3, self.a4, self.a5,
                     self.a6]:
            item.connect([self.output_mixer])
        self.output_mixer.connect([*self.outs])

    def run(self):
        self.process_ins()
        self.af.amplify(dB=self.mast.params["AF"])
        self.a1.amplify(dB=self.mast.params["A1"])
        self.r1.resonate(ff=self.mast.params["FF"][0],
                         bw=self.mast.params["BW"][0])
        self.first_diff.differentiate()
        self.mixer.mix()
        self.an.amplify(dB=self.mast.params["AN"])
        self.rnp.resonate(ff=self.mast.params["FNP"],
                          bw=self.mast.params["BNP"])
        self.a2.amplify(dB=self.mast.params["A2"])
        self.r2.resonate(ff=self.mast.params["FF"][1],
                         bw=self.mast.params["BW"][1])
        self.a3.amplify(dB=self.mast.params["A3"])
        self.r3.resonate(ff=self.mast.params["FF"][2],
                         bw=self.mast.params["BW"][2])
        self.a4.amplify(dB=self.mast.params["A4"])
        self.r4.resonate(ff=self.mast.params["FF"][3],
                         bw=self.mast.params["BW"][3])
        self.a5.amplify(dB=self.mast.params["A5"])
        self.r5.resonate(ff=self.mast.params["FF"][4],
                         bw=self.mast.params["BW"][4])
        self.output_mixer.mix()
        self.process_outs()


class KlattRadiation1980(KlattSection):
    """
    Simulates the effect of radiation characteristic in the vocal tract.
    """
    def __init__(self, mast):
        KlattSection.__init__(self, mast)
        self.mixer = Mixer(mast=self.mast)
        self.firstdiff = Firstdiff(mast=self.mast)

    def patch(self):
        for _in in self.ins:
            _in.connect([self.mixer])
        self.mixer.connect([self.firstdiff])
        self.firstdiff.connect([*self.outs])

    def run(self):
        self.process_ins()
        self.mixer.mix()
        self.firstdiff.differentiate()
        self.process_outs()


class OutputModule(KlattSection):
    def __init__(self, mast):
        KlattSection.__init__(self, mast)
        self.mixer = Mixer(mast=self.mast)
        self.normalizer = Normalizer(mast=self.mast)
        self.output = np.zeros(self.mast.params["N_SAMP"])

    def patch(self):
        for _in in self.ins:
            _in.dests = [self.mixer]
        self.mixer.dests = [self.normalizer]
        self.normalizer.dests = [*self.outs]

    def run(self):
        self.process_ins()
        self.mixer.mix()
        self.normalizer.normalize()
        self.output[:] = self.normalizer.output[:]


##### COMPONENT DEFINITIONS #####
class Buffer(KlattComponent):
    """
    Utility component.
    """
    def __init__(self, mast, dests=None):
        KlattComponent.__init__(self, mast, dests)

    def process(self):
        self.output[:] = self.input[:]
        self.send()


class Resonator(KlattComponent):
    """
    Klatt resonator.
    """
    def __init__(self, mast, anti=False):
        KlattComponent.__init__(self, mast)
        self.anti = anti

    def calc_coef(self, ff, bw):
        c = -np.exp(-2*np.pi*bw*self.mast.params["DT"])
        b = (2*np.exp(-np.pi*bw*self.mast.params["DT"])\
             *np.cos(2*np.pi*ff*self.mast.params["DT"]))
        a = 1-b-c
        if self.anti:
            a_prime = 1/a
            b_prime = -b/a
            c_prime = -c/a
            return(a_prime, b_prime, c_prime)
        else:
            return(a, b, c)

    def resonate(self, ff, bw):
        a, b, c = self.calc_coef(ff, bw)
        self.output[0] = a[0]*self.input[0]
        if self.anti:
            self.output[1] = a[1]*self.input[1] + b[1]*self.input[0]
            for n in range(2, self.mast.params["N_SAMP"]):
                self.output[n] = a[n]*self.input[n] + b[n]*self.input[n-1] \
                                + c[n]*self.input[n-2]
        else:
            self.output[1] = a[1]*self.input[1] + b[1]*self.output[0]
            for n in range(2,self.mast.params["N_SAMP"]):
                self.output[n] = a[n]*self.input[n] + b[n]*self.output[n-1] \
                                + c[n]*self.output[n-2]
        self.send()


class Impulse(KlattComponent):
    """
    Time-varying impulse generator.
    """
    def __init__(self, mast):
        KlattComponent.__init__(self, mast)
        self.last_glot_pulse = 0

    def impulse_gen(self):
        glot_period = np.round(self.mast.params["FS"]
                            /self.mast.params["F0"])
        for n in range(self.mast.params["N_SAMP"]):
            if n - self.last_glot_pulse >= glot_period[n]:
                self.output[n] = 1
                self.last_glot_pulse = n
        self.send()


class Mixer(KlattComponent):
    def __init__(self, mast):
        KlattComponent.__init__(self, mast)

    def receive(self, signal):
        self.input[:] = self.input[:] + signal[:]

    def mix(self):
        self.output[:] = self.input[:]
        self.send()


class Amplifier(KlattComponent):
    """
    Simple amplifier, scales amplitude of signal by dB value.
    """
    def __init__(self, mast):
        KlattComponent.__init__(self, mast)

    def amplify(self, dB):
        dB = np.sqrt(10)**(dB/10)
        self.output[:] = self.input[:]*dB
        self.send()


class Firstdiff(KlattComponent):
    """
    Simple first difference operator.
    """
    def __init__(self, mast):
        KlattComponent.__init__(self, mast)

    def differentiate(self):
        self.output[0] = self.input[0]
        for n in range(1, self.mast.params["N_SAMP"]):
            self.output[n] = self.input[n] - self.input[n-1]
        self.send()


class Lowpass(KlattComponent):
    """
    Simple one-zero 6 dB/oct lowpass filter.
    """
    def __init__(self, mast):
        KlattComponent.__init__(self, mast)

    def filter(self):
        self.output[0] = self.input[0]
        for n in range(1, self.mast.params["N_SAMP"]):
            self.output[n] = self.input[n] + self.output[n-1]
        self.send()


class Normalizer(KlattComponent):
    """
    Normalizes signal so that abs(max value) is 1.
    """
    def __init__(self, mast):
        KlattComponent.__init__(self, mast)

    def normalize(self):
        self.output[:] = self.input[:]/np.max(np.abs(self.input[:]))
        self.send()


class Noisegen(KlattComponent):
    """
    Generates noise from a Gaussian distribution.
    """
    def __init__(self, mast):
        KlattComponent.__init__(self, mast)

    def generate(self):
        self.output[:] = np.random.normal(loc=0.0, scale=1.0,
                                          size=self.mast.params["N_SAMP"])
        self.send()


class Switch(KlattComponent):
    """
    Binary switch between two outputs.
    """
    def __init__(self, mast):
        KlattComponent.__init__(self, mast)
        self.output = []
        self.output.append(np.zeros(self.mast.params["N_SAMP"]))
        self.output.append(np.zeros(self.mast.params["N_SAMP"]))

    def send(self):
        self.dests[0].receive(signal=self.output[0][:])
        self.dests[1].receive(signal=self.output[1][:])
        self.input = np.zeros(self.mast.params["N_SAMP"])
        self.output = np.zeros(self.mast.params["N_SAMP"])

    def operate(self, choice):
        for n in range(self.mast.params["N_SAMP"]):
            if choice[n] == 0:
                self.output[0][n] = self.input[n]
                self.output[1][n] = 0
            elif choice[n] == 1:
                self.output[0][n] = 0
                self.output[1][1] = self.input[n]
        self.send()


def q():
    tvp, ntvp = klatt_fake()
    s = klatt_make(tvp, ntvp)
    s.run()
    plt.plot(s.output)
    plt.show()
    return(s)
