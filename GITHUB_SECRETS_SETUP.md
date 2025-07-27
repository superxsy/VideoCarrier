# GitHub Secrets Setup Guide

## Important Update: Migration to Kind for Local Testing

With the integration of Kind (Kubernetes in Docker) into our CI/CD workflow, we no longer require external Kubernetes cluster secrets (KUBE_CONFIG_STAGING and KUBE_CONFIG_PRODUCTION) for deployment testing. Kind creates a temporary local Kubernetes cluster during the GitHub Actions run, eliminating the need for AWS EKS or other cloud provider configurations.

### Benefits of Using Kind
- Removes dependency on external kubeconfig secrets
- Enables consistent local testing in CI/CD
- Reduces costs and setup complexity
- Improves workflow reliability

### Kind Integration in Workflow
The `.github/workflows/youtube-downloader.yml` now includes steps to:
1. Install Kind
2. Create a local cluster
3. Deploy and test applications
4. Clean up after testing

No additional secrets are required for Kubernetes operations.

## Legacy Secrets Information (For Reference Only)

If you need to revert to cloud-based deployments, the following secrets were previously required:

### Kubernetes Configuration Secrets

#### 1. KUBE_CONFIG_STAGING
- **Purpose**: Kubernetes configuration for staging environment
- **Format**: Base64 encoded kubeconfig file content
- **Usage**: Used in `deploy-staging` job for kubectl authentication

#### 2. KUBE_CONFIG_PRODUCTION
- **Purpose**: Kubernetes configuration for production environment
- **Format**: Base64 encoded kubeconfig file content
- **Usage**: Used in `deploy-production` job for kubectl authentication

## How to Set Up Secrets (Legacy)

### Step 1: Prepare Kubeconfig Files

#### For Other Cloud Providers

1. Obtain your kubeconfig files for staging and production environments
2. Ensure the kubeconfig files have the necessary permissions for:
   - Creating/updating deployments
   - Managing services
   - Accessing namespaces

### Step 2: Encode Kubeconfig Files

```bash
# For staging
cat ~/.kube/config-staging | base64 -w 0

# For production
cat ~/.kube/config-production | base64 -w 0
```

### Step 3: Add Secrets to GitHub Repository

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:

   - **Name**: `KUBE_CONFIG_STAGING`
     **Value**: [Base64 encoded staging kubeconfig]
   
   - **Name**: `KUBE_CONFIG_PRODUCTION`
     **Value**: [Base64 encoded production kubeconfig]

## Troubleshooting (Legacy)

### Error: "Input required and not supplied: kubeconfig"

This error occurs when:
1. The required secret is not set in the repository
2. The secret name doesn't match the one referenced in the workflow
3. The secret value is empty or invalid

**Solution**:
1. Verify the secret exists in GitHub repository settings
2. Check the secret name matches exactly: `KUBE_CONFIG_STAGING` or `KUBE_CONFIG_PRODUCTION`
3. Ensure the secret value is properly base64 encoded
4. Re-run the failed workflow after fixing the secret

### Verification

After setting up the secrets, you can verify the configuration by:
1. Triggering a new deployment
2. Checking the "Configure kubectl" step in the GitHub Actions logs
3. Ensuring no authentication errors occur

## Security Best Practices

1. **Limit Permissions**: Ensure kubeconfig files have minimal required permissions
2. **Regular Rotation**: Rotate kubeconfig credentials periodically
3. **Environment Separation**: Use separate kubeconfig files for staging and production
4. **Access Control**: Limit who can view/modify repository secrets

## Related Files

- `.github/workflows/youtube-downloader.yml` - Main CI/CD workflow
- `k8s/` - Kubernetes deployment manifests