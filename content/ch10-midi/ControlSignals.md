(control-signals)=
# Control Signals

```{note}
Placeholder section. Develop continuous control and parameter mapping.
```

Beyond discrete notes, music needs **continuous control**: a swell in volume, a
slow filter sweep, vibrato. MIDI carries these as *control change* messages and
*pitch bend*; in synthesis code they are simply slow-moving signals.

A useful distinction:

- **Audio-rate** signals — the sound itself, updated every sample.
- **Control-rate** signals — envelopes and LFOs, updated less often.

Pyquist lets the same kind of signal serve either role, which is what makes
modulation (Chapter 6) so flexible.

## To develop

- LFOs as control sources: vibrato, tremolo, auto-wah.
- Mapping a control range onto a parameter range.
- Smoothing controls to avoid clicks and zipper noise.
