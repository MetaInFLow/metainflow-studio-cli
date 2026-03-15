# metainflow-studio-cli 技术方案

## 目标

以 `parse-doc` 为首个核心能力，先形成稳定的文档解析基线，再逐步扩展到搜索、网页抓取、语音转写、图像理解等能力。

---

## 技术选型

### 1. 入口层

- CLI 框架：`Typer`
- 原因：
  - 子命令扩展简单
  - 类型注解直接映射参数
  - 自动生成帮助信息
  - 比 `argparse` 更适合后续多命令工具箱

### 2. 代码分层

- `main.py`：CLI 入口与参数解析
- `core/`：配置、错误、通用模型
- `services/`：业务编排
- `services/doc_parse/parsers.py`：格式解析实现

选择原则：
- CLI 只处理输入输出
- service 只负责业务编排
- parser 只负责具体格式解析

### 3. 配置方式

- 环境变量前缀：`PROVIDER_*`
- 当前保留项：
  - `PROVIDER_BASE_URL`
  - `PROVIDER_API_KEY`
  - `PROVIDER_TIMEOUT_SECONDS`
  - `PROVIDER_MAX_RETRIES`
  - `PROVIDER_MODEL_DOC_PARSE`
  - `PROVIDER_MODEL_WEB_SEARCH`

选择原则：
- 命名统一
- 后续接多 provider 时可直接扩展
- 对 CLI、API、Worker 三种形态都兼容

### 4. 输出契约

- 统一返回结构：
  - `success`
  - `data`
  - `meta`
  - `error`

选择原则：
- 便于 CLI 输出 JSON
- 便于后续复用到 API 层
- 便于前端和自动化脚本做稳定解析

### 5. 文档解析能力选型

- `.txt/.md`：直接读取
- `.csv`：标准库 `csv`
- `.html`：轻量文本提取
- `.docx/.pptx/.xlsx`：基于 OpenXML/ZIP 结构解析
- `.xls`：通过 `LibreOffice soffice` 转 `.xlsx`
- `.doc`：通过 `LibreOffice soffice` 转 `.docx`
- `.pdf`：先文本抽取，再 OCR 兜底

选择原则：
- 优先保证可控和可部署
- 先做本地解析，减少外部依赖
- 对 Ubuntu 生产环境友好

### 5.1 搜索摘要能力选型

- 命令：`search-summary`
- 形态：关键词搜索 + AI 总结
- skill：`metainflow-web-search`
- 外部用法：与 `miaoda-web-search` 保持一致
- 搜索：由 `metainflow-studio-cli` 自己获取结果
- 默认搜索源：`www.baidu.com` + `undetected-playwright`
- 兜底入口：`m.baidu.com`
- 总结：由配置模型基于标准化结果生成摘要

选择原则：
- 优先复用既有 skill 使用心智
- 先提供单命令搜索入口
- 保证搜索能力不依赖 provider-native web search
- 默认主路径优先保证百度搜索可抓取成功
- 入口选择以真实稳定性验证结果为准
- 后续再与 `web-crawl` 拆分协作

当前实现状态：
- 已实现 `playwright_search_provider + summary_provider + service` 三层拆分
- 当前默认入口是 `www.baidu.com`，`m.baidu.com` 仅作为 fallback
- 浏览器层使用 `undetected-playwright`
- 总结阶段调用普通模型接口，不依赖 provider-native web search
- 当前 `json` 模式支持在总结失败时保留已获取的搜索结果

当前表现观察：
- 当前设计选择更偏向“可抓取成功”而非“最低资源成本”
- Playwright 方案预期可提升百度搜索页的实际可用性，但也会引入更高的耗时和运行成本
- 真实联调已验证：当前环境下 `Playwright + 百度搜索 + 普通模型总结` 可返回非空结果与摘要
- 稳定性验证结果：`www.baidu.com` 连续多次可稳定返回结果；`m.baidu.com` 更容易出现验证码或空 DOM
- 当前真实返回的结果链接仍是百度跳转链接，尚未解析成最终落地 URL
- 因此当前版本更适合作为可用基线，而不是最终搜索质量形态

### 6. 系统依赖

- `libreoffice`
- `tesseract-ocr`
- `tesseract-ocr-chi-sim`
- `tesseract-ocr-eng`
- `poppler-utils`
- `fonts-noto-cjk`

选择原则：
- 满足 `.doc` 转换
- 满足扫描版 PDF OCR
- 满足中文场景

### 7. 测试策略

- 单元测试：parser、service、config、CLI
- 集成测试：真实样本矩阵
- 真实样本目录：`tests/integration/samples/`

选择原则：
- 先覆盖格式正确性
- 再覆盖真实文件回归
- 保证后续改 parser 不会破坏已有格式

### 8. 当前推荐架构形态

短期采用：`CLI + Service + Parser`

中期演进目标：`CLI + API + Worker`

原因：
- 当前阶段先把单机工具能力做稳
- 后续如果出现长任务、批处理、多人调用，再拆 API 和异步 Worker

---

## 当前约束

- 当前已实现 `parse-doc` 与 `search-summary`
- 运行环境以 Ubuntu 服务器为主
- 需要兼容 OpenCode skill 方式调用
- 当前更关注可用性、准确性、稳定性，不优先做复杂服务化

---

## TODOs

以下事项为技术建议项，当前统一标记为 **待定**，需要团队内部审核后再确认优先级与排期。

### P0

- [ ] 待定：增加 `metainflow doctor` 命令，检查 `soffice`、`tesseract`、`poppler` 是否可用
- [ ] 待定：增加 MIME 检测，避免只看文件后缀
- [ ] 待定：增加文件大小限制与超时控制
- [ ] 待定：增加损坏文件、伪造文件的 CLI 端到端错误测试
- [ ] 待定：增加真实样本逐文件断言，不只检查扩展名覆盖

### P1

- [ ] 待定：建立 `BaseParser` 抽象和 parser registry
- [ ] 待定：把 `parse-doc` 的 `blocks/tables` 结构输出补完整
- [ ] 待定：增加结构化日志和 `request_id`
- [ ] 待定：增加 URL 下载策略（超时、重试、白名单/黑名单）
- [ ] 待定：增加配置文件支持，和 `PROVIDER_*` 环境变量统一映射
- [ ] 待定：为 `search-summary` 增加 query 改写、结果过滤、去重与来源质量排序
- [ ] 待定：为 `search-summary` 增加多搜索源 fallback，不只依赖单一 Playwright 百度搜索
- [ ] 待定：为百度搜索结果增加跳转链接解析，尽量返回真实目标 URL
- [ ] 待定：把入口稳定性探测抽象成可配置策略，而不是只依赖固定顺序 fallback

### P2

- [ ] 待定：建立 `BaseProvider` 抽象
- [ ] 待定：为后续 `web-search / web-fetch / speech-to-text / image-understanding` 预留统一 service 接口
- [ ] 待定：设计 API 层输入输出模型
- [ ] 待定：设计异步任务模型（`task_id`, status, result_url）
- [ ] 待定：设计对象存储与结果持久化方案
- [ ] 待定：增加 `search -> web-crawl -> summarize` 的二阶段深度搜索模式
- [ ] 待定：评估搜索 API / SearXNG / 自建聚合层，降低纯 Playwright 搜索方案的长期资源成本

---

## 里程碑建议

### M1：稳定 CLI
- 完成 `parse-doc` 的依赖检查、安全控制、真实样本回归

### M2：标准化内核
- 完成 parser/provider 抽象和统一任务模型

### M3：服务化演进
- 增加 API 层和异步 Worker，支持企业级调用方式
