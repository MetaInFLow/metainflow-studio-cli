# XLSX Region Splitting Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split a single worksheet into multiple logical table regions after merged-cell expansion so complex templates preserve more readable structure.

**Architecture:** Keep the existing coordinate-based XLSX parser and merged-cell expansion. After building the expanded grid for each sheet, apply a minimal row-segment-based splitting heuristic to separate obviously disconnected table islands, then render markdown by concatenating the per-region tables.

**Tech Stack:** Python, `xml.etree.ElementTree`, `zipfile`, `pytest`

---

### Task 1: Cover region splitting behavior with tests

**Files:**
- Modify: `tests/services/test_parse_office_xml_formats.py`

**Step 1: Write the failing test**

Add a worksheet fixture with two separated non-empty table islands in the same sheet and assert `tables` contains the first block rows followed by the second block rows, without the giant empty columns/rows between them.

**Step 2: Run test to verify it fails**

Run: `pytest -q tests/services/test_parse_office_xml_formats.py::test_parse_xlsx_splits_disconnected_regions`

**Step 3: Write minimal implementation**

Add helpers in the XLSX parser that find connected non-empty cells and build one rectangular table per region.

**Step 4: Run test to verify it passes**

Run: `pytest -q tests/services/test_parse_office_xml_formats.py::test_parse_xlsx_splits_disconnected_regions`

### Task 2: Preserve merged cells within a region

**Files:**
- Modify: `tests/services/test_parse_office_xml_formats.py`
- Modify: `metainflow_studio_cli/services/doc_parse/parsers.py`

**Step 1: Write the failing test**

Add a fixture where a merged header and its body rows are one logical island while another small table sits elsewhere in the same sheet.

**Step 2: Run test to verify it fails**

Run: `pytest -q tests/services/test_parse_office_xml_formats.py::test_parse_xlsx_keeps_merged_block_together_when_splitting_regions`

**Step 3: Write minimal implementation**

Reuse the merged-cell-expanded grid as region input so the merged header block stays connected.

**Step 4: Run test to verify it passes**

Run: `pytest -q tests/services/test_parse_office_xml_formats.py::test_parse_xlsx_keeps_merged_block_together_when_splitting_regions`

### Task 3: Verify parser and target workbook behavior

**Files:**
- Modify: `metainflow_studio_cli/services/doc_parse/parsers.py`

**Step 1: Run focused parser tests**

Run: `pytest -q tests/services/test_parse_office_xml_formats.py`

**Step 2: Run real workbook verification**

Run: `python -m metainflow_studio_cli.main parse-doc --file "/Users/zsy/Desktop/openclaw/BeeClaw/客户测试样本/测评表及规划方案/市级、省级制造业单项冠军企业申报评估表-模版.xlsx" --output json`

**Step 3: Run broader verification**

Run: `pytest -q tests/integration/test_real_sample_matrix.py`

## Progress

- 已完成：定位复杂模板中的主要文本丢失热点，并产出区域切分设计。
- 已完成：补充区域切分与 merged block 相关测试草案，用于后续实现验证。
- 当前状态：区域切分原型已试验，但还未作为稳定版本纳入正式提交。

## Remaining TODOs

- 降低复杂模板中的长文本拆散问题，减少短语级文本丢失。
- 为区域切分增加更稳健的规则，降低复杂模板下的误拆/漏拆。
- 评估是否输出 `sheet` / `region` / `merge metadata`，提升调试与下游消费能力。
