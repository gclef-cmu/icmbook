(what-is-computer-music)=
# What is computer music?

**Computer music** is the use of computers to create, perform, analyze, and
transform music and sound. That covers a lot of ground — from synthesizing a
single tone, to designing audio effects, to writing programs that compose entire
pieces.

This book emphasizes *synthesis* and *programming*; recording, mixing, and music
information retrieval are large neighboring fields with their own courses.

It helps to separate two related activities:

```{glossary}
Sound synthesis
  Generating and shaping audio signals — the *sound* itself.

Composition and control
  Describing *musical structure* — which notes, when, how loud — and the
  processes that produce it.
```

A central theme of this book is that both activities are, in the end, **programs**.
A sound is a function evaluated over time; a composition is an algorithm that
decides what those functions should be. Once we can express musical ideas as
code, we can explore them at a speed and scale that is impossible by hand
{cite}`roads1996computer`.

## Sound as signal

Physically, sound is a pressure wave traveling through air. A computer represents
that wave as a **signal**: a sequence of numbers, called *samples*, measured many
thousands of times per second. {numref}`Chapter %s <digital-audio>` makes this
precise. For now, the key idea is simple:

> If we can compute the right sequence of numbers, we can produce any sound.

```{admonition} Why program music?
:class: note
Programming forces us to be precise about musical ideas, and it makes them
*reusable*: a synthesis technique written once can be applied to thousands of
notes, or shared, modified, and built upon by others.
```

## What's next

The {doc}`next section <AShortHistory>` traces how this idea developed, and
{numref}`Chapter %s <getting-started>` gets you generating sound with Pyquist.
