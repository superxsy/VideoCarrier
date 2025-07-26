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

#### For AWS EKS Clusters

1. **Install AWS CLI and kubectl**:
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   
   # Install kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```

2. **Configure AWS credentials**:
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, region, and output format
   ```

3. **Update kubeconfig for your EKS cluster**:
   ```bash
   # For staging environment
   aws eks update-kubeconfig --region <your-region> --name <staging-cluster-name> --kubeconfig ~/.kube/config-staging
   
   # For production environment
   aws eks update-kubeconfig --region <your-region> --name <production-cluster-name> --kubeconfig ~/.kube/config-production
   ```

4. **Verify cluster access**:
   ```bash
   # Test staging
   kubectl --kubeconfig ~/.kube/config-staging get nodes
   
   # Test production
   kubectl --kubeconfig ~/.kube/config-production get nodes
   ```

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

## AWS EKS Specific Configuration

### Required IAM Permissions

Your AWS user/role needs the following permissions for EKS cluster access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "eks:DescribeCluster",
                "eks:ListClusters"
            ],
            "Resource": "*"
        }
    ]
}
```

### EKS Cluster Authentication

1. **Add your user to the EKS cluster's aws-auth ConfigMap**:
   ```bash
   kubectl edit configmap aws-auth -n kube-system
   ```

2. **Add your user mapping**:
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: aws-auth
     namespace: kube-system
   data:
     mapUsers: |
       - userarn: arn:aws:iam::ACCOUNT-ID:user/USERNAME
         username: USERNAME
         groups:
           - system:masters
   ```

### Getting Cluster Information from AWS Console

From your AWS EKS console screenshot, you can find:
- **Cluster Name**: The name shown in the cluster list (e.g., "i-06ec244f7a26bb61")
- **Region**: Visible in the AWS console URL or cluster details
- **API Server Endpoint**: In the cluster configuration tab

### Example: Using Your EKS Cluster

Based on your AWS console, here's how to get the kubeconfig:

```bash
# Replace with your actual values
CLUSTER_NAME="i-06ec244f7a26bb61"  # From your console
REGION="your-region"  # e.g., us-west-2, us-east-1

# Generate kubeconfig for staging (if this is your staging cluster)
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME --kubeconfig ~/.kube/config-staging

# Or for production (if this is your production cluster)
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME --kubeconfig ~/.kube/config-production

# Verify the connection
kubectl --kubeconfig ~/.kube/config-staging get nodes
```

**Note**: Make sure to:
1. Replace `your-region` with your actual AWS region
2. Ensure your AWS credentials have access to this EKS cluster
3. Verify the cluster is in "Active" status before attempting to connect

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

### AWS EKS Specific Issues

#### Error: "You must be logged in to the server (Unauthorized)"
- **Cause**: AWS credentials not configured or insufficient permissions
- **Solution**: 
  1. Run `aws sts get-caller-identity` to verify AWS credentials
  2. Ensure your user has EKS cluster access permissions
  3. Check if your user is added to the cluster's aws-auth ConfigMap

#### Error: "The connection to the server was refused"
- **Cause**: Incorrect cluster endpoint or network issues
- **Solution**:
  1. Verify cluster name and region are correct
  2. Check if the cluster is running and accessible
  3. Ensure your network can reach the EKS API endpoint

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