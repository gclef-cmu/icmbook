(quantization)=
# Quantization

```{note}
Placeholder section. Develop bit depth, quantization error, and dynamic range.
```

Sampling discretizes a signal in *time*; **quantization** discretizes it in
*amplitude*. Each sample must be stored with a finite number of bits, so its
value is rounded to the nearest available level.

The **bit depth** sets the number of levels: $b$ bits gives $2^b$ levels. CD
audio uses 16 bits ($65\,536$ levels); floating-point audio, common inside
synthesis code, effectively removes this concern during computation.

## To develop

- Quantization error as noise, and the rule of thumb $\approx 6\ \text{dB}$ of
  dynamic range per bit.
- Why intermediate computation uses floating point.
- Dither, briefly.

```{admonition} Practical note
:class: tip
While synthesizing in Pyquist you will work with floating-point samples, usually
in the range $[-1, 1]$. Quantization matters mainly when you *write a file* or
*send audio to hardware*.
```
