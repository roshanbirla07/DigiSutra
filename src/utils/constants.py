from enum import Enum


class USER_TYPE(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SELLER = "seller"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

    @classmethod
    def choices(cls):
        return [(item.name, item.value) for item in cls]
