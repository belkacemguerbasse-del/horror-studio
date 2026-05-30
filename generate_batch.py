"""
Batch generator for LTX 2.3 i2v on ComfyUI.

Usage:
    python generate_batch.py projects/nurse_hospital_1994

Prerequisites:
    1. ComfyUI running locally (default http://127.0.0.1:8188)
    2. Workflow exported in API Format -> video_ltx2_3_i2v_api.json (at repo root)
    3. A project folder containing:
         frames/01.png ... frames/NN.png
         prompts.json   (see _template/prompts.json)
"""

import argparse
import copy
import json
import shutil
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

COMFY_HOST = "http://127.0.0.1:8000"
WORKFLOW_API = Path(__file__).parent / "video_ltx2_3_i2v_api.json"

# Node IDs from API-format export of video_ltx2_3_i2v.json
# Subgraph nodes are prefixed with "320:" (subgraph container id).
NODE_LOAD_IMAGE = "269"        # LoadImage              -> inputs.image
NODE_SAVE_VIDEO = "75"         # SaveVideo              -> inputs.filename_prefix
NODE_PROMPT_POS = "320:319"    # PrimitiveStringMultiline (positive prompt) -> inputs.value
NODE_PROMPT_NEG = "320:313"    # CLIPTextEncode (negative prompt) -> inputs.text
NODE_DURATION   = "320:301"    # PrimitiveInt "Duration" (seconds) -> inputs.value
NODE_FPS        = "320:300"    # PrimitiveInt "Frame Rate"         -> inputs.value
NODE_HEIGHT     = "320:299"    # PrimitiveInt "Height"             -> inputs.value
NODE_WIDTH      = "320:312"    # PrimitiveInt "Width"              -> inputs.value
NODE_LATENT     = "320:295"    # EmptyLTXVLatentVideo -> inputs.length (override)
NODE_AUDIO_LAT  = "320:305"    # LTXVEmptyLatentAudio -> inputs.frames_number (override)


def ltx_valid_length(duration_seconds: int, fps: int) -> int:
    """LTX requires pixel frame count = 8k + 1. Round UP to satisfy that
    so the rendered clip duration is >= the requested duration."""
    target = duration_seconds * fps
    # smallest n = 8k + 1 with n >= target
    k = (target - 1 + 7) // 8  # ceil((target - 1) / 8)
    return 8 * k + 1


