class Span:
    """Leaf value with colspan > 1."""
    def __init__(self, value, span: int):
        self.value = value
        self.span = span


class Listtocell:
    """Convert a nested dict/list to Excel-style merged-cell coordinates."""

    def __init__(self):
        self.depth: int = 0
        self.range_start: int = 1
        self._count: int = 0
        self._result: list = []
        self._colspan: dict = {}

    def get_cells(self, arr: dict, colspan: dict = None) -> list:
        """Traverse *arr* and return one entry per node with its cell reference.

        Args:
            arr: Nested dict or list representing the header structure.
            colspan: Optional mapping of top-level key → number of columns to
                span. ``Span`` inline values take priority over this dict.

        Returns:
            List of dicts, each with keys ``cell``, ``range``, ``value``,
            and ``column``.
        """
        self._colspan = colspan or {}
        self.depth = self._depth(arr)
        self._count = 0
        self._result = []
        range_list = list(range(self.range_start, self.depth + self.range_start))
        return self._cell(arr, 0, range_list)

    def _depth(self, arr) -> int:
        """Return the maximum nesting depth of *arr* (leaves count as 1)."""
        max_depth = 0
        for val in (arr if isinstance(arr, list) else arr.values()):
            if isinstance(val, (dict, list)):
                tmp = self._depth(val)
                if max_depth < tmp:
                    max_depth = tmp
        return max_depth + 1

    def _count_array(self, arr) -> int:
        """Count nested (non-leaf) nodes in *arr* across all levels."""
        count = 0
        if isinstance(arr, (dict, list)):
            for v in (arr if isinstance(arr, list) else arr.values()):
                if isinstance(v, (dict, list)):
                    count += self._count_array(v) + 1
        return count

    def _count_recursive(self, arr) -> int:
        """Count all nodes in *arr* across all levels (leaves + containers)."""
        count = len(arr)
        for v in (arr if isinstance(arr, list) else arr.values()):
            if isinstance(v, (dict, list)):
                count += self._count_recursive(v)
        return count

    def _cell(self, arr, index: int, range_list: list) -> list:
        """Recursively append cell entries for each node in *arr*.

        Nested nodes produce a merged header that spans their leaf columns;
        leaf nodes span the remaining rows down to ``range_list[-1]``.
        ``_count`` tracks the current 0-based column cursor.
        """
        items = enumerate(arr) if isinstance(arr, list) else arr.items()
        for i, (key, value) in enumerate(items):
            self._count += 1
            if i == 0:
                self._count -= 1

            # Span inline takes priority over colspan dict
            if isinstance(value, Span):
                span, actual_value, is_nested = value.span, value.value, False
            else:
                span = self._colspan.get(key, 1) if isinstance(key, str) else 1
                actual_value, is_nested = value, isinstance(value, (dict, list))

            col = self._column_name(self._count)
            if is_nested:
                count_arr = self._count_recursive(actual_value)
                rg = self._column_name(self._count + (count_arr - self._count_array(actual_value)) - 1)
            else:
                rg = self._column_name(self._count + span - 1)

            cell_ref = col + str(range_list[index])

            if is_nested:
                self._result.append({
                    'cell': cell_ref,
                    'range': cell_ref + ':' + rg + str(range_list[index]),
                    'value': key,
                    'column': key,
                })
                self._cell(actual_value, index + 1, range_list)
            else:
                self._result.append({
                    'cell': cell_ref,
                    'range': cell_ref + ':' + rg + str(range_list[-1]),
                    'value': actual_value,
                    'column': key,
                })
                if span > 1:
                    self._count += span - 1

        return self._result

    def _column_name(self, num: int) -> str:
        """Convert a 0-based column index to a spreadsheet letter (0→A, 26→AA)."""
        col = ""
        while num >= 0:
            col = chr(num % 26 + 0x41) + col
            num = num // 26 - 1
        return col
