---
name: animation-qc
description: "动画底层质检。Use when checking or preparing sprite/frame animation assets before they are used in a product UI. Focuses only on technical motion quality: frame grid, green-screen removal, transparency, body-center alignment, foot-baseline stability, jitter, floating, ghosting, and playback smoothness. Does not judge scene fit, copy, trigger logic, or generation ideas."
---

# 动画底层质检

This skill is the required technical gate before any product motion asset appears in the UI.

It answers one question: **can this sprite land in the page without drifting, floating, jittering, ghosting, or looking broken?**

It does **not** decide whether the action is suitable for a scene. Scene choice belongs to a product/creative workflow such as `$animation-sprite-workshop`.

Use this skill directly when `$animation-sprite-workshop` classifies the request as:

- `sprite_qc_only`: an existing sprite sheet only needs QC, alignment, GIF preview, timing, audit, and report.
- `sprite_from_existing`: an existing sprite sheet is the source for continued processing, frame selection, timing adjustment, or derivative preparation.

These cases should not restart character/base-frame generation unless the user explicitly asks for a new character or fresh redesign.

## Hard Gate

- Every motion asset used in a product UI should pass this QC first.
- Product code should reference processed output assets, normally named `*-aligned.png` or `*-aligned-transparent.png`.
- Never wire raw generated sprite sheets directly into the UI.
- Final animation exports must use real transparency after background cleanup. QC preview or audit backgrounds may be used for inspection, but must not be treated as final transparent animation outputs.
- Show the final transparent GIF when presenting an accepted asset. Use `*-preview.gif` only as a review artifact and label it as such.
- Before accepting a transparent GIF, check the outer edge for accidental black lines, white dividers, green spill, or other source-grid residue. If an edge artifact exists, clean/re-export before presenting it as final.
- If a sprite fails body-center or foot-baseline checks, fix/process/regenerate it before product integration.

## QC Checklist

Check these before product use:

- Grid is correct: default/recommended formats are often `3x2` or `4x2`, but they are not hard limits. Any regular grid can be used if every cell is the same size and preferably square. If auto-detection fails, ask for `cols / rows`.
- Background cleanup is correct: no green screen, white edge, halo, or residue.
- Final animation output background is truly transparent. Checkerboards or colored backgrounds are audit/debug views only, not final deliverables.
- Body center is stable: judge the character's main body, not props or effect marks.
- Foot baseline is stable: standing frames should not float or sink.
- No whole-character horizontal sliding unless the action explicitly requires travel.
- No sudden body scale/proportion changes.
- No accidental crop of head/top details, feet, hands, props, or effects.
- Frame order reads as one action, not unrelated expressions.
- Playback does not feel too fast, too slow, or ghosty.
- Final frame is holdable if the UI needs to pause on it.

## Pre-Generation Guardrails

If the user has not generated an image yet, this skill cannot run technical QC. In that case, provide only bottom-layer delivery constraints:

- Use a regular sprite grid. `3x2` and `4x2` are recommended defaults, not hard limits.
- Keep every cell the same size; square cells are preferred.
- Keep character scale, body center, and foot baseline stable across frames.
- Keep background transparent or a clean removable green screen.
- For UI icons, badges, and glossy objects, prefer true transparency. Use green screen only when the asset colors do not contain green, cyan-green, yellow-green, mint, or green-tinted glow.
- Keep props/effects outside the character anchor logic; they must not push the body off-center.
- Avoid unrelated poses inside one action; adjacent frames should read as one continuous motion.

Do not decide scene concept, action meaning, copy, or trigger logic here.

If the user has already provided a sprite sheet, this is not a pre-generation case. Treat it as `sprite_qc_only` or `sprite_from_existing` and proceed with QC/processing guidance.

## Anchor Rules

Every sequence needs a stable anchor policy. A foot baseline is only one kind of anchor policy.

Use subject anchors, not raw canvas anchors:

- Primary center: character main-body center.
- Primary vertical reference: either a center Y line, a foot/contact baseline, a rotation center, or a path anchor depending on the subject and motion.
- Secondary stability cue: any stable top/body landmark relationship.
- Props, hands, stars, hearts, smoke puffs, flags, umbrellas, speech marks, confetti, and tools must not affect the body center.

Audit guide types:

