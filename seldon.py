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
                                "failureThreshold": 3,
                                "initialDelaySeconds": 10000,
                                "periodSeconds": 120,
                                "successThreshold": 1,
                                "tcpSocket": {
                                    "port": "http"
                                },
                                "timeoutSeconds": 1
                            },
                            "readinessProbe": {
                                "failureThreshold": 3,
                                "initialDelaySeconds": 10000,
                                "periodSeconds": 120,
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

    # Writing to a YAML file
    with open('kubernetes_resources.yaml', 'w') as f:
        yaml.dump(kubernetes_resources, f)

# Example usage
#generate_kubernetes_yaml("s3://mlflow/0/4435bc456bc54879a09f9518c296d4f9/artifacts/model", "test3")
