"""Browser stand-in for ``soundfile``: WAV in/out via the stdlib.

Implements the two functions pyquist uses — ``sf.read`` and ``sf.write`` —
for RIFF WAV (PCM 8/16/24/32) with ``wave`` + numpy, matching soundfile's
conventions (float64 in [-1, 1] on read, 16-bit PCM on write, path or
file-like accepted). Anything else — compressed formats on read, non-WAV on
write — raises a clear ``LibsndfileError``. Delete this stub once the
in-browser kernel stack reaches Pyodide >= 0.28, which ships real soundfile.
"""

import os as _os
import wave as _wave

import numpy as _np

__version__ = "0.12.1.post901"

_BROWSER_MSG = (
    "the browser runtime can only read and write uncompressed WAV (PCM) "
    "files for now. Compressed formats such as MP3, FLAC, and OGG need the "
    "full soundfile library, which requires a newer in-browser Python "
    "runtime. Run this on your own computer to use them."
)


class LibsndfileError(RuntimeError):
    pass


def _as_target(file, probe):
    """Pass file-like objects straight to ``wave.open``; ``str()``-ing one
    would turn it into a bogus filename."""
    return file if hasattr(file, probe) else str(file)


def read(file, dtype="float64", always_2d=False, **kwargs):
    try:
        with _wave.open(_as_target(file, "read"), "rb") as w:
            n_channels = w.getnchannels()
            sampwidth = w.getsampwidth()
            sample_rate = w.getframerate()
            frames = w.readframes(w.getnframes())
    except FileNotFoundError:
        raise LibsndfileError(f"File not found: {file!r}.") from None
    except (_wave.Error, EOFError, OSError):
        # Not a WAV stream, most often a compressed file. `from None` hides
        # the stdlib wave.py traceback behind the plain-language message.
        raise LibsndfileError(
            f"Could not read {file!r} as a WAV file — {_BROWSER_MSG}"
        ) from None

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


def _target_format(file, format):
    """The format soundfile would infer: explicit ``format=``, else the
    path's extension, defaulting to WAV for nameless streams."""
    if format:
        return format.upper()
    name = None
    if isinstance(file, (str, _os.PathLike)):
        name = _os.fspath(file)
    elif isinstance(getattr(file, "name", None), str):
        name = file.name
    if not name:
        return "WAV"
    return (_os.path.splitext(name)[1].lstrip(".") or "WAV").upper()


def write(file, data, samplerate, *, subtype=None, format=None, **kwargs):
    fmt = _target_format(file, format)
    if fmt not in ("WAV", "WAVE"):
        # Don't silently write WAV bytes into a file the caller named .mp3 etc.
        raise LibsndfileError(f"Cannot write {fmt} files in the browser — {_BROWSER_MSG}")

    data = _np.asarray(data, dtype=_np.float64)
    if data.ndim == 1:
        n_channels = 1
    elif data.ndim == 2:
        n_channels = data.shape[1]
    else:
        raise LibsndfileError("data must be 1-D or 2-D")
    pcm = (_np.clip(data, -1.0, 1.0) * 32767.0).round().astype("<i2")
    try:
        with _wave.open(_as_target(file, "write"), "wb") as w:
            w.setnchannels(n_channels)
            w.setsampwidth(2)  # 16-bit PCM regardless of requested subtype
            w.setframerate(int(samplerate))
            w.writeframes(pcm.tobytes())
    except (_wave.Error, OSError) as e:
        raise LibsndfileError(f"Could not write {file!r} — {_BROWSER_MSG}") from e


def __getattr__(name):
    raise AttributeError(
        f"soundfile.{name} is not available in the browser stand-in; {_BROWSER_MSG}"
    )
