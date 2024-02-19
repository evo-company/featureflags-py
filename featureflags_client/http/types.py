from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union

from dataclass_wizard import JSONWizard


class VariableType(Enum):
    STRING = 1
    NUMBER = 2
    TIMESTAMP = 3
    SET = 4


class Operator(Enum):
    EQUAL = 1
    LESS_THAN = 2
    LESS_OR_EQUAL = 3
    GREATER_THAN = 4
    GREATER_OR_EQUAL = 5
    CONTAINS = 6
    PERCENT = 7
    REGEXP = 8
    WILDCARD = 9
    SUBSET = 10
    SUPERSET = 11


@dataclass
class CheckVariable:
    name: str
    type: VariableType


@dataclass
class Check:
    operator: Operator
    variable: CheckVariable
    value: Union[str, float, List[str], None] = None


@dataclass
class Condition:
    checks: List[Check]


@dataclass
class Flag:
    name: str
    enabled: bool
    overridden: bool
    conditions: List[Condition]


@dataclass
class RequestData:
    project_name: str
    flags: List[Flag]


@dataclass
class Variable:
    name: str
    type: VariableType


@dataclass
class PreloadFlagsRequest:
    project: str
    version: int
    variables: List[Variable] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)


@dataclass
class PreloadFlagsResponse(JSONWizard):
    version: int
    flags: List[Flag] = field(default_factory=list)


@dataclass
class SyncFlagsRequest:
    project: str
    version: int
    flags: List[str] = field(default_factory=list)


@dataclass
class SyncFlagsResponse(JSONWizard):
    version: int
    flags: List[Flag] = field(default_factory=list)
