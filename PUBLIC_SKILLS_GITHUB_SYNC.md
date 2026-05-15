# Public Animation Skills GitHub Sync Checklist

这两个 skill 当前安装在本机：

- `/Users/fantianxin/.codex/skills/animation-sprite-workshop`
- `/Users/fantianxin/.codex/skills/animation-qc`

当前 `.codex/skills` 不是 Git 仓库，所以不能直接在这个目录里 commit/push。同步到 GitHub 时，把下面文件复制到目标仓库或新仓库。

## 要同步的内容

### repository root

- `README.md`

### animation-sprite-workshop

- `SKILL.md`
- `README.md`
- `agents/openai.yaml`
- `references/generation-logic.md`
- `scripts/check_sprite_gate.py`
- `scripts/make_layout_guide.py`
- `docs/images/workflow-with-subject.png`
- `docs/images/seal-canonical-base-example.png`
- `docs/images/seal-raw-sheet-4x2.png`
- `docs/images/seal-final-transparent.gif`
- `docs/images/layout-guide-4x2.png`
- `docs/images/raw-template-4x2.png`

### animation-qc

- `SKILL.md`
- `README.md`
- `agents/openai.yaml`
- `scripts/process_sprite.py`
- `scripts/make_sequence_preview.py`
- `scripts/audit_product_usage.py`
- `docs/images/qc-edge-cleaning-example.png`
- `docs/images/seal-workflow-example.png`
- `docs/images/seal-qc-aligned-sheet.png`
- `docs/images/seal-final-transparent.gif`

## 不要同步的内容

- `__pycache__/`
- `*.pyc`
- 本轮 seal/海豹测试素材
- 私人项目里的临时输出目录
- `.DS_Store`

## 建议仓库结构

```text
animation-skills/
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

## 同步前检查

```bash
python3 -m py_compile \
  animation-sprite-workshop/scripts/check_sprite_gate.py \
  animation-sprite-workshop/scripts/make_layout_guide.py \
  animation-qc/scripts/process_sprite.py \
  animation-qc/scripts/make_sequence_preview.py \
  animation-qc/scripts/audit_product_usage.py
```

## 建议 commit message

```text
Document public animation sprite workflow and QC pipeline
```

## 建议 PR/Release Notes

```text
Added public documentation for animation-sprite-workshop and animation-qc.

- Explains the end-to-end sprite workflow from idea to transparent GIF.
- Adds visual examples for layout guides, raw templates, and edge cleanup.
- Documents the sprite geometry contract and pre-QC gate.
- Documents QC outputs, timing controls, transparent GIF export checks, and near-edge divider-line cleanup.
- Clarifies what belongs in generation vs QC and when to regenerate instead of repairing.
```
