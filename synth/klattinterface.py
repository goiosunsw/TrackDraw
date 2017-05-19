import math
try:
    import numpy as np
except ImportError:
    print("NumPy not available. Please install NumPy and run TrackDraw again. Exiting now.")
    import sys
    sys.exit()


class NTVParam1980:
    """
    Interface between TrackDraw and KlattSynth for non-time-varying parameters.

    Arguments:
        FS (int): Sampling rate in Hz
        N_FORM (int): Number of formants in vocal tract cascade simulation
        DUR (float): Duration in seconds

    Attributes:
        FS (int): Sampling rate in Hz
        N_FORM (int): Number of formants in vocal tract cascade simulation
        DUR (float): Duration in seconds
        N_SAMP (int): Number of samples to be synthesized
        VER (string): Algorithm to be used in synthesis

    Provides simple data storage and defaults for non-time-varying parameters
    for KlattSynth's KLSYN80 algorithm.
    """
    def __init__(self, FS=10000,
                       N_FORM=5,
                       DUR=1):
        self.FS = FS
        self.DUR = DUR
        self.N_FORM = N_FORM
        self.N_SAMP = round(FS*DUR)
        self.VER = "KLSYN80"


class TVParam1980:
    """
    Interface between TrackDraw and KlattSynth for time-varying parameters.

    Arguments:
        F0 (float): Fundamental frequency in Hz
        FF (list): List of floats, each one corresponds to a formant frequency
            in Hz
        BW (list): List of floats, each one corresponds to the bandwidth of a
            formant in Hz in terms of plus minus 3dB
        AV (float): Amplitude of voicing in dB
        AVS (float): Amplitude of quasi-sinusoidal voicing in dB
        AH (float): Amplitude of aspiration in dB
        AF (float): Amplitude of frication in dB
        SW (0 or 1): Controls switch from voicing waveform generator to cascade
            or parallel resonators
        FGP (float): Frequency of the glottal resonator 1 in Hz
        BGP (float): Bandwidth of glottal resonator 1 in Hz
        FGZ (float): Frequency of glottal zero in Hz
        BGZ (float): Bandwidth of glottal zero in Hz
        FNP (float): Frequency of nasal pole in Hz
        BNP (float): Bandwidth of nasal pole in Hz
        FNZ (float): Frequency on the nasal zero in Hz
        BNZ (float): Bandwidth of nasal zero in Hz
        BGS (float): Glottal resonator 2 bandwidth in Hz
        A1 (float): Amplitude of parallel formant 1 in Hz
        A2 (float): Amplitude of parallel formant 2 in Hz
        A3 (float): Amplitude of parallel formant 3 in Hz
        A4 (float): Amplitude of parallel formant 4 in Hz
        A5 (float): Amplitude of parallel formant 5 in Hz
        A6 (float): Amplitude of parallel formant 6 in Hz
        AN (float): Amplitude of nasal formant in dB
        track_npoints (int): number of points in tracks, essentially determines
            the time "resolution" of time-varying parameters in TrackDraw.

    Attributes:
        Each of the above time-varying parameteres is stored in a Track object
        as an attribute.
    """
    def __init__(self, F0=100,
                       FF=[500, 1500, 2500, 3500, 4500],
                       BW=[50, 100, 100, 200, 250],
                       AV=0, AVS=0, AH=0, AF=0,
                       SW=0, FGP=0, BGP=100, FGZ=1500, BGZ=6000,
                       FNP=250, BNP=100, FNZ=250, BNZ=100, BGS=200,
                       A1=0, A2=0, A3=0, A4=0, A5=0, A6=0, AN=0,
                       track_npoints=80, N_FORM=5):
        self.F0 = Track(np.ones(track_npoints)*F0)
        self.FF = [Track(np.ones(track_npoints)*FF[i]) for i in range(N_FORM)]
        self.BW = [Track(np.ones(track_npoints)*BW[i]) for i in range(N_FORM)]
        self.AV = Track(np.ones(track_npoints)*AV)
        self.AVS = Track(np.ones(track_npoints)*AVS)
        self.AH = Track(np.ones(track_npoints)*AH)
        self.AF = Track(np.ones(track_npoints)*AF)
        self.FNZ = Track(np.ones(track_npoints)*FNZ)
        self.SW = Track(np.ones(track_npoints)*SW)
        self.FGP = Track(np.ones(track_npoints)*FGP)
        self.BGP = Track(np.ones(track_npoints)*BGP)
        self.FGZ = Track(np.ones(track_npoints)*FGZ)
        self.BGZ = Track(np.ones(track_npoints)*BGZ)
        self.FNP = Track(np.ones(track_npoints)*FNP)
        self.BNP = Track(np.ones(track_npoints)*BNP)
        self.BNZ = Track(np.ones(track_npoints)*BNZ)
        self.BGS = Track(np.ones(track_npoints)*BGS)
        self.A1 = Track(np.ones(track_npoints)*A1)
        self.A2 = Track(np.ones(track_npoints)*A2)
        self.A3 = Track(np.ones(track_npoints)*A3)
        self.A4 = Track(np.ones(track_npoints)*A4)
        self.A5 = Track(np.ones(track_npoints)*A5)
        self.A6 = Track(np.ones(track_npoints)*A6)
        self.AN = Track(np.ones(track_npoints)*AN)


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
    Temporary utility function to create set of parameters for testing.
    """
    tvp = TVParam1980()
    ntvp = NTVParam1980()
    return(tvp, ntvp)

def klatt_make(tvparams=None, ntvparams=None):
    """
    Creates and properly prepares KlattSynth object

    Arguments:
        tvparams (TVParam1980): time-varying parameters object
        ntvparams (NTVParam1980): non-time-varying parameters object
    """
    # Choose defaults if custom parameters not available
    if tvparams is None:
        tvparams = TVParam1980()
    if ntvparams is None:
        ntvparams = NTVParam1980()

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

