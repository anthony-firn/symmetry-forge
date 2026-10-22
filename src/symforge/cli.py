from __future__ import annotations

import argparse
import importlib
from typing import Callable

from symforge import __version__


def _run_experiment(module_path: str, func_name: str, args: list[str]) -> int:
    module = importlib.import_module(module_path)
    func: Callable[..., int] = getattr(module, func_name)
    return func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="symforge")
    parser.add_argument("--version", action="store_true", help="print version")
    sub = parser.add_subparsers(dest="command")

    exp = sub.add_parser("experiment", help="run an experiment module")
    exp.add_argument("module", help="module path, e.g. experiments.e1_fano")
    exp.add_argument("--func", default="main", help="function name to call")
    exp.add_argument("args", nargs=argparse.REMAINDER)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "experiment":
        return _run_experiment(args.module, args.func, args.args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
