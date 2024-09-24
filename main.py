import yaml
import graphviz
import click

def parse_yaml(file_path):
    with open(file_path, 'r') as file:
        return list(yaml.safe_load_all(file))

def create_flowchart(yaml_data):
    dot = graphviz.Digraph(comment='Kubernetes Resource Flowchart', engine='dot')
    dot.attr(rankdir='LR', size='40,40', dpi='300', fontname='Helvetica', fontsize='12')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Helvetica', fontsize='12', margin='0.3,0.1')
    dot.attr('edge', fontname='Helvetica', fontsize='10')

    colors = {
        'Deployment': '#E6F3FF', 'Service': '#FFE6E6', 'ConfigMap': '#E6FFE6', 
        'Secret': '#FFE6FF', 'PersistentVolumeClaim': '#FFFFE6', 'Container': '#F0F0F0',
        'Ingress': '#FFF0E0', 'HTTPProxy': '#E0FFF0', 'Certificate': '#FFE0FF',
        'SealedSecret': '#E0E0FF'
    }
    
    deployments = {}
    services = {}
    secrets = {}
    ingresses = {}
    httpproxies = {}
    certificates = {}
    sealed_secrets = {}

    for resource in yaml_data:
        kind = resource.get('kind', 'Unknown')
        name = resource.get('metadata', {}).get('name', 'Unnamed')
        namespace = resource.get('metadata', {}).get('namespace', 'default')
        node_id = f"{kind}_{namespace}_{name}"
        
        color = colors.get(kind, '#FFFFFF')
        
        if kind == 'Deployment':
            label = f"{kind}\\n{name}"
            dot.node(node_id, label, fillcolor=color)
            deployments[node_id] = resource

            containers = resource.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
            for i, container in enumerate(containers):
                container_name = container.get('name', f'container-{i}')
                container_id = f"{node_id}_Container_{container_name}"
                image = container.get('image', 'unknown')
                
                dot.node(container_id, f"Container: {container_name}\\nImage: {image}", fillcolor=colors['Container'])
                dot.edge(node_id, container_id, "runs")
                
                ports = container.get('ports', [])
                if ports:
                    port_id = f"{container_id}_Ports"
                    port_info = '\\n'.join([f"{p.get('containerPort', 'unknown')}/{p.get('protocol', 'TCP')}" for p in ports])
                    dot.node(port_id, f"Ports:\\n{port_info}", shape='note', fillcolor='#D9E6F2')
                    dot.edge(container_id, port_id, "exposes")

                container_resources = container.get('resources', {})
                limits = container_resources.get('limits', {})
                requests = container_resources.get('requests', {})
                cpu_limit = limits.get('cpu', 'undefined')
                memory_limit = limits.get('memory', 'undefined')
                cpu_request = requests.get('cpu', 'undefined')
                memory_request = requests.get('memory', 'undefined')

                resources_id = f"{container_id}_Resources"
                resources_label = f"Resources\\nRequests: {cpu_request} CPU, {memory_request} Memory\\n" \
                                  f"Limits: {cpu_limit} CPU, {memory_limit} Memory"
                dot.node(resources_id, resources_label, shape='note', fillcolor='#F0F0F0')
                dot.edge(container_id, resources_id, "has")

                for volume_mount in container.get('volumeMounts', []):
                    mount_name = volume_mount.get('name', 'unnamed-mount')
                    mount_path = volume_mount.get('mountPath', 'unknown-path')
                    mount_id = f"{container_id}_Mount_{mount_name}"
                    dot.node(mount_id, f"Mount\\n{mount_name}\\n{mount_path}", shape='folder', fillcolor='#F0F0F0')
                    dot.edge(container_id, mount_id, "mounts")

                env_vars = container.get('env', [])
                for env in env_vars:
                    env_name = env.get('name', 'unnamed-env')
                    env_id = f"{container_id}_Env_{env_name}"
                    if 'value' in env:
                        env_value = env['value']
                        dot.node(env_id, f"Env\\n{env_name}={env_value}", shape='plaintext')
                    elif 'valueFrom' in env:
                        if 'configMapKeyRef' in env['valueFrom']:
                            cm_name = env['valueFrom']['configMapKeyRef'].get('name', 'unnamed-cm')
                            cm_key = env['valueFrom']['configMapKeyRef'].get('key', 'unnamed-key')
                            dot.node(env_id, f"Env\\n{env_name}\\nfrom ConfigMap\\n{cm_name}.{cm_key}", shape='plaintext')
                            dot.edge(env_id, f"ConfigMap_{namespace}_{cm_name}", "references", style='dotted')
                        elif 'secretKeyRef' in env['valueFrom']:
                            secret_name = env['valueFrom']['secretKeyRef'].get('name', 'unnamed-secret')
                            secret_key = env['valueFrom']['secretKeyRef'].get('key', 'unnamed-key')
                            dot.node(env_id, f"Env\\n{env_name}\\nfrom Secret\\n{secret_name}.{secret_key}", shape='plaintext')
                            dot.edge(env_id, f"Secret_{namespace}_{secret_name}", "references", style='dotted')
                            secrets[secret_name] = resource
                        else:
                            dot.node(env_id, f"Env\\n{env_name}\\nfrom Other Source", shape='plaintext')
                    else:
                        dot.node(env_id, f"Env\\n{env_name}", shape='plaintext')
                    dot.edge(container_id, env_id, "env", style='dashed')

            labels = resource.get('spec', {}).get('selector', {}).get('matchLabels', {})
            for key, value in labels.items():
                label_id = f"Label_{namespace}_{key}_{value}"
                dot.node(label_id, f"Label\\n{key}={value}", shape='ellipse', fillcolor='#FFFFD9')
                dot.edge(node_id, label_id, "selects", style='dashed')
            
            template = resource.get('spec', {}).get('template', {})
            volumes = template.get('spec', {}).get('volumes', [])
            
            for volume in volumes:
                vol_name = volume.get('name', 'unnamed-volume')
                if 'persistentVolumeClaim' in volume:
                    pvc_name = volume['persistentVolumeClaim'].get('claimName', 'unnamed-pvc')
                    pvc_size = "unknown"
                    for res in yaml_data:
                        if res.get('kind') == 'PersistentVolumeClaim' and res['metadata']['name'] == pvc_name:
                            pvc_size = res.get('spec', {}).get('resources', {}).get('requests', {}).get('storage', 'unknown')
                            break
                    pvc_id = f"PVC_{namespace}_{pvc_name}"
                    dot.node(pvc_id, f"PVC\\n{pvc_name}\\nSize: {pvc_size}", fillcolor=colors['PersistentVolumeClaim'])
                    dot.edge(node_id, pvc_id, "uses")
                elif 'configMap' in volume:
                    cm_name = volume['configMap'].get('name', 'unnamed-configmap')
                    cm_id = f"ConfigMap_{namespace}_{cm_name}"
                    dot.node(cm_id, f"ConfigMap\\n{cm_name}", fillcolor=colors['ConfigMap'])
                    dot.edge(node_id, cm_id, "uses")
                elif 'secret' in volume:
                    secret_name = volume['secret'].get('secretName', 'unnamed-secret')
                    secret_id = f"Secret_{namespace}_{secret_name}"
                    dot.node(secret_id, f"Secret\\n{secret_name}", fillcolor=colors['Secret'])
                    dot.edge(node_id, secret_id, "uses")
        
        elif kind == 'Service':
            ports = resource.get('spec', {}).get('ports', [])
            port_info = ', '.join([f"{p.get('port', 'unknown')}/{p.get('protocol', 'TCP')}" for p in ports])
            label = f"{kind}\\n{name}\\nPorts: {port_info}"
            dot.node(node_id, label, fillcolor=color)
            services[node_id] = resource
            selector = resource.get('spec', {}).get('selector', {})
            for key, value in selector.items():
                selector_id = f"Selector_{namespace}_{key}_{value}"
                dot.node(selector_id, f"Selector\\n{key}={value}", shape='diamond', fillcolor='#D9FFFF')
                dot.edge(node_id, selector_id, style='dashed')
        
        elif kind == 'Ingress':
            dot.node(node_id, f"Ingress\\n{name}", fillcolor=color)
            ingresses[node_id] = resource
            
            for rule in resource.get('spec', {}).get('rules', []):
                for path in rule.get('http', {}).get('paths', []):
                    service_name = path.get('backend', {}).get('serviceName')
                    if service_name:
                        service_id = f"Service_{namespace}_{service_name}"
                        dot.edge(node_id, service_id, "routes to")
            
            for tls in resource.get('spec', {}).get('tls', []):
                secret_name = tls.get('secretName')
                if secret_name:
                    secret_id = f"Secret_{namespace}_{secret_name}"
                    dot.edge(node_id, secret_id, "uses TLS")
        
        elif kind == 'HTTPProxy':
            dot.node(node_id, f"HTTPProxy\\n{name}", fillcolor=color)
            httpproxies[node_id] = resource
            
            for route in resource.get('spec', {}).get('routes', []):
                for service in route.get('services', []):
                    service_name = service.get('name')
                    if service_name:
                        service_id = f"Service_{namespace}_{service_name}"
                        dot.edge(node_id, service_id, "routes to")
            
            tls = resource.get('spec', {}).get('virtualhost', {}).get('tls', {})
            secret_name = tls.get('secretName')
            if secret_name:
                secret_id = f"Secret_{namespace}_{secret_name}"
                dot.edge(node_id, secret_id, "uses TLS")
        
        elif kind == 'Certificate':
            dot.node(node_id, f"Certificate\\n{name}", fillcolor=color)
            certificates[node_id] = resource
            
            secret_name = resource.get('spec', {}).get('secretName')
            if secret_name:
                secret_id = f"Secret_{namespace}_{secret_name}"
                dot.edge(node_id, secret_id, "creates")
        
        elif kind == 'SealedSecret':
            dot.node(node_id, f"SealedSecret\\n{name}", fillcolor=color)
            sealed_secrets[node_id] = resource
            
            secret_name = name  # Assuming SealedSecret creates a Secret with the same name
            secret_id = f"Secret_{namespace}_{secret_name}"
            dot.edge(node_id, secret_id, "unseals to", style='dashed')
        
        elif kind == 'Secret':
            dot.node(node_id, f"Secret\\n{name}", fillcolor=color)
            secrets[node_id] = resource
        
        else:
            dot.node(node_id, f"{kind}\\n{name}", fillcolor=color)

    # Link Services to Deployments based on selectors
    for svc_id, service in services.items():
        svc_selector = service.get("spec", {}).get("selector", {})
        for dep_id, deployment in deployments.items():
            dep_labels = deployment.get("spec", {}).get("template", {}).get("metadata", {}).get("labels", {})
            if all(dep_labels.get(k) == v for k, v in svc_selector.items()):
                dot.edge(svc_id, dep_id, "selects", color='#007ACC', penwidth='2')

    return dot

@click.command()
@click.option('--yaml_file', '-f', required=True, type=click.Path(exists=True), help='Path to the YAML file')
@click.option('--output', '-o', default='k8s_flowchart', help='Output file name (without extension)')
def k8sflowgen(yaml_file, output):
    """Generate a flowchart from a Kubernetes YAML file."""
    yaml_data = parse_yaml(yaml_file)
    dot = create_flowchart(yaml_data)
    dot.render(output, format='pdf', cleanup=True)
    click.echo(f"Flowchart generated: {output}.pdf")

if __name__ == '__main__':
    k8sflowgen()
