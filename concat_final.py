"""
Concatenate generated clips into a single final video for TikTok.
Auto-mixes the per-clip voice-over (voice/01.mp3 ... 10.mp3) onto the
matching video clip if those files exist.

Usage:
    python concat_final.py projects/babysitter_app
    python concat_final.py projects/babysitter_app --no-voice
    python concat_final.py projects/babysitter_app --voice-volume 1.0 --ambient-volume 0.20

Outputs: projects/<name>/<name>_final.mp4
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def clip_index(p: Path) -> str:
    """Extract the 2-digit index from a clip filename like '01_00001_.mp4' -> '01'."""
    m = re.match(r"^(\d+)", p.stem)
    return m.group(1).zfill(2) if m else p.stem


def resolve_ffmpeg():
    env = os.environ.get("FFMPEG_PATH", "").strip().strip('"')
    if env and Path(env).is_file():
        return env
    onpath = shutil.which("ffmpeg")
    if onpath:
        return onpath
    return None


def run(cmd: list[str]) -> int:
    """Run a subprocess inheriting stdio; return exit code."""
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd).returncode


def per_clip_mix(ffmpeg: str, video: Path, voice: Path | None,
                 out: Path, voice_vol: float, ambient_vol: float) -> int:
    """Produce a single mp4 with video + (optional) voice-over mixed
    over the original ambient audio. Audio runs exactly the video length."""
    if voice is None or not voice.is_file():
        # Just re-encode video to ensure consistent codec/timebase for concat
        cmd = [
            ffmpeg, "-y", "-i", str(video),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-pix_fmt", "yuv420p",
            str(out),
        ]
        return run(cmd)

    # Two-input mix: ambient (from video) lowered, voice on top, trim to video length.
    filt = (
        f"[0:a]volume={ambient_vol}[a0];"
        f"[1:a]volume={voice_vol},aresample=async=1[a1];"
        f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[a]"
    )
    cmd = [
        ffmpeg, "-y",
        "-i", str(video),
        "-i", str(voice),
        "-filter_complex", filt,
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out),
    ]
    return run(cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--no-voice", action="store_true",
                        help="Skip voice-over mixing even if voice/*.mp3 files exist")
    parser.add_argument("--voice-volume",   type=float, default=1.10,
                        help="Voice-over volume multiplier (default 1.10)")
    parser.add_argument("--ambient-volume", type=float, default=0.25,
                        help="Original LTX ambient/audio volume multiplier (default 0.25)")
    parser.add_argument("--ffmpeg", type=str, default=None,
                        help="Path to ffmpeg.exe (overrides FFMPEG_PATH and PATH)")
    args = parser.parse_args()

    ffmpeg_bin = args.ffmpeg or resolve_ffmpeg()
    if not ffmpeg_bin:
        sys.exit(
            "ffmpeg not found.\n"
            "  Option 1 — install globally: winget install Gyan.FFmpeg  (then restart your terminal)\n"
            "  Option 2 — set FFMPEG_PATH env var to a portable ffmpeg.exe\n"
            "  Option 3 — pass --ffmpeg C:\\path\\to\\ffmpeg.exe\n"
            "  Download: https://www.gyan.dev/ffmpeg/builds/"
        )
    print(f"[INFO] using ffmpeg: {ffmpeg_bin}")

    project = args.project_dir.resolve()
    out_dir   = project / "output"
    voice_dir = project / "voice"
    work_dir  = project / "_concat_work"
    if not out_dir.exists():
        sys.exit(f"No output folder at {out_dir}. Run generate_batch.py first.")

    clips = sorted(out_dir.glob("*.mp4"))
    if not clips:
        sys.exit(f"No .mp4 clips found in {out_dir}")

    voice_files = []
    if voice_dir.exists() and not args.no_voice:
        for c in clips:
            idx = clip_index(c)  # "01_00001_.mp4" -> "01"
            mp3 = voice_dir / f"{idx}.mp3"
            voice_files.append(mp3 if mp3.is_file() else None)
    else:
        voice_files = [None] * len(clips)

    found_voices = sum(1 for v in voice_files if v)
    print(f"[INFO] Found {len(clips)} clips · {found_voices}/{len(clips)} voice-over files")

    if found_voices == 0:
        print("[INFO] No voice-over found — output will use original LTX audio only.")

    work_dir.mkdir(exist_ok=True)
    mixed_clips = []
    for video, voice in zip(clips, voice_files):
        out = work_dir / f"mixed_{clip_index(video)}.mp4"
        rc = per_clip_mix(ffmpeg_bin, video, voice, out,
                          voice_vol=args.voice_volume,
                          ambient_vol=args.ambient_volume)
        if rc != 0:
            sys.exit(f"\n[ERROR] ffmpeg failed mixing {video.name} (exit {rc})")
        mixed_clips.append(out)

    # Concat all mixed clips (now all share codec/timebase → -c copy works)
    list_file = work_dir / "_list.txt"
    list_file.write_text(
        "\n".join(f"file '{c.as_posix()}'" for c in mixed_clips),
        encoding="utf-8",
    )

    final = project / f"{project.name}_final.mp4"
    rc = run([
        ffmpeg_bin, "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy",
        "-movflags", "+faststart",
        str(final),
    ])
    if rc != 0:
        sys.exit(f"\n[ERROR] ffmpeg concat failed (exit {rc})")

    # Cleanup intermediate files
    for f in mixed_clips:
        f.unlink(missing_ok=True)
    list_file.unlink(missing_ok=True)
    try:
        work_dir.rmdir()
    except OSError:
        pass  # not empty, leave it

    print(f"\n[OK] Final video: {final}")
    print(f"[OK] Size: {final.stat().st_size / 1024 / 1024:.1f} MB")
    if found_voices > 0:
        print(f"[OK] Voice-over: {found_voices}/{len(clips)} lines mixed "
              f"(voice {args.voice_volume:.2f} · ambient {args.ambient_volume:.2f})")


if __name__ == "__main__":
    main()
