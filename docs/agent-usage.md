# metainflow-studio-cli Agent Usage

本文件给 agent 和开发者使用，目标是两件事：
- 快速调用 `metainflow-studio-cli`
- 快速开发和验证新的 metainflow 能力与 skill

---

## 1. 这个项目是什么

当前 `metainflow-studio-cli` 是一个 Python CLI 工具箱。

现阶段已实现的主能力：
- `parse-doc`
- `search-summary`

其中 `search-summary` 的实现边界是：
- 搜索结果获取由 `metainflow-studio-cli` 自己完成
- 配置模型只负责总结，不负责联网搜索
- 当前默认搜索源是基于 `undetected-playwright` 的百度搜索
- 当前入口策略是：`www.baidu.com` 主路径，`m.baidu.com` 兜底

当前设计现状：
- 调用链路是 `CLI -> service -> search_provider -> summary_provider`
- `search_provider` 通过 undetected Playwright 打开百度搜索页并标准化 `title / url / snippet`
- `summary_provider` 再基于标准化结果调用普通模型接口做总结
- `json` 模式下，如果搜索成功但总结失败，会保留已获取的 `results`

当前表现判断：
- 优点：搜索与模型原生 web-search 能力已经解耦，切换模型不影响搜索主链路
- 优点：相比纯 HTTP 抓取，Playwright 更适合处理百度搜索页的动态行为与风控场景
- 优点：真实联调已验证 `Playwright + 百度搜索 + 普通模型总结` 主链路可跑通
- 优点：稳定性验证表明 `www.baidu.com` 在当前环境下显著优于 `m.baidu.com`
- 问题：Playwright 方案更重、更慢，部署和运行成本更高
- 问题：当前结果链接仍是百度跳转链接，尚未解到最终目标 URL
- 问题：当前仍是单搜索源方案，还没有多源 fallback 和正文抓取后的二次总结

当前待优化事项：
- 增加 query 改写和搜索结果质量过滤
- 增加多搜索源 fallback（如 SearXNG / 其他源）
- 增加结果去重、来源质量排序、官方站点优先策略
- 增加 `search -> web-crawl -> summarize` 的第二阶段深度模式
- 增加百度跳转链接解析，尽量返回真实目标 URL
- 评估是否在保留 Playwright 主路径的同时，引入更轻量的搜索 API 或自建聚合层作为补充
- 持续跟踪 `m.baidu.com` 的可用性，但目前只作为 fallback，不作为默认入口

对应 skill：
- `metainflow-doc-parse`
- `metainflow-web-search`

当前支持的文档类型：
- `.pdf`
- `.doc`
- `.docx`
- `.pptx`
- `.xls`
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
python -m playwright install chromium
hash -r
```

验证 CLI 已安装：

```bash
which metainflow
metainflow --help
metainflow parse-doc --help
metainflow search-summary --help
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
metainflow search-summary --query "React 19 新特性" --output json
```

如果 shell 里没有 `metainflow`，临时改用：

```bash
python -m metainflow_studio_cli.main parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
```

### 方式 B：通过 skill 调用

skill 源码目录在仓库内：

```text
metainflow-studio-cli/
  metainflow-skills/
    metainflow-doc-parse/
      SKILL.md
    metainflow-web-search/
      SKILL.md
```

这样做的目的：
- skill 和 CLI 代码一起版本管理
- 提交、评审、回滚更简单
- 避免 skill 与真实能力实现脱节

在仓库根目录挂载到 OpenCode 用户技能目录：

```bash
ln -sfn "$(pwd)/metainflow-skills/metainflow-doc-parse" "$HOME/.agents/skills/metainflow-doc-parse"
ln -sfn "$(pwd)/metainflow-skills/metainflow-web-search" "$HOME/.agents/skills/metainflow-web-search"
```

验证挂载：

```bash
ls -l "$HOME/.agents/skills/metainflow-doc-parse"
ls -l "$HOME/.agents/skills/metainflow-web-search"
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
python -m playwright install chromium
hash -r
```

### 第 1.1 步：准备搜索总结模型配置

```bash
export PROVIDER_BASE_URL="https://your-openai-compatible-endpoint/v1"
export PROVIDER_API_KEY="your-api-key"
export PROVIDER_MODEL_WEB_SEARCH="your-model-name"
export WEB_SEARCH_PAGE_TIMEOUT_SECONDS="30"
```

说明：
- `search-summary` 的搜索阶段不依赖 provider-native web search
- 这里只要求模型兼容普通文本总结调用
- `WEB_SEARCH_PAGE_TIMEOUT_SECONDS` 用于控制百度搜索页等待时间

### 第 2 步：检查命令路径

```bash
which metainflow
```

### 第 3 步：跑一个真实样本

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
metainflow search-summary --query "React 19 新特性" --output json
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

推荐原则：
- skill 源码放在仓库内的 `metainflow-skills/`
- `~/.agents/skills/` 只放软链接，不直接放源码

建议顺序：
1. 先把 CLI 能力做通
2. 再写 skill 文档
3. 再挂载到 `~/.agents/skills/`
4. 新开会话验证 skill 可发现

如果当前在 feature worktree 中验证 skill，挂载命令应指向该 worktree 路径。

---

## 6. 开发时重点关注

- 统一配置前缀：`PROVIDER_*`
- 统一输出契约：`success / data / meta / error`
- 先保证 `parse-doc` 稳定，再扩其他命令
- 真实样本优先，避免只测 mock
- skill 只是能力入口，核心仍然是 CLI / service / parser
- `search-summary` 要保持“搜索”和“总结”两层解耦，避免绑定 provider-native web search
- `search-summary` 当前是可用基线，但搜索质量和搜索源稳定性仍需持续优化
- Playwright 搜索链路要重点关注启动耗时、超时、验证码和浏览器环境依赖

## 7. 常见问题

### `zsh: command not found: metainflow`

执行：

```bash
python -m pip install -e '.[dev]'
hash -r
```

### `.doc` / `.xls` 解析失败，提示 `soffice not found`

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
