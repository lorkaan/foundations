ENTITY_REGISTRY = set()


def register_entity(model):
    if model in ENTITY_REGISTRY:
        return  # avoid duplicates silently (or raise if you prefer)

    ENTITY_REGISTRY.add(model)


def get_registered_entities():
    return ENTITY_REGISTRY