def cython_resonate(_in, out, delay, a, b, c):
    out[0] = a*_in[0] + b*delay[1] + c*delay[0]
    out[1] = a*_in[1] + b*_in[0] + c*delay[1]
    for n in range(len(_in)):
        out[n] = a*_in[n] + b*out[n-1] + c*out[n-2]
    return(out)