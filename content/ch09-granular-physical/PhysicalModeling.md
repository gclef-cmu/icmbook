(physical-modeling)=
# Physical Modeling

```{note}
Placeholder section. Develop physical modeling with Pyquist examples.
```

**Physical modeling** synthesizes sound by simulating the mechanics of a
vibrating object instead of describing its waveform directly. The parameters are
*physical* — string length, tension, stiffness — so the results respond
naturally to changes.

The classic introductory example is the **Karplus–Strong** plucked-string
algorithm: a short burst of noise fed into a filtered delay line. More general
**digital waveguide** methods extend this idea to tubes and other resonators
{cite}`smith1992physical`.

## To develop

- The Karplus–Strong algorithm, step by step.
- Delay lines as the core building block (links to {ref}`effects`).
- A brief tour of digital waveguides.
```{seealso}
Delay lines are developed further in {numref}`Chapter %s <effects>`.
```