def queue_prompt(workflow: dict, client_id: str) -> str:
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(f"{COMFY_HOST}/prompt", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["prompt_id"]


def upload_image(image_path: Path) -> str:
    """Upload image to ComfyUI input folder, return server-side filename."""
    import mimetypes
    boundary = uuid.uuid4().hex
    mime = mimetypes.guess_type(image_path.name)[0] or "image/png"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{image_path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + image_path.read_bytes() + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        f"{COMFY_HOST}/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["name"]


def wait_for_completion(prompt_id: str, poll: float = 2.0) -> dict:
    while True:
        with urllib.request.urlopen(f"{COMFY_HOST}/history/{prompt_id}") as r:
            data = json.loads(r.read())
        if prompt_id in data:
            return data[prompt_id]
        time.sleep(poll)


def download_outputs(history: dict, dest_dir: Path, out_name: str) -> list[Path]:
    saved = []
    for node_out in history.get("outputs", {}).values():
        for vid in node_out.get("videos", []) + node_out.get("gifs", []):
            params = urllib.parse.urlencode({
                "filename": vid["filename"],
                "subfolder": vid.get("subfolder", ""),
                "type": vid.get("type", "output"),
            })
            with urllib.request.urlopen(f"{COMFY_HOST}/view?{params}") as r:
                ext = Path(vid["filename"]).suffix or ".mp4"
                target = dest_dir / f"{out_name}{ext}"
                target.write_bytes(r.read())
                saved.append(target)
    return saved


def build_workflow(template: dict, *, image_name: str, prompt: str,
                   duration: int, fps: int, width: int, height: int,
                   save_prefix: str, negative: str = "") -> dict:
    wf = copy.deepcopy(template)
    for nid in (NODE_LOAD_IMAGE, NODE_SAVE_VIDEO, NODE_PROMPT_POS,
                NODE_DURATION, NODE_FPS, NODE_HEIGHT, NODE_WIDTH):
        if nid not in wf:
            raise KeyError(f"Node {nid} not found in API workflow. "
                           "Re-export workflow as API Format from ComfyUI.")

    length = ltx_valid_length(int(duration), int(fps))

    wf[NODE_LOAD_IMAGE]["inputs"]["image"] = image_name
    wf[NODE_SAVE_VIDEO]["inputs"]["filename_prefix"] = save_prefix
    silent_suffix = " The character's mouth stays closed throughout. No talking. No dialogue. Only ambient sounds and atmospheric audio."
    wf[NODE_PROMPT_POS]["inputs"]["value"] = prompt.rstrip() + silent_suffix
    if negative and NODE_PROMPT_NEG in wf:
        wf[NODE_PROMPT_NEG]["inputs"]["text"] = negative
    wf[NODE_DURATION]["inputs"]["value"] = int(duration)
    wf[NODE_FPS]["inputs"]["value"] = int(fps)
    wf[NODE_HEIGHT]["inputs"]["value"] = int(height)
    wf[NODE_WIDTH]["inputs"]["value"] = int(width)
    # Override the latent length with a literal int (bypass the math node
    # that rounds DOWN to 8k+1 and gives a clip shorter than requested).
    wf[NODE_LATENT]["inputs"]["length"] = length
    if NODE_AUDIO_LAT in wf:
        wf[NODE_AUDIO_LAT]["inputs"]["frames_number"] = length
    print(f"          length={length} frames -> {length/int(fps):.2f}s real")
    return wf


def main():
    global COMFY_HOST
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--only", type=str, default=None,
                        help="Comma-separated frame ids to render (e.g. 03,05)")
    parser.add_argument("--host", type=str, default=COMFY_HOST)
    args = parser.parse_args()
    COMFY_HOST = args.host.rstrip("/")

    if not WORKFLOW_API.exists():
        sys.exit(f"Missing {WORKFLOW_API}. Export your workflow as API Format from ComfyUI.")

    project = args.project_dir.resolve()
    cfg = json.loads((project / "prompts.json").read_text(encoding="utf-8"))
    out_dir = project / "output"
    out_dir.mkdir(exist_ok=True)

    template = json.loads(WORKFLOW_API.read_text(encoding="utf-8"))
    client_id = uuid.uuid4().hex
    only = set(args.only.split(",")) if args.only else None

    frames = [f for f in cfg["frames"] if not only or f["id"] in only]

    base_negative = (
        "talking, speaking, dialogue, mouth open wide, lip sync, lips moving, "
        "subtitles, captions, text overlay, watermark, logo, "
        "blurry, low quality, distorted face, deformed hands, extra fingers, "
        "cartoon, plastic skin, oversaturated, jpeg artifacts"
    )
    user_neg = (cfg.get("global_negative") or "").strip()
    negative = f"{base_negative}, {user_neg}" if user_neg else base_negative

    print(f"[INFO] {len(frames)} frame(s) to render for '{cfg['story_title']}'")
    print(f"[INFO] negative prompt: {negative[:80]}...")

    for f in frames:
        img_path = project / f["image"]
        if not img_path.exists():
            print(f"[SKIP] {f['id']} - missing image {img_path}")
            continue

        print(f"[UPLOAD] {f['id']} -> {img_path.name}")
        server_name = upload_image(img_path)

        save_prefix = f"video/{project.name}/{f['id']}"
        wf = build_workflow(
            template,
            image_name=server_name,
            prompt=f["prompt"],
            duration=f.get("duration", 10),
            fps=cfg.get("fps", 25),
            width=cfg.get("width", 720),
            height=cfg.get("height", 1280),
            save_prefix=save_prefix,
            negative=negative,
        )

        print(f"[QUEUE]  {f['id']} - duration={f.get('duration',10)}s")
        pid = queue_prompt(wf, client_id)
        history = wait_for_completion(pid)
        saved = download_outputs(history, out_dir, out_name=f["id"])
        print(f"[DONE]   {f['id']} -> {[str(p) for p in saved]}")

    print(f"\n[OK] All clips in {out_dir}")
    print("Next step: concatenate with ffmpeg, e.g.:")
    print(f'  ffmpeg -f concat -safe 0 -i list.txt -c copy {project.name}_final.mp4')


if __name__ == "__main__":
    main()
