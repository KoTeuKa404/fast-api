# app/levels.py
from enum import IntEnum

class Level(IntEnum):
    USER = 0
    PREMIUM = 10
    MODERATOR = 50
    MANAGER = 80
