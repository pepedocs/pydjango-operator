import os
import kopf
import yaml
import kubernetes

from jinja2 import Template


@kopf.on.create('pepedocs.org', 'v1', 'pydjangoapps')
def create(spec, name, namespace, logger, **kwargs):    

    image = spec.get('image')
    replicas = spec.get('replicas')
    djangoSpec = spec.get('djangoSpec')

    # Todo: How to cancel creation when an error happens?

    if image is None:
        raise kopf.PermanentError("PyDjangoApp field 'image' must be set.")

    if djangoSpec is None:
        raise kopf.PermanentError("PyDjangoApp field 'djangoSpec must be set.")

    paths = djangoSpec.get('paths')

    if paths is None:
        raise kopf.PermanentError("PyDjangoApp field 'paths must be set.")

    runScript = paths.get('runScript')
    managePy = paths.get('managePy')

    if runScript is None and managePy is None:
        raise kopf.PermanentError("At least one of the PyDjangoApp fields must be set (runScript, managePy)")

    host = djangoSpec.get('host', 'localhost')
    port = djangoSpec.get('port', 8000)
    template_file = os.path.join(os.path.dirname(__file__), 'pydjangoapp_deployment_template.jinja2')

    mapping = {
        "name": name,
        "image": image,
        "replicas": replicas,
        "host": host,
        "port": port
    }

    if runScript is not None:
        mapping["runScript"] = runScript
    else:
        mapping["managePy"] = managePy

    with open(template_file, 'r') as f:
        template = f.read()
        tm = Template(template)
        text = tm.render(**mapping)
        print(text)
        data = yaml.safe_load(text)
        api = kubernetes.client.AppsV1Api()
        api.create_namespaced_deployment(body=data, namespace=namespace)
