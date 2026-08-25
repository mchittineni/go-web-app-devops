# Prerequisites

Install these before creating a cluster. Pin versions in CI rather than
relying on whatever is on the machine.

| Tool | Purpose | Docs |
|---|---|---|
| `kubectl` | Talk to the cluster. Keep it within one minor version of the control plane. | [Install kubectl](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html) |
| `eksctl` | Create and manage EKS clusters declaratively. | [Install eksctl](https://eksctl.io/installation/) |
| `aws` CLI v2 | Authenticate and manage AWS resources. | [Install the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| `helm` | Install this app's chart. | [Install Helm](https://helm.sh/docs/intro/install/) |

## Configure AWS credentials

Prefer short-lived credentials over long-lived access keys:

```bash
# IAM Identity Center (formerly AWS SSO) — recommended
aws configure sso
aws sso login --profile my-profile

# Verify which identity you are actually using before creating anything
aws sts get-caller-identity
```

Long-lived `aws configure` access keys still work, but they are the most
commonly leaked AWS credential. If you must use them, scope them tightly and
rotate them on a schedule.

## Verify the toolchain

```bash
kubectl version --client
eksctl version
aws --version
helm version --short
```
