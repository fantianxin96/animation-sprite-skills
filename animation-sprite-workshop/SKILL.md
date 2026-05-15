---
name: animation-sprite-workshop
description: Use when turning an animation idea into a generic sprite-sheet image-generation brief before any image exists. Helps define character/IP locks, scene variables, action structure, shared visual setup, sprite grid delivery rules, and handoff to animation-qc. Generic and not tied to any specific mascot or product.
---

# 动画雪碧图生成工坊

This skill turns a rough animation idea into a usable sprite-sheet generation brief.

It is generic and not tied to any one IP or product.

## Boundary

Use this skill when there is **no image yet** or when the user wants a better generation prompt.

Use `$animation-qc` after an image exists.

This skill decides:
- how to recognize what kind of animation asset the user is asking for,
- how to maintain, switch, clear, or return to a current character/IP across a conversation,
- what must stay fixed about the character/IP,
- what variables should be asked or inferred,
- what action structure the animation should use,
- how to phrase the image-generation prompt,
- what delivery constraints make the output easier to QC.

This skill does not:
- inspect frame drift from an image,
- remove backgrounds,
- align frames,
- produce audit sheets,
- decide final product copy or trigger logic.

## Fit And Routing

This workflow is a short-frame animation asset workshop. It is not a universal motion-design generator.

Good fits:

- Character stickers, emotes, and reaction animations.
- Pixel/chibi/desktop-pet subjects and small mascot actions.
- Simple object animations with one readable subject.
- Lightweight icon feedback when the icon has few layers and no fine text.
- Sprite sheets for games, pets, chat companions, stickers, and short GIF-style assets.

Use caution:

- UI icons with glossy 3D material, particles, and highlights can work only when the subject is simple, text-free, and each frame has enough resolution.
- Longer sequences can work only when the sheet is large enough that each frame remains crisp.
- Green-screen delivery is only safe when the subject palette does not collide with the key color.

Poor fits:

- Complex achievement badges or collectible UI icon systems with many layers, fine 3D details, text, particles, and highlight sweeps.
- Motion that needs independent control of layers, masks, text, particles, and easing curves.
- High-fidelity product UI motion where text must remain sharp and layout-aware.
- Lottie-style or code-style interactions such as badge unlock modals, confetti systems, staged reveal cards, or reward ceremonies.

When a request is a poor fit, do not force a sprite sheet. Recommend a layered approach instead:

- Generate or provide a static transparent base asset.
- Separate layers such as base, subject, particles, highlight, and text.
- Animate with Lottie, CSS, Canvas, SVG, or app-native motion.
- Keep text in the UI layer when sharpness, localization, or accessibility matters.

## Core Principles

- Subject is not action. A cat, headset, hair clip, mascot, or object does not imply a default motion.
- Style is not action. Cute, gothic, romantic, or playful is a visual/performance direction, not a motion by itself.
- Reference overrides default anatomy. If the user provides a style/reference image, first follow the reference's character grammar, proportions, weirdness, limb logic, and line quality. Default "simple mascot with arms and legs" anatomy is only a fallback, not a rule.
- Reference intent matters. A reference image can mean "use this style" or "use this exact character/object". Do not redesign an exact provided character when the user wants that character copied or continued.
- For style references, extract a `reference_style_profile` before prompting. For exact character references, preserve identity first and only add the requested animation/base-reference structure.
- For UI icons, badges, props, and object systems, a reference image often defines **how to draw**, not **what object to copy**. Extract the visual system grammar first, then replace the requested subject inside that grammar.
- Reusable animated subjects need a confirmed canonical base. If the same character, sticker subject, icon, or object will be used across multiple images or actions, first create and confirm a clean `canonical_base`; later sprites must use that approved base as the visual source of truth.
- A local file path written inside a prompt is not a real visual reference. For identity-sensitive work, the reference image must be attached/visible to the image-generation path, not merely described as a path in text.
- "Beautiful but not the same subject" is a failed base frame when the user wants to continue an existing character/object.
- User review should focus on identity and taste, not mechanical canvas cleanup. After generating a `canonical_base`, normalize basic composition first: clean flat background, centered subject, stable contact/baseline when applicable, safe padding, and no text/decorations.
- Production rules are fixed; performance design stays open. Lock the asset requirements needed for animation/QC, but do not hard-code the exact acting, poses, gestures, squash/stretch, or emotional interpretation unless the user asks for them.
- The user should not have to choose technical motion categories. Infer the subject type and action intent internally, then write a subject-aware brief that gives the image model expressive freedom inside the production constraints.
- Scene/use case guides action direction, playback, frame count, and strictness.
- Subjects are confirmed once, then actions can be freely performed later.
- Motion planning defines action structure, not exact locked poses.
- Frame count is capacity, not rhythm. Timing is finalized after the sprite exists.
- Users do not need to know frame counts or grid layouts. Infer a sensible frame count and layout from the action, intended use, and requested length unless the user gives an exact frame count/layout.
- Rhythm has two layers: generation-time `rhythm_intent` describes how the frame sequence should progress; post-generation `timing` describes how long real frames should play after the image exists.
- User-facing delivery should be a usable next result, not an inspection burden. Do the basic asset checks, splitting, preview preparation, and QC handoff before asking the user to judge the work, unless generation failed and the failure itself needs a decision.
- `once` and `loop` playback must be handled differently.

## Input Recognition

Before writing a generation prompt, classify the user's input:

- `asset_type`: `sticker`, `sprite_animation`, `ui_state_motion`, `full_sequence_animation`, `character_base_frame`, `sprite_qc_only`, or `sprite_from_existing`.
- `subject_type`: `character`, `object`, `ui_element`, or `sticker_subject`.
- `subject`: the role or object, such as cat, headset, hair clip, mascot, button, sticker character.
- `action`: explicit action if provided. Do not invent a default action from the subject alone.
- `scene_or_use`: startup, loading, click feedback, success state, empty state, chat companion, idle loop, sticker/emote, etc.
- `style_or_mood`: cute, funny, romantic, calm, magic, European, etc.
- `motion_scope`: internal only: `micro_motion`, `expressive_motion`, `performance_motion`, `large_motion`, or unknown.
- `reference_intent`: `style_reference`, `exact_character_reference`, `mixed_reference`, or unknown.
- `reference_strength`: `0_style_only`, `1_recognizable_adaptation`, `2_close_copy`, or unknown.
- `playback`: `once`, `loop`, or unknown.
- `length_intent`: instant feedback, short reaction, standard sticker, mini performance, long sequence, process loop, custom, or unknown.
- `frame_hint`: exact frame count/layout, length preference, or unknown.
- `rhythm_intent`: internal only: reaction_once, reaction_loop, idle_loop, physical_once, physical_loop, process_loop, story_sequence, or unknown.

If the user only provides a subject and not an action/use case, ask one short question or offer action directions suitable for that subject. If the user chooses "free judgment", infer a sensible direction.

Users do not need to describe pose mechanics. Infer motion scope from the action:

- `micro_motion`: idle, breathing, blinking, tiny waiting, subtle loading companion.
- `expressive_motion`: small emotion/state changes where face, head, shoulders, hands, hair, or soft parts visibly move while the body anchor stays mostly stable.
- `performance_motion`: emotion/reaction words such as disdain, surprise, delight, shy, proud, angry, smug, confused, embarrassed, cheering, crying, laughing, or sticker/emote requests. Default to whole-body acting: head turn/tilt, torso lean, shoulder/hand/sleeve gesture, hair/clothing follow-through, and a clear peak pose. Do not reduce these to only eyes/mouth unless the user asks for subtle motion.
- `large_motion`: jump, run, fall, slide, spin, travel, attack, full entrance, or other explicit large physical action.

