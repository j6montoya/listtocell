from listtocell import Listtocell, get_cells, Span


class TestColumnName:
    def setup_method(self):
        self.atc = Listtocell()

    def test_zero_is_A(self):
        assert self.atc._column_name(0) == "A"

    def test_25_is_Z(self):
        assert self.atc._column_name(25) == "Z"

    def test_26_is_AA(self):
        assert self.atc._column_name(26) == "AA"

    def test_27_is_AB(self):
        assert self.atc._column_name(27) == "AB"

    def test_51_is_AZ(self):
        assert self.atc._column_name(51) == "AZ"

    def test_52_is_BA(self):
        assert self.atc._column_name(52) == "BA"


class TestFlatDict:
    """Flat dict (no nesting) -> all cells in row 1, one column each."""

    def test_flat_two_keys(self):
        result = get_cells({"Name": "John", "Age": 25})
        assert result == [
            {"cell": "A1", "range": "A1:A1", "value": "John", "column": "Name"},
            {"cell": "B1", "range": "B1:B1", "value": 25, "column": "Age"},
        ]

    def test_flat_three_keys(self):
        result = get_cells({"A": 1, "B": 2, "C": 3})
        assert result == [
            {"cell": "A1", "range": "A1:A1", "value": 1, "column": "A"},
            {"cell": "B1", "range": "B1:B1", "value": 2, "column": "B"},
            {"cell": "C1", "range": "C1:C1", "value": 3, "column": "C"},
        ]


class TestOneLevel:
    """Single level of nesting -> parent spans children in row 1, children in row 2."""

    def test_one_parent_two_children(self):
        result = get_cells({"Person": {"Name": "John", "Age": 25}})
        assert result == [
            {"cell": "A1", "range": "A1:B1", "value": "Person", "column": "Person"},
            {"cell": "A2", "range": "A2:A2", "value": "John", "column": "Name"},
            {"cell": "B2", "range": "B2:B2", "value": 25, "column": "Age"},
        ]

    def test_two_parents(self):
        result = get_cells({
            "Group1": {"X": 1, "Y": 2},
            "Group2": {"P": 3, "Q": 4},
        })
        assert len(result) == 6
        # parents in row 1
        assert result[0] == {"cell": "A1", "range": "A1:B1", "value": "Group1", "column": "Group1"}
        assert result[3] == {"cell": "C1", "range": "C1:D1", "value": "Group2", "column": "Group2"}
        # children in row 2
        assert result[1]["cell"] == "A2"
        assert result[2]["cell"] == "B2"
        assert result[4]["cell"] == "C2"
        assert result[5]["cell"] == "D2"


class TestTwoLevels:
    """Two levels of nesting -> verifies depth and ranges across 3 rows."""

    def test_two_levels(self):
        result = get_cells({"Group": {"Sub": {"Name": "John", "Age": 25}}})
        assert result == [
            {"cell": "A1", "range": "A1:B1", "value": "Group", "column": "Group"},
            {"cell": "A2", "range": "A2:B2", "value": "Sub", "column": "Sub"},
            {"cell": "A3", "range": "A3:A3", "value": "John", "column": "Name"},
            {"cell": "B3", "range": "B3:B3", "value": 25, "column": "Age"},
        ]


class TestMixedDepth:
    """Top-level dict with both nested and flat values."""

    def test_nested_and_flat(self):
        result = get_cells({"Col1": {"A": 1, "B": 2}, "Col2": "Value"})
        assert result[0] == {"cell": "A1", "range": "A1:B1", "value": "Col1", "column": "Col1"}
        assert result[1] == {"cell": "A2", "range": "A2:A2", "value": 1, "column": "A"}
        assert result[2] == {"cell": "B2", "range": "B2:B2", "value": 2, "column": "B"}
        # flat value spans full depth (rows 1 to 2)
        assert result[3] == {"cell": "C1", "range": "C1:C2", "value": "Value", "column": "Col2"}


