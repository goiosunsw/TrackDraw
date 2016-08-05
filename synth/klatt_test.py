#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KLATT TEST FILE - FOR PROFILING
"""

import klatt
# N_INV for easy control!
N_INV = 200

f0 = [100]*N_INV
ff = [[500]*N_INV, [1500]*N_INV, [2500]*N_INV, [3500]*N_INV, [4500]*N_INV]
bw = [[100]*N_INV, [100]*N_INV, [100]*N_INV, [100]*N_INV, [100]*N_INV]
env = None
fs = 10000
n_form = 5
n_inv = N_INV
inv_samp = 50
source = None

synth = klatt.Klatt_Synth(f0, ff, bw, fs, n_inv, n_form, inv_samp)
synth.synth()
