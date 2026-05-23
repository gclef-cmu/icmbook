(additive-synthesis)=
# Additive Synthesis

```{note}
Placeholder section. Develop additive synthesis with runnable Pyquist examples.
```

**Additive synthesis** builds a tone by summing sinusoids — typically members of
the **harmonic series**, at integer multiples of a fundamental frequency $f_0$:

$$
x[n] = \sum_{k=1}^{K} A_k \cdot \sin\!\left(2\pi (k f_0) \frac{n}{f_s}\right).
$$

The amplitudes $A_k$ determine the timbre. This is the most direct expression of
the idea that **timbre is spectrum**.

```{admonition} Design idea
:class: tip
A sawtooth-like tone has $A_k \propto 1/k$; a square-like tone keeps only odd
$k$. Try giving the $A_k$ their own envelopes so the timbre evolves over time.
```

## To develop

- Building a harmonic tone from a list of amplitudes.
- Inharmonic spectra (bells, metallic sounds).
- Cost of additive synthesis, and why modulation methods (Chapter 6) were
  invented as a cheaper alternative {cite}`chowning1973synthesis`.
