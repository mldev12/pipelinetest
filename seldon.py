import yaml

def generate_kubernetes_yaml(model_uri, run_id):
    kubernetes_resources = {
        "apiVersion": "v1",
        "kind": "List",
        "items": [
            {
                "apiVersion": "machinelearning.seldon.io/v1",
                "kind": "SeldonDeployment",
                "metadata": {
                    "name": run_id   # using run_id as the metadata name
                },
                "spec": {
                    "name": "income-model",
                    "predictors": [{
                        "graph": {
                            "children": [],
                            "implementation": "MLFLOW_SERVER",
                            "modelUri": model_uri,
                            "name": "mlflow-model"
                        },
                        "name": "default",
                        "replicas": 1,
                    }]
                }
            },
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": f"{run_id}-service"
                },
                "spec": {
                    "type": "ClusterIP",
                    "ports": [{"port": 80, "targetPort": 9000}],
                    "selector": {
                        "seldon-app": run_id + "-income-model-default"
                    }
                }
            },
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "Ingress",
                "metadata": {
                    "name": f"{run_id}-ingress"
                },
                "spec": {
                    "rules": [
                        {
                            "http": {
                                "paths": [
                                    {
                                        "path": "/predict",
                                        "pathType": "Prefix",
                                        "backend": {
                                            "service": {
                                                "name": f"{run_id}-service",
                                                "port": {
                                                    "number": 80
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        ]
    }

    with open('kubernetes_resources.yaml', 'w') as f:
        yaml.dump(kubernetes_resources, f)

# Example usage
generate_kubernetes_yaml(model_uri, run_id)