- `center_cross`: for floating UI icons, badges, stickers, and objects without a contact surface. Use center X plus center Y; the subject should stay visually centered unless the action explicitly travels.
- `contact_baseline`: for standing characters or objects sitting on a surface. Use body/object center X plus foot/bottom contact line.
- `rotation_center`: for spinning objects. Use the intended rotation center; do not judge the lower edge as a baseline.
- `path_anchor`: for travel, slide, entrance, or exit motion. Do not force the subject to stay centered; judge whether the motion path is intentional and stable.

When `$animation-sprite-workshop` has confirmed a character, prefer that character's `anchor_profile` over generic detection:

- Anchor profiles are per character, not global.
- A new character should have a new anchor profile.
- Returning to a previous character should restore that character's previous anchor profile.
- One-off characters may use a temporary anchor profile without overwriting the current character.
- Default character anchor is the body/main object; only ask the user when the body/core object is ambiguous.
- Ignore temporary clothing edges, props, motion lines, sparkles, bubbles, and small moving hands/feet when judging center.
- For object/icon assets, use the object visual center unless an explicit contact line exists.
- For UI object/icon reward animations that intentionally pop, scale, or reveal from small to large, set `baseline_anchor` to `none` and allow intentional scale change. Judge the `center_cross`, crop, edge cleanliness, and playback readability instead of foot baseline.
- For soft-body, jelly, elastic, or bendable characters, allow shape deformation but keep the contact line stable unless jump/fall/slide/float/travel is explicit.

When a character profile is available, pass it to the QC script with `--anchor-profile /path/to/profile.json`.
Without an anchor profile, the script falls back to generic foreground detection and may be less reliable when props, motion lines, or effects are visually connected to the subject.

Minimal anchor profile shape:

```json
{
  "name": "character name",
  "subject_type": "character",
  "anchor_profile": {
    "center_anchor": "body_visual_center",
    "baseline_anchor": "contact_baseline",
    "ignore_for_center": ["ears", "tail", "small hand motion", "props", "motion lines"],
    "baseline_rule": "grounded frames keep the same contact line unless jump/fall/slide/float/travel is explicit"
  }
}
```

Minimal UI object/icon profile:

```json
{
  "name": "ui badge or icon name",
  "subject_type": "ui_element",
  "anchor_profile": {
    "center_anchor": "object_visual_center",
    "baseline_anchor": "none",
    "ignore_for_center": ["sparkles", "coins", "particles", "highlight sweep"],
    "baseline_rule": "No foot/contact baseline. Judge center_cross, crop, and edge cleanliness instead."
  }
}
```

Target after processing:

- Foot baseline error: ideal `0-2px`, warning above `2px`, fail above `6px`.
- Body center error: ideal `0-4px`, warning above `4px`, fail above `12px`.
- Page-rendered visual drift: should feel stable at product size.

If a frame needs a very different shift from neighboring frames, inspect the GIF and audit sheet. Large shifts can mean the original drawing changed stance or scale, not just position.

## Delivery Gate

Audit and report are not optional attachments. They decide whether the asset is ready to show as a usable result.

- Generated art may be expressive, but delivery must be mechanical and stable.
- Always cut frames, inspect the audit/report, and normalize when the anchor is clear before treating an animation as usable.
- If the audit shows large center drift, large foot/contact drift, crop risk, or big unexplained shifts, do not present the GIF as a finished result.
- If per-frame normalization fixes the drift within thresholds, the asset can continue as a warning/pass result.
- If normalization would require artistic choices, redrawing, changing poses, or guessing the intended contact path, regenerate or request a more suitable source.
- For standing, dancing, expression, and sticker performance actions, center/body anchor and contact baseline are the default gate.
- For rolling, spinning, lying, crawling, floating, or object animations, use a matching anchor policy such as subject bbox center, rotation center, contact surface, or object visual center instead of forcing a foot baseline.
- For UI object/icon pop-in animations, scale change can be intended. It should not block delivery by itself when the visual center is stable, the subject remains crisp, and there is no crop or edge residue.
- If keying removes internal colors, creates holes, causes color loss, or leaves green halos, block delivery and regenerate with true transparency or a non-conflicting processing background.
- The user should see the final transparent GIF only after this gate is satisfied or clearly labeled as an experiment/failure.

