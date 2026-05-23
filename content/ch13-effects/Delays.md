(delays)=
# Delays

```{note}
Placeholder section. Develop delay lines and delay-based effects.
```

A **delay line** stores past samples and plays them back later. A single delay
with feedback produces **echo**:

$$
y[n] = x[n] + g \cdot y[n - D],
$$

where $D$ is the delay in samples and $g$ (with $|g| < 1$) sets how quickly the
echoes decay.

Delay lines are everywhere: they also power Karplus–Strong synthesis
({ref}`physical-modeling`) and the reverberation algorithms in the next section.

Modulating the delay time produces a family of effects:

```{list-table}
:header-rows: 1

* - Effect
  - Delay time
  - Modulation
* - Echo
  - Long (100 ms+)
  - None
* - Chorus
  - Short (20–30 ms)
  - Slow, gentle
* - Flanger
  - Very short (1–10 ms)
  - Slow, with feedback
```

## To develop

- Implementing a delay line in Pyquist.
- Feedback, decay, and stability ($|g| < 1$).
- Modulated delays: chorus and flanger.
