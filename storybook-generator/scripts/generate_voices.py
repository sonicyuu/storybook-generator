#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘本语音生成脚本
读取 metadata.json，遍历所有 voice_segments，调用 MiniMax TTS API 生成音频。
音频以 hex 编码返回，解码后保存为 MP3 文件，并回写 metadata.json 的 file 字段。
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    from config import (
        MINIMAX_API_KEY, MINIMAX_API_BASE, MINIMAX_API_BASE_BJ,
        TTS_MODEL, STORYBOOKS_OUTPUT_DIR
    )
except ImportError:
    print("[WARN] 无法导入 config.py，使用环境变量")
    MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
    MINIMAX_API_BASE = "https://api.minimaxi.com"
    MINIMAX_API_BASE_BJ = "https://api-bj.minimaxi.com"
    TTS_MODEL = "speech-2.8-hd"
    STORYBOOKS_OUTPUT_DIR = "/Users/xiexiaomeng/OpenClawWorkspace/storybooks"

TTS_URLS = [
    f"{MINIMAX_API_BASE}/v1/t2a_v2",
    f"{MINIMAX_API_BASE_BJ}/v1/t2a_v2",
]

# MiniMax 官方合法 emotion 枚举
# 官方值: happy, sad, angry, fearful, disgusted, surprised, calm, fluent, whisper
_EMOTION_MAP = {
    "brave":     "happy",
    "calm":      "calm",
    "fearful":   "fearful",
    "sad":       "sad",
    "surprised": "surprised",
    "angry":     "angry",
    "happy":     "happy",
    "fear":      "fearful",       # 旧名兼容
    "sadness":   "sad",           # 旧名兼容
    "surprise":  "surprised",     # 旧名兼容
    "neutral":   "calm",          # neutral 不在枚举，映射为最接近的 calm
    "contempt":  "angry",         # contempt 不在枚举，映射为 angry
    "disgust":   "disgusted",     # 官方枚举是 disgusted
}

def load_metadata(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_metadata(metadata, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def generate_tts(text, voice_id, emotion, output_path, retry=3):
    """
    调用 MiniMax TTS API，音频以 hex 编码返回。
    emotion 映射到官方合法枚举值：angry, contempt, disgust, fear, neutral, sadness, surprise, happy
    """
    mapped_emotion = _EMOTION_MAP.get(emotion, "neutral")

    payload = {
        "model": TTS_MODEL,
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 1,
            "vol": 2,
            "pitch": 0,
            "emotion": mapped_emotion,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
    }

    for attempt in range(1, retry + 1):
        for url in TTS_URLS:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {MINIMAX_API_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    audio_hex = result.get("data", {}).get("audio", "")
                    if audio_hex:
                        audio_bytes = bytes.fromhex(audio_hex)
                        with open(output_path, "wb") as f:
                            f.write(audio_bytes)
                        print(f"  ✅ {os.path.basename(output_path)} ({len(audio_bytes)//1024}KB)")
                        return True
                    else:
                        print(f"  ⚠️ {url}: {result.get('base_resp', {}).get('status_msg', 'no audio')}")
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                try:
                    err_json = json.loads(err_body)
                    print(f"  ❌ HTTP {e.code}: {err_json.get('base_resp', {}).get('status_msg', err_body[:100])}")
                except:
                    print(f"  ❌ HTTP {e.code}: {err_body[:100]}")
            except Exception as e:
                print(f"  ❌ {url}: {e}")

        if attempt < retry:
            wait = attempt * 3
            print(f"  ⏳ 等待 {wait}s 后重试...")
            time.sleep(wait)

    print(f"  ❌ 失败: {os.path.basename(output_path)}")
    return False

def main(metadata_json_path, voices_output_dir=None):
    print("=" * 60)
    print("🎙️ 绘本语音生成器")
    print("=" * 60)

    metadata = load_metadata(metadata_json_path)
    title = metadata.get("title", "绘本")
    narrator_voice = metadata.get("narrator_voice", "Chinese (Mandarin)_Soft_Girl")
    pages = metadata.get("pages", [])

    if voices_output_dir:
        voices_dir = voices_output_dir
    else:
        story_dir = os.path.join(STORYBOOKS_OUTPUT_DIR, title)
        voices_dir = os.path.join(story_dir, "voices")

    os.makedirs(voices_dir, exist_ok=True)
    print(f"📁 绘本: {title}")
    print(f"📁 语音输出目录: {voices_dir}")
    print(f"🎤 narrator voice: {narrator_voice} (model: {TTS_MODEL})")
    print()

    total_segs = 0
    success_count = 0
    fail_count = 0

    for page in pages:
        page_num = page.get("page_number", 0)
        segments = page.get("voice_segments", [])

        for seg_idx, seg in enumerate(segments, start=1):
            seg_key = f"p{page_num}_s{seg_idx}"
            text = seg.get("text", "").strip()
            emotion = seg.get("emotion", "neutral")
            output_file = os.path.join(voices_dir, f"{seg_key}.mp3")

            if os.path.exists(output_file):
                print(f"  ⏩ {seg_key} 已存在，跳过")
                seg["file"] = f"{seg_key}.mp3"
                continue

            total_segs += 1
            print(f"[TTS] {seg_key}: {text[:40]}... emotion={emotion}")
            if generate_tts(text, narrator_voice, emotion, output_file):
                success_count += 1
                seg["file"] = f"{seg_key}.mp3"
            else:
                fail_count += 1
                seg["file"] = ""

            time.sleep(0.3)

    save_metadata(metadata, metadata_json_path)

    print()
    print("=" * 60)
    print(f"📊 完成！共 {total_segs} 条，成功 {success_count}，失败 {fail_count}")
    print(f"📝 metadata.json 已更新 file 字段")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 generate_voices.py <metadata.json> [voices_output_dir]")
        sys.exit(1)
    metadata_path = sys.argv[1]
    voices_dir = sys.argv[2] if len(sys.argv) > 2 else None
    main(metadata_path, voices_dir)
