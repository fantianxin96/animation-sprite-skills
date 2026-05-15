# Generic Sprite Animation Generation Logic

Use this reference when writing or reviewing a sprite-sheet generation prompt.

## 0. Input Recognition And Character Context

Before writing a prompt, identify what the user actually gave:

- `asset_type`: `sticker`, `sprite_animation`, `ui_state_motion`, `full_sequence_animation`, `character_base_frame`, `sprite_qc_only`, or `sprite_from_existing`.
- `subject_type`: `character`, `object`, or `ui_element`.
- `subject`: the character or object being designed.
- `action`: explicit action if provided.
- `scene_or_use`: where the asset will be used.
- `style_or_mood`: visual/performance direction.
- `reference_intent`: `style_reference`, `exact_character_reference`, `mixed_reference`, or unknown.
- `playback`: `once`, `loop`, or unknown.
- `frame_hint`: exact count/layout, length preference, or unknown.

Do not treat a subject as an action. "A cat" does not mean waving. "A headset" does not mean bouncing. "Cute" is style, not action.

If the user provides a reference image, first classify what the reference means:

- `style_reference`: the reference provides style, mood, line language, character grammar, or visual taste. Generate a new subject in that style.
- `exact_character_reference`: the reference is the character/object to use. Do not redesign it or replace it with a similar one.
- `mixed_reference`: preserve the specified subject while borrowing only the requested style dimensions.
- Unknown: ask one short question, such as "是参考这个风格，还是就用图里这个角色继续做？"

If the user says "use this", "this exact one", "复刻这个", "就是这个角色", "按这个形象", or "不要重新设计", treat it as `exact_character_reference`.

For `style_reference`, analyze the reference before applying default character anatomy:

- follow the reference's character grammar, proportion logic, weirdness, line quality, and level of polish;
- default "simple mascot with arms and legs" anatomy is only a fallback;
- do not automatically normalize the subject into a neat cute mascot;
- if the reference has varied or strange limb structures, allow the new character to also have non-standard limbs, root-like feet, branch-like arms, missing limbs, asymmetry, or object-like anatomy;
- only ask about anatomy/personification when the reference and the user's subject leave a major fork, such as object-first vs character-person-first, or when animation usability conflicts with preserving the reference's weirdness.

Use an internal `reference_style_profile`:

```yaml
reference_style_profile:
  line_language:
  shape_language:
  face_language:
  limb_language:
  proportion_language:
  composition_language:
  color_material_language:
  polish_level:
  weirdness_or_personality_source:
  what_not_to_average:
```

For `exact_character_reference`, use an internal `exact_character_profile`:

```yaml
exact_character_profile:
  identity_lock:
  silhouette:
  face:
  proportions:
  colors_materials:
  outfit_accessories:
  signature_details:
  allowed_changes:
  forbidden_changes:
```

Exact references are not a prompt to create "something similar". They are source identity. Add animation base structure only as needed, such as a clean base frame, three-view reference, or sprite grid.

If the user already provides a sprite sheet:

- `sprite_qc_only`: do not write a new image-generation prompt. Send the existing sheet to `$animation-qc` for QC, alignment, GIF preview, timing, audit, and report.
- `sprite_from_existing`: inspect the existing sheet first and use it as source material. Do not restart character/base-frame generation unless the user explicitly asks for a new character or a fresh redesign.

## 0.5 Normal User Flow

The user should not need to know the workflow. Internally route them through these stages:

0. **Entry routing**
   - If the user gives enough information, proceed directly instead of asking setup questions.
   - If the user is unsure how to start, ask one entry question:
     "你现在是想：1. 做一个新角色 2. 给已有角色做动作 3. 检查已有雪碧图？"
   - If the user provides only a subject, treat it as character/base setup unless they explicitly ask for an immediate action.
   - If the user provides only an action, ask what character or source image to use.
   - If the user provides an existing sprite sheet, route to QC/processing, not fresh character generation.
   - If the user provides an existing character reference that is a character sheet, multi-pose board, labeled image, decorated reference page, or complex-background image, automatically route to clean base extraction before action generation.

1. **New subject/IP request**
   - Treat this as character/base setup, not action generation.
   - Generate or propose a base frame first.
   - Ask for confirmation on face, shape, style, proportions, and vibe.
   - If confirmed, optionally name the character and store `current_character`.

1b. **Existing character reference but not a clean base**
   - Do not ask whether to clean it first.
   - Automatically extract/generate a clean single-character base frame.
   - Preserve exact character identity when the user intends to use that character.
   - Remove labels, text, extra poses, decorative frames, background ornaments, and unrelated props.
   - Keep one centered character with clear body/main-object center and contact/baseline.
   - Ask the user to confirm whether the cleaned base still looks like the provided character before making action sprites.