Default rule: for emotional reactions and stickers, use `performance_motion` unless the user says "微动", "轻一点", "只要表情", "不要动作太大", or the scene requires calm idle behavior.

Keep this classification internal. Do not ask the user to choose `motion_scope` by default. The user says the desired action in normal language; the workflow translates it into a generation brief.

If the user provides a reference image, classify intent before generating:

- `style_reference`: the reference provides style, mood, line language, character grammar, or visual taste. Generate a new subject in that style.
- `exact_character_reference`: the reference is the character/object to use. Do not redesign it or substitute a similar character; preserve the exact identity, silhouette, proportions, face, colors/materials, outfit/accessories, and distinctive details.
- `mixed_reference`: the user wants both a specific subject and style influence. Preserve the specified subject while borrowing only the style dimensions the user asked for.
- Unknown: ask one short question, such as "是参考这个风格，还是就用图里这个角色继续做？"

When the user provides an existing character/object/icon/sticker reference that is not already a clean animation base, ask how to use the reference before generating the clean base unless the user already made it clear. Do not expose internal parameter names such as `reference_strength` to the user.

```text
你想要这张参考图怎么用？

1. 只借风格：可以长得不一样，只保留风格/质感
2. 保留识别点：像同一个角色/物件，但允许更干净、更规整
3. 尽量贴近原图：脸/轮廓/比例/颜色/关键细节都尽量贴近
```

Default recommendations:

- Existing character/object that should continue into animations: recommend "尽量贴近原图" and internally map it to `2_close_copy`.
- Sticker pack from a loose vibe/reference board: recommend "保留识别点" and internally map it to `1_recognizable_adaptation`.
- New subject in an existing style: recommend "只借风格" and internally map it to `0_style_only`.

Do not use cropping/cutout as the default formal base-generation path for a decorated reference sheet. Cropping or background removal is only a fallback/inspection aid when the original single pose is already usable. For reference sheets, multi-pose images, decorated boards, or images with text/background clutter, regenerate a clean `canonical_base` with the chosen reference strength.

For `reference_strength: 2_close_copy`, use grounded generation:

- The image-generation path must receive the reference image as a real input image.
- If using the built-in image generation path with a local file, first load/inspect the local image so it is visible in the conversation context, then generate/edit from that visible image.
- Do not rely on a prompt that merely says `use /path/to/file.png`.
- If the current image generation path cannot attach or edit from the reference image, stop and explain the limitation before generating. Offer a true image-input/edit path instead of producing a prompt-only imitation.

For `style_reference`, create an internal `reference_style_profile` before writing the generation prompt:

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

Use this profile to write concrete style constraints. Avoid vague-only prompts like "cute", "quirky", or "hand-drawn" when the reference has more specific visual grammar.

For UI icon, badge, prop, or object-system references, create an internal `reference_visual_system` before prompting. Do this when the user says things like "照这个风格画一个...", "同一系列", "只换主体", "边框/样式保持一致", or when the reference clearly shows a reusable asset system:

```yaml
reference_visual_system:
  canvas_context:
  container_shape:
  container_depth_and_edge:
  material_language:
  color_logic:
  lighting_and_shadow:
  camera_angle:
  subject_scale_and_position:
  subject_container_relationship:
  break_frame_or_overflow_rule:
  auxiliary_element_density:
  text_or_label_treatment:
  series_consistency_locks:
  replaceable_subject_slots:
  what_not_to_change:
```

Use this rule:

```text
Reference image controls the drawing system.
User request controls the replacement subject/theme.
First lock how it is drawn, then replace what is drawn.
```

Do not reduce this kind of request to "draw an object with the same name." For example, if the reference is a collectible badge system and the user asks for a red packet badge, keep the badge system grammar and replace only the hero subject/theme. Do not invent a generic game icon or unrelated illustration style.

For `exact_character_reference`, create or preserve a character profile from the provided image instead of inventing a new design:

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

Only ask about exact-copy intent when ambiguous. If the user says "use this", "就是这个", "按这个角色", "复刻这个", or "不要重新设计", treat it as `exact_character_reference`.

If the user already provides a sprite sheet, do not restart character creation by default:

- `sprite_qc_only`: existing sprite sheet, only needs QC, alignment, GIF preview, timing, audit, and report. Hand off to `$animation-qc`.
- `sprite_from_existing`: existing sprite sheet should be processed, continued, frame-selected, timing-adjusted, or used as the source for a derivative asset. Inspect the existing sheet first; do not recreate the character from scratch.

## Normal User Flow

Most users will not know the names of the steps. Guide them through the workflow without exposing technical internals by default.

Start by detecting the user's entry point. Do not assume the user already knows the workflow.

Entry routing:

- If the user already gives a clear subject, action, and frame/length hint, proceed with minimal confirmation.
- If the user gives a clear subject but no action, treat it as character/base setup or ask one short action question.
- If the user gives a clear action but no character/current character, ask where the character comes from: new character, existing image, or current character.
- If the user says they want animation assets but does not know how to start, ask one entry question:
  "你现在是想：1. 从零做一个可动画化的主体 2. 让已有角色/物件/图标动起来 3. 检查已有雪碧图？"
- If the user provides an existing sprite sheet, route to `$animation-qc` instead of restarting generation.
- If the user provides an existing character/object/icon/sticker reference that is not a clean animation base frame, automatically enter base-reference preparation before action generation. Ask only the plain-language reference-use question if the desired fidelity is not already clear.
- If enough information is already provided, do not ask the entry question again.

Default flow:

1. **Subject/base first**
   - If the user asks for a new reusable subject, character, object, icon, sticker subject, or "a thing that can move", treat it as subject setup.
   - If they provide only a subject or style reference, generate or propose a base subject first. Do not jump directly to an action.
   - If they provide an existing character sheet, multi-pose image, decorated reference board, image with labels/text, or a complex background, first generate a clean single-subject `canonical_base`. Preserve the existing identity according to the selected reference strength; do not default to cutout/cropping as the formal base.
   - Ask the user to confirm the base: face, shape, style, proportions, and general vibe.
   - If accepted, treat the approved base as the visual source of truth for later action/sticker/object animations.
   - If accepted, optionally ask for a name so later action requests can reuse the character naturally.

2. **Action second**
   - Once a subject is confirmed, ask for the desired action if the user has not provided one.
   - If the user gives a vague mood such as "cute", "cool", "sleepy", or "happy", convert it into an action direction only after checking the scene/use or giving a few simple action suggestions.
   - Do not ask the user to describe every frame. Internally plan the action structure.

3. **Length intent and frame/layout inference before action generation**
   - Do not make the user choose a frame count by default. Infer frame count and layout from the action, intended use, playback, and any length words the user used.
   - If the user says "短一点", "快速反馈", "小表情", "完整一点", "长一点", "一段流程", "循环挂着", or similar, map that length intent to an appropriate frame count/layout internally.
   - If the user gives an exact frame count or layout, follow it without asking again.
   - Ask about length only when it materially changes the output and cannot be inferred from the action/use case.
   - Keep the user-facing wording simple, such as "我先按一个标准表情动图来做" or "这个动作像小表演，我会给它多一点帧数".
   - Before generation, write an internal `sprite_geometry_contract` with exact `cols`, `rows`, `frame_count`, target whole-sheet pixel size, target cell size, playback type, and a generic cell/sequence map. For example: `3x2`, `6 cells`, `1536x1024`, `512x512 cells`, `sequence_a uses row 1 cells 1-3`, `sequence_b uses row 2 cells 1-3`.
   - If the image-generation path cannot honor exact pixel dimensions, still keep the same contract and treat it as the post-generation gate. Do not relax the contract just because the generated image "looks like" a grid.

