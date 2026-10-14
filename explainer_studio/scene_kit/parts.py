"""Named parts that survive copying.

Builders return mobjects with named parts (table.cells[r][c], diagram.nodes["api"], chart.graphs["loss"]). ManimGL's
Mobject.copy only remaps attributes that are mobjects inside the family, so parts kept in a dict, a list, a new
VGroup of family members or a KeyedGroup would keep pointing at the original after .copy() (and so after .animate,
dim(), Transform targets). Parts remaps them.
"""

from __future__ import annotations

import math

from manimlib import Group, Mobject, VGroup

__all__ = ["KeyedGroup", "Parts", "PartsMixin", "choose_tick_step", "compute_decimal_place_count", "remap_parts"]

_SKIPPED_ATTRIBUTES = frozenset({"submobjects", "family", "parents", "target", "saved_state", "updaters", "data",
                                 "uniforms", "textures"})


def remap_parts(source: Mobject, destination: Mobject) -> None:
    """Point destination's named parts (attributes holding family members, directly or in dicts, lists, tuples,
    VGroups and KeyedGroups built from family members) at destination's own family. destination is a fresh shallow
    copy of source."""
    family_index_by_object_id_map = {id(member): family_index
                                     for family_index, member in enumerate(source.get_family())}
    family = destination.get_family()
    rebuilt_group_by_object_id_map: dict[int, object] = {}

    def remap_value(value, depth=0):
        if isinstance(value, Mobject):
            family_index = family_index_by_object_id_map.get(id(value))
            if family_index is not None:
                return family[family_index]
            if id(value) in rebuilt_group_by_object_id_map:
                return rebuilt_group_by_object_id_map[id(value)]
            if type(value) not in (VGroup, Group, KeyedGroup):
                return value    # something outside the component (e.g. a speech bubble the scene attached): shared
            if isinstance(value, KeyedGroup):
                part_by_key_map = {key: remap_value(mobject) for key, mobject in value.items()}
                if any(part_by_key_map[key] is mobject for key, mobject in value.items()):
                    return value
                remapped = KeyedGroup(part_by_key_map)
            else:
                remapped_submobjects = [remap_value(mobject) for mobject in value.submobjects]
                if any(remapped_element is original_element
                       for remapped_element, original_element in zip(remapped_submobjects, value.submobjects)):
                    return value
                remapped = type(value)(*remapped_submobjects)
            rebuilt_group_by_object_id_map[id(value)] = remapped
            return remapped
        if depth >= 2:
            return value
        if isinstance(value, dict):
            remapped = {key: remap_value(element, depth + 1) for key, element in value.items()}
            return value if all(remapped[key] is element for key, element in value.items()) else remapped
        if isinstance(value, (list, tuple)):
            remapped = [remap_value(element, depth + 1) for element in value]
            is_unchanged = all(remapped_element is original_element
                               for remapped_element, original_element in zip(remapped, value))
            return value if is_unchanged else type(value)(remapped)
        return value

    for attribute_name, value in list(source.__dict__.items()):
        if attribute_name in _SKIPPED_ATTRIBUTES:
            continue
        remapped = remap_value(value)
        if remapped is not value:
            setattr(destination, attribute_name, remapped)


class PartsMixin:
    """Mix into any Mobject subclass whose instances carry named parts; copy() then remaps them (see remap_parts)."""

    def copy(self, deep: bool = False):
        result = super().copy(deep)
        if not deep:   # a deep copy maps everything through copy.deepcopy's memo already
            remap_parts(self, result)
        return result


class Parts(PartsMixin, VGroup):
    """A VGroup with named parts that belong to each copy. Every kit builder returns one (or a subclass)."""


class KeyedGroup(Parts):
    """A VGroup whose parts can also be looked up by key: g["api"], g[("a", "b")], g.keys()/values()/items().
    Integer indices and iteration behave like a VGroup (they give mobjects), so FadeIn(g) animates every part."""

    def __init__(self, part_by_key_map: dict | None = None):
        part_by_key_map = dict(part_by_key_map or {})
        super().__init__(*part_by_key_map.values())
        self._part_by_key_map = part_by_key_map

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return super().__getitem__(key)
        return self._part_by_key_map[key]

    def __contains__(self, key):
        return key in self._part_by_key_map

    def keys(self):
        return self._part_by_key_map.keys()

    def values(self):
        return self._part_by_key_map.values()

    def items(self):
        return self._part_by_key_map.items()

    def get(self, key, default=None):
        return self._part_by_key_map.get(key, default)


def compute_decimal_place_count(step: float) -> int:
    """Decimal places a tick step needs (0.2 → 1, 0.05 → 2, 5 → 0)."""
    return 0 if step >= 1 else math.ceil(-math.log10(step) - 1e-9)


def choose_tick_step(span: float) -> float:
    if span <= 0:
        return 1
    rough_step = span / 5
    magnitude = 10 ** math.floor(math.log10(rough_step))
    for multiplier in (1, 2, 5, 10):
        if rough_step <= multiplier * magnitude:
            return multiplier * magnitude
    return 10 * magnitude
