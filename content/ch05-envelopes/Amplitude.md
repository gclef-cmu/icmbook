(amplitude)=
# Amplitude and Loudness

```{note}
Placeholder section. Develop amplitude control and perceived loudness.
```

**Amplitude** is the size of a signal; multiplying a signal by a number scales
it. Perceived **loudness**, however, is roughly *logarithmic*, which is why audio
levels are measured in **decibels**:

$$
L_\text{dB} = 20 \log_{10}\!\left(\frac{A}{A_\text{ref}}\right).
$$

A useful landmark: a factor of 2 in amplitude is about $+6\ \text{dB}$ — a modest
but clearly audible change in loudness.

## To develop

- Linear gain vs. decibels in practice.
- Avoiding clipping: keeping samples within range.
- Why constant amplitude sounds lifeless — motivating envelopes.
