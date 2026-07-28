from enum import StrEnum


class ActiveState(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ALL = "all"

class ComparisonOperator(StrEnum):
    EQ = "eq"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"

class SystemState(StrEnum):
    NON_SYSTEM = "non_system"
    SYSTEM = "system"
    ALL = "all"