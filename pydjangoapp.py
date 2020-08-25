import os
import kopf
import yaml
import kubernetes


@kopf.on.create('pepedocs.org', 'v1', 'pydjangoapps')
def create(spec, name, namespace, logger, **kwargs):

    image = spec.get('image')
    name = spec.get('name')
    replicas = spec.get('replicas')

    if image is None:
        raise kopf.PermanentError("PyDjangoApp field 'image' must be set.")
    
    if name is None:
        raise kopf.PermanentError("PyDjangoApp field 'name' must be set.")

    path = os.path.join(os.path.dirname(__file__), 'pydjangoapp_deployment_template.yaml')

    with open(path, 'r') as f:
        template = f.read() 
        text = template.format(name=name, image=image, replicas=replicas)
        data = yaml.safe_load(text)
        api = kubernetes.client.AppsV1Api()
        obj = api.create_namespaced_deployment(body=data, namespace=namespace)
    
        logger.info("PyDjangoApp created: %s" % obj)
