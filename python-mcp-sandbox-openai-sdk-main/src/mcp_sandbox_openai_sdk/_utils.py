import random
import string


def _id_generator(size=12, chars=string.ascii_lowercase) -> str:
    return "".join(random.choice(chars) for _ in range(size)).lower()
