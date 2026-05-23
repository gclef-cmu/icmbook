(filters)=
# Filters

```{note}
Placeholder section. Develop filter types and parameters with Pyquist examples.
```

A **filter** boosts or attenuates parts of a signal's spectrum. The basic types:

```{list-table}
:header-rows: 1

* - Filter
  - Passes
  - Common use
* - Lowpass
  - Frequencies below the cutoff
  - Darkening a bright tone
* - Highpass
  - Frequencies above the cutoff
  - Removing rumble
* - Bandpass
  - A band around a center frequency
  - Vowel-like, focused tones
* - Notch
  - Everything except a narrow band
  - Removing a specific frequency
```

Two parameters matter most: the **cutoff** (or center) frequency, and the
**resonance** (emphasis near the cutoff).

## To develop

- Applying filters in Pyquist.
- Sweeping cutoff with an envelope or LFO — the classic subtractive gesture.
- A first look at how filters work; full detail in {ref}`spectral`.
