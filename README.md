# K8sFlowGen

K8sFlowGen is a Kubernetes resource flowchart generator that visualizes the relationships between various Kubernetes objects in a cluster. It creates a comprehensive diagram showing how different components interact, including Deployments, Services, Ingress resources, HTTPProxies, Certificates, SealedSecrets, ConfigMaps, and PersistentVolumeClaims.

## Features

- **Visual Representation**: Generates flowcharts that illustrate the relationships between Kubernetes resources.
- **Resource Details**: Displays important information such as container images, port configurations, and resource limits.
- **Grouped Resources**: Organizes resources by type (e.g., Deployments, Services) in separate subgraphs for clarity.
- **Connection Mapping**: Shows connections between resources, such as Services selecting Deployments or Ingress routing to Services.

## Installation

You can install K8sFlowGen using pip:

```bash
pip install k8sflowgen
```
Ensure that you have Graphviz installed on your system as well. You can download it from Graphviz's official website.
Usage
After installation, you can use K8sFlowGen from the command line:
bash
k8sflowgen -f your_kubernetes_file.yaml -o output_flowchart

## Sample

