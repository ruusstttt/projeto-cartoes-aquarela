"""Trilha instrumental original dos Reels de Natal."""

import math
import wave

import numpy as np


def compor(filename, total=20.4, *, extended=False):
    # A 3/4 fingerpicked cue, composed to resolve on the last shot.
    sr = 48000
    mix = np.zeros((round(total * sr), 2), dtype=np.float64)
    rng = np.random.default_rng(762)


    def place(at, mono, level, pan=0):
        i = round(at * sr)
        n = min(len(mono), len(mix) - i)
        if n > 0:
            mix[i : i + n] += (
                level
                * mono[:n, None]
                * np.array([math.sqrt((1 - pan) / 2), math.sqrt((1 + pan) / 2)])
            )


    def pluck(midi, at, amp, pan=0, hold=2.5, bell=False):
        f = 440 * 2 ** ((midi - 69) / 12)
        t = np.arange(round(sr * hold)) / sr
        signal = np.zeros_like(t)
        if bell:
            for ratio, power, dec in [
                (1, 1, 1.15),
                (2.008, 0.30, 0.65),
                (3.98, 0.13, 0.4),
                (5.45, 0.055, 0.19),
            ]:
                signal += power * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / dec)
        else:
            position = rng.uniform(0.18, 0.26)
            for h in range(1, 10):
                power = np.sin(np.pi * h * position) / (h**1.48)
                signal += (
                    power
                    * np.sin(2 * np.pi * f * h * (1 + 0.000009 * h * h) * t)
                    * np.exp(-t * (1.42 + 0.32 * h))
                )
            signal += rng.normal(0, 0.017, len(t)) * np.exp(-t * 160)
        signal *= np.minimum(1, t / 0.008) * np.minimum(1, (hold - t) / 0.05)
        place(at, signal, amp, pan)
        for delay, level in [(0.039, 0.10), (0.073, 0.075), (0.121, 0.05)]:
            place(at + delay, signal, amp * level, -pan)


    beat = 0.60
    chords = [
        [50, 57, 62, 66, 69],
        [47, 54, 59, 62, 66],
        [43, 55, 59, 62, 66],
        [45, 52, 57, 62, 64],
        [50, 57, 62, 66, 69],
        [47, 54, 59, 62, 69],
        [43, 55, 59, 62, 66],
        [45, 52, 57, 61, 64],
        [43, 55, 59, 62, 67],
        [45, 52, 57, 62, 64],
        [50, 57, 62, 66, 69],
    ]
    if extended:
        chords = chords[:8] + chords[4:8] + chords[8:]
    for b, ch in enumerate(chords):
        start = 0.10 + b * 3 * beat
        pattern = [
            (0, 0, 0.24),
            (0.49, 2, 0.17),
            (1.0, 3, 0.18),
            (1.52, 1, 0.155),
            (2.02, 4, 0.16),
            (2.52, 2, 0.115),
        ]
        if b == len(chords) - 1:
            pattern = [
                (0, 0, 0.25),
                (0.12, 1, 0.19),
                (0.24, 2, 0.16),
                (0.39, 3, 0.18),
                (0.58, 4, 0.13),
            ]
        for j, (o, n, amp) in enumerate(pattern):
            pluck(
                ch[n],
                start + o * beat + rng.uniform(-0.008, 0.008),
                amp * rng.uniform(0.87, 1.05),
                [-0.17, 0.19, -0.09, 0.22, 0.08, -0.13][j],
            )
    for at, pitch, level in [
        (0.56, 78, 0.031),
        (3.72, 74, 0.05),
        (6.4, 78, 0.045),
        (8.0, 81, 0.038),
        (11.63, 74, 0.05),
        (14.68, 78, 0.047),
        (16.2, 81, 0.039),
        (18.48, 78, 0.033),
    ]:
        pluck(pitch, at, level, 0.26, 1.8, True)
    mix *= min(2.9, 0.78 / max(1e-6, np.abs(mix).max()))
    mix[-round(0.40 * sr) :] *= np.linspace(1, 0, round(0.40 * sr))[:, None]
    with wave.open(str(filename), "wb") as out:
        out.setparams((2, 2, sr, 0, "NONE", "not compressed"))
        out.writeframes(np.int16(np.clip(mix, -1, 1) * 32767).tobytes())