2. **Action request**
   - If there is a confirmed `current_character`, reuse it by default.
   - If there is no confirmed character, ask whether to use the newly described subject as a character first.
   - If the action is missing, ask one short action question or offer subject-appropriate action suggestions.
   - Do not force the user to define every frame. The motion plan handles action structure internally.

3. **Frame/length selection**
   - If the user specifies frame count/layout, follow it.
   - If unspecified and the action complexity matters, ask in plain language:
     "你想要这个动图大概多长？4帧很短，6帧标准，8帧更完整，12帧更像小表演。也可以让我判断。"
   - If asking would interrupt a simple flow, infer a default and say it plainly:
     "我先按 6 帧标准短动图来做。"
   - Recommendations:
     - 4 frames: tiny feedback, blink, small expression.
     - 6 frames: default short action.
     - 8 frames: clearer small performance, wave, stretch, bend-and-return, prop gesture.
     - 12 frames: entrance, dance, mini-story, multi-beat performance.

4. **Sprite generation**
   - Use the confirmed visual rules and anchor profile.
   - Generate the sprite only after subject/character, action, and rough length are known or inferred.
   - After image generation, guide to GIF preview and stability check.

5. **QC decision**
   - Show GIF first.
   - Then guide the user to accept, adjust speed, regenerate, drop frames, or integrate.

If the user is creating a new IP or object, first establish a base reference.

If the user provides an existing character sheet or reference board, first establish a clean animatable base reference from it. This is required and should not be treated as an optional extra step.

Reference depth:

- Lightweight default: one neutral front base frame.
- Stability upgrade: a three-view character sheet (`front / side / back` or `front / 3/4 / side`) when the character is complex, likely to become a long-term IP, needs many actions, needs turns/side poses, has important outfit/accessory details, or the user asks for more consistency.
- Do not force three views when the user is only exploring a quick one-off action.

```yaml
current_character:
  name:
  subject_type:
  reference_image:
  base_reference:
    type: single_front / three_view
    file:
    views:
      - front
      - side
      - back
  visual_rules:
  anchor_profile:
    center_anchor: body_main_axis / body_visual_center / object_visual_center
    baseline_anchor: foot_baseline / contact_baseline / sitting_baseline / none
    ignore_for_center:
      - hands
      - moving_feet
      - facial_marks
      - motion_lines
      - props
      - temporary_outfit_edges
      - skirt_or_cape_edges
      - sparkles_bubbles_effects
    baseline_rule: grounded actions keep one contact line unless jump/fall/slide/float/travel is explicit.
    uncertainty: ask only when the body/core object is ambiguous.
  confirmed: true / false
  previous_characters: []
```

Support character context operations:

- "change character" / "new character": start a new base-frame confirmation flow.
- "do not use current character this time": make a one-off asset and preserve the current character.
- "go back to previous character": restore the previous confirmed character when available.
- "clear current character": remove current character context and ask for subject/reference next time.

Naming is optional. Ask whether to name the character after confirmation only when it helps reuse.

Anchor profile rules:

- Every confirmed character gets its own `anchor_profile`.
- Reuse the current character's `anchor_profile` for later action sprite sheets.
- A new character creates a new `anchor_profile`; going back to an old character restores the old one.
- One-off characters may use a temporary `anchor_profile` without overwriting the current character.
- Default center anchor is the body/main object. Do not ask the user unless the body/core object is ambiguous.
- Do not treat temporary clothing edges, props, motion lines, sparkles, bubbles, or small moving hands/feet as the center anchor.
- If a temporary outfit or prop becomes a permanent character design, update the character's visual rules, but keep the body/main object as the default anchor unless the user explicitly changes it.

## 1. Character Lock

Start by identifying what makes the character recognizable.

When a reference image is provided, lock the reference's visual grammar before locking generic animation convenience:

- looseness and imperfection,
- odd or restrained proportions,
- line pressure and hand-drawn quality,
- how limbs are attached or omitted,
- how faces are simplified,
- how much the design avoids polish or cuteness.

If the reference is exact-character intent, lock identity before visual grammar:

- exact silhouette,
- exact face,
- exact proportions,
- exact colors/materials,
- exact outfit/accessory logic,
- signature details,
- what may change for animation,
- what must never be changed.

Lock:
- main silhouette,
- body material/color,
- face style,
- line style,
- limb proportions,
- signature accessories or body parts,
- overall illustration style.
- same face,
- same body proportions,
- same character size,
- same outfit/accessory/hair/fur/color setup across frames.

Allow variation only as external changes:
- clothes,
- small accessories,
- hand props,
- scene effects,
- expression rhythm.

Do not let style variations mutate the character itself.

Do not suddenly add or remove clothes, accessories, props, or major visual elements during the animation unless the action explicitly introduces them.

## 2. Run Setup

Before prompting, decide:
- scene/use case,
- mood,
- style/theme,
- action goal,
- props/effects,
- required elements,
- forbidden elements.

