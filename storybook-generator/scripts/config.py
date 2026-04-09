# -*- coding: utf-8 -*-
"""
绘本生成器配置文件
MiniMax Coding Plan API 配置
"""
import os

# MiniMax API 配置（Coding Plan Key）
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "sk-cp-xxx")
MINIMAX_API_BASE = "https://api.minimaxi.com"       # 主节点
MINIMAX_API_BASE_BJ = "https://api-bj.minimaxi.com"  # 备用节点

# MiniMax TTS 模型（推荐 speech-2.8-hd，支持 emotion）
TTS_MODEL = "speech-2.8-hd"

# MiniMax 图片生成模型
IMAGE_MODEL = "image-01"

# 可选的 narrator voice 列表（随机选择）
# 已验证可用的中文女声
NARRATOR_VOICES = [
    "Chinese (Mandarin)_Warm_Bestie",
    "female-shaonv",
    "Chinese (Mandarin)_Soft_Girl",
]

# 背景音乐与主题的对应关系
THEME_MUSIC_MAP = {
    "adventure":    "adventure.mp3",
    "peaceful":     "peaceful.mp3",
    "happy":        "happy.mp3",
    "dreamy":       "dreamy.mp3",
    "mysterious":  "mysterious.mp3",
    "sad":          "sad.mp3",
    "heroic":      "heroic.mp3",
    "warm_family":  "warm_family.mp3",
    "family_rescue": "heroic.mp3",
    "friendship":   "warm_family.mp3",
    "fantasy":      "dreamy.mp3",
}

# 绘本输出根目录
STORYBOOKS_OUTPUT_DIR = "/Users/xiexiaomeng/OpenClawWorkspace/storybooks"

# 模板目录
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "template")
TEMPLATE_HTML = os.path.join(TEMPLATE_DIR, "index.html")

# 技能工作目录
SKILL_DIR = os.path.join(os.path.dirname(__file__), "..")
