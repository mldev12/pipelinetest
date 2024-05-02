import yaml

def generate_kubernetes_yaml(model_uri, run_id):
    kubernetes_resources = {
        "apiVersion": "v1",
        "kind": "List",
        "items": [
            {
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
                            "model_uri": model_uri,
                            "envSecretRefName": "seldon-init-container-secret",
                            "name": "mlflow-model"
                        },
                        "name": "default",
                        "replicas": 1,
                        "componentSpecs": [{
                            "spec": {
                                "containers": [{
                                    "name": "classifier",
                                    "image": "seldonio/mlflowserver:latest",
                                    "envFrom": [{
                                        "secretRef": {
                                            "name": "seldon-init-container-secret"
                                        }
                                    }],
                                    "livenessProbe": {
                                        "failureThreshold": 3,
                                        "initialDelaySeconds": 5000,
                                        "periodSeconds": 5,
                                        "successThreshold": 1,
                                        "tcpSocket": {
                                            "port": "http"
                                        },
                                        "timeoutSeconds": 1
                                    },
                                    "readinessProbe": {
                                        "failureThreshold": 3,
                                        "initialDelaySeconds": 5000,
                                        "periodSeconds": 5,
                                        "successThreshold": 1,
                                        "tcpSocket": {
                                            "port": "http"
                                        },
                                        "timeoutSeconds": 1
                                    }
                                }]
                            }
                        }]
                    }]
                }
            }
        ]
    }

    with open('kubernetes_resources.yaml', 'w') as f:
        yaml.dump(kubernetes_resources, f)

# Example usage
# generate_kubernetes_yaml("s3://example-model-uri", "12345")