If the user gives a theme, use it. If not, infer a restrained setup.

For multi-sheet animation, the setup must be consistent across all sheets. A hat, outfit, prop, or major effect should not randomly appear or disappear unless the action explicitly introduces it.

## 3. Skeleton vs Performance

A good prompt separates:

- **Skeleton**: what role this animation plays.
- **Performance**: how the character acts it out.

Examples:

- Startup skeleton: `entrance -> welcome/interaction -> closing/idle`
- Completion skeleton: `receive -> process -> feedback`
- Companion skeleton: `listen -> react softly -> hold`
- Data skeleton: `observe -> record -> small encouragement`

The skeleton can be stable. The performance should vary.

Motion planning should define structure, not rigid poses:

- start,
- reaction or preparation,
- development,
- peak or emphasis,
- recovery,
- end or loop return.

Do not lock exact poses frame-by-frame unless the user explicitly requests them. Let image generation freely interpret concrete poses inside the planned structure.

## 4. Frame And Segment Rules

Single action:
- one sprite sheet is usually enough,
- final frame should be holdable,
- do not force return to default unless requested.
- if the user does not specify exact poses, infer an internal motion-phase progression for the action, not rigid frame-by-frame poses.

Multi-segment action:
- define all segments first,
- lock shared setup,
- state transition pose at the end of each segment,
- repeat that pose as the first frame of the next segment,
- preview stitched sequence before product use.

## 5. Output Rules

Use these for generation:

- Match strictness to asset type.
- `sticker` / emote: prioritize emotional expression and readability; strict foot baseline, exact center, and continuous frame motion are optional unless the user wants a playable animation.
- `sprite_qc_only`: skip generation and hand off to `$animation-qc`.
- `sprite_from_existing`: preserve the existing sprite as source of truth; use QC or derivative prompting depending on the user's ask.
- `sprite_animation`, `ui_state_motion`, and `full_sequence_animation`: use strict animation asset rules.
- Output is an animation sprite sheet, not a single illustration.
- Use a regular grid.
- Follow the user's exact frame count or layout if provided.
- Custom frame counts and layouts are allowed. If the user asks for 10 frames, 16 frames, `4x3`, `5x2`, or multiple sheets, follow that request.
- If unspecified, use one of: 4 frames, 6 frames (`3x2`), 8 frames (`4x2`), or 12 frames (`3x4` / `4x3`, depending on the action).
- Every cell must be the same size and `1:1` square.
- Transparent background or clean `#00FF00` background.
- No text.
- No watermark.
- No infographic.
- No complex background.
- The same character, same face, same proportions, same size, same outfit/accessory/hair/fur/color setup, and same visual style stay stable across all frames.
- Character scale stays stable.
- Main-body center stays stable.
- Foot/contact baseline stays stable.
- For grounded actions such as dancing, bending, nodding, swaying, stretching, or squash/stretch without an explicit jump, keep the foot/contact point on one horizontal baseline across all frames. Let the pose deform above the contact line; do not move the whole subject up/down to create motion.
- If jumping, falling, sliding, or traveling is intended, say so explicitly. Make takeoff, airborne/travel, and landing/contact frames legible, and return to the same baseline at the end unless the user requested position travel.
- Character stays close to the visual center area of each cell.
- Whitespace around the character stays as consistent as possible in every cell.
- The whole character must not drift left/right, drift up/down, or change size.
- If the action is not a jump, fall, or travel action, do not let the whole character leave the ground.
- Only the parts required by the action should move.
- Keep the torso/main body/root position as stable as possible.
- Props and effects can extend outward but must not redefine the character center.
- Adjacent frame changes should be small enough to feel continuous.
- Do not recompose each frame for beauty.
- Do not change camera angle, viewpoint, perspective, or background between frames.
- Do not make each frame look like a separate posed illustration.

## 6. Prompt Template

