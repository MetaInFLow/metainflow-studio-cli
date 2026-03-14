# metainflow-studio-cli Agent Usage

本文件给 agent 和开发者使用，目标是两件事：
- 快速调用 `metainflow-studio-cli`
- 快速开发和验证新的 metainflow 能力与 skill

---

## 1. 这个项目是什么

当前 `metainflow-studio-cli` 是一个 Python CLI 工具箱。

现阶段已实现的主能力：
- `parse-doc`

对应 skill：
- `metainflow-doc-parse`

当前支持的文档类型：
- `.pdf`
- `.doc`
- `.docx`
- `.pptx`
- `.xlsx`
- `.csv`
- `.txt`
- `.md`
- `.html`

---

## 2. 首次上手

在项目根目录执行：

```bash
python -m pip install -e '.[dev]'
hash -r
```

验证 CLI 已安装：

```bash
which metainflow
metainflow --help
metainflow parse-doc --help
```

普通使用方式请看：`docs/usage.md`

---

## 3. Agent 如何调用这个工具

### 方式 A：直接调用 CLI

适合：
- 调试能力是否可用
- 本地快速验证
- 不依赖 skill 的脚本调用

最小示例：

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
```

如果 shell 里没有 `metainflow`，临时改用：

```bash
python -m metainflow_studio_cli.main parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
```

### 方式 B：通过 skill 调用

skill 目录：

```text
metainflow-skills/
  metainflow-doc-parse/
    SKILL.md
```

挂载到 OpenCode 用户技能目录：

```bash
ln -sfn "/Users/zsy/Desktop/openclaw/BeeClaw/metainflow-skills/metainflow-doc-parse" "/Users/zsy/.agents/skills/metainflow-doc-parse"
```

验证挂载：

```bash
ls -l "/Users/zsy/.agents/skills/metainflow-doc-parse"
```

注意：
- 新 skill 挂载后，当前会话可能看不到
- 这通常是会话缓存问题
- 新开一个 OpenCode 会话再验证最稳妥

---

## 4. 本地更新后的正确步骤

当 CLI 代码有更新时，推荐固定执行下面 4 步：

### 第 1 步：重新安装

```bash
python -m pip install -e '.[dev]'
hash -r
```

### 第 2 步：检查命令路径

```bash
which metainflow
```

### 第 3 步：跑一个真实样本

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
```

### 第 4 步：跑测试

```bash
pytest -q
```

如果只想验证真实样本矩阵：

```bash
METAINFLOW_RUN_SAMPLE_MATRIX=1 pytest -q tests/integration/test_real_sample_matrix.py
```

---

## 5. 开发新能力时的建议流程

### 新增 CLI 能力

通常会改这些位置：
- `metainflow_studio_cli/main.py`
- `metainflow_studio_cli/core/`
- `metainflow_studio_cli/services/`
- `tests/`

建议顺序：
1. 先写测试
2. 再写 service 逻辑
3. 最后接 CLI 命令
4. 用真实样本回归

### 新增 skill

通常会改这些位置：
- `metainflow-skills/<skill-name>/SKILL.md`

建议顺序：
1. 先把 CLI 能力做通
2. 再写 skill 文档
3. 再挂载到 `~/.agents/skills/`
4. 新开会话验证 skill 可发现

---

## 6. 开发时重点关注

- 统一配置前缀：`PROVIDER_*`
- 统一输出契约：`success / data / meta / error`
- 先保证 `parse-doc` 稳定，再扩其他命令
- 真实样本优先，避免只测 mock
- skill 只是能力入口，核心仍然是 CLI / service / parser

## 7. 常见问题

### `zsh: command not found: metainflow`

执行：

```bash
python -m pip install -e '.[dev]'
hash -r
```

### `.doc` 解析失败，提示 `soffice not found`

说明系统缺 LibreOffice。

Ubuntu 安装：

```bash
sudo apt-get update
sudo apt-get install -y libreoffice
```

### PDF 输出为空

一般是 OCR 依赖不完整。

Ubuntu 安装：

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng poppler-utils fonts-noto-cjk
```