4. **Generate action sprite**
   - Use the confirmed character/subject, visual rules, canonical base, and anchor profile.
   - For reusable subjects, attach or otherwise provide the approved canonical base to the image-generation path. Do not use prompt-only generation for identity-sensitive action sprites.
   - When generating multi-frame sheets, create or provide a simple layout guide before generation whenever the image-generation path supports input images. The guide is for exact frame count, row/grid structure, slot spacing, centering, safe padding, and anchor/baseline placement only; it must not appear in the output.
   - If no image-input layout guide is possible, say that this run is prompt-constrained, write the exact geometry contract into the prompt, and expect stricter post-generation rejection/regeneration. Do not imply prompt-only geometry is guaranteed.
   - Generate a playable sprite sheet only after subject + action + rough length are known or reasonably inferred.
   - If multiple actions are requested together, a combined multi-row sheet is allowed as a generation batch. It is not the final user-facing deliverable by itself.
   - After generation, do not stop at the image. Run basic gates, split multi-sequence batches into per-sequence assets when needed, then continue to GIF preview and stability check.

5. **QC and decision**
   - Run or recommend `$animation-qc` after the generated sheet passes basic gates.
   - For multiple actions, each action gets its own preview and QC path.
   - Show the GIF previews first, not a raw combined sheet as the main result.
   - Then guide the user to accept, adjust speed, regenerate one action, drop frames, or continue to integration.

User-facing prompt examples:

```text
你现在是在定角色，不是在做动作。我先帮你出一个基准造型，你看脸、比例、气质对不对。
```

```text
角色我先记住了。接下来你想让它做什么动作？如果你还没想好，我可以给你几个适合它的动作方向。
```

```text
动作方向有了。我先按一个标准表情动图来做；如果你想要更短、更夸张，或者像一小段表演，我会在生成前帮你换成更合适的长度。
```

## Current Subject / Character

When the user is creating a new character, sticker subject, object mascot, animated icon, or reusable UI object, start with a base-frame confirmation flow instead of immediately generating an action.

Track the current subject conceptually. `current_character` is still a valid alias when the subject is a character:

```yaml
current_subject:
  name:
  subject_type: character / object / ui_element / sticker_subject
  reference_images:
  reference_strength: 0_style_only / 1_recognizable_adaptation / 2_close_copy
  canonical_base:
    image:
    confirmed: true / false
    generation_mode: prompt_only / grounded_reference / image_edit
  visual_rules:
    silhouette:
    colors:
    face_style:
    line_style:
    proportions:
    outfit_accessories:
    material:
  anchor_profile:
    center_anchor: body_main_axis / body_visual_center / object_visual_center
    baseline_anchor: foot_baseline / contact_baseline / sitting_baseline / none
    default_alignment:
      center: body_or_object_itself
      baseline: grounded_contact_line_when_applicable
    audit_reference:
      - center_cross_for_floating_icons_or_objects
      - contact_baseline_for_grounded_subjects
      - rotation_center_for_spinning_subjects
      - path_anchor_for_traveling_subjects
    ignore_for_center:
      - hands
      - feet_if_moving_slightly
      - facial_marks
      - motion_lines
      - props
      - temporary_outfit_edges
      - skirt_or_cape_edges
      - sparkles_bubbles_effects
    baseline_rule: grounded actions keep the same contact line unless the action explicitly jumps, falls, slides, floats, or travels.
    uncertainty: ask only when the body/core object is ambiguous.
  confirmed: true / false
  previous_subjects: []
```

Rules:

- If there is a confirmed current subject, later action requests should reuse it by default.
- A confirmed subject should also carry its own `anchor_profile`. This profile is per subject, not global.
- A confirmed subject should carry an approved `canonical_base`. Later identity-sensitive generations must use that base as a grounding image whenever the generation path supports it.
- By default, character assets use the body/main object as the center anchor. Object/icon assets use the object visual center unless they have an explicit contact line. Do not ask the user every time unless the body/core object is ambiguous.
- Every sequence needs a stable anchor policy, but not every sequence needs a foot line. Floating UI icons and badges use a `center_cross` (center X plus center Y). Grounded characters and objects use center X plus foot/contact baseline. Spinning subjects use a rotation center. Traveling subjects use a path anchor.
- When switching to a new subject, create a new base frame and a new `anchor_profile`.
- When returning to a previous subject, restore that subject's previous `canonical_base` and `anchor_profile`.
- One-off subjects can have temporary bases/profiles, but they should not overwrite the current subject unless the user confirms.
- If the user says "change character", "new character", "new object", or similar, enter a new base-frame confirmation flow.
- If the user says "do not use the current subject this time", treat the request as a one-off without overwriting the current subject.
- If the user says "go back to the previous character/object", restore the previous confirmed subject when context is available.
- If the user says "clear current character/subject", remove the current subject context and ask for a subject/reference before the next action.
- Naming is optional. After a subject is confirmed, ask whether the user wants to name it only when that would make later reuse easier.

Base-frame flow:

1. Choose the subject reference depth:
   - Lightweight default: one neutral front base frame.
   - Stability upgrade: three-view character sheet (`front / side / back` or `front / 3/4 / side`) when the character is complex, likely to become a long-term IP, needs many motion assets, needs turns/side poses, has important outfit/accessory details, or the user asks for more stability.
   - If the user is only exploring or making one small action, do not force three views.
2. Generate or define the chosen base reference: normal posture/state, centered, correct proportions, stable visual style, and clear contact/baseline.
3. If the user provided an existing character/object/icon/sticker reference that is not clean enough for animation, automatically enter clean base generation before any action generation:
   - one subject only;
   - neutral standing or stable default pose unless the user needs a different base state;
   - ask how closely to follow the reference in plain language if not already clear;
   - for `0`, transfer style language to the requested subject without copying identity;
   - for `1`, preserve the recognizable subject while allowing cleanup, simplification, and animation-friendly regularization;
   - for `2`, preserve exact identity as much as possible: face/shape, silhouette, proportions, colors/materials, outfit/accessories, markings, and signature details;
   - for `2`, require real reference-image input/grounded generation; do not generate from text path descriptions alone;
   - remove labels, UI text, decorative stickers, surrounding poses, background ornaments, and unrelated props;
   - keep the subject centered with a clear body/main-object anchor and contact/baseline when applicable;
   - do not ask whether to prepare a clean base; it is the required bridge from "reference board" to "animatable subject". Ask only the fidelity/strength question when needed.
4. If the user provided a reference image, match its character language before animation convenience:
   - preserve its looseness, odd proportions, construction logic, line quality, and level of polish;
   - do not normalize the subject into a generic cute mascot unless the user asks for that;
   - do not automatically add standard small arms/legs if the reference suggests stranger anatomy.
   - If the reference is an exact character/object reference, preserve that character instead of making a new character in a similar style.
   - If the reference is a style reference, first summarize the reference style profile internally and use concrete style constraints from that profile.
5. Ask the user to confirm or adjust. A base that is attractive but no longer matches the intended subject is not accepted for `1` or `2`.
6. After confirmation, infer a default `anchor_profile` from the base reference:
   - character: body/main torso or core body as center anchor;
   - standing character: body center plus foot/contact baseline;
   - sitting character: body center plus sitting/contact baseline;
   - soft body, jelly, elastic, or bendable character: visual body center plus contact baseline, allowing shape deformation without whole-subject drift;
   - object/icon: main object visual center and `center_cross`, no foot baseline unless it has a clear contact line;
   - spinning object/icon: rotation center;
   - entrance/exit/travel animation: path anchor, not fixed center.
