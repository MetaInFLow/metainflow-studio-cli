# Real Sample Fixtures

Put real-world sample files here for integration validation.

Required extensions for the full matrix:

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

Run the matrix check with:

```bash
METAINFLOW_RUN_SAMPLE_MATRIX=1 pytest -q tests/integration/test_real_sample_matrix.py
```