## Positioning Rules

By default, QC should fix mechanical placement drift when the anchor is reliable.

- Default alignment mode is `--align-mode auto`.
- `auto`: inspect masks and proposed shifts first; when anchor confidence is high, apply the proposed alignment and then report any review risks.
- `audit_only`: cut frames, remove green, output GIF/audit/report/timing, but never move frames.
- `light_align`: allow only small clamped corrections.
- `force_align`: apply full anchor shifts only when the user explicitly asks.
- Large proposed shifts are warnings for review, not a reason to leave an otherwise machine-cuttable raw sprite unaligned.
- For clean raw sprite sheets with one pose per cell, clear foreground, and a valid anchor profile, offset frames should be aligned by default. The user should not have to ask for `force_align` just because a generated frame is 20-40px off.
- If a proposed shift exceeds `20px` or `5%` of the cell size, `auto` should still align when confidence is high, then mark the result `needs_review` if crop, scale, or pose-continuity risk remains.
- If mask confidence is low, background is not pure green, or the foreground mask likely includes background residue, `auto` should skip alignment and warn.
- Do not let QC "recompose" a frame. Alignment is a small correction, not a full redraw or layout reset.
- For UI object/icon reward animations with `baseline_anchor: none`, pass the UI object anchor profile and use `--allow-scale-change` when the scale change is part of the intended action.

When alignment is applied, processed frames should be **centered inside each square cell** after they are aligned.

- `--position-mode center` places the detected anchor at the center target.
- In a `512 x 512` cell, the default body-center target is `x = 256`.
- The foot baseline is preserved from the first/base frame unless `--target-foot` is provided.
- When `baseline_anchor` is `none`, vertical foot/contact checks are not the gate; visual-center stability and crop are the gate.
- Use `--position-mode source` only when you intentionally want to preserve the first/base frame's original placement.
- Use `--target-cx` and `--target-foot` when a product or engine has an explicit anchor standard.

This means QC should solve both problems:

1. Every frame stays stable relative to the other frames.
2. The finished sprite is not accidentally stuck to the left, right, top, or bottom of its cell.

For soft-body, squash/stretch, jelly, elastic, dancing, or jumping characters, scale and outline changes may be part of the action. Treat width/height changes as warnings first, not automatic failure, unless the character is clearly cropped, broken, or replaced by a different drawing.

## Composition Audit

Keep frame-to-frame stability separate from in-cell visual composition.

Frame-to-frame stability checks whether frames drift relative to each other:

- body/contact anchor range,
- foot/contact baseline range,
- proposed per-frame shifts,
- jitter risk,
- scale or pose discontinuity.

In-cell visual composition checks whether the subject sits comfortably inside each square cell:

- overall subject center relative to the cell center,
- top/bottom/left/right padding balance,
- subject size relative to the cell,
- possible edge crop.

P0 behavior:

- Report composition findings only.
- Do not automatically apply global recenter.
- Use `suggested_position_strategy` to recommend the next step.
- Keep existing `auto`, `audit_only`, `light_align`, and `force_align` frame-stability behavior unchanged.

Composition warnings may include:

- `overall_subject_low`
- `overall_subject_high`
- `overall_subject_left`
- `overall_subject_right`
- `unbalanced_padding`
- `subject_too_small`
- `subject_too_large`
- `possible_crop_top`
- `possible_crop_bottom`
- `possible_crop_side`

Suggested position strategies:

- `none`: composition looks acceptable.
- `audit_only`: only inspect; do not move.
- `global_recenter_suggested`: the group appears consistently offset; if the user approves later, move every frame by the same shift.
- `manual_review`: crop, scale, or uncertainty needs human review.

Important: visual centering is not the same for every asset. Standing characters can sit lower because foot/contact baseline matters. Icons and objects usually prefer visual center. Soft-body, sticker, and expressive assets should be treated cautiously.

Important: QC can detect that a flattened sprite is technically unstable, dirty, or too low-resolution, but it should not force complex UI ceremonies into sprite sheets. If the asset needs separate text, particles, glow masks, highlight sweeps, and easing curves, recommend a layered Lottie/code workflow after reporting the technical issue.

## Preview Rhythm

GIF preview is only a review artifact, but it should still feel like animation:

