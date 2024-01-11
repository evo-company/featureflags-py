import re
from typing import Any, Callable, Dict, Optional, Set

from featureflags_protobuf.graph_pb2 import Check as CheckProto
from featureflags_protobuf.graph_pb2 import Result as ResultProto

_undefined = object()


def false(ctx: Dict[str, Any]) -> bool:
    return False


def except_false(func: Callable) -> Callable:
    def wrapper(ctx: Dict[str, Any]) -> Any:
        try:
            return func(ctx)
        except TypeError:
            return False

    return wrapper


def equal(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        return ctx.get(name, _undefined) == value

    return proc


def less_than(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _undefined)
        ctx_val + 0  # quick type checking in Python 2
        return ctx_val is not _undefined and ctx_val < value

    return proc


def less_or_equal(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _undefined)
        ctx_val + 0  # quick type checking in Python 2
        return ctx_val is not _undefined and ctx_val <= value

    return proc


def greater_than(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _undefined)
        ctx_val + 0  # quick type checking in Python 2
        return ctx_val is not _undefined and ctx_val > value

    return proc


def greater_or_equal(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _undefined)
        ctx_val + 0  # quick type checking in Python 2
        return ctx_val is not _undefined and ctx_val >= value

    return proc


def contains(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        return value in ctx.get(name, "")

    return proc


def percent(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _undefined)
        return ctx_val is not _undefined and hash(ctx_val) % 100 < value

    return proc


def regexp(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any], _re: re.Pattern = re.compile(value)) -> bool:
        return _re.match(ctx.get(name, "")) is not None

    return proc


def wildcard(name: str, value: Any) -> Callable:
    re_ = "^" + "(?:.*)".join(map(re.escape, value.split("*"))) + "$"
    return regexp(name, re_)


def subset(name: str, value: Any) -> Callable:
    if value:

        @except_false
        def proc(ctx: Dict[str, Any], _value: Optional[Set] = None) -> bool:
            _value = _value or set(value)
            ctx_val = ctx.get(name)
            return bool(ctx_val) and _value.issuperset(ctx_val)

    else:
        proc = false

    return proc


def superset(name: str, value: Any) -> Callable:
    if value:

        @except_false
        def proc(ctx: Dict[str, Any], _value: Optional[Set] = None) -> bool:
            _value = _value or set(value)
            ctx_val = ctx.get(name)
            return bool(ctx_val) and _value.issubset(ctx_val)

    else:
        proc = false

    return proc


OPS = {
    CheckProto.EQUAL: equal,
    CheckProto.LESS_THAN: less_than,
    CheckProto.LESS_OR_EQUAL: less_or_equal,
    CheckProto.GREATER_THAN: greater_than,
    CheckProto.GREATER_OR_EQUAL: greater_or_equal,
    CheckProto.CONTAINS: contains,
    CheckProto.PERCENT: percent,
    CheckProto.REGEXP: regexp,
    CheckProto.WILDCARD: wildcard,
    CheckProto.SUBSET: subset,
    CheckProto.SUPERSET: superset,
}


class DummyReport:
    def add(self, error: str) -> None:
        pass


def check_proc(
    result: ResultProto,
    check_id: int,
    report: DummyReport = DummyReport(),
) -> Callable:
    check = result.Check[check_id]
    if not check.variable.Variable:
        report.add(f"Check[{check_id}].variable is unset")
        return false
    if check.operator == CheckProto.__DEFAULT__:
        report.add(f"Check[{check_id}].operator is unset")
        return false
    kind = check.WhichOneof("kind")
    if not kind:
        report.add(f"Check[{check_id}].kind is unset")
        return false
    variable = result.Variable[check.variable.Variable]
    if not variable.name:
        report.add(f"Variable[{check.variable}].name is unset")
        return false
    value = getattr(check, check.WhichOneof("kind"))
    # TODO: check value type and if operator is supported
    return OPS[check.operator](variable.name, value)


def flag_proc(
    result: ResultProto,
    flag_id: int,
    report: DummyReport = DummyReport(),
) -> Optional[Callable]:
    flag = result.Flag[flag_id]
    if not flag.HasField("overridden"):
        report.add(f"Flag[{flag_id}].overridden is unset")
        return None
    if not flag.HasField("enabled"):
        report.add(f"Flag[{flag_id}].enabled is unset")
        return false
    if not flag.overridden.value:
        return None

    conditions = []
    for condition_ref in flag.conditions:
        condition = result.Condition[condition_ref.Condition]
        checks = [
            check_proc(result, check_ref.Check, report)
            for check_ref in condition.checks
        ]
        if checks:
            conditions.append(checks)
        else:
            report.add(f"Condition[{condition_ref.Condition}].checks is empty")
            # in case of invalid condition it would be safe to replace it
            # with a falsish condition
            conditions.append([false])

    if flag.enabled.value and conditions:

        def proc(ctx: Dict[str, Any]) -> bool:
            return any(
                all(check(ctx) for check in checks_) for checks_ in conditions
            )

    else:

        def proc(ctx: Dict[str, Any]) -> bool:
            return flag.enabled.value

    return proc


def load_flags(
    result: ResultProto,
    report: DummyReport = DummyReport(),
) -> Dict[str, Callable]:
    procs = {}
    for flag_ref in result.Root.flags:
        flag = result.Flag[flag_ref.Flag]
        if not flag.name:
            report.add(f"Flag[{flag_ref.Flag}].name is not set")
            continue
        proc = flag_proc(result, flag_ref.Flag, report)
        if proc is not None:
            procs[flag.name] = proc
    return procs
