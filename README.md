# Animation Sprite Skills

一句话：这是一套把 AI 生成的角色动作图，整理成可用透明 GIF 的 Codex skills。

我做它，是因为 AI 很容易画出“看起来像雪碧图”的东西，但真正拿去做桌宠、表情包、小游戏、产品动效时，会冒出一堆细小问题。

格子看起来是 `4x2`，实际图片比例却不对。  
角色看起来在动，切成 GIF 后每帧都在漂。  
绿色背景去掉了，边缘还有绿边。  
白色分隔线看着很细，播放时突然闪成一条线。  
透明 GIF 明明导出了，在某些预览器里还是会闪黑边。

所以这套流程没有只停在“帮我写一个生图 prompt”。它把动画资产拆成两段：先把图生成得像资产，再把图处理成资产。

![real workflow](animation-sprite-workshop/docs/images/workflow-with-subject.png)

## What This Includes

这个仓库里有两个 skill。

`animation-sprite-workshop` 负责生图前的事情。它会帮你把一个模糊想法整理成明确的 sprite 生产要求：角色基准图、动作方向、格子数量、每格尺寸、layout guide、raw sheet 规则，还有生成后必须通过的几何检查。

`animation-qc` 负责生图后的事情。它会切帧、去绿、清白线、对齐主体中心和脚底线，检查节奏，最后导出透明 GIF、audit 图和 report。

它们配合起来，大概是这个顺序：

```text
idea / reference
-> canonical base
-> sprite geometry contract
-> layout guide or raw template
-> raw sprite sheet
-> geometry gate
-> QC cleanup and alignment
-> transparent GIF
```

## The Real Problem

雪碧图最麻烦的地方，不是“有没有画出动作”。  
麻烦的是它要能被机器切开。

比如这张 raw sheet：

![seal raw sheet](animation-sprite-workshop/docs/images/seal-raw-sheet-4x2.png)

它不是一张海报，也不是一个角色摆在整张图中间。它必须满足几个很死的规则：

- `4 columns x 2 rows`
- 整张图比例是 `2:1`
- 每个 cell 都是 `1:1`
- 每个 cell 里都有一个完整主体
- 主体不能跨格
- 绿色背景和白色分隔线只是中间源，最终必须清掉

这几个规则只要错一个，后面就会很痛苦。

## Step 1: Use animation-sprite-workshop

先别急着生图。先把这个合同写清楚：

```yaml
sprite_geometry_contract:
  cols: 4
  rows: 2
  frame_count: 8
  target_canvas_px: [2048, 1024]
  target_cell_px: [512, 512]
  cell_aspect: 1:1
  whole_sheet_aspect: 4:2
  playback: loop
  background: chroma_green
  raw_sheet_format: chroma_green_with_white_dividers
  anchor_policy: body center stable, contact baseline stable
```

然后在 prompt 里明确写出来：

```text
4 columns x 2 rows.
Whole sheet aspect ratio exactly 2:1.
Every cell is exactly square.
Each frame stays fully inside its own 1:1 cell.
Use pure chroma green background and thin white dividers.
No labels, no numbers, no guide marks.
```

如果模型支持输入图，可以先给它 layout guide：

![layout guide](animation-sprite-workshop/docs/images/layout-guide-4x2.png)

如果模型经常把 layout guide 当成画面内容抄进去，就换成 raw template 思路：

![raw template](animation-sprite-workshop/docs/images/raw-template-4x2.png)

生成后不要凭眼睛说“差不多”。先跑 gate：

```bash
python3 animation-sprite-workshop/scripts/check_sprite_gate.py \
  --input /path/to/raw-sheet.png \
  --cols 4 \
  --rows 2 \
  --target-width 2048 \
  --target-height 1024 \
  --target-cell 512 \
  --allow-guide-background \
  --check-visible-grid
```

如果 bitmap 尺寸不对，它就不能直接进入 QC。  
有些图视觉上像 `4x2`，但实际是 `1774x887`。这种图只能在格子边界非常清楚时做确定性重排。不能补画，不能发明新帧。否则就重新生成。

## Step 2: Use animation-qc

过了 gate，再进入 QC。

```bash
python3 animation-qc/scripts/process_sprite.py \
  --input /path/to/raw-sheet.png \
  --out /path/to/output-dir \
  --scene qc \
  --action example-action \
  --cols 4 \
  --rows 2 \
  --playback loop \
  --anchor-profile /path/to/anchor-profile.json \
  --clear-border 4 \
  --line-clean-margin 40
```

QC 会输出一组文件：

```text
qc-example-action-aligned-transparent.png
qc-example-action-preview.gif
qc-example-action-transparent.gif
qc-example-action-audit.png
qc-example-action-report.json
qc-example-action-timing.json
qc-example-action-rhythm-advice.json
```

处理后的透明 sheet 长这样：

![seal qc aligned sheet](animation-qc/docs/images/seal-qc-aligned-sheet.png)

最终透明 GIF：

![seal final gif](animation-qc/docs/images/seal-final-transparent.gif)

## The Edge-Line Lesson

这套 skill 里有一个很具体的规则，是实际踩坑踩出来的。

一开始我只检查 GIF 最外圈几像素，结果用户还是看到了白线。后来才发现，白线不是在最外圈。它来自 raw sheet 的白色分隔线。对齐时，整帧被平移，分隔线也跟着被推到了画面内部，比如 `x=14`、`x=20` 这种位置。

所以 QC 现在不是只裁最外层边缘。它会按这个顺序处理：

```text
split cell
-> remove green
-> clear original cell border
-> remove near-edge divider lines
-> align
-> clear border again
-> scan near-edge divider lines
-> export gif
```

示意图：

![edge cleaning example](animation-qc/docs/images/qc-edge-cleaning-example.png)

report 里也不会只写一个模糊的 `edge_artifacts: pass`。现在会拆开看：

```json
{
  "edge_artifacts": {
    "outer_border_clean": true,
    "near_edge_long_line_clean": true
  },
  "gif_export": {
    "transparent_index_ok": true,
    "gif_background_index_ok": true
  }
}
```

这几个字段分别抓不同问题。少一个都不够。

## When To Regenerate

QC 不是魔法。它能修机械问题，不能修画坏的动作。

这些情况建议回到生成阶段：

- 每帧角色长得不一样。
- 动作不是连续过程，只是几张无关表情。
- 角色太大，清边会切到身体。
- cell 太小，细节糊掉。
- 道具和主体粘在一起，anchor 很难判断。
- 需要文字、粒子、光效、遮罩和复杂缓动。

这时候不要硬救。拆小批次，放大 cell，重新生成。

## Repository Layout

```text
animation-sprite-workshop/
  SKILL.md
  README.md
  agents/
  references/
  scripts/
  docs/images/

animation-qc/
  SKILL.md
  README.md
  agents/
  scripts/
  docs/images/
```

更多细节：

- [animation-sprite-workshop/README.md](animation-sprite-workshop/README.md)
- [animation-qc/README.md](animation-qc/README.md)

## What Not To Commit

同步到 GitHub 时，不要提交这些：

```text
__pycache__/
*.pyc
private project output folders
temporary generated assets that are not docs examples
```

公共文档里可以保留真实案例图。它比抽象占位图更容易说明问题。这里的海豹案例就是为了让读者一眼看懂：主体怎么进格子，raw sheet 怎么进 QC，最后怎么变成透明 GIF。
