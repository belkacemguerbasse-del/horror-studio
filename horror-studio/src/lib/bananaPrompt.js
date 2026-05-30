// ───────────────────────────────────────────────────────────────────────────
// Banana / Nano Banana 2 prompts — split into 2 separate calls.
// Gemini Image often skips the image when the prompt is long and mixed
// (image + text). Splitting into 2 focused prompts is far more reliable.
// ───────────────────────────────────────────────────────────────────────────

export function buildBananaImagePrompt(storyIntent, visualStyle = '') {
  const style = visualStyle?.trim() || `Hyper-realistic photographic style, 35mm grain, anamorphic feel. Cinematic horror lighting: low-key, hard practicals, deep shadows, motivated sources, subtle volumetric fog. Color palette: desaturated greens, cold blues, dirty amber, pure blacks. No neon.`;

  return `Generate ONE image: a 10-panel vertical storyboard grid for a horror TikTok video.

### Layout
- 5 columns × 2 rows = 10 panels
- Each panel is strictly 9:16 vertical (TikTok format)
- Thin white borders separate the panels
- No captions, no frame numbers, no text overlays

### VISUAL STYLE — MANDATORY (apply identically to ALL 10 panels)
${style}

### Continuity
STRICT visual continuity across the 10 panels: same protagonist, wardrobe, hair, props, environment, lighting palette, color grading. The protagonist must be instantly recognizable from panel to panel.

### Composition variation (one per panel — never repeat)
wide, medium, close-up, extreme close-up, POV, over-the-shoulder, low-angle, Dutch angle, high-angle, hand-held

### Story arc (10 panels = 4 beats)
- Panels 1-2 : setup / false calm
- Panels 3-5 : rising tension (sound, shadow, displaced object, presence)
- Panels 6-7 : revelation (threat appears)
- Panels 8-10 : climax & cold resolution

### Character rule
The protagonist's mouth is CLOSED in every panel — story is told via voice-over. Allowed: held breath, silent gasp, lips slightly parted in fear. NEVER mid-speech.

### Story
${storyIntent || '[Add your story intent here]'}

Output: ONLY the 10-panel image grid. No text, no description, no commentary.`;
}

export function buildBananaTextPrompt(storyIntent) {
  return `You are an award-winning horror cinematographer writing for a 70-second TikTok horror video composed of 10 vertical clips of 7 seconds each.

You will produce TWO outputs based on the Story Intent below:
  1. 10 Motion Prompts (one per clip)
  2. 10 Voice-Over lines (one per clip, 1:1 mapped)

The video has NO spoken dialogue from characters — only voice-over narration. Characters' mouths must stay CLOSED in every clip.

### Story Intent
${storyIntent || '[Add your story intent here]'}

### Story arc (10 clips = 4 beats)
- Clips 1-2 : setup / false calm
- Clips 3-5 : rising tension
- Clips 6-7 : revelation (threat appears)
- Clips 8-10 : climax & cold resolution


────────────────────────────────────────────────────────
## OUTPUT 1 — Motion Prompts (numbered 1 to 10)

For each clip, write a Motion Prompt of 1-2 sentences describing what happens in the NEXT 7 SECONDS from the opening frame.

Include for each:
- **Subject action** — slow, deliberate, one micro-action only. Mouth stays CLOSED. Allowed: sharp inhale, held breath, silent gasp, lips trembling.
- **Camera move** — push-in, slow pan, handheld drift, static, whip-pan on scares. 7s = subtle moves only.
- **Ambient sound + one diegetic cue** — wind, footsteps, music boxes, off-screen whispers. NEVER include character dialogue.
- **One atmospheric detail** — dust motes, flickering bulb, breath visible, volumetric fog.

Format strictly:
Frame 01: [description]
Frame 02: [description]
...
Frame 10: [description]


────────────────────────────────────────────────────────
## OUTPUT 2 — Voice-Over Script (numbered 1 to 10)

THIRD-PERSON OMNISCIENT NARRATION — an external storyteller recounts the story over the video. This is NOT the character speaking. The character NEVER talks. The narrator tells the audience what happened.

Reference tones: Tales from the Crypt narrator, classic creepypasta read aloud, Edgar Allan Poe narration, a calm true-crime podcast host telling a chilling case. NOT the character's inner monologue.

Rules:
- Third-person past tense ("She walked toward the door", "He had drawn the same man for thirteen years", NEVER "I walked")
- Refer to the protagonist as "she" / "he" / "they" — or by first name if the Story Intent gives one
- The narrator KNOWS more than the character — can foreshadow ("She did not know that this would be the last door she would ever open")
- ~10-15 words per line (~6 seconds spoken at 125 wpm)
- Slow, measured, slightly menacing tone — never theatrical, never panicked
- Do NOT describe the visuals literally (the camera shows them) — instead reveal context, history, fate, the character's hidden thoughts, or what the audience cannot see
- No exclamations, no "suddenly", no quoted dialogue
- Emotional arc:
  - Lines 1-2: calm, neutral, establishing the character and their normal world
  - Lines 3-5: the narrator hints something is wrong (one detail per line)
  - Lines 6-7: the narrator confirms the threat / the realization
  - Lines 8-9: restrained dread, short clipped sentences (5-8 words)
  - **Line 10 MUST be cold, final, declarative — the narrator delivers the twist or the fate. No question, no scream. A statement that recontextualizes the whole story.**

Format strictly:
VO 01: <your sentence here>
VO 02: <your sentence here>
...
VO 10: <your sentence here>

Example tone (do not copy, just match the voice):
  VO 01: For thirteen years, Elara had drawn the same man.
  VO 02: She called it remembering. Her mother called it a curse.
  ...
  VO 10: He had come for her. She had been waiting all along.`;
}

// Backward-compatible combined version (kept for the optional "all-in-one" button)
export function buildBananaPrompt(storyIntent) {
  return buildBananaImagePrompt(storyIntent) + '\n\n────────────────────────────────────────\n\n' + buildBananaTextPrompt(storyIntent);
}

export function buildVoiceoverPrompt(story) {
  return `Write a 70-second THIRD-PERSON omniscient narration for a horror TikTok video — like a Tales from the Crypt narrator or a creepypasta read aloud. NOT first-person, NOT the character's inner monologue.
- 10 lines, one per video clip of 7 seconds each
- Past tense, third-person ("She walked", "He saw", never "I")
- Slow, measured, slightly menacing — A24 slow-burn tone
- Refer to the character by "she/he/they" or first name
- The narrator knows more than the character (can foreshadow)
- Last line MUST be cold and declarative — delivers the twist or fate
- Output as: VO 01: ... / VO 02: ... / ... / VO 10: ...

Story:
${story}`;
}