```text
Generate an animation sprite sheet for the reference character.

[Input Recognition]
- Asset type:
- Subject type:
- Subject:
- Action:
- Scene/use case:
- Reference intent: style_reference / exact_character_reference / mixed_reference / unknown
- Playback:
- Frame count/layout:
- Current character: use / one-off / new / previous / cleared
- Existing sprite source, if any:

[Character Lock]
- Character:
- Base reference: single front frame / three-view sheet
- If style reference: include a concise reference_style_profile and apply it to the requested subject.
- If exact character reference: include an exact_character_profile and preserve the provided identity rather than redesigning.
- Core silhouette:
- Colors/materials:
- Face style:
- Line/rendering style:
- Signature features:
- Do not change:
- If using an existing sprite sheet, preserve it as the source of truth and do not recreate the character from scratch.

[Run Setup]
- Scene/use case:
- Mood:
- Style/theme:
- Outfit/accessory:
- Props/effects:
- Required elements:
- Forbidden elements:

[Action Structure]
- Type: single action / multi-segment animation
- Segment(s):
- Concrete performance:
- Motion phases: start -> reaction/preparation -> development -> peak/emphasis -> recovery -> end/loop return
- If exact poses are not specified, let concrete poses be freely interpreted inside those phases:
- Transition locks, if multi-segment:
- Final hold pose:

[Output Rules]
- For sticker/emote assets, prioritize expression and readability; strict animation continuity is optional unless requested.
- For sprite_qc_only, skip generation and use animation-qc directly.
- For sprite_from_existing, base any derivative prompt on the existing sprite sheet.
- For playable sprite/UI/full-sequence animation, follow strict animation asset rules.
- Animation sprite sheet, not a single illustration, when the asset is meant to play as animation.
- Regular grid. Follow the user's exact frame count/layout if given.
- Custom frame counts and layouts are valid when requested, such as 10 frames, 16 frames, 4x3, 5x2, or multiple connected sheets.
- If unspecified, use one of: 4 frames, 6 frames (3x2), 8 frames (4x2), or 12 frames (3x4 / 4x3).
- Same-size cells; every cell must be 1:1 square.
- Transparent background or clean #00FF00 background.
- Strictly keep the same character, same face, same proportions, same size, same outfit/accessory/hair/fur/color setup, and same visual style.
- Do not suddenly add or remove clothes, accessories, props, or major visual elements.
- Character size, main-body center, and foot/contact baseline stay stable.
- For grounded actions, keep the foot/contact point on one horizontal baseline across all frames; bending, squash/stretch, dancing, and rebound happen above that stable contact line.
- Only allow baseline changes when the motion explicitly includes jumping, falling, sliding, or traveling, and make those frames look intentional.
- Character stays close to the visual center area of each cell.
- Whitespace around the character stays consistent.
- Adjacent frames are small continuous changes.
- Do not recompose each frame; do not change camera angle, viewpoint, perspective, or background.
- No text, watermark, infographic, or complex background.
```

## 7. Handoff To QC

After image generation:

1. Use `$animation-qc`.
2. If the asset uses a confirmed character, pass that character's `anchor_profile` to QC with `--anchor-profile /path/to/character-anchor-profile.json`.
3. Inspect GIF first.
4. Inspect audit image for center/baseline stability.
5. Read report JSON for numeric drift.
6. Decide pass, drop frames, manual adjust, or regenerate.

## 8. Stage Navigation Output

Every stage must end with a short workflow handoff so the user knows what to do next.

Do not stop at "image generated". Action sprite sheets are only intermediate assets until QC has produced a preview GIF, audit image, timing file, and report. If the image-generation tool can only return the image, resume this handoff in the next assistant message.

Use:

```text
当前步骤：
当前结果：
下一步：
需要你确认：
```

Default handoff should be understandable without technical context:

- Keep script names, JSON paths, `anchor_profile`, exact shifts, and report fields out of the main handoff.
- Use plain checks: "会不会飘", "会不会抖", "节奏顺不顺", "边缘干不干净".
- Show the GIF before audit/report unless the user is debugging.
- Add technical notes only when the user asks why, or when warning/fail needs evidence.

After a character base frame:

- Ask whether the character body passes: shape, style, expression, proportions, name.
- If the user accepts, continue to action planning.
- If the user rejects, revise the base frame before generating any action.

Example:

```text
当前步骤：角色基准造型
当前结果：我先把这个角色的样子定出来了。你看它的脸、比例、气质对不对。
下一步：如果你觉得可以，我再帮它做动作图。
需要你确认：保留这一版，还是想改得更酷/更软/更接近参考图？
```

After an action sprite sheet:

- State that the action frames are generated, but not yet ready to use.
- Immediately explain that the next step is GIF preview and stability check.
- Do not imply the asset is ready until QC has produced a preview and stability check.
- Mention that grounded actions need a check for floating/sliding, but avoid technical baseline terms unless needed.

Example:

```text
当前步骤：动作图已生成
当前结果：现在它还只是一张雪碧图，先不能直接当成最终动图用。
下一步：我会把它做成 GIF 预览，并检查会不会飘、会不会抖、节奏顺不顺。
需要你确认：你先看 GIF 的动作感觉对不对。
```

After QC:

- State whether it can be used, needs a quick look, or should be regenerated.
- Show preview GIF first; mention audit/report only when useful.
- Give one concrete next step: use asset, adjust timing, drop frames, regenerate, or revise prompt.

Example:

```text
当前步骤：动图检查完成
当前结果：这版基本可以，但有一点点需要你看 GIF 判断。
下一步：你先看动作感觉。如果觉得顺，我们就用这一版；如果觉得怪，我再帮你重生或调节奏。
需要你确认：动作感觉对吗？
```
