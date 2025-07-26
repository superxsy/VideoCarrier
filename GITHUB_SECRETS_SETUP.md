# GitHub Secrets Setup Guide

## Required Secrets for CI/CD Pipeline

The YouTube Downloader CI/CD pipeline requires the following GitHub repository secrets to be configured:

### Kubernetes Configuration Secrets

#### 1. KUBE_CONFIG_STAGING
- **Purpose**: Kubernetes configuration for staging environment
- **Format**: Base64 encoded kubeconfig file content
- **Usage**: Used in `deploy-staging` job for kubectl authentication

#### 2. KUBE_CONFIG_PRODUCTION
- **Purpose**: Kubernetes configuration for production environment
- **Format**: Base64 encoded kubeconfig file content
- **Usage**: Used in `deploy-production` job for kubectl authentication

## How to Set Up Secrets

### Step 1: Prepare Kubeconfig Files

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

## Troubleshooting

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