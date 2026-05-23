(frequency-modulation)=
# Frequency Modulation

```{note}
Placeholder section. Develop FM synthesis with Pyquist examples.
```

In **frequency modulation**, the modulator controls the carrier's *frequency*. A
basic two-oscillator FM instrument is

$$
x[n] = \sin\!\left(2\pi f_c \frac{n}{f_s} + I \cdot \sin\!\left(2\pi f_m \frac{n}{f_s}\right)\right),
$$

where $f_c$ is the carrier, $f_m$ the modulator, and $I$ the **modulation
index**. Larger $I$ produces more sidebands and a brighter tone.

```{admonition} Why FM mattered
:class: note
Chowning's insight was that FM produces complex, evolving spectra from just two
oscillators — far cheaper than additive synthesis on 1970s hardware
{cite}`chowning1973synthesis`. It became the basis of a generation of digital
synthesizers.
```

## To develop

- The carrier-to-modulator ratio and harmonic vs. inharmonic spectra.
- Animating $I$ with an envelope for evolving brightness.
- Multi-operator FM.
