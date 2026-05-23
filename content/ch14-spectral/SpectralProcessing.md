(spectral-processing)=
# Spectral Processing

```{note}
Placeholder section. Develop transformations in the frequency domain.
```

Once a sound is represented as an STFT, we can transform it before resynthesis.
This *analysis–transform–synthesis* loop enables effects that are difficult or
impossible in the time domain:

- **Time-stretching** — change duration while holding pitch constant.
- **Pitch-shifting** — change pitch while holding duration constant.
- **Spectral filtering** — attenuate or boost individual frequency bins.
- **Cross-synthesis** — combine the spectral envelope of one sound with the
  excitation of another.

```{admonition} The big idea of Part 4
:class: tip
Effects ({ref}`effects`) work in *time*; spectral processing works in
*frequency*. Many modern tools combine both.
```

## To develop

- Phase-vocoder time-stretching and pitch-shifting.
- Spectral filtering and gating.
- Cross-synthesis and the spectral envelope.