- Preview backgrounds are allowed for QC readability when clearly treated as previews or audits.
- The final exported animation GIF must preserve transparency; do not bake in a checkerboard, grid, white box, beige card, or fake transparent background for the final output.
- For `once` playback, exported GIFs should not loop forever by default. Use a finite loop count or product timing playback so the final hold does not snap immediately back to frame 1.
- If a generated chroma-key sheet has textured/non-pure green or anti-aliased edges, remove green spill around the foreground edge before exporting the transparent GIF.
- If the source sheet uses visible cell dividers, remove any divider residue attached to frame borders. A one-frame black/white line on the left edge is an export bug, not acceptable final output.
- Use this cleanup order for divider/grid sources: `split cell -> remove green -> clear original cell border -> remove near-edge divider lines -> align -> clear border again -> scan near-edge divider lines -> export gif`.
- Final exported frames should clear a small transparent safety border on all four sides, normally `3-4px`, before writing the transparent GIF. If clearing this border would cut the subject, the source composition is too tight and should be regenerated or recomposed with more padding.
- Edge checks must include near-edge long-line residue, not only the outermost pixels. Alignment can shift a source grid line inward, for example from `x=0` to `x=14`; this is still a divider-line artifact and must be removed before export.
- Reports should split edge results into `outer_border_clean`, `near_edge_long_line_clean`, `transparent_index_ok`, and `gif_background_index_ok`. Do not collapse these into one vague `edge_artifacts: pass`, because each catches a different failure mode.
- For transparent GIF export, the GIF background index must be the same as the transparent index and frame optimization should stay conservative. If edge pixels scan clean but a viewer still flashes black/white/green lines during playback, suspect GIF disposal/background-index behavior and re-export with a transparent background index before blaming the art.
- Do not preview every frame at one identical fast speed by default.
- Give the first frame a small read time.
- Let transition frames move faster.
- Hold key/near-final poses slightly longer.
- Hold the final frame long enough to judge whether it is usable as a resting pose.

`process_sprite.py` runs a frame-difference timing review by default and writes the exact timing to `preview_durations` in the report.
The timing reviewer looks at the real processed frames, then gives large visual changes more read time, lets small transition frames pass faster, and handles `once` / `loop` differently.
Use `--durations` when a specific action needs hand-authored timing.

## Timing Suggestions

Timing should not interrupt the user every time.

Default behavior:

- Use `timing_review` automatically and output the final preview/timing assets.
- When no custom `--durations` are provided, `timing_review` is the default selected timing.
- Do not force the user to choose between timing versions when the QC result is clean and the preview feels acceptable.
- After a GIF exists, describe timing in user-facing feeling words before showing technical durations. The user should choose "更自然", "更慢一点", "更轻快", "最后停久一点", or "循环更顺", not milliseconds.
- For character performance, dance, rolling, and other readable actions, avoid a default that feels like short UI feedback. If it feels "鬼畜", slow the default and offer alternatives.
- After a GIF exists, always provide one short AI rhythm opinion before asking the user to accept it. The opinion should say where the action reads too fast/too slow, which frame or phase needs a hold, and which timing version to try next.
- Do not only say "timing is adjustable". Give a concrete recommendation such as "前 3 帧太快，摘下来的第 4 帧应该多停一下，最后抱住头套再停久一点".
- For cute, silly, blank-stare, shy, sleepy, healing, or pet companion actions, default to a much slower readable option when the generated GIF feels like a quick UI tap feedback. A six-frame character performance often needs `3.5s-5s` total playback to avoid feeling like it flashes by.
- If slowing a six-frame GIF still feels steppy, say that this is a frame-count issue: timing can make it readable, but smoother motion needs more in-between frames, usually `8-12` frames for a small performance.

Only present timing choices to the user when:

- the user asks for timing adjustment,
- QC status is `warning` or `fail`,
- the system detects that rhythm may affect perceived quality,
- the preview feels too fast, too slow, too mechanical, ghosty, or abrupt.

When timing choices are shown, include `use_for` so the user understands each version:

