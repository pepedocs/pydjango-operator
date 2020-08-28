import os
import time
import unittest
import urllib3
import subprocess as sp
import json

from kubernetes import client
from kubernetes.client.configuration import Configuration
from kubernetes.config import kube_config


DEFAULT_E2E_HOST = '127.0.0.1'


def print_json(jsn):
    print(json.dumps(jsn, indent=2))


def get_e2e_configuration():
    config = Configuration()
    config.host = None

    if os.path.exists(
            os.path.expanduser(kube_config.KUBE_CONFIG_DEFAULT_LOCATION)):
        kube_config.load_kube_config(client_configuration=config)
    else:
        print('Unable to load config from %s' %
              kube_config.KUBE_CONFIG_DEFAULT_LOCATION)
        for url in ['https://127.0.0.1:8443',
                    'http://127.0.0.1:8080']:
            try:
                urllib3.PoolManager().request('GET', url)
                config.host = url
                config.verify_ssl = False
                urllib3.disable_warnings()
                break
            except urllib3.exceptions.HTTPError:
                pass
    if config.host is None:
        raise unittest.SkipTest('Unable to find a running Kubernetes instance')
    print('Running test against : %s' % config.host)
    config.assert_hostname = False
    return config


def check_output(*args, **kwargs):
    return sp.check_output(args, kwargs).decode('ascii')


class SequentialTestLoader(unittest.TestLoader):
    def getTestCaseNames(self, testCaseClass):
        test_names = super().getTestCaseNames(testCaseClass)
        testcase_methods = list(testCaseClass.__dict__.keys())
        test_names.sort(key=testcase_methods.index)
        return test_names


class TestPyDjangoOperator(unittest.TestCase):
    """Test cases for pydjango-operator"""

    def setUp(self):
        self.tests_dir = os.path.dirname(__file__)
        self.namespace = "pydjango-operator-tests"
        self.config = get_e2e_configuration()
        k8s_client = client.api_client.ApiClient(configuration=self.config)
        core_v1 = client.CoreV1Api(api_client=k8s_client)

        # Delete and create a new namespace for every test run
        try:
            core_v1.delete_namespace(name=self.namespace)
        except client.rest.ApiException:
            pass

        retries = 10

        while retries > 0:
            try:
                body = client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=self.namespace))
                core_v1.create_namespace(body=body)
                break
            except:
                print('Waiting for the namespace %s to get deleted.' %
                      self.namespace)
                time.sleep(5)
                retries -= 1
                continue

        if retries == 0:
            self.fail('Failed to delete namespace for tests: %s' %
                      self.namespace)

    def test_create_pydjangoapp_crd(self):
        """Test that PyDjangoApp CRD can be created"""
        self.assertTrue(sp.check_call([
            'kubectl',
            'apply',
            '-f',
            'pydjangoapp.yaml',
            '-n',
            self.namespace
        ]) == 0)

    def test_create(self):
        """Test that a PyDjangoApp CR can be created"""
        ret = sp.check_call([
            'kubectl',
            'apply',
            '-f',
            'tests/recipe-api.yaml',
            '-n',
            self.namespace
        ])
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main(testLoader=SequentialTestLoader())
