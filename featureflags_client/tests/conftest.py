import faker
import pytest

from featureflags_client.http.types import (
    Check,
    CheckVariable,
    Condition,
    Flag,
    Operator,
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
def flag(condition):
    return Flag(
        name=f.pystr(),
        enabled=True,
        overridden=True,
        conditions=[condition],
    )
