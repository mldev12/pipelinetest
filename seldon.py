import yaml

def generate_kubernetes_yaml(model_uri, run_id):
    kubernetes_resources = {
        "apiVersion": "machinelearning.seldon.io/v1alpha2",
        "kind": "SeldonDeployment",
        "metadata": {
            "name": f"sdp-{run_id}",
            "namespace": "seldon-system"
        },
        "spec": {
            "name": "income-model",
            "predictors": [{
                "graph": {
                    "children": [],
                    "implementation": "MLFLOW_SERVER",
                    "modelUri": model_uri,
                    "envSecretRefName": "seldon-init-container-secret",
                    "name": "classifier"
                },
                "name": "default",
                "replicas": 1,
                "componentSpecs": [{
                    "spec": {
                        "containers": [{
                            "name": "classifier",
                            "image": "seldonio/mlflowserver:latest",
                            "livenessProbe": {
                                "initialDelaySeconds": 80,
                                "failureThreshold": 200,
                                "periodSeconds": 5,
                                "successThreshold": 1,
                                "httpGet": {
                                    "path": "/health/ping",
                                    "port": "http",
                                    "scheme": "HTTP"
                                }
                            },
                            "readinessProbe": {
                                "initialDelaySeconds": 80,
                                "failureThreshold": 200,
                                "periodSeconds": 5,
                                "successThreshold": 1,
                                "httpGet": {
                                    "path": "/health/ping",
                                    "port": "http",
                                    "scheme": "HTTP"
                                }
                            }
                        }]
                    }
                }]
            }]
        }
    }

    # Writing to a YAML file
    with open('kubernetes_resources.yaml', 'w') as f:
        yaml.dump(kubernetes_resources, f)

# Example usage
#generate_kubernetes_yaml("s3://mlflow/0/9728e59a56a54d4d869bc7134176cadc/artifacts/model", "test")
