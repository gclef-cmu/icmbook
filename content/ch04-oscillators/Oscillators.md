(osc-section)=
# Oscillators

```{note}
Placeholder section. Develop oscillator types and how Pyquist generates them.
```

An **oscillator** produces a periodic signal at a chosen frequency. The simplest
is the sine oscillator,

$$
x[n] = A \cdot \sin\!\left(2\pi f \frac{n}{f_s} + \phi\right),
$$

where $n$ is the sample index and $f_s$ is the sample rate.

## Common waveforms

```{list-table}
:header-rows: 1

* - Waveform
  - Harmonic content
  - Character
* - Sine
  - Fundamental only
  - Pure, hollow
* - Triangle
  - Odd harmonics, fast roll-off
  - Soft, mellow
* - Square
  - Odd harmonics, slow roll-off
  - Hollow, reedy
* - Sawtooth
  - All harmonics
  - Bright, buzzy
```

## To develop

- Generating each waveform in Pyquist.
- Phase, and why it usually does not matter for a single tone.
- Band-limited oscillators and avoiding aliasing (see {ref}`sampling`).
