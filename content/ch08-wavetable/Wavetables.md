(wavetables)=
# Wavetable Synthesis

```{note}
Placeholder section. Develop wavetable oscillators with Pyquist examples.
```

A **wavetable** is one cycle of a waveform stored in an array. An oscillator
reads through it repeatedly, stepping by a *phase increment* set by the desired
frequency. This is how most digital oscillators are actually implemented.

Storing several related wavetables and *interpolating* between them lets the
timbre morph smoothly over time — the basis of modern **wavetable synthesizers**.

## To develop

- Phase accumulation and the read-index increment.
- Interpolation between table entries to reduce noise.
- Morphing across a set of wavetables with an envelope or LFO.
