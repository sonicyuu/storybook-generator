---
name: storybook-generator
description: >
  绘本生成技能 - 培养孩子的表达能力和创造力。
  孩子讲述故事，AI 协助完善故事情节和内容，生成图文结合的交互式 HTML 绘本。
  适用于 4-12 岁孩子，支持角色图片上传保持一致性，多种绘画风格可选。
  支持背景音乐、精美排版、角色一致性、丰富故事内容、语音朗读。
license: MIT
metadata:
  version: "5.1"
  category: education
---

# 绘本生成器 v5.0

帮助孩子将讲述的故事转化为精美的交互式绘本，支持语音朗读功能。

## 功能概述

| 功能 | 说明 |
|------|------|
| 故事输入 | 孩子讲述故事，可详细或简略 |
| **AI 丰富故事** | 自动扩展情节，每页 30-80 字 |
| **角色提取** | 自动分析故事，生成角色卡片 |
| **风格锁定** | 生成统一风格 Prompt，保证画风一致 |
| **语音朗读** | voice_segments 自动从 page.text 提取，不同情感表达 |
| 分镜规划 | 自动分成 8-20 页，每页配文字+配图+语音 |
| **图片生成** | scripts/generate_images.py（已还原）调用 MiniMax 图片 API |
| **语音生成** | scripts/generate_voices.py（已还原）调用 MiniMax TTS API |
| **HTML组装** | scripts/build_html.py（已还原）从模板渲染最终绘本 |
| **TTS脚本** | scripts/tts/generate_voice.sh（已还原）单条/批量语音生成 |
| **背景音乐** | scripts/music/*.mp3（已同步），根据主题自动匹配 |
| 角色一致性 | 角色描述库 + 统一风格前缀 |
| 风格选择 | 卡通/水彩/国风/Pixar动画，默认卡通 |
| 背景音乐 | 根据主题自动选择匹配的音乐模板 |
| 输出 | HTML 绘本，支持翻页交互、背景音乐、语音朗读 |

---

## 核心改进 (v4.1)

### 1. 图片 Prompt 完整生成（关键修复）

**必须使用 metadata.json 中的完整 image_prompt**，格式为：

```
[角色] 角色外观描述
[场景] 场景描述
[动作] 动作描述
[风格] {stylePrompt}，与本绘本的画风保持完全一致
```

**❌ 错误做法**：用简化英文 prompt 替代
**✅ 正确做法**：必须用 metadata.json 中 page.image_prompt 的完整中文内容

### 2. voice_segments 必须从 page.text 提取

- `voice_segments.text` 必须等于 `page.text` 的子字符串
- 不能简化、不能遗漏、不能改写

---

## 使用流程

```
┌─────────────────────────────────────────┐
│  1. 收集信息                             │
│     - 孩子年龄、绘本名称、故事内容          │
│     - 角色照片（可选，用于参考）             │
│     - 风格选择                            │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  2. 分析故事 → 生成角色卡片                │
│     - 提取所有角色                        │
│     - 生成 appearance、personality、actions │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  3. 生成统一风格 Prompt                   │
│     - 画风定义（Pixar/水彩/国风等）        │
│     - 色调/光线/角色设计语言              │
│     - 风格锁定语                         │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  4. 生成故事分镜 + voice_segments         │
│     - 每页 page.text 控制在 30-80 字      │
│     - 每页 image_prompt 必须包含完整结构   │
│     - voice_segments 从 page.text 提取     │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  5. 生成图片（使用完整 image_prompt）      │
│     - 封面 + 每页图片                     │
│     - 必须用 metadata 中的 image_prompt   │
│     - 确保画风一致                        │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  6. 生成语音文件                         │
│     - 根据 voice_segments 逐段生成         │
│     - 自动更新 file 字段                  │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  7. 生成 HTML 绘本                       │
└─────────────────────────────────────────┘
```

---

## 朗读声音选择

从以下3个推荐声音中**随机选择**一个作为 narrator_voice：

| voice_id | 名称 | 描述 |
|----------|------|------|
| `Chinese (Mandarin)_Warm_Bestie` | 温暖闺蜜 | 温暖亲切，适合儿童 |
| `female-shaonv` | 少女 | 年轻活泼，甜美可爱 |
| `Chinese (Mandarin)_Soft_Girl` | 柔和少女 | 柔和细腻，声线好听 |

---

## metadata.json 结构 (v4.1)

```json
{
  "title": "绘本名称",
  "author": "作者",
  "created_at": "2026-04-07",
  
  "style": "cartoon_princess",
  "theme": "adventure",
  "target_age": "7",
  
  "characters": [...],
  
  "stylePrompt": "[风格锁定] Disney卡通风格...",
  
  "narrator_voice": "Chinese (Mandarin)_Soft_Girl",
  
  "pages": [
    {
      "page_number": 1,
      "text": "很久很久以前，有一个漂亮的公主...",
      "image_prompt": "[角色] 公主描述\n[场景] 王宫场景\n[动作] 公主在跳舞\n[风格] Disney卡通风格, 鲜艳色彩。与本绘本的画风保持完全一致",
      "voice_segments": [
        {"type": "narrator", "text": "很久很久以前，有一个漂亮的公主...", "emotion": "calm", "file": "voices/p1_s1.mp3"}
      ]
    }
  ]
}
```

---

## Prompt 模板

### 步骤1: 角色提取 Prompt

```
分析以下儿童故事，提取所有角色并生成标准化的角色描述。

故事内容：
{用户提供的故事}

要求：
1. 为每个角色生成 appearance（外观描述）
2. 生成 personality（性格特点）
3. 生成 actions（常用动作）

输出JSON数组格式（无markdown）：
[
  {
    "id": "角色英文ID",
    "name": "角色中文名",
    "type": "角色类型",
    "appearance": "详细外观描述",
    "personality": "性格特点",
    "actions": ["动作1", "动作2"]
  }
]
```

### 步骤2: 风格生成 Prompt

```
为以下儿童绘本生成统一的风格描述。

故事主题：{主题}
故事背景：{背景}

输出格式（无markdown）：
[风格锁定] + 详细的风格描述，包含画风、光线、色调、角色设计语言等
```

### 步骤3: 分镜生成 Prompt（关键）

```
你是一个儿童绘本作家。请为以下故事生成{页数}页分镜。

角色卡片：
{characters_json}

统一风格（必须严格遵守）：
{style_prompt}

故事内容：
{story_text}

【重要】输出要求：
1. page.text 控制在 30-80 字
2. image_prompt 必须包含以下4个部分：
   - [角色]：**必须严格引用角色卡片的 appearance 字段**，不得自由发挥。使用紧凑格式：`角色名(外观)`，多个角色用`,`分隔。禁止改写或补充 appearance 原文
   - [场景]：该页的场景描述
   - [动作]：该页的动作/情节
   - [风格]：{style_prompt}，与本绘本的画风保持完全一致
3. **【角色一致性强制要求】**：同一角色在不同页出现时，[角色]字段中的外观描述必须完全引用角色卡片的 appearance，不得有任何差异或补充文字
4. voice_segments 必须从 page.text 提取，text 必须完全一致（按标点拆分为完整句子）
5. emotion 根据内容情感选择（MiniMax 合法值）：neutral(平静), happy(开心), sadness(悲伤), fear(害怕), angry(生气), surprise(惊讶), contempt, disgust

【角色字段正确格式示例】：
```
# 角色卡片：
{"id": "haha", "name": "哈哈", "appearance": "7岁小男孩,黑色短发,大眼睛,蓝T恤,橙短裤,黄色小背包"}
{"id": "xixi", "name": "嘻嘻", "appearance": "和嘻嘻外观一致的小女孩"}

# 正确（严格引用 appearance）：
[角色] 哈哈(7岁小男孩,黑色短发,大眼睛,蓝T恤,橙短裤,黄色小背包), 嘻嘻(和嘻嘻外观一致的小女孩)

# 错误（自由发挥/改写）：
[角色] 哈哈是一个活泼的小男孩，他穿着蓝色的上衣...
```

JSON格式（无markdown）：
{
  "pages": [
    {
      "page_number": 1,
      "text": "【完整的故事文字，30-80字】",
      "image_prompt": "[角色] 角色名(角色卡片中的appearance原文)\n[场景] 场景描述\n[动作] 动作描述\n[风格] {style_prompt}，与本绘本的画风保持完全一致",
      "voice_segments": [
        {"type": "narrator", "text": "【page.text 第一个完整句子，以句号/感叹号/问号结尾】", "emotion": "happy"},
        {"type": "narrator", "text": "【page.text 第二个完整句子】", "emotion": "neutral"}
      ]
    }
  ]
}
```

---

## TTS 语音生成

### 命令格式

```bash
bash scripts/tts/generate_voice.sh tts \
  "语音文本内容" \
  --voice-id {narrator_voice} \
  --emotion {emotion} \
  -o "output.mp3"
```

### 情感参数

| emotion | 描述 | 适用场景 |
|---------|------|---------|
| neutral | 平静、自然 | 旁白叙述、平静场景 |
| happy | 开心、活泼 | 开心台词 |
| sad | 悲伤、难过 | 悲伤台词 |
| fearful | 害怕、紧张 | 害怕、紧张台词 |
| angry | 生气、愤怒 | 生气台词 |
| surprised | 惊讶 | 惊讶台词 |
| angry | 轻蔑 | 轻蔑台词 |
| disgusted | 厌恶 | 厌恶台词 |

---

## 目录结构 (v4.1)

```
storybooks/
├── template/
│   ├── index.html        # 绘本 HTML 框架
│   └── music/            # 背景音乐模板
│       ├── adventure.mp3
│       ├── peaceful.mp3
│       ├── happy.mp3
│       ├── dreamy.mp3
│       ├── mysterious.mp3
│       ├── sad.mp3
│       ├── heroic.mp3
│       └── warm_family.mp3
├── 绘本名称/
│   ├── metadata.json      # 包含角色卡片、风格、voice_segments、image_prompt
│   ├── images/
│   │   ├── cover.png
│   │   └── page_N.png
│   ├── voices/
│   │   ├── p1_s1.mp3
│   │   └── ...
│   ├── music/
│   │   └── background.mp3
│   └── index.html
└── ...
```

---

## 风格关键词

| 风格 | 关键词 |
|------|--------|
| 卡通_Pixar | Pixar/Disney 3D animation style, vibrant colors, soft lighting, smooth rendering, cute characters |
| 卡通 | cartoon, colorful, children illustration, cute characters, happy atmosphere |
| 水彩 | watercolor painting, soft colors, artistic, delicate, hand-painted feel |
| 国风 | Chinese traditional style, ink painting, elegant, brush stroke aesthetic |
| 写实 | photorealistic, realistic style, detailed, natural lighting |

---

## 音乐主题匹配

| 主题 | 音乐文件 | 适用场景 |
|------|----------|----------|
| adventure | adventure.mp3 | 冒险、探索、旅行、追逐 |
| peaceful | peaceful.mp3 | 睡前故事，自然风光、温馨场景 |
| happy | happy.mp3 | 节日、聚会、游戏、团圆 |
| dreamy | dreamy.mp3 | 童话、魔法、幻想、外星球 |
| mysterious | mysterious.mp3 | 神秘、悬疑、黑暗、紧张时刻 |
| sad | sad.mp3 | 悲伤、感动、失去、分离 |
| heroic | heroic.mp3 | 英雄、勇敢、战斗、胜利 |
| warm_family | warm_family.mp3 | 亲情、家庭、温情、关爱 |

---

## 注意事项

- **image_prompt 完整结构**：`[角色]\n[场景]\n[动作]\n[风格]` 四部分，缺一不可
- **voice_segments 原则**：text 必须等于 page.text 的子字符串，不简化、不遗漏、不改写
- **角色一致性**：每次生成图片都必须引用角色卡片中的 appearance 描述
- **风格锁定**：每个 image_prompt 必须包含完整的 stylePrompt + 锁定语
- **页面数量**：控制在 8-20 页，根据故事长度动态调整
- **图片比例**：封面 3:4，内容页 16:9
- **文字长度**：每页 30-80 字儿童语言
- **朗读声音**：从3个推荐声音中随机选择
- **生成顺序**：角色卡片 → 风格 → 分镜(含正确格式的voice_segments和image_prompt) → 图片 → 语音文件 → 更新file字段 → HTML

---

## 音量规则

- **背景音乐音量**：固定为系统音量的 10%（`bgMusic.volume = 0.1`），不可调节
- **朗读音量**：跟随系统音量（`voiceAudio.volume = 1.0`，由浏览器/系统控制）
- **交互控制**：仅保留 🎵 音乐开关（开/关），去除了音量滑块

---

## 输出信息

生成完成后，告诉用户：
- 绘本保存路径
- 如何在浏览器中打开
- 翻页操作方式
- 音乐控制方法（仅开关，无滑块）
- 语音朗读功能（🔊按钮，音量跟随系统）
