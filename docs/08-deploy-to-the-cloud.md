# Part 08 · Deploy to a real cloud cluster

!!! danger "This part costs real money"

    An AWS EKS cluster bills roughly **$0.10 per hour for the control plane
    alone**, plus compute and load balancers — around **$75–150 per month** if
    you leave it running.

    Everything up to Part 07 was free. Do this part in one sitting and delete
    the cluster when you finish. Set a billing alert first.

Nothing conceptually new happens here. The same Helm chart, on someone else's
computers.

You need an AWS account and two more tools:

```bash title="terminal — anywhere"
brew install awscli eksctl
aws configure sso        # preferred: short-lived credentials
aws sts get-caller-identity
```

That last command tells you *which identity you are about to create things as*.
Run it before anything that costs money.

## Create the cluster

```bash title="terminal — anywhere"
eksctl create cluster \
  --name demo-cluster \
  --region us-east-1 \
  --version 1.32 \
  --fargate \
  --with-oidc
```

This takes **15–20 minutes**. It is building a real network, a control plane and
IAM roles. Go and get a coffee — but do not close the terminal.

`--fargate` means AWS manages the servers, so you never patch a node.
`--with-oidc` lets pods get narrowly scoped AWS permissions later instead of
sharing one broad role.

## Point kubectl at it and deploy

```bash title="terminal — in the project folder"
aws eks update-kubeconfig --name demo-cluster --region us-east-1
kubectl get nodes

helm upgrade --install go-web-app ./helm/go-web-app-chart \
  --set image.repository=YOUR_DOCKERHUB_USERNAME/go-web-app \
  --set image.tag=latest \
  --atomic --timeout 5m
```

Notice this is the *same command as [Part 06](06-package-with-helm.md)*. That is
the payoff of packaging with Helm: your laptop and AWS take identical
instructions.

## Expose it to the internet

Install an ingress controller — the thing that actually accepts public traffic:

```bash title="terminal — anywhere"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.15.1/deploy/static/provider/aws/deploy.yaml

kubectl wait --namespace ingress-nginx \
  --for=condition=Ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=180s

kubectl get svc -n ingress-nginx ingress-nginx-controller
```

The `EXTERNAL-IP` column will show an AWS load balancer address. Point a DNS
record at it, or test with the hostname the chart expects.

## Delete the cluster when you are done

This is the step people forget and then get a surprise bill for.

```bash title="terminal — when finished"
helm uninstall go-web-app
eksctl delete cluster --name demo-cluster --region us-east-1 --wait
```

Then check nothing was orphaned — load balancers and disks can outlive a failed
delete and keep charging:

```bash title="terminal — after deleting"
aws elbv2 describe-load-balancers --region us-east-1 \
  --query 'LoadBalancers[].LoadBalancerName'
aws ec2 describe-volumes --region us-east-1 \
  --filters Name=status,Values=available --query 'Volumes[].VolumeId'
```

Both should return an empty list `[]`.

!!! success "Checkpoint"

    - The site was reachable through a public address.
    - The cluster is deleted and both AWS queries return `[]`.
