from .core import Listtocell, Span


def get_cells(arr: dict, range_start: int = 1, colspan: dict = None) -> list:
    c = Listtocell()
    c.range_start = range_start
    return c.get_cells(arr, colspan=colspan)


__all__ = ["Listtocell", "Span", "get_cells"]