7. Ask about the anchor only if the core body/object is unclear, such as an abstract character, multi-subject group, body fused with a large prop, or user-specified special anchor.
8. Ask about anatomy/personification only when it materially changes the design:
   - the reference style conflicts with later animation needs;
   - the subject can reasonably be interpreted as object-first or person-first;
   - the first version becomes too template-like compared with the reference.
9. After confirmation, optionally name the subject.
10. Use the confirmed base reference, visual rules, and anchor profile for later actions.

## Grounded Generation And Layout Guides

Use this grounded generation pattern for any reusable animated subject:

1. Prepare or receive one or more user reference images.
2. Generate a clean `canonical_base` using the selected reference strength.
3. Normalize the generated base before showing it to the user.
4. Ask the user to approve the normalized base before any action/sticker/object animation generation.
5. Save or remember the approved normalized base as the visual source of truth.
6. For each action/sticker/animated-icon sheet, generate with:
   - original reference image(s), when available;
   - the approved `canonical_base`;
   - a layout guide when the generator supports input images;
   - a strict prompt that says only pose/action may change.
7. After the sheet exists, hand off to `$animation-qc`.

Canonical base normalization:

- Run this before user review whenever practical.
- Check that the background is true flat chroma key or true transparency, not checkerboard/fake transparency.
- If outputting both a transparent asset and a checkerboard view, treat them differently:
  - the transparent PNG is the real `canonical_base` and the only image that should ground later action generation;
  - the checkerboard image is only a `review_preview` for inspecting edges, padding, centering, and contact/anchor placement;
  - never use the checkerboard preview as an image-generation reference for later actions, because the generator may copy the fake transparency pattern;
  - do not present both files as equal base images. Make the transparent PNG the primary result and clearly label the checkerboard as a visual preview.
- Check subject bounds and padding; if the whole subject is only slightly off-center, recenter it automatically on a clean square canvas.
- For grounded character assets, keep the feet/contact line clear and stable; a standing character may sit slightly lower than pure visual center if that better preserves the baseline.
- For object/icon/sticker assets without a contact line, use visual center and balanced padding.
- For UI icons, badges, and detailed glossy objects, prefer true transparency when the generation path can provide it. Use green screen only when the subject palette clearly does not contain green, cyan-green, yellow-green, or edge glows that can collide with keying.
- If a subject uses green/mint/teal/lime materials, or has translucent highlights near green, do not default to `#00FF00`. Request transparent output or use a clearly non-conflicting temporary background for processing.
- Remove only mechanical canvas/background issues. Do not redraw, crop into the body, change the face, change style, change outfit/materials, or alter subject identity during normalization.
- If the base has identity drift, bad crop, dirty edges that affect the subject, missing limbs/details, non-flat background that cannot be safely removed, or composition that requires taste judgment, do not silently normalize it. Regenerate or ask for confirmation.
- Present the normalized transparent base to the user, not the raw generated base, unless the raw/normalized comparison is needed for debugging.
- For normal user-facing confirmation, summarize normalization in plain language such as "透明底、已居中、留白安全". Do not show exact alpha values, pixel offsets, script flags, or padding numbers unless the user is debugging or asks why.

Layout guide purpose:

- communicate exact frame count and row/grid structure;
- show slot spacing, centering, and safe padding;
- help prevent blank cells, overlapping poses, cropping, and inconsistent scale.
- enforce the intended whole-sheet aspect ratio: `columns:rows`. If each cell is square, a `3x2` sheet is `3:2`, a `4x2` sheet is `2:1`, a `2x2` sheet is `1:1`, and a `4x3` sheet is `4:3`.

Layout guide rules:

- The guide is an input-only construction reference.
- The generated output must not include visible boxes, guide lines, center marks, labels, guide colors, or guide background.
- If no image-input guide is possible, write the slot constraints explicitly in the prompt and inspect the output more strictly.
- For playable sprite sheets, a layout guide is only a planning aid. The stronger default is a machine-cuttable raw sprite output with visible cell separation, exact square cells, and a clean key/transparent background.
- Skip layout guides only when the user is making a quick concept exploration, the tool cannot accept an input guide, or a single-row/single-action output is trivial enough to verify after generation.
- The guide should have exact pixel dimensions whenever practical. Prefer simple deterministic targets such as `1024x1024` for `4x4`, `1024x512` for `4x2`, `768x512` for `3x2`, and `1024x768` for `4x3`. The cell size must be an integer and every cell must be square.
- The guide should mark a safe area, subject center line, and baseline/contact line when useful. These marks are input-only construction aids; the generated output must remove them.
- If a confirmed `canonical_base` exists, place or reference it with the guide so the generator has both identity and frame-slot structure. Do not rely on text-only identity plus text-only grid instructions for reusable character animation unless no grounded path is available.

Raw sprite cell template:

- For playable sprite sheets, prefer asking the image model to output a raw production sheet, not a poster-like collage.
- A raw production sheet may include visible cell dividers and a clean chroma-key background because those are part of the machine-cuttable source, not decorative guide marks.
- Recommended raw sheet format:
  - pure chroma green `#00FF00` or true transparency in every cell;
  - thin clean divider lines between cells when using chroma green;
  - one complete pose fully contained in each `1:1` cell;
  - no labels, numbers, center marks, baseline marks, guide colors, or UI text;
  - no frame overlap across dividers;
  - stable body/root placement and stable contact/baseline unless travel is explicit.
- If the model struggles to follow an input-only layout guide, switch to this visible raw sprite template requirement before regenerating.
- Do not confuse this with a final transparent product asset. The green/divider raw sheet is allowed as a source for cutting and QC; `animation-qc` must still remove/key the background and export transparent outputs.

Sprite geometry contract:

Before any playable sprite generation, record the exact contract internally and include the important parts in the prompt:

```yaml
sprite_geometry_contract:
  cols:
  rows:
  frame_count:
  target_canvas_px: [width, height]
  target_cell_px: [width, height]
  cell_aspect: 1:1
  whole_sheet_aspect: cols:rows
  cell_or_sequence_map:
  valid_cells:
  empty_cells:
  playback:
  background: transparent_or_clean_key
  raw_sheet_format: transparent_or_chroma_green_with_cell_dividers
  anchor_policy:
```

This contract is the pass/fail target after generation. If a generated sheet has a different pixel size but can be deterministically recomposed into the contract without changing art, do that before QC. If it cannot, regenerate.

Production execution checklist:

- In the image-generation prompt, restate the geometry contract in plain hard terms, not only as abstract intent: `N columns x M rows`, `whole sheet aspect ratio N:M`, `every cell exactly square`, `target_canvas_px`, `target_cell_px`, `valid_cells`, and `empty_cells`.
- After the image is generated, inspect the actual file dimensions before QC. Do not trust the preview shape, visible grid, or model's apparent compliance.
- Run `scripts/check_sprite_gate.py` against the contract before `$animation-qc`, including target width/height/cell whenever those are known. For green sheets with visible dividers, also check visible grid alignment.
- If a generated image visually contains the intended grid but the actual dimensions are wrong or non-integral for the contract, such as `1774x887` for a `4x2` sheet, do not pass it to QC. Deterministically recompose/resize it to the target canvas only when cell boundaries and per-cell artwork are unambiguous and no art must be invented or redrawn; then run the gate again.
- If deterministic recomposition cannot be done cleanly, regenerate with a stronger layout guide/raw-template requirement or split the action into a smaller sheet with larger cells.

