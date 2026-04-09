#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘本 HTML 组装脚本
读取 metadata.json，从 template/index.html 渲染，最终输出完整绘本目录。
使用 MP3-based 语音播放（voice_segments[].file）。
"""

import json
import os
import sys
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    from config import (
        STORYBOOKS_OUTPUT_DIR, TEMPLATE_HTML,
        THEME_MUSIC_MAP, SKILL_DIR
    )
except ImportError:
    SKILL_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    STORYBOOKS_OUTPUT_DIR = "/Users/xiexiaomeng/OpenClawWorkspace/storybooks"
    TEMPLATE_HTML = os.path.join(SKILL_DIR, "template", "index.html")
    THEME_MUSIC_MAP = {
        "adventure": "adventure.mp3", "peaceful": "peaceful.mp3",
        "happy": "happy.mp3", "dreamy": "dreamy.mp3",
        "mysterious": "mysterious.mp3", "sad": "sad.mp3",
        "heroic": "heroic.mp3", "warm_family": "warm_family.mp3",
        "family_rescue": "heroic.mp3", "friendship": "warm_family.mp3",
        "fantasy": "dreamy.mp3",
    }

SKILL_ROOT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SCRIPTS_MUSIC_DIR = os.path.join(SKILL_ROOT_DIR, "music")

def load_metadata(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_pages_data(metadata):
    """
    构建 PAGES_DATA 数组。
    第0项为封面数据；第1-N项为内容页（含 voice_segments）。
    """
    pages_data = []
    pages = metadata.get("pages", [])

    # 内容页（含 voice_segments）
    for page in pages:
        page_num = page.get("page_number", 0)
        image_path = page.get("image_path", f"images/page_{page_num}.png")
        page_text = page.get("text", "")
        voice_segments = page.get("voice_segments", [])
        emotion = page.get("emotion", "calm")

        if not voice_segments:
            voice_segments = [
                {"type": "narrator", "text": page_text, "emotion": emotion, "file": ""}
            ]
        else:
            # 确保 file 字段有 voices/ 前缀
            for seg in voice_segments:
                if seg.get("file") and not seg["file"].startswith("voices/"):
                    seg["file"] = "voices/" + seg["file"]

        pages_data.append({
            "page_number": page_num,
            "text": page_text,
            "image": image_path,
            "emotion": emotion,
            "voice_segments": voice_segments
        })

    return pages_data

def select_background_music(metadata):
    """根据主题选择背景音乐文件"""
    theme = metadata.get("theme", "")
    music_file = THEME_MUSIC_MAP.get(theme, "peaceful.mp3")
    return f"music/{music_file}"

def main(metadata_json_path):
    print("=" * 60)
    print("🎨 绘本 HTML 组装器")
    print("=" * 60)

    metadata = load_metadata(metadata_json_path)
    title = metadata.get("title", "绘本")
    # 自动设置作者：优先用 metadata 中的 author，否则取第一个角色名
    author = metadata.get("author", "")
    if not author or author == "小朋友":
        characters = metadata.get("characters", [])
        if characters:
            author = characters[0].get("name", "小朋友")
        else:
            author = "小朋友"
    created_at = metadata.get("created_at", "")
    theme = metadata.get("theme", "")

    # 输出目录
    output_dir = os.path.join(STORYBOOKS_OUTPUT_DIR, title)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "voices"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "music"), exist_ok=True)

    print(f"📁 绘本目录: {output_dir}")
    print(f"📚 标题: {title}")

    # ── 读取模板 HTML ───────────────────────────────────────────
    if not os.path.exists(TEMPLATE_HTML):
        print(f"❌ 模板不存在: {TEMPLATE_HTML}")
        return

    with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
        html_template = f.read()

    # ── 注入变量 ───────────────────────────────────────────────
    pages_json = build_pages_data(metadata)
    pages_json_str = json.dumps(pages_json, ensure_ascii=False)

    music_file = select_background_music(metadata)

    html_out = html_template
    html_out = html_out.replace("{{TITLE}}", title)
    html_out = html_out.replace("{{AUTHOR}}", author)
    html_out = html_out.replace("{{DATE}}", created_at)
    html_out = html_out.replace("{{MUSIC_FILE}}", music_file)
    html_out = html_out.replace("{{PAGES_JSON}}", pages_json_str)

    # ── 写 HTML ─────────────────────────────────────────────────
    html_out_path = os.path.join(output_dir, "index.html")
    with open(html_out_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"✅ HTML 写入: {html_out_path}")

    # ── 复制背景音乐 ─────────────────────────────────────────────
    # 始终复制到 background.mp3（HTML 里写死的是 background.mp3）
    src_music = os.path.join(SCRIPTS_MUSIC_DIR, os.path.basename(music_file))
    dst_music = os.path.join(output_dir, "music", "background.mp3")
    if os.path.exists(src_music):
        shutil.copy2(src_music, dst_music)
        print(f"✅ 背景音乐: {dst_music} (source: {os.path.basename(music_file)})")
    else:
        print(f"⚠️ 背景音乐不存在: {src_music}")

    # ── 复制 metadata.json ─────────────────────────────────────
    dst_metadata = os.path.join(output_dir, "metadata.json")
    if os.path.abspath(metadata_json_path) != os.path.abspath(dst_metadata):
        shutil.copy2(metadata_json_path, dst_metadata)
        print(f"✅ metadata.json 已复制")

    print()
    print("=" * 60)
    print(f"🎉 绘本生成完成！")
    print(f"📂 路径: {output_dir}")
    print(f"🌐 打开: file://{os.path.abspath(html_out_path)}")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 build_html.py <metadata.json>")
        sys.exit(1)
    main(sys.argv[1])
