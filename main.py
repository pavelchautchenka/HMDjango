import lesson13a
from lesson13a.abstract import AbstractStorage

s = lesson13a.InMemoryStorage()


def add_to_storage(storage: AbstractStorage, key: str, value):
    storage.set(key, value)
