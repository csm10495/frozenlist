import copy
import os
import types
from collections.abc import MutableSequence
from functools import total_ordering

__version__ = "1.8.1.dev0"

__all__ = (
    "FrozenList",
    "PyFrozenList",
)  # type: Tuple[str, ...]


NO_EXTENSIONS = bool(os.environ.get("FROZENLIST_NO_EXTENSIONS"))  # type: bool


@total_ordering
class FrozenList(MutableSequence):
    __slots__ = ("_frozen", "_items")
    __class_getitem__ = classmethod(types.GenericAlias)

    def __init__(self, items=None):
        self._frozen = False
        if items is not None:
            items = list(items)
        else:
            items = []
        self._items = items

    @property
    def frozen(self):
        return self._frozen

    def freeze(self):
        self._frozen = True

    def __getitem__(self, index):
        return self._items[index]

    def __setitem__(self, index, value):
        if self._frozen:
            raise RuntimeError("Cannot modify frozen list.")
        self._items[index] = value

    def __delitem__(self, index):
        if self._frozen:
            raise RuntimeError("Cannot modify frozen list.")
        del self._items[index]

    def __len__(self):
        return self._items.__len__()

    def __iter__(self):
        return self._items.__iter__()

    def __reversed__(self):
        return self._items.__reversed__()

    def __eq__(self, other):
        return list(self) == other

    def __le__(self, other):
        return list(self) <= other

    def insert(self, pos, item):
        if self._frozen:
            raise RuntimeError("Cannot modify frozen list.")
        self._items.insert(pos, item)

    def __repr__(self):
        return f"<FrozenList(frozen={self._frozen}, {self._items!r})>"

    def __hash__(self):
        if self._frozen:
            return hash(tuple(self))
        else:
            raise RuntimeError("Cannot hash unfrozen list.")

    def __deepcopy__(self, memo: dict[int, object]):
        obj_id = id(self)

        # Return existing copy if already processed (circular reference)
        if obj_id in memo:
            return memo[obj_id]

        # Create new instance and register immediately
        new_list = self.__class__([])
        memo[obj_id] = new_list

        # Deep copy items
        new_list._items[:] = [copy.deepcopy(item, memo) for item in self._items]

        # Preserve frozen state
        if self._frozen:
            new_list.freeze()

        return new_list

    def __reduce__(self):
        return (
            _reconstruct_pyfrozenlist,
            (self._items, self._frozen),
        )


def _reconstruct_pyfrozenlist(items: list[object], frozen: bool) -> "PyFrozenList":
    """Helper function to reconstruct the pure Python FrozenList during unpickling.
    This function is needed since otherwise the class renaming confuses pickle."""
    fl = PyFrozenList(items)
    if frozen:
        fl.freeze()
    return fl


# Store a reference to the pure Python implementation before it's potentially replaced
PyFrozenList = FrozenList


if not NO_EXTENSIONS:
    try:
        from ._frozenlist import FrozenList as CFrozenList  # type: ignore
    except ImportError:  # pragma: no cover
        pass
    else:
        FrozenList = CFrozenList  # type: ignore