class TestColspan:
    """colspan via external dict and Span inline wrapper."""

    def test_external_colspan_flat(self):
        result = get_cells({"Name": "John", "Extra": "x"}, colspan={"Extra": 2})
        assert result[0] == {"cell": "A1", "range": "A1:A1", "value": "John", "column": "Name"}
        assert result[1] == {"cell": "B1", "range": "B1:C1", "value": "x", "column": "Extra"}

    def test_external_colspan_with_depth(self):
        # Extra is first key → A1:B2 (2 cols × 2 rows)
        result = get_cells({"Extra": "x", "Group": {"X": 1}}, colspan={"Extra": 2})
        assert result[0] == {"cell": "A1", "range": "A1:B2", "value": "x", "column": "Extra"}
        assert result[1] == {"cell": "C1", "range": "C1:C1", "value": "Group", "column": "Group"}
        assert result[2] == {"cell": "C2", "range": "C2:C2", "value": 1, "column": "X"}

    def test_span_inline(self):
        result = get_cells({"Extra": Span("x", 2), "Group": {"X": 1}})
        assert result[0] == {"cell": "A1", "range": "A1:B2", "value": "x", "column": "Extra"}
        assert result[1] == {"cell": "C1", "range": "C1:C1", "value": "Group", "column": "Group"}
        assert result[2] == {"cell": "C2", "range": "C2:C2", "value": 1, "column": "X"}

    def test_span_no_depth(self):
        result = get_cells({"Name": Span("John", 3)})
        assert result[0] == {"cell": "A1", "range": "A1:C1", "value": "John", "column": "Name"}

    def test_span_one_is_identity(self):
        # Span(val, 1) must produce the same result as a plain value
        result_plain = get_cells({"Name": "John", "Age": 25})
        result_span = get_cells({"Name": Span("John", 1), "Age": 25})
        assert result_plain == result_span

    def test_colspan_key_absent_from_dict(self):
        # colspan key not present in arr is silently ignored
        result = get_cells({"Name": "John"}, colspan={"Ghost": 5})
        assert result == [{"cell": "A1", "range": "A1:A1", "value": "John", "column": "Name"}]

    def test_colspan_with_range_start(self):
        result = get_cells({"Extra": "x", "Group": {"X": 1}}, colspan={"Extra": 2}, range_start=3)
        assert result[0] == {"cell": "A3", "range": "A3:B4", "value": "x", "column": "Extra"}
        assert result[1] == {"cell": "C3", "range": "C3:C3", "value": "Group", "column": "Group"}
        assert result[2] == {"cell": "C4", "range": "C4:C4", "value": 1, "column": "X"}


class TestList:
    """List as input (top-level or nested)."""

    def test_list_top_level(self):
        result = get_cells(["hola", "mundo"])
        assert result == [
            {"cell": "A1", "range": "A1:A1", "value": "hola", "column": 0},
            {"cell": "B1", "range": "B1:B1", "value": "mundo", "column": 1},
        ]

    def test_list_as_nested_value(self):
        result = get_cells({"prueba": ["hola", "mundo"]})
        assert result == [
            {"cell": "A1", "range": "A1:B1", "value": "prueba", "column": "prueba"},
            {"cell": "A2", "range": "A2:A2", "value": "hola", "column": 0},
            {"cell": "B2", "range": "B2:B2", "value": "mundo", "column": 1},
        ]


class TestRangeStart:
    """range_start != 1 shifts all row numbers."""

    def test_range_start_2_flat(self):
        result = get_cells({"Name": "John"}, range_start=2)
        assert result == [
            {"cell": "A2", "range": "A2:A2", "value": "John", "column": "Name"},
        ]

    def test_range_start_3_nested(self):
        result = get_cells({"P": {"X": 1, "Y": 2}}, range_start=3)
        assert result[0]["cell"] == "A3"
        assert result[0]["range"] == "A3:B3"
        assert result[1]["cell"] == "A4"
        assert result[2]["cell"] == "B4"
