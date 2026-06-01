from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping


def make_strict_json_schema(schema: Mapping[str, Any]) -> Dict[str, Any]:
    strict_schema = deepcopy(dict(schema))
    _make_objects_strict(strict_schema)
    return strict_schema


def _make_objects_strict(node: Any) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            properties = node.get("properties", {})
            if isinstance(properties, dict):
                node["required"] = list(properties.keys())
            node["additionalProperties"] = False

        node.pop("default", None)

        for value in node.values():
            _make_objects_strict(value)
    elif isinstance(node, list):
        for item in node:
            _make_objects_strict(item)
