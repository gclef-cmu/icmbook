# 3. Additive Synthesis

In Chapter 2, we synthesized our first sounds, but they were all sine waves. A sine wave is a useful starting point, but it sounds thin and featureless compared to richer sounds we encounter in music:

:::{audio}
[A bare sine wave at 220 Hz](./assets/audio-intro-sine.wav)

A sine wave at 220 Hz.
:::

:::{audio}
[A richer tone at 220 Hz](./assets/audio-intro-rich.wav)

A richer tone, also at 220 Hz.
:::

Hopefully you agree that the second has a fuller, brighter quality. How do we get from one to the other? Here we will explore _additive synthesis_, a technique for synthesizing richer tones by summing multiple sine waves together. It is the first synthesis technique we'll study that's capable of producing non-trivial, musically interesting tones.

This chapter develops additive synthesis as a "full stack" example, from mathematical principles to implementation to modern practice. We start with the sine wave as an elementary building block, formalize the mathematical result (the _Fourier series_) that lets us decompose any periodic sound into sine waves, and then introduce _wavetable synthesis_, an efficient algorithm that makes additive synthesis practical.
