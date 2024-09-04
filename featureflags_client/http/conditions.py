import logging
import re
from typing import Any, Callable, Dict, List, Optional, Set, Union

from featureflags_client.http.types import Check, Flag, Operator, Value
from featureflags_client.http.utils import hash_flag_value

log = logging.getLogger(__name__)

_UNDEFINED = object()


def false(_ctx: Dict[str, Any]) -> bool:
    return False


def except_false(func: Callable) -> Callable:
    def wrapper(ctx: Dict[str, Any]) -> Any:
        try:
            return func(ctx)
        except (TypeError, ValueError):
            return False

    return wrapper


def equal(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        return ctx.get(name, _UNDEFINED) == value

    return proc


def less_than(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _UNDEFINED)
        return ctx_val is not _UNDEFINED and ctx_val < value

    return proc


def less_or_equal(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _UNDEFINED)
        return ctx_val is not _UNDEFINED and ctx_val <= value

    return proc


def greater_than(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _UNDEFINED)
        return ctx_val is not _UNDEFINED and ctx_val > value

    return proc


def greater_or_equal(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _UNDEFINED)
        return ctx_val is not _UNDEFINED and ctx_val >= value

    return proc


def contains(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        return value in ctx.get(name, "")

    return proc


def percent(name: str, value: Any) -> Callable:
    @except_false
    def proc(ctx: Dict[str, Any]) -> bool:
        ctx_val = ctx.get(name, _UNDEFINED)
        if ctx_val is _UNDEFINED:
            return False

        hash_ctx_val = hash_flag_value(name, ctx_val)
        return hash_ctx_val % 100 < int(value)

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


OPERATIONS_MAP: Dict[Operator, Callable[..., Callable[..., bool]]] = {
    Operator.EQUAL: equal,
    Operator.LESS_THAN: less_than,
    Operator.LESS_OR_EQUAL: less_or_equal,
    Operator.GREATER_THAN: greater_than,
    Operator.GREATER_OR_EQUAL: greater_or_equal,
    Operator.CONTAINS: contains,
    Operator.PERCENT: percent,
    Operator.REGEXP: regexp,
    Operator.WILDCARD: wildcard,
    Operator.SUBSET: subset,
    Operator.SUPERSET: superset,
}


def check_proc(check: Check) -> Callable:
    if check.value is None:
        log.debug(f"Check[{check}].value is None")
        return false

    return OPERATIONS_MAP[check.operator](check.variable.name, check.value)


def flag_proc(flag: Flag) -> Optional[Callable]:
    if not flag.overridden:
        # Flag was not overridden on server, use value from defaults.
        log.debug(
            f"Flag[{flag.name}] is not overriden yet, using default value"
        )
        return None

    conditions = []
    for condition in flag.conditions:
        checks_procs = [check_proc(check) for check in condition.checks]

        # in case of invalid condition it would be safe to replace it
        # with a falsish condition
        if not checks_procs:
            log.debug("Condition has empty checks")
            checks_procs = [false]

        conditions.append(checks_procs)

    if flag.enabled and conditions:

        def proc(ctx: Dict[str, Any]) -> bool:
            return any(
                all(check(ctx) for check in checks) for checks in conditions
            )

    else:
        log.debug(
            f"Flag[{flag.name}] is disabled or do not have any conditions"
        )

        def proc(ctx: Dict[str, Any]) -> bool:
            return flag.enabled

    return proc


def update_flags_state(flags: List[Flag]) -> Dict[str, Callable[..., bool]]:
    """
    Assign a proc to each flag which has to be computed.
    """

    procs = {}

    for flag in flags:
        proc = flag_proc(flag)
        if proc is not None:
            procs[flag.name] = proc

    return procs


def str_to_int(value: Union[int, str]) -> Union[int, str]:
    try:
        return int(value)
    except ValueError:
        return value


def value_proc(value: Value) -> Union[Callable, int, str]:
    if not value.overridden:
        # Value was not overridden on server, use value from defaults.
        log.debug(
            f"Value[{value.name}] is not override yet, using default value"
        )
        return str_to_int(value.value_default)

    conditions = []
    for condition in value.conditions:
        checks_procs = [check_proc(check) for check in condition.checks]

        # in case of invalid condition it would be safe to replace it
        # with a falsish condition
        if not checks_procs:
            log.debug("Condition has empty checks")
            checks_procs = [false]

        conditions.append(
            (condition.value_override, checks_procs),
        )

    if value.enabled and conditions:

        def proc(ctx: Dict[str, Any]) -> Union[int, str]:
            for condition_value_override, checks in conditions:
                if all(check(ctx) for check in checks):
                    return str_to_int(condition_value_override)
            return str_to_int(value.value_override)

    else:
        log.debug(
            f"Value[{value.name}] is disabled or do not have any conditions"
        )

        def proc(ctx: Dict[str, Any]) -> Union[int, str]:
            return str_to_int(value.value_override)

    return proc


def update_values_state(
    values: List[Value],
) -> Dict[str, Callable[..., Union[int, str]]]:
    """
    Assign a proc to each values which has to be computed.
    """

    procs = {}

    for value in values:
        proc = value_proc(value)
        if proc is not None:
            procs[value.name] = proc

    return procs
