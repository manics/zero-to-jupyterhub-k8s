#!/usr/bin/env python
import json
from argparse import ArgumentParser
from importlib import import_module

import jupyterhub.traitlets
from traitlets.traitlets import (
    Any,
    Bool,
    Bytes,
    Callable,
    Dict,
    Enum,
    Float,
    Int,
    List,
    Set,
    Unicode,
    Union,
)


def lookup_schema_type(t):
    UNKNOWN_TYPE = "object"
    traitlets_schema_map = {
        Any: "object",
        Bool: "bool",
        Bytes: "string",
        Callable: UNKNOWN_TYPE,
        Dict: "object",
        Enum: UNKNOWN_TYPE,
        Float: "number",
        Int: "number",
        List: "array",
        Set: "array",
        Unicode: "string",
        Union: None,
        jupyterhub.traitlets.ByteSpecification: "string",
        jupyterhub.traitlets.Callable: UNKNOWN_TYPE,
        jupyterhub.traitlets.Command: "string",
        jupyterhub.traitlets.EntryPointType: UNKNOWN_TYPE,
        jupyterhub.traitlets.URLPrefix: "string",
    }
    return traitlets_schema_map[t]


# https://json-schema.org/understanding-json-schema/reference/type.html
def get_schema_types(traitlet):
    t = lookup_schema_type(traitlet.__class__)
    if t:
        return [t]
    if traitlet.__class__ == Union:
        ts = []
        for t in traitlet.trait_types:
            ts.extend(get_schema_types(t))
        return ts
    raise ValueError(f"Unknown traitlet type: {traitlet.__class__}")


def get_traitlets_schema(module_name, class_name):
    mod = import_module(module_name)
    cls = getattr(mod, class_name)

    configurables = cls.class_traits(config=True)

    schema = {}

    for k, v in configurables.items():
        ts = get_schema_types(v)
        s = {"type": ts}
        if v.allow_none:
            s["type"].append("null")
        s["description"] = v.help
        schema[k] = s

    return schema


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "module_name", help="Module name containing the class, e.g. 'kubespawner'"
    )
    parser.add_argument("class_name", help="Class name, e.g. 'KubeSpawner'")
    args = parser.parse_args()
    schema = get_traitlets_schema(args.module_name, args.class_name)
    print(json.dumps(schema, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
