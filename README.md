# listtocell

Convert nested Python dicts into Excel-style merged-cell coordinates (`A1`, `A1:C1`, `A1:B2`).

Useful for building multi-level table headers with merged cells in spreadsheet libraries like **openpyxl** or **xlsxwriter** — without manually calculating ranges.

## Installation

```bash
pip install listtocell
# or
uv add listtocell
```

## Quick start

```python
from listtocell import get_cells

result = get_cells({
    "Person": {"Name": "John", "Age": 25},
    "Score": 99,
})
```
```json
[
  {"cell": "A1", "range": "A1:B1", "value": "Person", "column": "Person"},
  {"cell": "A2", "range": "A2:A2", "value": "John", "column": "Name"},
  {"cell": "B2", "range": "B2:B2", "value": 25, "column": "Age"},
  {"cell": "C1", "range": "C1:C2", "value": 99, "column": "Score"}
]
```

Each entry contains:

| Key | Description |
|-----|-------------|
| `cell` | Top-left cell of the merge (e.g. `A1`) |
| `range` | Full merge range (e.g. `A1:B1`) |
| `value` | Cell content |
| `column` | Original dict key |

## How it works

### Flat dict — single header row

```python
get_cells({"Name": "John", "Age": 25})
```
```json
[
  {"cell": "A1", "range": "A1:A1", "value": "John", "column": "Name"},
  {"cell": "B1", "range": "B1:B1", "value": 25, "column": "Age"}
]
```

### Nested dict — merged parent + child row

```python
get_cells({"Person": {"Name": "John", "Age": 25}})
```
```json
[
  {"cell": "A1", "range": "A1:B1", "value": "Person", "column": "Person"},
  {"cell": "A2", "range": "A2:A2", "value": "John", "column": "Name"},
  {"cell": "B2", "range": "B2:B2", "value": 25, "column": "Age"}
]
```

### Mixed depth — flat value spans remaining rows

When a flat value sits alongside nested values, it automatically rowspans to fill the depth:

```python
get_cells({"Group": {"X": 1, "Y": 2}, "Total": 99})
```
```json
[
  {"cell": "A1", "range": "A1:B1", "value": "Group", "column": "Group"},
  {"cell": "A2", "range": "A2:A2", "value": 1, "column": "X"},
  {"cell": "B2", "range": "B2:B2", "value": 2, "column": "Y"},
  {"cell": "C1", "range": "C1:C2", "value": 99, "column": "Total"}
]
```

### Multiple nesting levels

```python
get_cells({"Report": {"Summary": {"Total": 100, "Avg": 50}}})
```
```json
[
  {"cell": "A1", "range": "A1:B1", "value": "Report", "column": "Report"},
  {"cell": "A2", "range": "A2:B2", "value": "Summary", "column": "Summary"},
  {"cell": "A3", "range": "A3:A3", "value": 100, "column": "Total"},
  {"cell": "B3", "range": "B3:B3", "value": 50, "column": "Avg"}
]
```

### List as value — expanded like a dict

Lists are treated as nested structures with integer keys:

```python
get_cells({"Tags": ["python", "excel"]})
```
```json
[
  {"cell": "A1", "range": "A1:B1", "value": "Tags", "column": "Tags"},
  {"cell": "A2", "range": "A2:A2", "value": "python", "column": 0},
  {"cell": "B2", "range": "B2:B2", "value": "excel", "column": 1}
]
```

## Use cases

### openpyxl — grouped headers

```python
from openpyxl import Workbook
from openpyxl.styles import Alignment
from listtocell import get_cells

wb = Workbook()
ws = wb.active

headers = {
    "Personal": {"Name": "Alice", "Age": 30},
    "Financial": {"Salary": 5000, "Bonus": 500, "Total": 5500},
}

for entry in get_cells(headers):
    ws[entry["cell"]] = entry["value"]
    if entry["cell"] != entry["range"].split(":")[1]:  # is a merge
        ws.merge_cells(entry["range"])
        ws[entry["cell"]].alignment = Alignment(horizontal="center")

wb.save("report.xlsx")
```

### xlsxwriter — grouped headers

```python
import xlsxwriter
from listtocell import get_cells

workbook = xlsxwriter.Workbook("report.xlsx")
ws = workbook.add_worksheet()
merge_fmt = workbook.add_format({"align": "center", "bold": True})

headers = {
    "Q1": {"Jan": 100, "Feb": 120, "Mar": 110},
    "Q2": {"Apr": 130, "May": 140, "Jun": 150},
}

for entry in get_cells(headers):
    cell_start, cell_end = entry["range"].split(":")
    if cell_start == cell_end:
        ws.write(entry["cell"], entry["value"])
    else:
        ws.merge_range(entry["range"], entry["value"], merge_fmt)

workbook.close()
```

### Dynamic headers from config

Headers can be built programmatically from any data source — database schema, API response, config file:

```python
from listtocell import get_cells

# Config driven
schema = {
    "user": {"id": None, "email": None, "role": None},
    "audit": {"created_at": None, "updated_at": None},
}

cells = get_cells(schema)
# Use cells to render a table header in any output format
```

### Row offset (`range_start`)

When writing below existing content (e.g. a title row), shift all row numbers:

```python
result = get_cells({"Group": {"X": 1, "Y": 2}}, range_start=3)
```
```json
[
  {"cell": "A3", "range": "A3:B3", "value": "Group", "column": "Group"},
  {"cell": "A4", "range": "A4:A4", "value": 1, "column": "X"},
  {"cell": "B4", "range": "B4:B4", "value": 2, "column": "Y"}
]
```

### Column span (`colspan` / `Span`)

Two ways to make a leaf cell span multiple columns:

**External dict:**

```python
from listtocell import get_cells

result = get_cells(
    {"Notes": "see below", "Group": {"X": 1, "Y": 2}},
    colspan={"Notes": 2},
)
```
```json
[
  {"cell": "A1", "range": "A1:B2", "value": "see below", "column": "Notes"},
  {"cell": "C1", "range": "C1:D1", "value": "Group", "column": "Group"},
  {"cell": "C2", "range": "C2:C2", "value": 1, "column": "X"},
  {"cell": "D2", "range": "D2:D2", "value": 2, "column": "Y"}
]
```

**`Span` inline** — keeps the colspan next to the value:

```python
from listtocell import get_cells, Span

result = get_cells({"Notes": Span("see below", 2), "Group": {"X": 1, "Y": 2}})
```
```json
[
  {"cell": "A1", "range": "A1:B2", "value": "see below", "column": "Notes"},
  {"cell": "C1", "range": "C1:D1", "value": "Group", "column": "Group"},
  {"cell": "C2", "range": "C2:C2", "value": 1, "column": "X"},
  {"cell": "D2", "range": "D2:D2", "value": 2, "column": "Y"}
]
```

## API reference

### `get_cells(arr, *, range_start=1, colspan=None)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `arr` | `dict \| list` | Header structure to traverse |
| `range_start` | `int` | First row number (default `1`) |
| `colspan` | `dict` | Mapping of key → column span for leaf values |

### `Span(value, span)`

Wraps a leaf value with an explicit column span. Takes priority over the `colspan` dict when both are provided for the same key.

### `Listtocell` (class)

Lower-level class for cases where you need to reuse an instance or set `range_start` separately:

```python
from listtocell import Listtocell

ltc = Listtocell()
ltc.range_start = 2
result = ltc.get_cells({"A": {"X": 1, "Y": 2}})
```

## License

MIT
