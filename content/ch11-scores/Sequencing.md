(sequencing)=
# Sequencing

```{note}
Placeholder section. Develop scheduling and combining events with Pyquist.
```

**Sequencing** turns a score into sound by *scheduling*: deciding when each event
starts and letting the synthesis engine render it. Two operations do most of the
work:

- **Sequence** — place events one after another in time.
- **Mix** — overlap events so they sound together.

With these, plus the ability to *transform* a sequence (transpose, stretch,
repeat), you can assemble whole pieces from small fragments.

## To develop

- Building a melody by sequencing notes.
- Layering parts by mixing.
- Reusable transformations: transpose, time-scale, repeat.
