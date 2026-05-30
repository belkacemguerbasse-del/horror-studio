# Horror Studio

Desktop app (Electron + React) to manage your daily horror TikTok pipeline:
Nano Banana 2 storyboard → ComfyUI LTX 2.3 video generation → ElevenLabs voice-over → final ffmpeg concat.

## Install

```powershell
cd horror-studio
npm install
```

## Run in dev (hot reload)

```powershell
npm run dev
```

Opens the Electron window pointing to the Vite dev server on `http://localhost:5173`.

## Build a Windows installer

```powershell
npm run build
```

Produces `release/Horror Studio Setup *.exe`.

## First-time setup

1. Open **Settings** (sidebar).
2. Confirm **ComfyUI URL** (default `http://127.0.0.1:8000`) — make sure ComfyUI is running.
3. Confirm the paths to:
   - `generate_batch.py` (the existing Python script at the repo root)
   - `concat_final.py` (same)
   - `video_ltx2_3_i2v_api.json` (the API-format workflow)
   - Projects root folder (default: `../projects/`)
4. Paste your **ElevenLabs API key** and click **Load voices**, pick a default voice.
5. Save.

## Daily workflow

1. Click **+ New episode** → give it a title and a scheduled date.
2. Walk through the 7 wizard steps in the episode view:
   1. **Story & Banana prompt** — write story intent, copy the auto-generated Banana prompt, paste into Nano Banana 2.
   2. **Import storyboard** — pick the 10 sliced PNGs from Banana, app renames them `01–10` automatically.
   3. **Motion prompts** — paste the 10 motion prompts from Banana (any format), tweak durations.
   4. **Generate videos** — runs `generate_batch.py`, live log + per-frame progress.
   5. **Voice-over** — generates 10 MP3s via ElevenLabs (saved under `voice/`).
   6. **Final concat** — runs `concat_final.py`, previews the final 9:16 MP4.
   7. **Publish & track** — paste the TikTok URL, mark as posted.

Episodes appear in the sidebar (Upcoming / Past) with live status badges.

## Folder layout

Each episode lives in its own folder:

```
projects/
  ep_20260527_babysitter/
    meta.json              ← created/updated by the app
    prompts.json           ← compatible with generate_batch.py
    voiceover.md           ← optional notes
    frames/01.png ... 10.png
    voice/01.mp3 ... 10.mp3
    output/01.mp4 ... 10.mp4
    ep_20260527_babysitter_final.mp4
```

The Python scripts are unchanged — the app just orchestrates them.

## Troubleshooting

- **"ComfyUI offline"** in sidebar → start ComfyUI, then click Ping in Settings.
- **TTS fails** → re-check your ElevenLabs key has TTS credits + a voice is selected.
- **Generation hangs** → open the log in the Generate step; verify the workflow API export still has the expected node IDs (`320:319`, `320:299`, etc.).
- **App can't find Python** → set the absolute path in Settings → Python executable (e.g. `C:\Python313\python.exe`).
