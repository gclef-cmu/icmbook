(installation)=
# Installation

```{note}
Placeholder. Replace with the official install steps once Pyquist is published.
```

You will need **Python 3.10+** and the course audio library, **Pyquist**.

## Recommended setup

```sh
# Create and activate an environment
conda create -n icm python=3.11
conda activate icm

# Install the libraries used in the book
pip install numpy matplotlib jupyter

# Install Pyquist (TODO: replace with the official source)
pip install pyquist
```

## Check your installation

```python
import pyquist
print(pyquist.__version__)
```

If that runs without error, you are ready for the {doc}`next section <HelloSound>`.

```{admonition} Trouble?
:class: warning
Audio playback depends on your operating system's sound setup. If you cannot
hear output, first confirm that other applications can play sound, then check
the course website for platform-specific notes.
```
