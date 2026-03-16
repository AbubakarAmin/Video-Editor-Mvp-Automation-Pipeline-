# 🎬 AI Video Automation Pipeline

> **Script in → Finished video out.** A fully automated pipeline that turns a text script into a complete, ready-to-publish video — short-form or long-form — with zero manual editing.

---

## 🚀 What It Does

This tool takes a written script and automatically produces a finished, rendered video by chaining together AI generation, stock media retrieval, audio synthesis, and FFmpeg-based video assembly — end to end, no manual editing required.

**Full pipeline at a glance:**

```
Script (text)
    │
    ▼
Gemini AI  ──►  Scene breakdown + narration
    │
    ▼
TTS Engine ──►  Voiceover audio (.mp3)
    │
    ▼
Stock Fetcher ──►  Clips + images (Pixabay & open-source sources)
    │
    ▼
Auto-Cutter ──►  Clips trimmed to match audio timing
    │
    ▼
FFmpeg Stitcher ──►  Final rendered video (.mp4)
```

**Output formats supported:** Short-form (Reels / Shorts / TikTok) and long-form (YouTube / explainers / promos)

---

## ✨ Features

- **Script-to-video in one command** — feed a script, get a `.mp4` back
- **Gemini-powered narration** — AI breaks your script into scenes and writes visual direction
- **Realistic TTS voiceover** — text-to-speech audio synced to every scene
- **Automatic stock media sourcing** — fetches relevant video clips and images from open-source libraries (Pixabay, etc.)
- **Smart clip cutting** — trims and pads footage to perfectly match voiceover duration
- **FFmpeg stitching** — assembles everything into a single polished output file
- **Short & long-form support** — configure output aspect ratio and duration for any platform

---

## 🛠 Tech Stack

| Layer | Tool |
|---|---|
| AI / Scene Planning | Google Gemini API |
| Text-to-Speech | TTS Engine (configurable) |
| Stock Media | Pixabay API + open-source video sources |
| Video Processing | FFmpeg |
| Orchestration | Python |

---

## ⚙️ Setup

### Prerequisites

- Python 3.9+
- FFmpeg installed and on your `PATH`
- Google Gemini API key
- Pixabay API key

### Installation

```bash
git clone https://github.com/AbubakarAmin/Video-Editor-Mvp-Automation-Pipeline-.git
cd Video-Editor-Mvp-Automation-Pipeline-
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
PIXABAY_API_KEY=your_pixabay_api_key_here
```

---

## 🎯 Usage

```bash
python main.py --script "your script text here" --format short
```

**Options:**

| Flag | Description | Default |
|---|---|---|
| `--script` | Path to script file or inline text | required |
| `--format` | `short` (vertical 9:16) or `long` (horizontal 16:9) | `long` |
| `--output` | Output file path | `output.mp4` |
| `--voice` | TTS voice ID | default voice |

**Example:**

```bash
python main.py --script scripts/product_demo.txt --format short --output reel.mp4
```

---

## 📁 Project Structure

```
├── main.py                  # Entry point — runs the full pipeline
├── pipeline/
│   ├── scene_planner.py     # Gemini: breaks script into scenes
│   ├── tts_engine.py        # Generates voiceover audio
│   ├── media_fetcher.py     # Pulls stock clips + images
│   ├── clip_cutter.py       # Trims clips to match audio timing
│   └── stitcher.py          # FFmpeg assembly + final render
├── scripts/                 # Sample input scripts
├── output/                  # Rendered videos saved here
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🤝 Use Cases

This pipeline is built for:

- **Content creators** — automate faceless YouTube channels or social media content
- **Marketing agencies** — generate product promo videos at scale
- **Small businesses** — create explainer or ad videos without a video editor
- **Developers** — integrate automated video generation into any product or workflow

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 👤 Author

**Abubakar Amin**  
Available for freelance automation & AI tooling projects.  
📧 [your email here] · 🔗 [your LinkedIn or portfolio here]
