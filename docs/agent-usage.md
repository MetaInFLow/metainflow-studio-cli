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
- 当前默认搜索策略是：智谱结构化搜索主路径，百度 `undetected-playwright` 兜底

当前设计现状：
- 调用链路是 `CLI -> service -> search_provider -> summary_provider`
- `search_provider` 先尝试 provider web search，再在失败时回退到百度 `undetected-playwright`，并统一标准化 `title / url / snippet`
- `summary_provider` 再基于标准化结果调用普通模型接口做总结
- `json` 模式下，如果搜索成功但总结失败，会保留已获取的 `results`

当前表现判断：
- 优点：搜索与模型原生 web-search 能力已经解耦，切换模型不影响搜索主链路
- 优点：搜索源从单一路径提升为“智谱主、百度备”，更适合生产兜底
- 优点：相比纯 HTTP 抓取，Playwright 更适合处理百度搜索页的动态行为与风控场景
- 问题：Playwright 方案更重、更慢，部署和运行成本更高
- 问题：当前结果链接仍是百度跳转链接，尚未解到最终目标 URL
- 问题：当前仍没有正文抓取后的二次总结

当前待优化事项：
- 增加 query 改写和搜索结果质量过滤
- 增加多搜索源 fallback（如 SearXNG / 其他源）
- 增加结果去重、来源质量排序、官方站点优先策略
- 增加 `search -> web-crawl -> summarize` 的第二阶段深度模式
- 增加百度跳转链接解析，尽量返回真实目标 URL
- 评估是否在保留 Playwright 主路径的同时，引入更轻量的搜索 API 或自建聚合层作为补充
- 继续补充 provider web search 的高级参数支持（域名过滤、时间范围、摘要长度等）

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
export PROVIDER_API_KEY="your-api-key"
# 可选：如果总结阶段要走别的端点或 Key，可单独配置
# export SUMMARY_BASE_URL="https://your-summary-endpoint/v1"
# export SUMMARY_API_KEY="your-summary-api-key"
# 可选：单独指定“总结阶段”的模型
# export SUMMARY_MODEL="glm-4.7-flash"
export SEARCH_PAGE_TIMEOUT_SECONDS="30"
export WEB_SEARCH_BACKEND="auto"
export SEARCH_PROVIDER_ENGINE="search_pro"
export SEARCH_RESULT_COUNT="10"
```

说明：
- `search-summary` 的搜索阶段不依赖 provider-native web search
- 当前默认先使用 provider web search；这里只要求模型兼容普通文本总结调用
- `PROVIDER_BASE_URL` 默认值已内置为 `https://open.bigmodel.cn/api/paas/v4`
- 如果总结阶段要走其他端点或 API Key，可单独使用 `SUMMARY_BASE_URL` 与 `SUMMARY_API_KEY`
- `SEARCH_PROVIDER_ENGINE` 控制搜索阶段使用的 provider 搜索引擎/档位
- `SEARCH_RESULT_COUNT` 控制搜索阶段返回的结果数量
- `SUMMARY_MODEL` 控制总结阶段使用的模型；如果没有设置，默认使用 `glm-4.7-flash`
- `SEARCH_PAGE_TIMEOUT_SECONDS` 用于控制百度搜索页等待时间
- `WEB_SEARCH_BACKEND` 可选 `auto|zhipu-web-search|baidu-playwright`

### 第 2 步：检查命令路径

```bash
which metainflow
```

### 第 3 步：跑一个真实样本

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
metainflow search-summary --query "React 19 新特性" --output json
```

### 第 3.1 步：验证 web-search skill 指向当前 worktree

```bash
which metainflow
python -c "import metainflow_studio_cli, inspect; print(inspect.getfile(metainflow_studio_cli))"
ls -ld "$HOME/.agents/skills/metainflow-web-search"
ls -ld "$HOME/.agents/skills/metainflow-doc-parse"
```

当前推荐检查点：
- `metainflow_studio_cli` 应来自当前 feature worktree
- `metainflow-web-search` 和 `metainflow-doc-parse` 都应指向同一个 worktree 下的 `metainflow-skills/`

### 第 3.2 步：验证 web-search 聚焦测试

```bash
pytest tests/services/test_web_search_playwright_provider.py tests/services/test_web_search_service.py tests/cli/test_search_summary_json.py -q
```

### 第 3.3 步：验证 OpenCode 中的 skill 调用

建议新开一个 OpenCode 会话后发送：

```text
使用 metainflow-web-search skill 搜索“React 19 新特性”，返回完整 JSON，并告诉我 search_provider 是什么。
```

预期检查点：
- 能识别并使用 `metainflow-web-search`
- 返回 JSON 中存在 `data.results` 与 `data.summary`
- 当前应看到 `meta.search_provider = "baidu-playwright"`

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
