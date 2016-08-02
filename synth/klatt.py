"""
@name:    klatt.py
@author:  Daniel R Guest
@date:    07/29/2016
@version: 0.3
@purpose: Klatt voice synthesizer and interface between TrackDraw 2016 and
          Klatt syntheiszer.

@overview:
    klatt.py is composed of three sections: klatt_make, klatt_bridge, and
    Klatt_Synth. klatt_make accepts a Parameters object from the TrackDraw 2016
    program and extracts necessary synthesis parameters from the object.
    klatt_bridge accepts these extracted synthesis parameters, converts them 
    to a format better suited for Klatt synthesis, and passes them to an
    instance of a Klatt_Synth object. Then, klatt_bridge calls the object's
    synth() method, which synthesizes the waveform. Finally, klatt_bridge takes
    the object's output and returns it to klatt_make, which in turn returns it
    to TrackDraw 2016.
    
    klatt.py is based on Klatt (1980), but only includes the portions necessary
    for synthesis of isolated vowels. The main synthesis procedure synthesizes 
    the output vowel waveform in small intervals (default 50 samples). 
    
    Klatt, D. (1980). Software for a cascade/parallel formant synthesizer. 
    The Journal Of The Acoustical Society Of America, 67(3), 971. 
    http://dx.doi.org/10.1121/1.383940
"""
def klatt_make(parms):
    """
    Extracts necessary parameters from TrackDraw 2016 Parameters object.
    
    parms -- input TrackDraw 2016 Parameters object
    
    klatt_make extracts necessary parameters from a Parameters object for
    syntheisizing a vowel waveform in the Klatt synthesizer, then calls
    klatt_bridge and passes it all the relevant parameters. The parameters are
    each explained in the klatt_bridge() doc string:
    """
    f0 = parms.F0
    ff = parms.FF
    bw = parms.BW
    fs = parms.synth_fs
    dur = parms.dur
    env = parms.ENV
    source = parms.voicing
    y = klatt_bridge(f0, ff, bw, fs, dur, env, source)
    return(y)
    
def klatt_bridge(f0, ff, bw, fs, dur, env, source, inv_samp=50):
    """
    Processes/interpolates input parameters for Klatt synth, runs synth.
    
    Takes a variety of synthesis parameters passed to it from klatt_make and 
    interpolates them or derives other values from them as necessary for Klatt
    synthesis. Then passes them to a Klatt_Synth object and runs the synthesis
    routine, returning the resultant waveform back to klatt_make. 
    
    f0 -- fundamental frequency contour (Track object)
    ff -- formant frequency contour (list of Track objects)
    bw -- bandwidth values for formants (should be as many as there are 
          formants to be synthesized, in numpy array)
    fs -- sample rate to synthesize at (integer)
    dur -- duration in seconds (float)
    env -- envelope contour (numpy array)
    source -- type of source to be used (string, see TrackDrawSlots)
    """
    from scipy.interpolate import interp1d
    import numpy as np
    
    # First, determine necessary number of update intervals
    n_inv = round(dur*fs/inv_samp)
    # Next, determine the number of formants
    n_form = ff.shape[1]
    # Next, take all input parameters and interpolate as necessary
    def interpolate(input_vector, n_inv):
        """
        Takes input vector, linearlly interpolates to output vector with length
        n_inv, returns as list.
        """
        try:
            n_input_steps = len(input_vector)
            seq = np.arange(0, n_input_steps)
            seq_new = np.linspace(0, n_input_steps-1, n_inv)
            return(list(interp1d(seq, input_vector)(seq_new)))
        except TypeError:
            return([input_vector] * n_inv) # Returns constant function in len = 1
    interp_f0 = []
    interp_ff = []
    interp_bw = []
    interp_env = []
    interp_f0 = interpolate(f0, n_inv)
    for i in range(n_form):
            interp_ff.append(interpolate(ff[:,i], n_inv))
            try:
                interp_bw.append(interpolate(bw[:,i], n_inv))
            except IndexError:
                interp_bw.append(interpolate(bw[i], n_inv))
    interp_env = interpolate(env, n_inv)
    # Finally, create synth object, run it, and return its output waveform    
    synth = Klatt_Synth(f0=interp_f0, ff=interp_ff, bw=interp_bw,
                        env=interp_env, fs=fs, n_inv=n_inv, n_form=n_form,
                        inv_samp=inv_samp, source=source)
    synth.synth()
    return(synth.output)
    
    
