import os
import kopf
import yaml
import kubernetes


@kopf.on.create('pepedocs.org', 'v1', 'pydjangoapps')
def create(spec, name, namespace, logger, **kwargs):    
    image = spec.get('image')
    replicas = spec.get('replicas')
    djangoSpec = spec.get('djangoSpec')

    if image is None:
        raise kopf.PermanentError("PyDjangoApp field 'image' must be set.")

    if djangoSpec is None:
        raise kopf.PermanentError("PyDjangoApp field 'djangoSpec must be set.")

    managePyPath = djangoSpec.get('managePyPath')
    host = djangoSpec.get('host', 'localhost')
    port = djangoSpec.get('port', 8000)

    if managePyPath is None:
        raise kopf.PermanentError("PyDjangoApp field 'managePyPath must be set.")

    path = os.path.join(os.path.dirname(__file__), 'pydjangoapp_deployment_template.yaml')

    with open(path, 'r') as f:
        template = f.read() 
        text = template.format(
            name=name, 
            image=image, 
            replicas=replicas,
            host=host,
            port=port, 
            managePyPath=managePyPath)
        data = yaml.safe_load(text)
        api = kubernetes.client.AppsV1Api()
        obj = api.create_namespaced_deployment(body=data, namespace=namespace)
    
        logger.info("PyDjangoApp created: %s" % obj)

