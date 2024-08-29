from typing import Any, Callable

from featureflags_client.http.conditions import (
    _UNDEFINED,
    OPERATIONS_MAP,
    check_proc,
    contains,
    equal,
    false,
    flag_proc,
    greater_or_equal,
    greater_than,
    less_or_equal,
    less_than,
    percent,
    regexp,
    subset,
    superset,
    value_proc,
    wildcard,
)
from featureflags_client.http.types import Operator
from featureflags_client.http.utils import hash_flag_value

TEST_OPERATOR_NAME = "test_operator"
TEST_VARIABLE_NAME = "test_operator"


def check_op(left: Any, op: Callable, right: Any) -> bool:
    context = {TEST_VARIABLE_NAME: left} if left is not _UNDEFINED else {}
    return op(TEST_OPERATOR_NAME, right)(context)


def test_false():
    assert false({}) is False


def test_equal():
    assert check_op(1, equal, 1) is True
    assert check_op(2, equal, 1) is False
    assert check_op(1, equal, 2) is False
    assert check_op(1, equal, "1") is False
    assert check_op("1", equal, 1) is False
    assert check_op(_UNDEFINED, equal, 1) is False


def test_less_than():
    assert check_op(1, less_than, 2) is True
    assert check_op(1, less_than, 1) is False
    assert check_op(2, less_than, 1) is False
    assert check_op(_UNDEFINED, less_than, 1) is False
    assert check_op("1", less_than, 2) is False


def test_less_or_equal():
    assert check_op(1, less_or_equal, 2) is True
    assert check_op(1, less_or_equal, 1) is True
    assert check_op(2, less_or_equal, 1) is False
    assert check_op(_UNDEFINED, less_or_equal, 1) is False
    assert check_op("1", less_or_equal, 2) is False


def test_greater_than():
    assert check_op(2, greater_than, 1) is True
    assert check_op(1, greater_than, 1) is False
    assert check_op(1, greater_than, 2) is False
    assert check_op(_UNDEFINED, greater_than, 1) is False
    assert check_op("2", greater_than, 1) is False


def test_greater_or_equal():
    assert check_op(2, greater_or_equal, 1) is True
    assert check_op(1, greater_or_equal, 1) is True
    assert check_op(1, greater_or_equal, 2) is False
    assert check_op(_UNDEFINED, greater_or_equal, 1) is False
    assert check_op("2", greater_or_equal, 1) is False


def test_contains():
    assert check_op("aaa", contains, "a") is True
    assert check_op("aaa", contains, "aa") is True
    assert check_op("aaa", contains, "aaa") is True
    assert check_op("a", contains, "aaa") is False
    assert check_op("aaa", contains, "b") is False
    assert check_op(_UNDEFINED, contains, "a") is False
    assert check_op(1, contains, "a") is False
    assert check_op("a", contains, 1) is False


def test_percent():
    # If percent <= 0 return False
    for i in range(-150, 150):
        assert check_op(i, percent, 0) is False

    # If percent >= 100 return True
    for i in range(-150, 150):
        assert check_op(i, percent, 100) is True

    # Check not integer values
    assert check_op(_UNDEFINED, percent, 100) is False
    assert check_op(50, percent, _UNDEFINED) is False
    assert check_op(_UNDEFINED, percent, _UNDEFINED) is False
    assert check_op("foo", percent, "not_number") is False

    # Check string values
    assert check_op("foo", percent, "100") is True
    assert check_op("foo", percent, "0") is False
    assert check_op("foo", percent, 100) is True
    assert check_op("foo", percent, 0) is False

    # Check hash comparison
    foo_hash = hash_flag_value(TEST_VARIABLE_NAME, "foo")
    assert check_op("foo", percent, foo_hash % 100 + 1) is True
    assert check_op("foo", percent, foo_hash % 100 - 1) is False


def test_regexp():
    assert check_op("anything", regexp, ".") is True
    assert check_op("kebab-style", regexp, r"\w+-\w+") is True
    assert check_op("snake_style", regexp, r"\w+-\w+") is False
    assert check_op(_UNDEFINED, regexp, ".") is False
    assert check_op(1, regexp, ".") is False


def test_wildcard():
    assert check_op("foo-value", wildcard, "foo-*") is True
    assert check_op("value-foo", wildcard, "*-foo") is True
    assert check_op("foo-value-bar", wildcard, "foo-*-bar") is True
    assert check_op("value", wildcard, "foo-*") is False
    assert check_op(_UNDEFINED, wildcard, "foo-*") is False
    assert check_op(1, wildcard, "foo-*") is False


def test_subset():
    assert check_op(set("ab"), subset, set("abc")) is True
    assert check_op(set("bc"), subset, set("abc")) is True
    assert check_op(set("ac"), subset, set("abc")) is True
    assert check_op(set("ae"), subset, set("abc")) is False
    assert check_op(_UNDEFINED, subset, set("abc")) is False
    assert check_op(1, subset, set("abc")) is False


def test_superset():
    assert check_op(set("abc"), superset, set("ab")) is True
    assert check_op(set("abc"), superset, set("bc")) is True
    assert check_op(set("abc"), superset, set("ac")) is True
    assert check_op(set("abc"), superset, set("ae")) is False
    assert check_op(_UNDEFINED, superset, set("abc")) is False
    assert check_op(1, superset, set("abc")) is False


def test_valid_check_proc(check, variable):
    proc = check_proc(check)
    assert proc({variable.name: check.value}) is True
    assert proc({variable.name: ""}) is False


def test_supported_check_proc_ops():
    assert set(OPERATIONS_MAP) == set(Operator)


def test_check_proc_no_value(check):
    check.value = None
    assert check_proc(check) is false


def test_valid_flag_proc(flag, check, variable):
    proc = flag_proc(flag)
    assert proc({variable.name: check.value}) is True


def test_valid_str_value_proc(value, check, variable):
    proc = value_proc(value)
    assert (
        proc({variable.name: check.value}) is value.conditions[0].value_override
    )


def test_valid_int_value_proc(value_int, check, variable):
    proc = value_proc(value_int)
    assert (
        proc({variable.name: check.value})
        is value_int.conditions[0].value_override
    )
