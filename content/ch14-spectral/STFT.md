(stft)=
# The Short-Time Fourier Transform

```{note}
Placeholder section. Develop the STFT and the spectrogram.
```

The **Fourier transform** decomposes a signal into the sinusoids that make it up.
Because the spectrum of music *changes over time*, we apply it to short,
overlapping **frames**: this is the **short-time Fourier transform** (STFT).

Plotting the magnitude of the STFT over time gives a **spectrogram** — a picture
of how energy is distributed across frequency as the sound evolves.

Frame length sets a trade-off: longer frames give finer frequency detail but blur
events in time.

## To develop

- Framing, windowing, and overlap.
- Reading a spectrogram.
- The time–frequency resolution trade-off.
```{seealso}
For the underlying mathematics of frequency, see {doc}`../appendix/Math` and a
dedicated DSP text such as {cite}`puckette2007theory`.
```
