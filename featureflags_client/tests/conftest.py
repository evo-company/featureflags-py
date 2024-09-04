import faker
import pytest

from featureflags_client.http.types import (
    Check,
    CheckVariable,
    Condition,
    Flag,
    Operator,
    Value,
    ValueCondition,
    VariableType,
)

f = faker.Faker()


@pytest.fixture
def variable():
    return CheckVariable(name=f.pystr(), type=VariableType.STRING)


@pytest.fixture
def check(variable):
    return Check(
        operator=Operator.EQUAL,
        variable=variable,
        value=f.pystr(),
    )


@pytest.fixture
def condition(check):
    return Condition(checks=[check])


@pytest.fixture
def value_condition(check):
    return ValueCondition(checks=[check], value_override=f.pystr())


@pytest.fixture
def value_condition_int_value(check):
    return ValueCondition(checks=[check], value_override=f.pyint())


@pytest.fixture
def flag(condition):
    return Flag(
        name=f.pystr(),
        enabled=True,
        overridden=True,
        conditions=[condition],
    )


@pytest.fixture
def value(value_condition):
    return Value(
        name=f.pystr(),
        enabled=True,
        overridden=True,
        value_default=f.pystr(),
        value_override=f.pystr(),
        conditions=[value_condition],
    )


@pytest.fixture
def value_int(value_condition_int_value):
    return Value(
        name=f.pystr(),
        enabled=True,
        overridden=True,
        value_default=f.pyint(),
        value_override=f.pyint(),
        conditions=[value_condition_int_value],
    )
