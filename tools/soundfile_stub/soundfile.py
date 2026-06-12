"""Browser stand-in for ``soundfile``: WAV in/out via the stdlib.

pyquist touches exactly two functions (``Audio.from_file`` -> ``sf.read``,
``Audio.write`` -> ``sf.write``). This module implements both for RIFF WAV
(PCM 8/16/24/32) using ``wave`` + numpy, matching soundfile's conventions:
``read`` returns float64 in [-1, 1], 1-D for mono and (frames, channels)
otherwise; ``write`` emits 16-bit PCM. Compressed formats (mp3/flac/ogg)
and float WAVs raise a clear error — the real WASM soundfile arrives when
the in-browser kernel stack reaches Pyodide >= 0.28.
"""

import wave as _wave

import numpy as _np

__version__ = "0.12.1.post900"

_BROWSER_MSG = (
    "the browser runtime can only read/write standard WAV (PCM) files for "
    "now — other formats need the full soundfile library, which requires a "
    "newer in-browser Python runtime. Run this on your own computer instead."
)


class LibsndfileError(RuntimeError):
    pass


def read(file, dtype="float64", always_2d=False, **kwargs):
    try:
        with _wave.open(str(file), "rb") as w:
            n_channels = w.getnchannels()
            sampwidth = w.getsampwidth()
            sample_rate = w.getframerate()
            frames = w.readframes(w.getnframes())
    except (_wave.Error, EOFError) as e:
        raise LibsndfileError(f"Could not read {file!r}: {_BROWSER_MSG}") from e

    if sampwidth == 1:  # unsigned 8-bit
        samples = (_np.frombuffer(frames, dtype=_np.uint8).astype(_np.float64) - 128.0) / 128.0
    elif sampwidth == 2:
        samples = _np.frombuffer(frames, dtype="<i2").astype(_np.float64) / 32768.0
    elif sampwidth == 3:  # packed little-endian 24-bit
        raw = _np.frombuffer(frames, dtype=_np.uint8).reshape(-1, 3).astype(_np.int32)
        vals = raw[:, 0] | (raw[:, 1] << 8) | (raw[:, 2] << 16)
        vals = (vals ^ 0x800000) - 0x800000  # sign-extend
        samples = vals.astype(_np.float64) / 8388608.0
    elif sampwidth == 4:
        samples = _np.frombuffer(frames, dtype="<i4").astype(_np.float64) / 2147483648.0
    else:
        raise LibsndfileError(f"Unsupported WAV sample width {sampwidth}: {_BROWSER_MSG}")

    if n_channels > 1:
        samples = samples.reshape(-1, n_channels)
    elif always_2d:
        samples = samples.reshape(-1, 1)
    if dtype != "float64":
        samples = samples.astype(dtype)
    return samples, sample_rate


def write(file, data, samplerate, **kwargs):
    data = _np.asarray(data, dtype=_np.float64)
    if data.ndim == 1:
        n_channels = 1
    elif data.ndim == 2:
        n_channels = data.shape[1]
    else:
        raise LibsndfileError("data must be 1-D or 2-D")
    pcm = (_np.clip(data, -1.0, 1.0) * 32767.0).round().astype("<i2")
    try:
        with _wave.open(str(file), "wb") as w:
            w.setnchannels(n_channels)
            w.setsampwidth(2)  # 16-bit PCM regardless of requested subtype
            w.setframerate(int(samplerate))
            w.writeframes(pcm.tobytes())
    except (_wave.Error, OSError) as e:
        raise LibsndfileError(f"Could not write {file!r}: {_BROWSER_MSG}") from e


def __getattr__(name):
    raise AttributeError(
        f"soundfile.{name} is not available in the browser stand-in; {_BROWSER_MSG}"
    )