Sprite sheet geometry check:

- After generation and before QC, verify sheet geometry.
- For a grid with `cols x rows`, the whole image must have aspect ratio `cols:rows` if every cell is square.
- Width must divide cleanly by `cols`; height must divide cleanly by `rows`; computed cell width and cell height must match.
- Do not accept "visually looks like a grid" as a pass. The sheet must be machine-cuttable: integer cell dimensions, equal cell sizes, expected cell count, and no ambiguous gutters or merged frames.
- For multi-sequence sheets, verify both geometry and cell semantics: each declared sequence has the expected number of usable frames, blank/placeholder cells match the contract, and no cell secretly contains an unrelated pose, subject, or phase.
- Basic sprite gate result controls routing:
  - `pass`: split per action and continue to `$animation-qc`.
  - `recompose`: only when frame content is clear and deterministic placement into exact cells will not redraw or invent art.
  - `regenerate`: when dimensions, cells, gutters, missing frames, overlapping poses, nontransparent background, crop, or cell/sequence mapping are ambiguous.
- If the generated art has good identity/action but the sheet canvas is wrong, deterministic recomposition into a correct sheet is allowed: crop each generated pose as an already-generated visual output and place it into clean square cells. Do not redraw, invent missing poses, alter identity, or claim recomposition fixed animation quality.
- If pose extraction is ambiguous, frames overlap, cells are missing, or recomposition would require artistic choices, regenerate instead.

Generation-mode rules:

- `prompt_only`: allowed for new subjects or `0_style_only` exploration.
- `grounded_reference`: required for `1_recognizable_adaptation` when user identity matters, and always required for `2_close_copy`.
- `image_edit`: preferred when the user asks to clean up an existing image while preserving identity or composition.

If the available generation tool cannot provide real image grounding for `2_close_copy`, stop and explain that limitation. Do not produce a prompt-only lookalike and call it a close copy.

Layout guide helper:

Use the helper script when you need a concrete guide image for a sprite run:

```bash
python3 scripts/make_layout_guide.py \
  --cols 3 \
  --rows 2 \
  --cell 512 \
  --labels seq_a,seq_b \
  --out /tmp/sprite-3x2-layout-guide.png
```

The helper output is an input-only construction guide. Do not treat it as a final product asset, and do not allow the generated sprite sheet to include its guide lines, labels, background, or colors.

Basic sprite gate helper:

Use the gate immediately after generation and before `$animation-qc`:

```bash
python3 scripts/check_sprite_gate.py \
  --input /path/to/raw-sheet.png \
  --cols 4 \
  --rows 2 \
  --target-width 2048 \
  --target-height 1024 \
  --target-cell 512 \
  --allow-guide-background \
  --check-visible-grid
```

If this fails because the generated sheet has a visual grid but the bitmap size is wrong, fix it only through deterministic recomposition into the declared target. Do not send the failed sheet directly to `$animation-qc`.

## Length Intent And Layout

Infer frame count and grid layout from the user's natural request. The user does not need to know sprite-sheet geometry.

If the user gives an exact frame count or layout, obey it:

- `4 frames`: usually `2x2`; `4x1` is acceptable for small UI/icon strips.
- `6 frames`: usually `3x2`.
- `8 frames`: usually `4x2`.
- `9 frames`: usually `3x3`.
- `12 frames`: usually `4x3` for horizontal sheets, `3x4` when vertical organization is more appropriate.
- `16 frames`: usually `4x4`.
- Higher counts such as `20`, `24`, or custom counts are allowed. Choose a balanced grid or split into multiple sheets when one sheet becomes too wide, too tall, or semantically overloaded.
- For visually detailed subjects, small pixel/chibi characters with many identity details, or assets where crispness matters, prefer fewer cells per generation and larger cells over one dense all-in-one sheet. A dense combined sheet is acceptable as a process test, but not the default path for final-quality assets if each cell becomes too small or blurry.

If the user describes length or use instead of frame count, infer:

- Instant UI feedback or tiny expression: `4-6` frames.
- Standard sticker/reaction: `6-8` frames.
- A readable mini performance with entrance, development, peak, and hold: `8-12` frames.
- Idle/ambient loop: `4-8` frames, usually subtle and loopable.
- Walk/run/spin/loading/process loop: enough frames to loop smoothly, often `6-12`.
- A longer flow, short story, or multi-beat action: `12-24` frames or multiple connected sheets.

Hard geometry rule:

- Every frame cell must be square.
- Whole-sheet aspect ratio must equal `columns:rows`.
- Do not force all sprite sheets to be square. A `3x2` sheet should be `3:2`; a `4x2` sheet should be `2:1`; a `4x3` sheet should be `4:3`.

This inference is a default, not a creative limit. If the action needs more room, choose more frames. If the user wants a quick test, choose fewer frames.

## Subject-Aware Performance

Use subject-aware performance direction instead of one fixed acting template.

First classify the subject:

- `character`: human-like, mascot, doll, chibi person, humanoid IP.
- `animal`: pet, creature, animal mascot, animal-like IP.
- `object`: product, prop, item, tool, icon-like object, non-human thing.
- `ui_element`: button, card, badge, loader, panel, app-state component.
- `abstract`: blob, shape, symbol, particle, non-literal visual subject.

Then translate the user's action into open performance boundaries:

- For `character`, expression may involve face, head, torso, shoulders, arms/hands, clothing, hair, posture, and weight shift.
- For `animal`, expression may involve face, head, ears, tail, paws, body squash/stretch, posture, and weight shift.
- For `object`, do not automatically add a human face, arms, or legs. Expression may use tilt, bounce, squash/stretch, rotation, lid/flap/part movement, material response, shine, state change, or small attached effects if allowed.
- For `ui_element`, use UI-native motion such as scale, press, tilt, bounce, shimmer, reveal, loading rhythm, state transition, or icon transformation.
- For `abstract`, use shape change, rhythm, direction, color/brightness change, particle grouping, or motion path.

For emotional/sticker actions, the prompt should say the action is a readable mini performance, not a face-only expression. Let the image model choose the concrete acting choices, as long as identity, frame layout, background, safe padding, and anchor/baseline rules remain intact.

Avoid frame-by-frame pose scripts such as "frame 1 do X, frame 2 do Y" by default. Use semantic phases instead: start, anticipation, reaction develops, peak expression/action, recovery, and holdable end.

Only prescribe exact poses when the user requested them, when repairing a failed generation, or when a specific product interaction demands a particular physical state.

## Rhythm Intent And AI Timing Review

Separate `rhythm_intent` from concrete `timing`.

Generation-time rhythm intent:

- This is a loose sequence direction, not a frame-by-frame storyboard.
- It tells the image model what kind of frame progression it is making: a reaction, a loop, a physical action, a process, or a story.
- It should not specify exact gestures, exact poses, or exact milliseconds unless the user asked.

Common rhythm intents:

- `reaction_once`: an action/reaction that starts, develops, reaches a readable peak, and can hold at the end.
- `reaction_loop`: an expressive reaction that should return naturally to the first frame.
- `idle_loop`: subtle continuous motion with no strong peak.
- `physical_once`: preparation, action, result, and settle.
- `physical_loop`: continuous physical cycle with clean loop return.
- `process_loop`: ongoing activity with persistent rhythm, not a hard endpoint.
- `story_sequence`: multiple beats or events in order.