class Klatt_Synth:
    """
    Synthesizes vowels ala Klatt 1980.

    Arguments:
        f0 (list, len n_inv) -- fundamental frequency contour
        ff (lists, n_form, len n_inv) -- formant frequency contours
        bw (lists, n_form, len n_inv) -- bandwidth contours
        env -- DEPRICATED, TODO - remove
        fs (integer) -- sample rate in Hz
        n_inv (integer) -- number of intervals of length inv_samp samples to be
            synthesized.
        n_form (integer) -- number of formants to be synthesized (integer).
            Cannot vary over the duration of the synthesized vowel.
        inv_samp (integer) -- length of each interval in samples
        source -- DEPRICATED, TODO - remove
    
    To generate a waveform from a Klatt_Synth object using the parameters
    provided to it, call its synth() method.
    
    Klatt_Synth synthesizes the waveform inv_samp samples at a time, so its
    synth() method loops n_inv times and writes the final result of all the
    synthesis operations in each interval to the Klatt_Synth object's output 
    vector.
    
    A Klatt_Synth object has as attributes all necessary synthesis parameters,
    a set of values which keep track of the current interval/sample index while
    synthesis is taking place, and a number of sections. Sections are objects
    which represent organizational abstractions drawn from the Klatt 1980
    paper. Each section is composed of multiple components, which are small
    signal processing units (like individual filters, resonators, amplifiers,
    etc.). Any section has a run() method which performs the operation
    that section is designed to do. For example, a Klatt_Voice section's run()
    method generates a voicing waveform. 
    
    Nearly all sections and components use the input_connect system. When
    initialized, a section or component is passed an input_connect argument,
    which is simply another section or component. When a component is run,
    it first calls the universal pull() method, which set's the component's
    input to the component's input_connect object's output. This allows a
    perpetuation of the signal between components. Note that while sections and
    components both have input_connect arguments, sections always pass their
    input_connect down to a child component, thus only components have pull()
    methods (and thus while components have their own input and output vectors,
    sections only have output vectors). 
    
    TODO -- add AV/AVS input dB values
    TODO -- remove references to source and env arguments
    TODO -- add nasal resonators
    TODO -- Add other sections (noise source and parallel branch)
    TODO -- Optimize
    """
    def __init__(self, f0, ff, bw, env, fs, n_inv, n_form, inv_samp, source):
        # Initialize time-varying synthesis parameters
        self.f0 = f0
        self.ff = ff
        self.bw = bw
        self.fs = fs
        self.env = env
        self.dt = 1/self.fs
        
        # Initialize non-time-varying synthesis parameters 
        self.inv_samp = inv_samp
        self.n_inv = n_inv
        self.n_form = n_form
        
        # Initialize trackers
        self.last_glot_pulse = 0
        self.current_inv = 0 # Index in terms of intervals
        self.next_inv = 1
        self.current_ind = self.current_inv*self.inv_samp # Index in terms of samples
        self.next_ind = self.next_inv*self.inv_samp
        
        # Initialize output vector
        self.output = [0] * self.n_inv*self.inv_samp

        # Initialize sections
        self.voice = Klatt_Voice(self)
        self.cascade = Klatt_Cascade(self, [self.voice])
        self.radiation = Klatt_Radiation(self, [self.cascade])
        self.output_module = Klatt_Output(self, [self.radiation])
        
    def synth(self):
        """
        Runs each section of the synthesizer in the correct order.
        """
        import time
        start = time.time()
        for i in range(self.n_inv):
            self.voice.run()
            self.cascade.run()
            self.radiation.run()
            self.output_module.run()
            self.update_inv() 
        self.reset()
        end = time.time()
        print("Elapsed: ", end-start)
                
    def update_inv(self):
        """
        Updates current and next interval trackers
        """
        self.current_inv = self.current_inv + 1
        self.next_inv = self.next_inv + 1
        self.current_ind = self.current_inv*self.inv_samp
        self.next_ind = self.next_inv*self.inv_samp
        
    def reset(self):
        """
        Sets current and next interval trackers back to initial values.
        """
        self.current_inv = 0
        self.next_inv = 1
        self.current_ind = self.current_inv*self.inv_samp
        self.next_ind = self.next_inv*self.inv_samp


