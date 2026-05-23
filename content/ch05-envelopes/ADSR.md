(adsr)=
# The ADSR Envelope

```{note}
Placeholder section. Develop the ADSR model with Pyquist examples.
```

An **envelope** is a slowly varying control signal. The classic amplitude
envelope has four stages:

```{glossary}
Attack
  Time to rise from silence to peak level.

Decay
  Time to fall from peak to the sustain level.

Sustain
  The level held while a note is "on".

Release
  Time to fall from sustain back to silence after the note is released.
```

An envelope can shape *any* parameter, not just amplitude — try applying one to
filter cutoff or modulation depth.

## To develop

- Generating ADSR envelopes in Pyquist and applying them to a tone.
- Linear vs. exponential segments and why exponential often sounds natural.
- Envelopes as reusable control signals across the synthesis chapters.