Post-generation AI timing review:

- After the sprite sheet exists and passes basic geometry/action gates, inspect the actual frames before final GIF timing.
- Do not rely only on fixed default durations when the frame content varies.
- Identify which frames are start/read, transition, peak/key pose, recovery, loop-return, and hold/end based on the actual image.
- Decide whether similar frames should pass quickly, larger visual changes should breathe, peaks should hold, and whether the final frame should hold or return quickly.
- For `once`, a comfortable final pose may hold longer.
- For `loop`, avoid a long final hold unless explicitly requested; the last frame should return naturally to the first.
- If the animation feels too fast, too slow, mechanical, jumpy, or "鬼畜", revise timing before presenting it as acceptable.
- After a GIF exists, timing should become a user-facing feeling choice when needed: natural, slower/cuter, livelier, stronger final hold, or smoother loop. Do not make the user choose raw milliseconds by default.

The output of timing review should be a selected timing plan, such as `recommended`, plus optional alternatives only when needed. It should feed the GIF preview and final `timing.json`; it should not redraw the asset.

## Multi-Action Batches

When the user asks for several motions, clips, or states at once, treat it as a batch request but keep the final assets sequence-specific.

- A single generation may contain multiple sequences, such as one row per sequence or one rectangular block per sequence, when this helps preserve identity and style consistency.
- A combined multi-sequence sheet is an internal batch artifact or debug artifact, not the normal user-facing final result.
- Multi-sequence generation is allowed, but it should be planned by available cell budget and clarity, not by hard-coded action names. Empty cells are valid only when declared in the `sprite_geometry_contract` and kept as clean placeholders.
- If a multi-sequence sheet makes the subject visibly softer, smaller, or harder to key, split the request into smaller batches with larger target cells before treating the art as final-quality source.
- Immediately after generation, run the basic gates on the combined sheet: overall geometry, expected sequence/cell mapping, cell count, square cells, background, subject visibility, crop, and sequence readability.
- If the combined sheet passes geometry gates, split it into one independent sheet per sequence before preview/QC.
- If the combined sheet does not match the `sprite_geometry_contract`, do not send it to `$animation-qc`. First either deterministically recompose it into the contract or regenerate with a stronger layout guide.
- If one sequence is good and another is bad, keep the good sequence asset and regenerate only the failed sequence when possible.
- Each final sequence must receive its own GIF preview, timing review, QC output, audit, and report.
- Do not ask the user to inspect the raw combined sheet unless there is a failure, ambiguity, or the user specifically wants to compare the batch.
- The user-facing checkpoint should be the playable previews with a simple status line, such as "已检查格子和背景，已拆成两个预览".

For example, if the user asks for "不屑" and "惊喜满眼冒光":

- Generating a `4 columns x 2 rows` sheet is allowed as a batch draft: row 1 is disdain, row 2 is sparkling surprise.
- Before showing it as a result, verify the sheet is `2:1`, every cell is square, and both rows have four readable frames.
- Split row 1 into `disdain` and row 2 into `sparkling_surprise`.
- Produce separate GIF previews and timing plans for each action.

## Global Logic

Every prompt should have four layers:

1. **Character Lock**
   - Define immutable identity: character shape, color, material, face style, line style, proportions, signature parts.
   - If using an exact character reference, identity preservation is stricter than style imitation. Do not reinterpret the character into a nearby mascot.
   - If using a style reference, transfer the extracted style profile onto the requested new subject instead of copying the reference character itself.
   - Decorations, clothes, props, and effects are external. They cannot change the core character.

2. **Run Setup**
   - Decide scene/use case, mood, style/theme, props/effects, and forbidden elements.
   - If the user specifies a theme, follow it.
   - If the user is vague, infer a restrained setup with only a few external elements.
   - For multi-sheet animations, lock the setup across all sheets.

3. **Action Structure**
   - Separate skeleton from performance.
   - Skeleton is the narrative role of the animation; performance is how the character acts it out.
   - Do not force one fixed action template.
   - For emotional, sticker, or reaction actions, ask for a readable mini performance, not a face-only expression. Preserve identity and baseline, but do not lock the body/object into the canonical base pose.
   - Match performance language to subject type: a character may act with posture and hands; an object may act through tilt, bounce, squash/stretch, parts, or state change; a UI element may act through UI-native motion.
   - Motion planning should define semantic phases such as start, reaction, development, peak, recovery, and end.
   - Motion planning should not lock exact poses unless the user explicitly requested them.
   - If the user does not specify poses, allow the image model to freely interpret poses inside the planned structure.
   - Multi-segment animations need transition locks: the next segment should begin from the previous segment's final pose.

4. **Technical Delivery**
   - Match strictness to asset type.
   - For `sticker` / emote assets, prioritize emotional expression and visual appeal; strict foot baseline, exact body center, and perfect frame continuity are optional unless the user wants a playable animation. Identity still matters when the sticker belongs to a confirmed subject.
   - For animated icon/object assets, use the object visual center, `center_cross`, and a stable bounding box. Use a contact baseline only when the object sits on a surface or has an explicit contact point.
   - For simple UI icon/object sprite assets, avoid baking UI text into the sprite unless the text itself is the animated subject. Product text should usually be rendered by the UI layer.
   - For complex UI motion with multiple independent layers, fine text, particle systems, or highlight masks, recommend Lottie/code animation instead of a single flattened sprite sheet.
   - For `sprite_qc_only`, skip fresh image generation and hand off the existing sheet to `$animation-qc`.
   - For `sprite_from_existing`, use the existing sprite sheet as the source of truth; only generate derivative prompts when the user asks for a new variation.
   - For `sprite_animation`, `ui_state_motion`, and `full_sequence_animation`, use strict animation asset rules.
   - Output as a sprite sheet when the target is playable animation, UI motion, or a full sequence.
   - Use a regular grid. If the user gives an exact frame count or layout, follow it.
   - Custom frame counts and layouts are allowed. If the user asks for 10 frames, 16 frames, `4x3`, `5x2`, or multiple sheets, follow that request.
   - If unspecified, infer frame count and layout from the requested action, use case, length intent, and playback. Do not expose frame math to the user unless it helps the decision.
   - For row-strip generation, a single horizontal row is allowed and often preferable when using a layout guide; still keep every frame slot the same size.
   - Every cell must be a `1:1` square with the same size.
   - Transparent background or clean removable green screen. Prefer true transparency for UI icons/badges and any asset whose palette could collide with green-screen keying.
   - No text, watermark, infographic, or complex background.
   - Keep the same character, face, proportions, scale, outfit/accessories, hair/fur/color setup, and visual style across all frames.
   - Do not suddenly add or remove clothes, accessories, props, or major visual elements during the animation unless the action explicitly introduces them.
   - Keep the appropriate anchor policy stable: `center_cross` for floating icons/objects, center plus contact baseline for grounded subjects, rotation center for spinning subjects, or path anchor for intentional travel.
   - For grounded actions such as dancing, bending, nodding, swaying, stretching, or squash/stretch without an explicit jump, keep the foot/contact point on one horizontal baseline. The body may bend, squash, stretch, or rebound above that baseline, but the whole character must not float or sink.
   - If the action includes a real jump, fall, slide, or travel, state that explicitly and make takeoff, airborne/travel, and landing/contact frames visually clear. Start and end contact frames should return to the same baseline unless the user asked for travel.
   - Place the character as close as possible to the visual center area of each cell.
   - Keep whitespace around the character as consistent as possible in every cell.
   - Do not let the whole character drift left/right, drift up/down, or change size.
   - If the action is not a jump, fall, or travel action, do not let the whole character leave the ground.
   - Change only the parts that need to move; keep the torso/main body/root position as stable as possible.
   - Do not recompose each frame for beauty. Do not change camera angle, perspective, background, or viewpoint between frames.
   - Props and effects must not push the character off-center.
   - Adjacent frames must read as continuous animation frames, not separate illustrations or disconnected poses.