##### START SECTIONS #####
class Klatt_Section:
    """
    Parent class for section-level objects in the TrackDraw Klatt synthesizer.
    
    Arguments:
        master (Klatt_Synth object) -- Klatt_Synth object this section is part of
    
    All sections have a master (which refers back to the Klatt_Synth object
    they are a part of), an output of length inv_samp, and a run method.
    """
    def __init__(self, master):
        self.master = master
        self.output = [0]*self.master.inv_samp

class Klatt_Voice(Klatt_Section):
    """
    Generates a voicing waveform. 
    """
    def __init__(self, master):
        Klatt_Section.__init__(self, master)
        self.impulse = Impulse(master=self.master)
        self.rgp = Resonator(master=self.master, input_connect=[self.impulse])
        self.rgz = Resonator(master=self.master, input_connect=[self.rgp], anti=True)
        self.rgs = Resonator(master=self.master, input_connect=[self.rgp])
        self.av = Amplifier(master=self.master, input_connect=[self.rgz])
        self.avs = Amplifier(master=self.master, input_connect=[self.rgs])
        self.mixer = Mixer(master=self.master, input_connect=[self.av, self.avs])
        
    def run(self):
        self.impulse.impulse_gen()
        self.rgp.resonate(ff=0, bw=100)
        self.rgz.resonate(ff=1500, bw=6500)
        self.av.amplify(dB=0)
        self.rgs.resonate(ff=0, bw=200)
        self.avs.amplify(dB=-40) # current dB @ -40 essentially disables it
        self.mixer.mix()
        self.output[:] = self.mixer.output[:]
        
class Klatt_Cascade(Klatt_Section):
    """
    Simulates a vocal tract with a cascade of resonators.
    
    Arguments:
        input_connect (Klatt_Section object) -- see Klatt_Synth doc string
    """
    def __init__(self, master, input_connect=None):
        Klatt_Section.__init__(self, master)
        self.mixer = Mixer(master=self.master, input_connect=input_connect)
        self.formants = []
        self.formants.append(Resonator(master=self.master, input_connect=[self.mixer]))
        previous_formant = self.formants[0]
        for i in range(1, self.master.n_form):
            self.formants.append(Resonator(master=self.master, input_connect=[previous_formant]))
            previous_formant = self.formants[i]

    def run(self):
        self.mixer.mix()
        for form in range(self.master.n_form):
            self.formants[form].resonate(self.master.ff[form][self.master.current_inv],
                                         self.master.bw[form][self.master.current_inv])
        self.output[:] = self.formants[-1].output[:]

class Klatt_Radiation(Klatt_Section):
    """
    Simulates the effect of radiation characteristic in vocal tract. 
    
    Arguments:
        input_connect (Klatt_Section object) -- see Klatt_Synth doc string
    """
    def __init__(self, master, input_connect=None):
        Klatt_Section.__init__(self, master)
        self.mixer = Mixer(master=self.master, input_connect=input_connect)
        self.radiation_characteristic = Rad_Char(master=self.master,
                                                 input_connect=[self.mixer])
        
    def run(self):
        self.mixer.mix()
        self.radiation_characteristic.radiate()
        self.output[:] = self.radiation_characteristic.output[:]


class Klatt_Output(Klatt_Section):
    """
    Transfers output buffer of final section to Klatt_Synth's main output
    
    Arguments:
        input_connect (Klatt_Section object) -- see Klatt_Synth doc string
    """
    def __init__(self, master, input_connect=None):
        Klatt_Section.__init__(self, master)
        self.output = Output(master=self.master, input_connect=input_connect)
        
    def run(self):
        self.output.run()
##### END SECTIONS #####        


##### START COMPONENTS #####
class Klatt_Component:
    """
    Parent class for component-level objects in the TrackDraw Klatt synthesizer. 
    
    Arguments:
        master (Klatt_Synth object) -- Klatt_Synth object this section is part of
        input_connect (Klatt_Section object) -- see Klatt_Synth doc string
    """
    def __init__(self, master, input_connect=None):
        self.master = master
        self.input = [0]*self.master.inv_samp
        self.output = [0]*self.master.inv_samp
        self.input_connect = input_connect
        
    def pull(self):
        """ Perpetuates signal from previous component to this component """
        self.input = [0]*self.master.inv_samp
        self.output = [0]*self.master.inv_samp
        self.input[:] = self.input_connect[0].output[:]
        

