import kopf


@kopf.on.create('pepedocs.org', 'v1', 'pydjangoapps')
def create_fn(body, **kwargs):
    print(f"A handler is called with body: {body}")