Read `references/generation-logic.md` when writing a full prompt.

## Workflow

1. Identify whether the user wants a single action, a short loop/expression, or a multi-segment animation.
2. Identify whether the user is defining a new reusable subject or requesting an action for an existing confirmed subject.
   - Existing sprite sheet only: classify as `sprite_qc_only` or `sprite_from_existing`, then skip base-frame generation.
   - New reusable subject: generate or define a base frame first, then ask for confirmation.
   - Existing confirmed subject: reuse its `canonical_base` and `anchor_profile` unless the user switches, clears, or opts out.
   - Existing reference image but no confirmed base: ask how closely to follow the reference in plain language, then create a clean canonical base before action generation.
3. Ask only for missing variables that materially change the result. Infer safe defaults when possible.
   - If frame count/layout is missing, infer it from the action, intended use, playback, and length words instead of asking the user to choose frame math by default.
   - If the user is vague but wants a quick result, choose a compact frame count/layout suitable for the action and say it in plain language.
   - If the user provides an exact or custom frame count/layout, follow that instead.
   - If the user does not specify exact poses, design an internal motion structure instead of forcing the user to describe every pose.
   - If asset type is `sticker`, do not force strict animation constraints unless playback is required.
4. Write a layered generation brief:
   - input recognition,
   - subject lock,
   - run setup,
   - action structure,
   - output rules.
5. Before generating playable sprites, create or state the `sprite_geometry_contract`; create a layout guide when the tool can use one, but also require the generated source to be a machine-cuttable raw sprite sheet. If no guide can be attached, clearly treat the run as prompt-constrained and make the visible raw sprite template requirement stricter.
6. If the user asks to generate immediately, use the available image-generation tool with the brief, confirmed subject, layout guide/contract when available, and explicit raw sheet rules such as chroma green background, visible cell dividers, one pose per square cell, and no frame overlap.
7. If identity consistency matters, ensure the generation path is grounded with the real reference image and/or approved canonical base before generating. If grounding is unavailable for `2_close_copy`, stop and explain instead of prompt-only generation.
8. After generation, run the basic sprite gate before QC: exact geometry, divisibility by cols/rows, square cells, expected frame count, background, visible subject per cell, crop, declared sequence/cell mapping, and sequence validity. If the sequence itself is not acceptable, regenerate instead of trying to fix it with QC.
9. If the basic sprite gate fails, do not hand the sheet to `$animation-qc`. Decide `recompose` only when frame extraction is unambiguous and deterministic; otherwise regenerate with a stronger guide or split the request into smaller sheets.
10. If the generated image contains multiple requested sequences, split it into independent per-sequence assets after the basic gates pass. Do not use the combined sheet as the normal final checkpoint.
11. Hand off to `$animation-qc` for frame cutting, audit, normalization, timing review, and transparent export.
12. Treat QC `audit/report/delivery_gate` as the asset gate, not as optional explanation. If the gate blocks delivery, regenerate, drop bad frames, or run a suitable per-frame normalization before presenting the asset as usable.
13. Only present the GIF/transparent GIF as an acceptable result after geometry, sequence splitting when needed, QC gate, and timing review are reasonable.
14. If the user already provided a sprite sheet and only wants QC/preview/timing/audit, call `$animation-qc` directly instead of generating a new image.

## Stage Navigation

After every generated or processed artifact, tell the user exactly where they are in the workflow. Do not leave the user with only an image and no next step.

This is a hard handoff rule:

- After a base-frame image, guide the user to confirm or revise the character before any action generation.
- After an action sprite sheet image, run the basic gates and guide the asset to `$animation-qc` before treating it as usable.
- After a multi-sequence batch image, split it into per-sequence assets before the normal user-facing checkpoint. The user should see the per-sequence GIF previews as the main result, not a raw combined sheet to inspect.
- When handing off a confirmed character to `$animation-qc`, include or create that character's `anchor_profile` and tell QC to pass it via `--anchor-profile`. This is required for non-default characters so QC aligns the character's own body/main object instead of guessing from generic color rules.
- After QC output, read the delivery gate first. If it passes, guide the user to approve, adjust timing, regenerate, drop frames, or proceed to integration. If it does not pass, say the art may be cute but the animation asset is not stable enough yet.
- If the image-generation tool returns an image without allowing text in the same turn, resume this stage navigation in the very next assistant message. The user should never have to ask "what next?".

Use this shape:

```text
当前步骤：
当前结果：
下一步：
需要你确认：
```

Default to a user-facing handoff, not an engineering log.

- Keep the default handoff short and human-readable.
- Do not mention `anchor_profile`, JSON files, script flags, or exact paths unless the user is debugging, asks why, or the result is warning/fail.
- Translate technical checks into plain language: "会不会飘", "会不会抖", "节奏顺不顺", "边缘干不干净".
- Give one clear next action first. Put alternatives after the user has seen the GIF or asks for options.
- If a technical handoff is needed, add it as a short "技术备注", not as the main message.

For a character base frame:

- Current step: `角色基准造型`.
- Current result: describe the generated subject in plain language.
- If a checkerboard image is shown, explicitly say it is only for reviewing edges/position. The transparent PNG is the actual base for later animation.
- Ask the user to confirm shape, style, face, proportions, and whether it feels like the character they want.
- If the character is accepted and unnamed, optionally ask for a name so later actions can reuse it naturally.
- If this is likely to become a long-term IP or needs many future actions, mention whether a three-view sheet would improve consistency before generating many sprites.
- If rejected, ask for concrete direction such as "more handsome", "simpler", "remove limbs", "change color", or "closer to reference".
- If accepted, mark `current_character.confirmed = true` conceptually and proceed to action planning.

Plain-language example:

```text
当前步骤：角色基准造型
当前结果：我先把这个角色整理成透明基准图了。checker 只是方便看边缘和位置，后续动作会用透明 PNG。
下一步：如果你觉得这个角色可以，我再帮它做动作图。
需要你确认：保留这一版，还是想改得更酷/更软/更接近参考图？
```

For an existing reference image that needs base preparation:

- Current step: `角色/主体基准整理`.
- Current result: explain that the provided image is a reference sheet/decorated image/style reference, not yet an animation base.
- Ask only the plain-language reference-use question if fidelity is unclear.
- If the user chooses "尽量贴近原图", tell them the next generation must use the visible/attached reference image, not just a text prompt.

Plain-language example:

```text
当前步骤：角色基准整理
当前结果：这张是参考图，还不是干净动作基准。我们先决定它要被参考到什么程度。
下一步：你选一种参考方式后，我再生成干净基准图。
需要你确认：只借风格 / 保留识别点 / 尽量贴近原图。
```

For an action sprite sheet:

- Current step: `动作雪碧图`.
- Current result: state that the action frames are generated, but not yet ready for use.
- Next step: hand off to `$animation-qc`.
- Tell the user the next step is to make a GIF preview and check whether it drifts, jitters, or feels broken.
- Do not imply the sprite is ready until QC has produced at least a preview GIF and a stability check.
- If the action is grounded, say the check will also make sure the character does not float or slide.

Plain-language example:

