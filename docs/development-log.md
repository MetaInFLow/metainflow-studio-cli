# metainflow-studio-cli 开发日志

## 2026-03-14

### 阶段目标
- 初始化 `metainflow-studio-cli` 项目结构。
- 优先实现 `parse-doc` 命令。
- 支持文档格式矩阵：`.pdf .doc .docx .pptx .xlsx .csv .txt .md .html`。
- 建立真实样本验证基线。

### 已完成内容
- 创建项目基础文件：`pyproject.toml`、包入口、测试目录。
- 实现 CLI 命令：`parse-doc --file --output text|json`。
- 实现 `PROVIDER_*` 配置读取基础：
  - `PROVIDER_BASE_URL`
  - `PROVIDER_API_KEY`
  - `PROVIDER_TIMEOUT_SECONDS`
  - `PROVIDER_MAX_RETRIES`
  - `PROVIDER_MODEL_DOC_PARSE`
- 实现解析服务主链路（按扩展名分发）：
  - 文本：`.txt`, `.md`
  - 表格：`.csv`, `.xlsx`
  - Office：`.docx`, `.pptx`, `.doc`（通过 soffice 转换）
  - 网页：`.html`
  - PDF：文本抽取 + OCR 兜底
- 实现 URL 输入下载能力（HTTP/HTTPS）。
- 建立统一输出 envelope：`success/data/meta/error`。
- 实现错误码映射：
  - `0` 成功
  - `1` 处理失败
  - `2` 参数/校验失败
  - `3` 外部依赖或网络失败

### 测试与验证结果
- 单元/服务测试：`pytest -q` 结果 `15 passed, 1 skipped`。
- 样本矩阵校验：
  - 命令：`METAINFLOW_RUN_SAMPLE_MATRIX=1 pytest -q tests/integration/test_real_sample_matrix.py`
  - 结果：`1 passed`
- 真实样本逐个命令验证（`parse-doc --output json`）：
  - 通过：`pdf/docx/pptx/xlsx/csv/txt/md/html`
  - 失败：`doc`（当前环境缺少 `soffice`）

### 当前已知问题
- `.doc` 解析依赖 LibreOffice：若系统无 `soffice`，会返回错误。

### 下一步计划
- 在 Ubuntu 服务器安装并验证系统依赖：`libreoffice`、`tesseract-ocr`、`poppler-utils` 等。
- 增加真实样本端到端断言（不止检查扩展名覆盖，还检查输出字段和内容质量）。
- 根据真实样本结果持续修正解析器细节。
