from argparse import ArgumentParser
from importlib import import_module
from inspect import getmembers
import json
import sys
from traitlets.traitlets import Any, Bool, Callable, Dict, Float, Int, List, Set, Unicode, Union
import jupyterhub.traitlets


def lookup_schema_type(t):
    traitlets_schema_map = {
        Any: "object",
        Bool: "bool",
        Callable: None,
        Dict: "object",
        Float: "number",
        Int: "number",
        List: "array",
        Set: "array",
        Unicode: "string",
        Union: None,

        jupyterhub.traitlets.ByteSpecification: "string",
        jupyterhub.traitlets.Callable: None,
        jupyterhub.traitlets.Command: "string",
    }
    return traitlets_schema_map[t]


# https://json-schema.org/understanding-json-schema/reference/type.html
def get_schema_types(traitlet):
    # ignore_type_strs = [f"<class '{t}'>" for t in (
    #     "traitlets.traitlets.Callable",
    #     "jupyterhub.traitlets.ByteSpecification",
    #     "jupyterhub.traitlets.Callable",
    #     "jupyterhub.traitlets.Command",
    # )]
    t = lookup_schema_type(traitlet.__class__)
    if t:
        return [t]
    if traitlet.__class__ == Union:
        ts = []
        for t in traitlet.trait_types:
            ts.extend(get_schema_types(t))
        return ts
    return []


def get_traitlets_schema(module_name, class_name):
    mod = import_module(module_name)
    cls = getattr(mod, class_name)

    members = getmembers(cls)

    configurables = {}
    for (k, v) in members:
        m = getattr(v, "metadata", None)
        if m and m.get("config"):
            configurables[k] = v

    schema = {}

    for k, v in configurables.items():
        ts = get_schema_types(v)
        if not ts:
            print(f"Skipping {k}", file=sys.stderr)
            continue
        s = {"type": ts}
        if v.allow_none:
            s["type"].append("null")
        s["description"] = v.help
        schema[k] = s

    return schema


def main():
    parser = ArgumentParser()
    parser.add_argument("module_name", help="Module name containing the class, e.g. 'kubespawner'")
    parser.add_argument("class_name", help="Class name, e.g. 'KubeSpawner'")
    args = parser.parse_args()
    schema = get_traitlets_schema(args.module_name, args.class_name)
    print(json.dumps(schema, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
