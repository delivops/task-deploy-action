# Task Deploy Action

This project provides a workflow for deploying ECS tasks using an AWS SAM template. It includes utilities to generate a SAM template from a simple YAML configuration and deploy ECS tasks in a streamlined, reproducible way.

## Features

- Generates AWS SAM templates for ECS Step Functions from user-friendly YAML configs
- Deploys ECS tasks using the AWS SAM template
- Supports custom task definition ARNs and workflow parameters
- Integrates with GitHub Actions or can be run manually
- Simplifies and automates the ECS task deployment process

## Usage

### 1. Prepare Your Configuration

- Write your workflow configuration in YAML (e.g., `examples/sam.yaml`).
- Prepare a `samconfig` file with your environment-specific values (e.g., cluster ARN, subnet IDs, security group IDs).

### 2. Generate the SAM Template

Use the provided script to generate a SAM template:

```bash
python3 scripts/generate_step_function.py \
  --config examples/sam.yaml \
  --task-arn <YOUR_TASK_DEFINITION_ARN> \
  --samconfig <PATH_TO_SAMCONFIG>
```

This will generate a `template.yaml` file in the output directory (default: `terraform/`).

### 3. Deploy the SAM Template

You can deploy the generated `template.yaml` using the AWS SAM CLI:

```bash
sam deploy --template-file terraform/template.yaml --guided
```

Or integrate this process into your CI/CD pipeline.

## Example Workflow (GitHub Actions)

```yaml
name: Deploy ECS Task
on:
  push:
    branches:
      - main
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate SAM Template
        run: |
          python3 scripts/generate_step_function.py \
            --config examples/sam.yaml \
            --task-arn ${{ secrets.ECS_TASK_ARN }} \
            --samconfig samconfig.yaml
      - name: Deploy to AWS
        run: |
          sam deploy --template-file terraform/template.yaml --no-confirm-changeset --no-fail-on-empty-changeset --stack-name my-ecs-task-stack
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: us-east-1
```

## Notes
- Ensure your `samconfig` file contains the necessary ECS and networking parameters.
- The script and template support customization for your ECS workloads.
- See the scripts and examples for more advanced usage.

      # Build and tag your image here  
      
      - name: Deploy to ECS
        uses: delivops/ecs-deploy-action@main
        with:
          environment: production
          ecs_service: my-service
          image_name: my-app
          tag: ${{ github.sha }}
          task_config_yaml: apps/my-service/.aws/production.yaml
          ecs_cluster: ${{ vars.ECS_CLUSTER }}
          aws_region: ${{ vars.AWS_REGION }}
          aws_account_id: ${{ secrets.AWS_ACCOUNT_ID }}
```

## YAML Configuration Format

Create a YAML configuration file with the following structure:

```yaml
name: my_app                    # Application name
cpu: 1024                       # CPU units
memory: 8192                    # Memory in MB
include_otel_collector: true    # Include OpenTelemetry collector sidecar

# cpu_arch: X86_64                # Optional: CPU architecture (default: X86_64)
# otel_collector_ssm_config: otel-config.yaml  # Optional: Custom OTEL config name on SSM

role_arn: arn:aws:iam::123456789:role/appTaskRole

# Environment variables
env:
  - KEY1: value1
  - KEY2: value2

# Secrets from AWS Secrets Manager
secrets:
  - SECRET_NAME: arn:aws:secretsmanager:region:account:secret:path
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `ecs_service` | The name of the ECS service | Yes | |
| `image_name` | The name of the Docker image | Yes | |
| `tag` | The tag of the Docker image | Yes | |
| `task_config_yaml` | Path to the YAML configuration file | Yes | |
| `aws_account_id` | The AWS account ID | Yes | |
| `aws_region` | The AWS region | Yes | |
| `ecs_cluster` | The name of the ECS cluster | Yes | |
| `aws_role` | The AWS IAM role to assume | No | `github_services` |

## Important Note on AWS Credentials

This action includes steps to configure AWS credentials and interact with ECR and ECS. In most GitHub Actions workflows, it's best practice to configure AWS credentials at the workflow level rather than within each action to avoid credential scope issues and provide better security control.

## How It Works

1. The action reads your YAML configuration file
2. Generates a proper ECS task definition JSON
3. Injects your Docker image with the specified tag
4. Deploys the task definition to your ECS service
5. Verifies that the deployment succeeded

## Development

If you need to modify the task definition generation, edit the Python script at `scripts/generate_task_def.py`. The script uses argparse for clear parameter parsing and validation.