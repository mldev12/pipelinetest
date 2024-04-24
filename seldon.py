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
                    "name": run_id,  # No change needed here if SeldonDeployment supports UUID as name directly
                    "namespace": "seldon-system"
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
                    "name": f"svc-{run_id}",
                    "namespace": "seldon-system"
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
                    "name": f"ing-{run_id}",
                    "namespace": "seldon-system"
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
                                                "name": f"svc-{run_id}",
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
