(midi-basics)=
# MIDI Basics

```{note}
Placeholder section. Develop the MIDI message model and Pyquist integration.
```

**MIDI** (Musical Instrument Digital Interface) carries *control data*, not
audio. Its core events are **note-on** and **note-off** messages, each with:

```{glossary}
Note number
  An integer pitch, 0–127, where 60 is middle C.

Velocity
  How hard the note was struck, 0–127 — usually mapped to loudness.

Channel
  One of 16 streams, often used to address different instruments.
```

A MIDI note number $m$ converts to frequency with

$$
f = 440 \cdot 2^{(m - 69)/12}.
$$

## To develop

- The common MIDI messages and their bytes.
- Reading a MIDI file or live input in Pyquist.
- Mapping MIDI notes to synthesis parameters.
