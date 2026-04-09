#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘本图片生成脚本
读取 metadata.json，遍历每页的 image_prompt，调用 MiniMax 图片 API 生成封面+每页图。
API: POST https://api.minimaxi.com/v1/image_generation
返回: JSON { "data": { "image_base64": [...] } } 或 { "data": { "image_urls": [...] } }
生成后自动更新 metadata.json 中的 image_path 字段。
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import base64

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    from config import (
        MINIMAX_API_KEY, MINIMAX_API_BASE, MINIMAX_API_BASE_BJ,
        IMAGE_MODEL, STORYBOOKS_OUTPUT_DIR
    )
except ImportError:
    print("[WARN] 无法导入 config.py，使用环境变量")
    MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
    MINIMAX_API_BASE = "https://api.minimaxi.com"
    MINIMAX_API_BASE_BJ = "https://api-bj.minimaxi.com"
    IMAGE_MODEL = "image-01"
    STORYBOOKS_OUTPUT_DIR = "/Users/xiexiaomeng/OpenClawWorkspace/storybooks"

IMAGE_URLS = [
    f"{MINIMAX_API_BASE}/v1/image_generation",
    f"{MINIMAX_API_BASE_BJ}/v1/image_generation",
]

def load_metadata(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_metadata(metadata, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def generate_image(prompt, output_path, size="1:1", retry=3):
    """
    调用 MiniMax 图片生成 API。
    size: "1:1"(封面 3:4) 或 "16:9"(内容页)
    """
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "aspect_ratio": size,
        "n": 1,
        "response_format": "base64"   # 优先用 base64，不依赖 URL 时效
    }

    for attempt in range(1, retry + 1):
        for url in IMAGE_URLS:
            print(f"  [IMG Attempt {attempt}] {prompt[:60]}...")
            req = urllib.request.Request(
                url,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {MINIMAX_API_KEY}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

                    # 优先取 base64
                    image_data = None
                    base64_list = result.get("data", {}).get("image_base64", [])
                    if base64_list:
                        image_data = base64.b64decode(base64_list[0])
                    else:
                        # 备选：取 URL 并下载
                        image_urls = result.get("data", {}).get("image_urls", [])
                        if image_urls:
                            img_url = image_urls[0]
                            img_req = urllib.request.Request(img_url)
                            with urllib.request.urlopen(img_req, timeout=60) as img_resp:
                                image_data = img_resp.read()

                    if image_data:
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        size_kb = os.path.getsize(output_path) // 1024
                        print(f"  ✅ 生成成功: {output_path} ({size_kb}KB)")
                        return True
                    else:
                        msg = result.get("base_resp", {}).get("status_msg", str(result)[:100])
                        print(f"  ⚠️ {url}: {msg}")
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                try:
                    err_json = json.loads(err_body)
                    print(f"  ❌ HTTP {e.code}: {err_json.get('base_resp', {}).get('status_msg', err_body[:150])}")
                except:
                    print(f"  ❌ HTTP {e.code}: {err_body[:150]}")
            except Exception as e:
                print(f"  ❌ {url}: {e}")

        if attempt < retry:
            wait = attempt * 5
            print(f"  ⏳ 等待 {wait}s 后重试...")
            time.sleep(wait)

    print(f"  ❌ 最终失败: {output_path}")
    return False

def main(metadata_json_path, story_output_dir=None):
    print("=" * 60)
    print("📖 绘本图片生成器")
    print("=" * 60)

    metadata = load_metadata(metadata_json_path)
    title = metadata.get("title", "绘本")
    style_prompt = metadata.get("stylePrompt", "")
    pages = metadata.get("pages", [])

    if not pages:
        print("❌ pages 为空，请检查 metadata.json")
        return

    # 确定绘本输出目录
    if story_output_dir:
        output_dir = story_output_dir
    else:
        output_dir = os.path.join(STORYBOOKS_OUTPUT_DIR, title, "images")

    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 输出目录: {output_dir}")
    print(f"📚 绘本: {title}，共 {len(pages)} 页 + 封面")
    print(f"🖼️  模型: {IMAGE_MODEL}")
    print()

    success_count = 0
    fail_count = 0

    # ── 生成封面 ────────────────────────────────────────────────
    # 引用全部角色的标准化 appearance
    char_parts = []
    for c in metadata.get("characters", []):
        name = c.get("name", "")
        appearance = c.get("appearance", "")
        if name and appearance:
            char_parts.append(f"{name}({appearance})")
    role_line = ", ".join(char_parts) if char_parts else "故事角色"

    # 复用第1页的场景作为封面背景
    first_page = pages[0] if pages else {}
    first_prompt = first_page.get("image_prompt", "")
    scene_line = "故事主题场景"
    action_line = "温馨开场画面"
    for line in first_prompt.split("\n"):
        l = line.strip()
        if l.startswith("[场景]"):
            scene_line = l.replace("[场景]", "").strip()
        elif l.startswith("[动作]"):
            action_line = l.replace("[动作]", "").strip()

    cover_prompt = (
        f"[角色] {role_line}\n"
        f"[场景] {scene_line}\n"
        f"[动作] {action_line}\n"
        f"[风格] {style_prompt}，与本绘本的画风保持完全一致"
    )
    print(f"[COVER] {role_line[:60]}...")
    cover_path = os.path.join(output_dir, "cover.png")
    if os.path.exists(cover_path):
        print(f"  ⏩ 封面已存在，跳过")
    elif generate_image(cover_prompt, cover_path, size="3:4"):
        success_count += 1
        metadata["_cover_image_path"] = "images/cover.png"
    else:
        fail_count += 1

    print()

    # ── 生成每页图片 ────────────────────────────────────────────
    for page in pages:
        page_num = page.get("page_number", 0)
        image_prompt_raw = page.get("image_prompt", "")
        page_path = os.path.join(output_dir, f"page_{page_num}.png")

        # 已有则跳过
        if os.path.exists(page_path):
            print(f"  ⏩ 第 {page_num} 页已存在，跳过")
            page["image_path"] = f"images/page_{page_num}.png"
            continue

        full_prompt = image_prompt_raw if image_prompt_raw else (
            f"[角色] 故事角色\n"
            f"[场景] 故事场景\n"
            f"[动作] 主要情节\n"
            f"[风格] {style_prompt}，与本绘本的画风保持完全一致"
        )

        print(f"[IMG] 第 {page_num} 页...")
        if generate_image(full_prompt, page_path, size="16:9"):
            success_count += 1
            page["image_path"] = f"images/page_{page_num}.png"
        else:
            fail_count += 1

        time.sleep(1)  # API 限速

    # 保存更新后的 metadata
    save_metadata(metadata, metadata_json_path)

    print()
    print("=" * 60)
    print(f"📊 完成！成功 {success_count} 页，失败 {fail_count} 页")
    print(f"📁 图片目录: {output_dir}")
    print(f"📝 metadata.json 已更新 image_path 字段")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 generate_images.py <metadata.json> [story_output_dir]")
        sys.exit(1)

    metadata_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    main(metadata_path, output_dir)
