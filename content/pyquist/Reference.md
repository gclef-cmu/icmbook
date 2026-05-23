(pyquist-reference)=
# API Reference

```{note}
Placeholder. The entries below show a **suggested format** for documenting the
Pyquist API. Replace them with the real functions, signatures, and behavior.

Once Pyquist ships with Python docstrings, consider generating this page
automatically with [Sphinx autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
instead of maintaining it by hand.
```

## Generators

`osc(freq, dur, amp=1.0, wave='sine', phase=0.0)`
: Create an oscillator. *(Placeholder signature.)*

  - **freq** — frequency in hertz.
  - **dur** — duration in seconds.
  - **amp** — peak amplitude.
  - **wave** — `'sine'`, `'square'`, `'saw'`, or `'triangle'`.
  - **phase** — initial phase in radians.
  - **Returns** — a `Sound`.

`noise(dur, color='white', amp=1.0)`
: Create a noise generator. *(Placeholder signature.)*

## Envelopes

`adsr(attack, decay, sustain, release)`
: Create an ADSR envelope usable as a control signal. *(Placeholder signature.)*

## Processors

`lowpass(sound, cutoff, resonance=0.0)`
: Apply a resonant lowpass filter. *(Placeholder signature.)*

`delay(sound, time, feedback=0.0, mix=0.5)`
: Apply a feedback delay. *(Placeholder signature.)*

## Scores

`seq(*sounds)`
: Schedule sounds one after another in time. *(Placeholder signature.)*

`mix(*sounds)`
: Overlap sounds so they play together. *(Placeholder signature.)*

## I/O

`Sound.play()`
: Play a sound through the default audio device. *(Placeholder.)*

`Sound.write(path)`
: Write a sound to an audio file. *(Placeholder.)*

`load(path)`
: Read an audio file into a `Sound`. *(Placeholder.)*
