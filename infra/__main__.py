import pulumi
from pulumi_azure_native import containerservice, network, resources

# Load Pulumi configuration
config = pulumi.Config()
azure_config = pulumi.Config("azure-native")

location = config.require("location")
resource_group_name = config.require("resourceGroupName")
dev_vm_size = config.require("devNodePoolVMSize")
staging_vm_size = config.require("stagingNodePoolVMSize")
prod_vm_size = config.require("prodNodePoolVMSize")
node_count_dev = config.require_int("nodeCountDev")
min_count_dev = config.require_int("minCountDev")
max_count_dev = config.require_int("maxCountDev")
node_count_staging = config.require_int("nodeCountStaging")
min_count_staging = config.require_int("minCountStaging")
max_count_staging = config.require_int("maxCountStaging")
node_count_prod = config.require_int("nodeCountProd")
min_count_prod = config.require_int("minCountProd")
max_count_prod = config.require_int("maxCountProd")
vnet_cidr = config.require("vnetCidr")
system_subnet_cidr = config.require("systemSubnetCidr")
dev_subnet_cidr = config.require("devSubnetCidr")
staging_subnet_cidr = config.require("stagingSubnetCidr")
prod_subnet_cidr = config.require("prodSubnetCidr")

# Create an Azure Resource Group
resource_group = resources.ResourceGroup(
    resource_name=resource_group_name,
    resource_group_name=resource_group_name,
    location=location,
)

# Create a Virtual Network for the AKS cluster
vnet = network.VirtualNetwork(
    resource_name="aksVNet",
    resource_group_name=resource_group.name,
    address_space=network.AddressSpaceArgs(
        address_prefixes=[vnet_cidr]
    )
)

# Create Subnets for each environment
system_subnet = network.Subnet(
    resource_name="systemSubnet",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix=system_subnet_cidr)

dev_subnet = network.Subnet(
    resource_name="devSubnet",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix=dev_subnet_cidr)

staging_subnet = network.Subnet(
    resource_name="stagingSubnet",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix=staging_subnet_cidr)

prod_subnet = network.Subnet(
    resource_name="prodSubnet",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix=prod_subnet_cidr)


# Define the AKS cluster with a default node pool
aks_cluster = containerservice.ManagedCluster(
    resource_name="aksCluster",
    resource_group_name=resource_group.name,
    location=location,
    agent_pool_profiles=[
        containerservice.ManagedClusterAgentPoolProfileArgs(
            name="systempool",
            count=1,
            max_pods=110,
            vnet_subnet_id=system_subnet.id,
            mode=containerservice.AgentPoolMode.SYSTEM,
            vm_size="Standard_D4s_v3",
            os_sku=containerservice.OSSKU.UBUNTU,
            enable_auto_scaling=True,
            max_count=1,
            min_count=1,
            node_taints=["CriticalAddonsOnly=true:NoExecute"]
        ),
    ],
    dns_prefix="AKS-Cluster-CWY",
    network_profile={
        "network_plugin": "azure",
        "dns_service_ip": "10.0.10.10",
        "service_cidr": "10.0.10.0/24",
        "docker_bridge_cidr": "172.17.0.1/16",
    },
    service_principal_profile=containerservice.ManagedClusterServicePrincipalProfileArgs(
       client_id=azure_config.require("clientId"),
       secret=azure_config.require_secret("clientSecret"),
    ),
)

# Node Pool for Development
dev_node_pool = containerservice.AgentPool(
    "devpool",
    resource_group_name=resource_group.name,
    resource_name_=aks_cluster.name,
    vm_size=dev_vm_size,
    os_sku=containerservice.OSSKU.UBUNTU,
    mode=containerservice.AgentPoolMode.USER,
    enable_auto_scaling=True,
    count=node_count_dev,
    min_count=min_count_dev,
    max_count=max_count_dev,
    agent_pool_name="devpool",
    vnet_subnet_id=dev_subnet.id,  # Use the development subnet
    node_labels = {"environment": "dev"},
    node_taints = [f"environment=dev:NoExecute"],
)

# Node Pool for Staging
staging_node_pool = containerservice.AgentPool(
    "stagingpool",
    resource_group_name=resource_group.name,
    resource_name_=aks_cluster.name,
    vm_size=staging_vm_size,
    os_sku=containerservice.OSSKU.UBUNTU,
    mode=containerservice.AgentPoolMode.USER,
    enable_auto_scaling=True,
    count=node_count_staging,
    min_count=min_count_staging,
    max_count=max_count_staging,
    agent_pool_name="stagingpool",
    vnet_subnet_id=staging_subnet.id,  # Use the development subnet
    node_labels = {"environment": "staging"},
    node_taints = [f"environment=staging:NoExecute"],
)

# Node Pool for Production
prod_node_pool = containerservice.AgentPool(
    "prodpool",
    resource_group_name=resource_group.name,
    resource_name_=aks_cluster.name,
    vm_size=prod_vm_size,
    os_sku=containerservice.OSSKU.UBUNTU,
    mode=containerservice.AgentPoolMode.USER,
    enable_auto_scaling=True,
    count=node_count_prod,
    min_count=min_count_prod,
    max_count=max_count_prod,
    agent_pool_name="prodpool",
    vnet_subnet_id=prod_subnet.id,  # Use the development subnet
    node_labels = {"environment": "prod"},
    node_taints = [f"environment=prod:NoExecute"],
)

# Export the kubeconfig for the cluster
#pulumi.export("kubeconfig", aks_cluster.)
