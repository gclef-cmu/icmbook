(sampling)=
# Sampling

```{note}
Placeholder section. Develop sampling, sample rate, and the Nyquist limit.
```

**Sampling** records the value of a continuous signal at evenly spaced instants
in time. The number of samples taken per second is the **sample rate**, $f_s$,
measured in hertz. A common rate for music is $f_s = 44100\ \text{Hz}$ — at which
one second of mono audio is an array of 44 100 numbers.

The time between samples is therefore

$$
T = \frac{1}{f_s}.
$$

```{prf:definition} Nyquist frequency
:label: def-nyquist
The **Nyquist frequency** is half the sample rate, $f_s / 2$. A sampled signal
can faithfully represent frequency content only *below* this limit.
```

Frequencies above the Nyquist limit are **aliased** — they masquerade as lower
frequencies — which is a key constraint when synthesizing sound digitally.

## To develop

- The sampling theorem and a worked aliasing example.
- Choosing a sample rate; trade-offs of 44.1 kHz vs. 48 kHz.
- How aliasing appears (and is avoided) in oscillator design.
