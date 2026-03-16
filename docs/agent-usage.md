# metainflow-studio-cli Agent Usage

本文件给 agent 和开发者使用，目标是两件事：
- 快速调用 `metainflow-studio-cli`
- 快速开发和验证新的 metainflow 能力与 skill

## 1. 这个项目是什么

当前 `metainflow-studio-cli` 是一个 Python CLI 工具箱。

现阶段已实现的主能力：
- `parse-doc`
- `web-crawl`

对应 skill：
- `metainflow-doc-parse`
- `metainflow-web-fetch`

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
metainflow web-crawl --help
```

## 3. Agent 如何调用这个工具

### 方式 A：直接调用 CLI

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
metainflow web-crawl --url https://example.com --output json
```

### 方式 B：通过 skill 调用

在仓库根目录挂载到 OpenCode 用户技能目录：

```bash
ln -sfn "$(pwd)/metainflow-skills/metainflow-doc-parse" "$HOME/.agents/skills/metainflow-doc-parse"
ln -sfn "$(pwd)/metainflow-skills/metainflow-web-fetch" "$HOME/.agents/skills/metainflow-web-fetch"
```

验证挂载：

```bash
ls -l "$HOME/.agents/skills/metainflow-doc-parse"
ls -l "$HOME/.agents/skills/metainflow-web-fetch"
```

## 4. 本地更新后的正确步骤

```bash
python -m pip install -e '.[dev]'
hash -r
pytest -q
```

## 5. 开发时重点关注

- 统一配置前缀：`PROVIDER_*`
- 统一输出契约：`success / data / meta / error`
- `web-crawl` 默认使用 Crawl4AI 进行页面抓取与内容抽取
- 真实样本优先，避免只测 mock

Attribution: This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web data extraction.
