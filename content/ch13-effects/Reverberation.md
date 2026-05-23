(reverberation)=
# Reverberation

```{note}
Placeholder section. Develop artificial reverberation.
```

**Reverberation** is the dense wash of reflections a sound picks up in a real
space. Artificial reverb recreates it, either by *algorithm* or by *convolution*.

- **Algorithmic reverb** combines many delay lines and filters to approximate
  the statistics of a room's reflections.
- **Convolution reverb** convolves the sound with an *impulse response* recorded
  in a real space — accurate, but more expensive.

A key descriptor is the **RT60**: the time for the reverb to decay by 60 dB.

## To develop

- Early reflections vs. the late, diffuse tail.
- A simple algorithmic reverb from comb and allpass filters.
- Convolution reverb and impulse responses.
