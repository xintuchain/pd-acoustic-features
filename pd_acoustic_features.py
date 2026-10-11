#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD Acoustic Features — 单文件最小示例（免费版）
================================================

输入一段语音音频，输出 8 个已被广泛研究的声学扰动特征：

    jitter_local / jitter_rap / jitter_ppq5 / shimmer_local
    shimmer_db / hnr_mean / f0_mean / f0_sd_semitone

依赖（仅两个）：**parselmouth**（Praat 的 Python 接口）+ **numpy**

    pip install parselmouth numpy

用法：

    python pd_acoustic_features.py voice.wav

    # 或作为库调用
    from pd_acoustic_features import extract_acoustic_features
    feats = extract_acoustic_features("voice.wav")

⚠️ **本工具只输出声学特征值，不做患病判断、不做严重度分级、不做诊断。**
   完整源码（`tests/` 自测、HTTP 服务封装、完整文档）见付费版。

许可：GPL-3.0-or-later（全文见 LICENSE）。
实现：每个特征对应的 Praat 命令与参数见下方 FEATURE_SCHEMA 与 README「实现」列。
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional

import numpy as np
import parselmouth
from parselmouth.praat import call

# ---- 分析参数（Praat 惯例默认值）-------------------------------------------
PITCH_FLOOR_HZ = 75.0          # 基频下限：覆盖成人男声
PITCH_CEILING_HZ = 600.0       # 基频上限：覆盖成人女声与较高基频
PERIOD_FLOOR = 0.0001          # 周期下限（s）
PERIOD_CEILING = 0.02          # 周期上限（s）
MAX_PERIOD_FACTOR = 1.3        # 最大周期因子
MAX_AMPLITUDE_FACTOR = 1.6     # 最大幅度因子
HARMONICITY_TIME_STEP = 0.01   # Harmonicity 时间步（s）
HARMONICITY_MIN_PITCH = 75.0   # Harmonicity 最低基频（Hz）
HARMONICITY_SILENCE_THRESHOLD = 0.1
HARMONICITY_PERIODS_PER_WINDOW = 1.0
F0_SEMITONE_REFERENCE_HZ = 27.5  # 半音基准

# 特征定义与实现来源（Praat 命令 + 参数）
FEATURE_SCHEMA: Dict[str, Dict[str, str]] = {
    "jitter_local": {
        "unit": "ratio",
        "desc": "局部基频周期扰动（无量纲比例）",
        "impl": 'Praat "Get jitter (local)"：周期 0.1–20 ms，最大周期因子 1.3',
    },
    "jitter_rap": {
        "unit": "ratio",
        "desc": "3 点相对平均基频扰动（RAP）",
        "impl": 'Praat "Get jitter (rap)"：周期 0.1–20 ms，最大周期因子 1.3',
    },
    "jitter_ppq5": {
        "unit": "ratio",
        "desc": "5 点基频扰动商（PPQ5）",
        "impl": 'Praat "Get jitter (ppq5)"：周期 0.1–20 ms，最大周期因子 1.3',
    },
    "shimmer_local": {
        "unit": "ratio",
        "desc": "局部幅度扰动（无量纲比例）",
        "impl": 'Praat "Get shimmer (local)"：最大幅度因子 1.6',
    },
    "shimmer_db": {
        "unit": "dB",
        "desc": "幅度扰动（分贝制）",
        "impl": 'Praat "Get shimmer (local_dB)"：参数同 shimmer_local',
    },
    "hnr_mean": {
        "unit": "dB",
        "desc": "谐噪比均值",
        "impl": 'Praat "To Harmonicity (cc)"→"Get mean"（时间步 0.01 s，最低基频 75 Hz）',
    },
    "f0_mean": {
        "unit": "Hz",
        "desc": "基频均值（仅统计有声帧）",
        "impl": 'Praat "To Pitch"（75–600 Hz）→ 有声帧均值',
    },
    "f0_sd_semitone": {
        "unit": "semitone",
        "desc": "基频标准差（半音，相对 27.5 Hz）",
        "impl": 'Praat "To Pitch" → 12·log2(F0/27.5) 的标准差',
    },
}


