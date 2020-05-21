def to_camel_case(name: str) -> str:
    if not name:
        return name
    return name[0] + name.title().replace("_", "")[1:]