class Resonator(Klatt_Component):
    """
    Klatt resonator.
    
    Arguments:
        anti (boolean) -- if True, Resonator will act as antiresonator
    """
    def __init__(self, master, input_connect=None, anti=False):
        Klatt_Component.__init__(self, master, input_connect)
        self.anti = anti
        self.delay = [0]*2

    def calc_coef(self, ff, bw, anti=False):
        """
        Calculates coefficients for digital resonator according to Klatt 1980
        
        Arguments:
            ff (float) -- center frequency in Hz
            bw (float) -- bandwidth in Hz
            anti (boolean) -- if True, will calculate coefficients for
                antiresonator
        """
        import math
        c = -math.exp(-2*math.pi*bw*self.master.dt)
        b = (2*math.exp(-math.pi*bw*self.master.dt)\
             *math.cos(2*math.pi*ff*self.master.dt))
        a = 1-b-c
        if anti:
            a_prime = 1/a
            b_prime = -b/a
            c_prime = -c/a
            a = a_prime
            b = b_prime
            c = c_prime
        return(a, b, c)  
    
    def resonate(self, ff, bw):
        self.pull()
        a, b, c = self.calc_coef(ff, bw, anti=self.anti)
        self.output[0] = a*self.input[0] + b*self.delay[1] + c*self.delay[0]
        self.output[1] = a*self.input[1] + b*self.output[0] + c*self.delay[1]
        for n in range(2, self.master.inv_samp):
            self.output[n] = a*self.input[n] + b*self.output[n-1] + c*self.output[n-2]
        self.delay[:] = self.output[len(self.output)-2:len(self.output)]


class Impulse(Klatt_Component):
    """
    Klatt time-varying impulse generator.
    """
    def __init__(self, master):
        Klatt_Component.__init__(self, master)
        
    def impulse_gen(self):
        self.output = [0]*self.master.inv_samp
        glot_period = round(self.master.fs/self.master.f0[self.master.current_inv])
        for n in range(self.master.inv_samp):
            if (self.master.current_ind + n) - self.master.last_glot_pulse >= glot_period:
                self.output[n] = 1
                self.master.last_glot_pulse = self.master.current_ind + n
                
                
class Amplifier(Klatt_Component):
    """
    Simple amplifier.
    """
    def __init__(self, master, input_connect=None):
        Klatt_Component.__init__(self, master, input_connect)
            
    def amplify(self, dB):
        """ Scales amplitude by dB value, e.g. dB=0 leaves unaltered """
        import math
        self.pull()
        dB = math.sqrt(10)**(dB/10)
        for n in range(self.master.inv_samp):
            self.output[n] = self.input[n]*dB


class Mixer(Klatt_Component):
    """
    Simple mixer. 
    """
    def __init__(self, master, input_connect=None):
        Klatt_Component.__init__(self, master, input_connect)
            
    def mix(self):
        """
        Similar operation to Klatt_Component.pull() but mixes multiple inputs
        together. 
        """
        for n in range(self.master.inv_samp):
            temp = []
            for j in range(len(self.input_connect)):
                temp.append(self.input_connect[j].output[n])
            self.input[n] = sum(temp)
        self.output[:] = self.input[:]


class Rad_Char(Klatt_Component):
    """
    Simple first difference operator to simulate radiation characteristic.
    """
    def __init__(self, master, input_connect=None):
        Klatt_Component.__init__(self, master, input_connect)
        self.delay = [0]*1

    def radiate(self):
        self.pull()
        self.output[0] = self.input[0] - self.delay[0]
        for n in range(1, self.master.inv_samp):
            self.output[n] = self.input[n] - self.input[n-1]
        self.delay[0] = self.input[-1]


class Output(Klatt_Component):
    """ Writes input buffer to master Klatt_Synth's main output """
    def __init__(self, master, input_connect=None):
        Klatt_Component.__init__(self, master, input_connect)
        
    def run(self):
        self.pull()
        self.master.output[self.master.current_ind:self.master.next_ind] = self.input[:]
##### END COMPONENTS #####                   