def _semitone_to_hz(semitone_from_27_5hz: float) -> float:
    """半音制（相对 27.5 Hz）转回 Hz。"""
    return 27.5 * (2.0 ** (semitone_from_27_5hz / 12.0))


def _safe_round(value: Any, digits: int) -> Optional[float]:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(v) or np.isinf(v):
        return None
    return round(v, digits)


def _praat_call(obj: Any, command: str, *args: Any) -> Optional[float]:
    """安全调用 Praat 命令；对象缺失或调用失败时返回 None。"""
    if obj is None:
        return None
    try:
        return call(obj, command, *args)
    except Exception:  # noqa: BLE001
        return None


def extract_acoustic_features(audio_path: str) -> Dict[str, Any]:
    """从单个音频文件提取标准声学特征；失败时返回 {"error": ..., "file": ...}。"""
    if not os.path.isfile(audio_path):
        return {"error": "file_not_found", "file": audio_path}

    try:
        snd = parselmouth.Sound(audio_path)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}", "file": audio_path}

    out: Dict[str, Any] = {"file": audio_path}

    pp = _praat_call(snd, "To PointProcess (periodic, cc)", PITCH_FLOOR_HZ, PITCH_CEILING_HZ)
    out["jitter_local"] = _safe_round(
        _praat_call(pp, "Get jitter (local)", 0, 0, PERIOD_FLOOR, PERIOD_CEILING, MAX_PERIOD_FACTOR), 6)
    out["jitter_rap"] = _safe_round(
        _praat_call(pp, "Get jitter (rap)", 0, 0, PERIOD_FLOOR, PERIOD_CEILING, MAX_PERIOD_FACTOR), 6)
    out["jitter_ppq5"] = _safe_round(
        _praat_call(pp, "Get jitter (ppq5)", 0, 0, PERIOD_FLOOR, PERIOD_CEILING, MAX_PERIOD_FACTOR), 6)

    shimmer_obj = [snd, pp] if pp is not None else None
    out["shimmer_local"] = _safe_round(
        _praat_call(shimmer_obj, "Get shimmer (local)", 0, 0, PERIOD_FLOOR, PERIOD_CEILING,
                    MAX_PERIOD_FACTOR, MAX_AMPLITUDE_FACTOR), 6)
    out["shimmer_db"] = _safe_round(
        _praat_call(shimmer_obj, "Get shimmer (local_dB)", 0, 0, PERIOD_FLOOR, PERIOD_CEILING,
                    MAX_PERIOD_FACTOR, MAX_AMPLITUDE_FACTOR), 4)

    harmonicity = _praat_call(snd, "To Harmonicity (cc)", HARMONICITY_TIME_STEP,
                              HARMONICITY_MIN_PITCH, HARMONICITY_SILENCE_THRESHOLD,
                              HARMONICITY_PERIODS_PER_WINDOW)
    out["hnr_mean"] = _safe_round(_praat_call(harmonicity, "Get mean", 0, 0), 3)

    try:
        pitch = snd.to_pitch(time_step=None, pitch_floor=PITCH_FLOOR_HZ, pitch_ceiling=PITCH_CEILING_HZ)
        freqs = np.asarray(pitch.selected_array["frequency"], dtype=float)
        voiced = freqs[np.isfinite(freqs) & (freqs > 0)]
    except Exception:  # noqa: BLE001
        voiced = np.array([])

    if voiced.size:
        out["f0_mean"] = _safe_round(float(np.mean(voiced)), 2)
        out["f0_sd_semitone"] = _safe_round(
            float(np.std(12.0 * np.log2(voiced / F0_SEMITONE_REFERENCE_HZ))), 3)
    else:
        out["f0_mean"] = None
        out["f0_sd_semitone"] = None

    core = ["jitter_local", "shimmer_db", "hnr_mean", "f0_mean"]
    if all(out.get(k) is None for k in core):
        return {"error": "no_voiced_segment", "file": audio_path}
    return out


def extract_batch(audio_paths: List[str]) -> List[Dict[str, Any]]:
    """批量提取，逐文件返回结果（单文件失败不影响其余）。"""
    return [extract_acoustic_features(p) for p in audio_paths]


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("用法: python pd_acoustic_features.py <audio_file>", file=sys.stderr)
        return 1
    result = extract_acoustic_features(argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