```json
{
  "timing_suggestions": {
    "recommended": {
      "name": "自然版",
      "use_for": "默认 UI 动效",
      "durations_ms": [240, 140, 160, 260, 160, 900],
      "reason": "起始稍停，关键姿势稍停，结束长停"
    },
    "lively": {
      "name": "活泼版",
      "use_for": "轻快反馈 / 表情包",
      "durations_ms": [180, 100, 120, 180, 120, 520],
      "reason": "节奏更快，反馈更轻"
    },
    "soft": {
      "name": "治愈版",
      "use_for": "治愈陪伴 / 情绪类动作",
      "durations_ms": [320, 180, 220, 360, 220, 1100],
      "reason": "停顿更长，观感更柔和"
    },
    "slow_cute": {
      "name": "慢萌版",
      "use_for": "呆萌表演 / 小动物动作",
      "durations_ms": [520, 360, 460, 680, 460, 1500],
      "reason": "每个姿势都有读秒，中段变化和最后笑点都留住"
    }
  }
}
```

For `loop` playback, avoid a long final hold unless explicitly requested. Timing should make the last frame return naturally to the first frame.

For `once` playback, the final frame can hold longer if it is a comfortable resting pose.

After-GIF rhythm opinion shape:

```text
节奏意见：
- 现在读得出来/太快/太慢/有点机械。
- 哪一段需要停：起手、关键变化、峰值动作、最后定格。
- 我建议下一版先试：[自然版/慢萌版/轻快版]。
```

This opinion should be based on the actual generated GIF and timing review, not on the prompt alone.

## Standard Workflow

1. Run `scripts/process_sprite.py` on the sprite sheet.
2. Read the JSON report and `delivery_gate` first.
3. Inspect the audit/contact sheet with center and baseline guides when the gate is warning/blocked or when motion feels unstable.
4. Inspect the generated GIF after the gate has decided whether it is a usable result, a warning result, or an experiment.
   - If `warnings` reports large source drift or large correction shifts, do not treat the asset as automatically approved. Inspect the GIF and audit sheet for pose discontinuity.
5. Decide QC status:
   - `pass`: stable enough for use.
   - `warning`: technically processable, but inspect timing, continuity, scale, or pose jump before use.
   - `fail`: regenerate, drop frames, or manually fix before use.
6. Decide action:
   - `pass`: use the aligned transparent output.
   - `drop_frames`: remove bad frames and reprocess.
   - `manual_adjust`: anchor logic worked but visual center still needs taste correction.
   - `regenerate`: stance, scale, crop, or continuity is not recoverable.
7. If timing is clean, use the automatic `timing_review` result by default. If status is warning/fail or the user asks, show timing suggestions.
   - After showing the GIF, include the rhythm opinion from `*-rhythm-advice.json` or summarize it in the same shape.
8. Only after the delivery gate passes, copy the aligned output into product assets and wire it.
9. Run `scripts/audit_product_usage.py` after wiring to catch raw sprite references.

## Result Navigation

After QC completes, always tell the user what happened and what to do next. Do not only show files.

Default to user-facing language. Do not lead with JSON, paths, `anchor_profile`, exact shift numbers, or script flags unless the user is debugging, asks why, or the result needs technical explanation.

Use this shape:

```text
当前步骤：动画 QC
当前结果：
先看：
下一步：
需要你确认：
```

For `pass`:

- Show the GIF preview first.
- Say the asset can be used.
- Mention audit/report only if the user wants details.

Plain-language example:

```text
当前步骤：动图检查完成
当前结果：这版可以用，动作没有明显飘或抖。
先看：我先给你 GIF。
下一步：如果你觉得动作感觉对，就可以进入使用/接入。
需要你确认：用这一版吗？
```

For `warning`:

- Explain the warning in plain language.
- Say whether frames were shifted or raw layout was kept.
- Show the GIF first, then audit/report when needed.
- Ask the user to accept, adjust timing, re-run with another mode, drop frames, or regenerate.

Plain-language example:

```text
当前步骤：动图检查完成
当前结果：这版基本能看，但有一点点偏移/节奏需要你判断。
先看：先看 GIF，动作感觉比数字更重要。
下一步：如果你觉得顺，我们保留；如果觉得怪，我建议重生或剔掉问题帧。
需要你确认：动作感觉对吗？
```

For `fail`:

- Do not pretend QC fixed it.
- Explain the failing reason: drift, crop, scale/proportion, bad continuity, or unreliable mask.
- Recommend regenerate, drop frames, manual repair, or a stricter generation prompt.

Plain-language example:

