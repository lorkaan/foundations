
from automation import models


class DataSensitivity(models.TextChoices):
    PUBLIC = "P"
    INTERNAL = "I"
    SENSITIVE = "S"
    HIGHLY_SENSITIVE = "H"

SENSITIVITY_RANK = {
    DataSensitivity.PUBLIC: 0,
    DataSensitivity.INTERNAL: 1,
    DataSensitivity.SENSITIVE: 2,
    DataSensitivity.HIGHLY_SENSITIVE: 3,
}