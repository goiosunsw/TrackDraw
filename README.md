TrackDraw
=========
TrackDraw (version 0.1.0) is an open-source speech analysis and synthesis tool.

People
======
TrackDraw was written by A.Y. Cho (M.S., pursuing Ph.D. at Harvard) and Daniel Guest (pursuing B.S. at UT Dallas).
Email Daniel at daniel.guest@utdallas.edu with questions.

History
=======
The original TrackDraw was a MATLAB package designed by Peter Assmann, Will Ballard, Laurie Bornstein, and Dwayne Paschall. This package allowed the user to draw tracks on a graphical user interface which served as the input for time-varying formant resonators in a Klatt synthesizer. It also supported drawing tracks over the spectrogram of an input speech waveform and sine-wave synthesis. More information about the original TrackDraw can be found here: http://www.utdallas.edu/~assmann/TRACKDRAW/about.html

In the summer of 2016, efforts began to modernize the original TrackDraw and expand on its features. This code represents the first complete alpha build of the modernized TrackDraw in Python 3.

Purpose
=======
TrackDraw is a speech analysis and synthesis tool, with a strong pedagogical focus. Features include:
- Spectrogram display of input speech waveform or synthesized speech waveform
- Variable display parameters and settings for the spectrogram plot, including window length and type
- Convenient graphical user interface for interaction with fully-featured custom Klatt synthesizer

We intend TrackDraw to be a tool for novices to learn about analyzing speech, using spectrograms, and synthesizing speech. For example, imagine a student in an introductory phonetics class learning about formants and vowels. The student could be assigned a speech sample (say, an /hVd/ syllable in a wav file) and be tasked with synthesizing a reasonable approximation to the speech sample using TrackDraw. The student would have to learn how to read a spectrogram and identify formants in the spectrogram. The student would then attempt to draw the formants in the vowel using the track GUI. If the synthesized waveform makes the same vowel sound as the speech sample, the student will immediately know that they identified the correct formants in the spectrogram. Similar exercises could be designed to teach students about narrowband versus broadband spectrograms, fundamental frequency contours, voice quality, etc. 

To this end, we intend to prioritize development of the graphical user interface and features of TrackDraw which lend themselves to its use a pedagogical tool. However, in the long-run, we also plan to include features which will make TrackDraw useful for various types of speech science researchers and clinicians, such as vocoding/utterance copy features, more advanced synthesis algorithms, analysis tools such as wavelet analysis, and interfaces with other programming languages.

Roadmap
=======
Features already implemented:
- Spectrogram display with variable settings
- Klatt 1980 synthesizer
- Track-style input for formant frequencies over time
- Loading input speech waveform

Features to be added in next update (version 0.2.0, estimated release - 09/25/2016):
- Variable thresholding on spectrogram
- Saving synthesized speech waveform to wav file
- Saving settings and synthesis parameters to disk
- Klatt 1988 synthesizer

Features to be added in next version change (version 1.0.0):
- Automatic utterance copy (i.e. decomposing input waveform into synthesis parameters automatically)
- Help menu and tooltips
- GUI control of every parameter in Klatt synthesizer
- Batch processing
- Wavelet analysis

Long term planned features:
- Interfaces to allow access to TrackDraw functionality inside of the R and MATLAB programming environments
