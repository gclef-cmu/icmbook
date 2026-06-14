"""Browser stub for the ``sounddevice`` package (Pyodide / WebAssembly).

Real-time audio hardware I/O (PortAudio) does not exist in the browser
sandbox. This stub lets ``import pyquist`` succeed; ``pq.play()`` never
touches sounddevice inside a notebook kernel (it renders an inline HTML5
player via ``IPython.display.Audio``). Anything that genuinely needs the
sound card raises a clear error instead of crashing at import time.

``pyquist.device`` only touches this module at import time via
``_apply_persisted_defaults()``, which is a no-op without a cached
device-defaults file — and the browser filesystem starts empty.
"""

__version__ = "0.5.1.post901"


class PortAudioError(RuntimeError):
    pass


class _Default:
    """Mimics sounddevice.default: attribute bag the real package exposes."""

    def __init__(self):
        self.device = (None, None)
        self.samplerate = None
        self.channels = None
        self.dtype = ("float32", "float32")
        self.latency = (None, None)


default = _Default()


def _unavailable(name):
    # Capability-first message: pyquist.record() calls query_devices() before
    # rec(), so leading with the function name would blame the wrong call.
    raise PortAudioError(
        "Live audio devices aren't available in the browser: sounddevice "
        "drives a real sound card (PortAudio), which the WebAssembly sandbox "
        "can't reach. In this book pq.play() still works — it shows an inline "
        "player under the cell. Recording (pq.record), device playback "
        "(pq.play(..., force_sounddevice=True)), and device queries only run "
        "when you execute Python on your own computer. "
        f"(triggered by sounddevice.{name}())"
    )


def play(*args, **kwargs):
    _unavailable("play")


def stop(*args, **kwargs):
    _unavailable("stop")


def wait(*args, **kwargs):
    _unavailable("wait")


def rec(*args, **kwargs):
    _unavailable("rec")


def query_devices(*args, **kwargs):
    _unavailable("query_devices")


def check_input_settings(*args, **kwargs):
    _unavailable("check_input_settings")


def check_output_settings(*args, **kwargs):
    _unavailable("check_output_settings")
