# Manual Azure checkpoint: Blob Storage

Local mock mode requires no Azure resources. Before real media storage integration, create the following manually. No Azure service is currently configured or connected.

## Why
Blob Storage will store uploaded video/image files for the real extraction pipeline. Start with storage only; Content Understanding regional availability, AI Search and Foundry will be configured in later checkpoints.

## Settings
1. In Azure Portal select your authorized subscription and create/select a project resource group.
2. Create a Storage account, choosing your own globally unique name and an allowed region. Use Standard performance, general-purpose v2 (StorageV2), LRS redundancy, and Hot access tier for the demonstration.
3. Require secure transfer, minimum TLS 1.2, and disable blob anonymous access. Leave hierarchical namespace, SFTP and NFS disabled.
4. For local development, allow selected networks and add your current client public IP if university policy permits. If private endpoints are mandatory, report that constraint before continuing.
5. Under Data storage → Containers, create a container with a name you choose and Private access (no anonymous access).
6. Assign your development identity Storage Blob Data Contributor at the container scope using Access control (IAM). Ask your administrator if role assignment is unavailable. Portal navigation using Entra credentials also requires at least Reader at the account scope; existing broader management permission can satisfy that part.

These are proposed MVP settings, not existing configuration. Review Azure costs before creation. We will use local Microsoft Entra sign-in rather than embedded storage keys.

## Reply after creation
Say “done” with only the storage account name, actual Blob service endpoint copied from the portal, container name, region, resource group, and confirmation of data-role/network configuration. Do not send keys, connection strings, SAS tokens or passwords.

Next we will implement and test an actual upload/read before marking Blob Storage connected. If setup fails, report the error rather than guessing values.

## Official references
- [Create a storage account](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-create)
- [Prevent anonymous blob access](https://learn.microsoft.com/en-us/azure/storage/blobs/anonymous-read-access-prevent)
- [Assign blob data access roles](https://learn.microsoft.com/en-us/azure/storage/blobs/assign-azure-role-data-access)
