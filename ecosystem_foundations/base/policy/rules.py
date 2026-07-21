from .sensitivity import DataSensitivity

SENSITIVITY_POLICY = {
    DataSensitivity.PUBLIC: {
        "encrypt": False,
        "mask": False,
    },
    DataSensitivity.INTERNAL: {
        "encrypt": False,
        "mask": False,
    },
    DataSensitivity.SENSITIVE: {
        "encrypt": True,
        "mask": True,
    },
    DataSensitivity.HIGHLY_SENSITIVE: {
        "encrypt": True,
        "mask": True,
    },
}

def should_encrypt(sensitivity):
    return SENSITIVITY_POLICY.get(sensitivity, {}).get("encrypt", False)