```text
当前步骤：动作图已生成
当前结果：现在它还只是一张雪碧图，先不能直接当成最终动图用。
下一步：我会把它做成 GIF 预览，并检查会不会飘、会不会抖、节奏顺不顺。
需要你确认：你先看 GIF 的动作感觉对不对。
```

Technical note only when needed:

```text
技术备注：这一步会带上当前角色的 anchor_profile 进入 animation-qc。
```

For a multi-segment sequence:

- Current step: `完整流程动画`.
- Current result: list each segment and whether shared visual setup is locked.
- Next step: generate/process each segment, then preview the stitched sequence.
- Ask the user to confirm whether the segment order and shared setup feel right before continuing if they materially affect the story.

For an existing sprite sheet:

- Current step: `已有雪碧图处理`.
- Current result: classify as `sprite_qc_only` or `sprite_from_existing`.
- Next step: use `$animation-qc`, not fresh generation, unless the user explicitly asks for a new variation.

After QC output:

- Current step: `动图检查完成`.
- Current result: state whether it "可以用", "基本可以但要看一下", or "建议重做/剔帧".
- Next step: show the preview GIF first; mention audit/report only if needed.
- Ask the user to choose one useful action: accept, adjust speed, regenerate, drop frames, or proceed to integration.

Plain-language example:

```text
当前步骤：动图检查完成
当前结果：这版基本可以，但有一点点需要你看 GIF 判断。
下一步：你先看动作感觉。如果觉得顺，我们就用这一版；如果觉得怪，我再帮你重生或调节奏。
需要你确认：动作感觉对吗？
```

## Minimal Prompt Shape

```text
Generate an animation sprite sheet for [subject].

Input recognition:
- Asset type: [sticker / sprite_animation / ui_state_motion / full_sequence_animation / character_base_frame / sprite_qc_only / sprite_from_existing]
- Subject type: [character / animal / object / ui_element / abstract]
- Subject:
- Action:
- Scene/use case:
- Internal motion interpretation: [infer from the user's action; do not ask the user by default]
- Reference intent: [style_reference / exact_character_reference / mixed_reference / unknown]
- Reference strength: [0_style_only / 1_recognizable_adaptation / 2_close_copy / unknown]
- Generation mode: [prompt_only / grounded_reference / image_edit]
- Playback: [once / loop]
- Length intent:
- Frame count/layout: [inferred from action/use unless user specified]
- Rhythm intent: [reaction_once / reaction_loop / idle_loop / physical_once / physical_loop / process_loop / story_sequence]
- Existing sprite source, if any:
- Input images:
  - reference image(s), if any:
  - canonical_base, if confirmed:
  - layout guide, if available:
- Sprite geometry contract:
  - cols:
  - rows:
  - frame_count:
  - target_canvas_px:
  - target_cell_px:
  - cell_or_sequence_map:
  - valid_cells:
  - empty_cells:
  - anchor_policy:

Subject lock:
- [immutable identity]
- If reference_intent is style_reference: include `reference_style_profile` and apply it to the new subject.
- If reference_intent is exact_character_reference: include `exact_character_profile` and preserve the provided character/object instead of redesigning.
- If the user wants to "尽量贴近原图" (`reference_strength: 2_close_copy` internally), the prompt must be grounded by real input images. Do not use text-only path descriptions as the reference.
- Do not change [core features].
- If using a confirmed current subject, keep the confirmed canonical-base proportions, face/shape, colors, style, and signature details.
- If creating a new reusable subject, first create a neutral centered base frame for user confirmation.
- For long-term reusable subjects, complex characters, or characters that need many actions/turns, consider a three-view base sheet before action generation.
- If using an existing sprite sheet, do not recreate the character from scratch; keep the existing sprite as the source of truth.

Run setup:
- Scene/use case:
- Mood:
- Style/theme:
- Props/effects:
- Forbidden elements:

Action structure:
- [single action or segment list]
- Describe the rhythm intent as a broad progression, not a frame-by-frame script.
- Define motion phases, not rigid poses: start, reaction/preparation, development, peak/emphasis, recovery, end.
- Keep performance open: describe the desired feeling and allowed moving parts for this subject type, but do not hard-code exact gestures unless the user asked.
- For emotional/reaction/sticker actions, make it a readable mini performance rather than face-only. For characters this can involve posture, head, shoulders, hands, hair, and clothing; for objects/icons this can involve tilt, bounce, squash/stretch, parts, shine, or state change.
- If poses are not user-specified, let the image generation interpret concrete poses freely inside the motion phases.
- Adjacent frames should read as continuous motion.
- Final frame should be holdable if the UI needs to pause.
- If playback is loop, ensure the final frame can naturally return to the first frame instead of using a long final hold.

Output rules:
- For sticker/emote assets, prioritize expression and readability; strict animation continuity is optional unless requested.
- For animated icon/object assets, keep the object visual center, `center_cross`, and bounding box stable; only use a contact baseline if the object has a clear grounded contact point.
- For sprite_qc_only, skip generation and use animation-qc directly.
- For sprite_from_existing, base any derivative work on the existing sprite sheet.
- For playable sprite/UI/full-sequence animation, follow strict animation asset rules.
- Sprite sheet, not a single illustration, when the asset is meant to play as animation.
- Regular grid. Follow the user's exact frame count/layout if given.
- Follow the `sprite_geometry_contract`. If it says `4x4 / 1024x1024 / 256x256 cells`, the sheet should be exactly that target when the generator can honor dimensions. If the generator returns a different size, the result must still be rejected or deterministically recomposed before QC.
- If a layout guide is attached, use it only for frame count, spacing, centering, and safe padding. Do not reproduce guide labels, center marks, baseline marks, or guide colors.
- For playable raw sprite outputs, visible cell dividers are allowed and often preferred. They are not guide leakage when they are clean production dividers used for machine cutting.
- For chroma-key raw sheets, use pure `#00FF00` in every cell and thin clean divider lines. For transparent raw sheets, cell boundaries must still be unambiguous through exact canvas geometry and non-overlapping poses.
- Whole-sheet aspect ratio must match the grid. For example, `3x2` means the final sheet is `3:2`, not a square canvas; `4x2` means `2:1`; `4x3` means `4:3`.
- Custom frame counts and layouts are valid when requested, such as 10 frames, 16 frames, 4x3, 5x2, or multiple connected sheets.
- If unspecified, infer frame count and layout from the requested action, use case, length intent, and playback. Do not expose frame math to the user unless it helps.
- Same-size cells; every cell must be 1:1 square.
- Transparent background or clean #00FF00 background.
- Strictly keep the same character, same face, same proportions, same size, same outfit/accessory/hair/fur/color setup, and same visual style.
- Do not suddenly add or remove clothes, accessories, props, or major visual elements.
- Keep the character's main-body center stable in every cell.
- Keep the foot/contact baseline stable in every cell.
- For grounded actions, keep the foot/contact point on one horizontal baseline across all frames; bending, squash/stretch, dancing, and rebound should happen above that stable contact line.
- Only allow baseline changes when the action explicitly includes jumping, falling, sliding, or traveling, and make those frames visually intentional.
- Keep whitespace around the character as consistent as possible.
- Keep the character close to the visual center area of each cell.
- Do not let the character drift left/right, drift up/down, or change size.
- If the action is not a jump/fall/travel action, do not let the whole character leave the ground.
- Move only the parts needed for the action; keep the torso/main body/root position stable.
- Do not recompose each frame. Do not change camera angle, viewpoint, perspective, or background.
- Adjacent frames must be small, continuous changes, not separate illustrations.
- No text, watermark, infographic, or complex background.
```