```text
当前步骤：动图检查完成
当前结果：这版不建议直接用，动作里有明显跳动或位置问题。
先看：我可以给你看 GIF 和审计图说明问题。
下一步：更稳的做法是重生一版，或者删掉问题帧再检查。
需要你确认：重生，还是先看问题在哪？
```

Add a short technical note only when useful:

```text
技术备注：这里是因为中心/接触线变化过大，不是 timing 能解决的问题。
```

For composition warnings:

- Explain that composition is separate from frame stability.
- Say whether the asset is frame-stable but visually low/high/left/right in the cell.
- Do not claim global recenter was applied unless it was explicitly requested in a future implementation.

## Commands

Process a sprite with auto-detected grid:

```bash
python3 scripts/process_sprite.py \
  --input /path/to/source.png \
  --out /tmp/animation-qc/action-name \
  --scene qc \
  --action action-name
```

Process a sprite with explicit grid when auto-detection is uncertain:

```bash
python3 scripts/process_sprite.py \
  --input /path/to/source.png \
  --out /tmp/animation-qc/action-name \
  --scene qc \
  --action action-name \
  --cols 4 \
  --rows 2
```

Audit only, without moving frames:

```bash
python3 scripts/process_sprite.py \
  --input /path/to/source.png \
  --out /tmp/animation-qc/action-name \
  --scene qc \
  --action action-name \
  --align-mode audit_only
```

Force alignment only when the user explicitly wants full anchor correction:

```bash
python3 scripts/process_sprite.py \
  --input /path/to/source.png \
  --out /tmp/animation-qc/action-name \
  --scene qc \
  --action action-name \
  --align-mode force_align
```

QC with a character anchor profile:

```bash
python3 scripts/process_sprite.py \
  --input /path/to/source.png \
  --out /tmp/animation-qc/action-name \
  --scene qc \
  --action action-name \
  --cols 4 \
  --rows 2 \
  --align-mode auto \
  --anchor-profile /path/to/character-anchor-profile.json
```

Preview selected useful frames:

```bash
python3 scripts/process_sprite.py \
  --input /path/to/source.png \
  --out /tmp/animation-qc/action-name \
  --scene qc \
  --action action-name \
  --frames 0,1,2,4,5
```

Preview with hand-authored timing:

```bash
python3 scripts/process_sprite.py \
  --input /path/to/source.png \
  --out /tmp/animation-qc/action-name \
  --scene qc \
  --action action-name \
  --frames 0,1,2,4,5 \
  --durations 260,140,180,300,900
```

Preserve the first frame's original placement instead of centering in the cell:

```bash
python3 scripts/process_sprite.py \
  --input /path/to/source.png \
  --out /tmp/animation-qc/action-name \
  --scene qc \
  --action action-name \
  --position-mode source
```

Audit current product references:

```bash
python3 scripts/audit_product_usage.py \
  /path/to/your/product-or-demo.html
```

## Output Files

`process_sprite.py` outputs:

- `*-aligned-transparent.png`: product-safe transparent sprite sheet.
- `*-preview.gif`: effect preview for QC/review.
- `*-transparent.gif`: final transparent animation output.
- `*-audit.png`: contact sheet with body-center and foot-baseline guides.
- `*-report.json`: numeric anchor report and shifts.

Target timing outputs for the workflow:

- `*-timing.json`: selected final timing for product playback.
- `*-timing-review.json`: automatic frame-difference timing review.
- `*-timing-suggestions.json`: optional timing choices when user review is needed.

`*-report.json` should include:

- `align_mode`
- `anchor_strategy`
- `mask_confidence`
- `anchor_confidence`
- `composition`
- `delivery_gate`
- `alignment_applied`
- `whether_frames_shifted`
- `alignment_reason`
- `alignment_gate`
- `proposed_max_shift`
- `baseline_anchor` behavior through the selected anchor profile
- `allow_scale_change` behavior when used for intentional UI object/icon pop-in animations
- `recommendation`

## Relationship To Other Skills

Use this skill for technical motion QC only.

Use `$animation-sprite-workshop` when the task involves scene fit, action concept, generation prompt, or product behavior rules.

Do not send `sprite_qc_only` work back to `$animation-sprite-workshop` unless the user needs a new prompt or wants to generate a new/derived sprite sheet.
