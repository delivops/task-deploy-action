#!/usr/bin/env python3

import argparse
import yaml
import json
import os
from pathlib import Path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate Step Functions and CloudWatch Event Rule from YAML config')
    parser.add_argument('--config', required=True, help='Path to YAML configuration file')
    parser.add_argument('--task-arn', required=True, help='ECS Task Definition ARN')
    parser.add_argument('--output-dir', default='terraform', help='Directory to output Terraform files')
    parser.add_argument('--cluster-arn', required=True, help='ECS Cluster ARN')
    parser.add_argument('--subnet-ids', required=True, nargs='+', help='List of subnet IDs')
    parser.add_argument('--security-group-ids', required=True, nargs='+', help='List of security group IDs')
    return parser.parse_args()

def load_config(config_path):
    """Load YAML configuration file."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)

def generate_terraform(config, task_arn, output_dir, cluster_arn, subnet_ids, security_group_ids):
    """Generate Terraform files for Step Functions and CloudWatch Events."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract configuration values
    name = config.get('name', 'default-workflow')
    description = config.get('description', '')
    schedule = config.get('schedule', '')
    role_arn = config.get('role_arn', '')
    
    execution_config = config.get('execution', {})
    timeout_seconds = execution_config.get('timeoutSeconds', 3600)
    
    retry_policy = config.get('retryPolicy', {})
    max_attempts = retry_policy.get('maxAttempts', 3)
    backoff_rate = retry_policy.get('backoffRate', 2.0)
    interval_seconds = retry_policy.get('intervalSeconds', 60)
    
    # Generate Terraform file
    terraform_content = f'''
# Generated Step Functions and CloudWatch Events for {name}
# Description: {description}

variable "name" {{
  description = "Name of the Step Function state machine"
  default     = "{name}"
}}

variable "role_arn" {{
  description = "IAM Role ARN for the Step Function"
  default     = "{role_arn}"
}}

variable "timeout_seconds" {{
  description = "Timeout for the state machine execution in seconds"
  default     = {timeout_seconds}
}}

variable "retry_attempts" {{
  description = "Maximum retry attempts for the task"
  default     = {max_attempts}
}}

variable "retry_interval_seconds" {{
  description = "Interval between retry attempts in seconds"
  default     = {interval_seconds}
}}

variable "retry_backoff_rate" {{
  description = "Backoff rate for retries"
  default     = {backoff_rate}
}}

variable "schedule_expression" {{
  description = "CloudWatch Events schedule expression"
  default     = "{schedule}"
}}

variable "ecs_cluster_arn" {{
  description = "ECS Cluster ARN"
  default     = "{cluster_arn}"
}}

variable "subnet_ids" {{
  description = "Subnet IDs for the ECS task"
  type        = list(string)
  default     = {json.dumps(subnet_ids)}
}}

variable "security_group_ids" {{
  description = "Security Group IDs for the ECS task"
  type        = list(string)
  default     = {json.dumps(security_group_ids)}
}}

resource "aws_ecs_task_definition" "this" {{
  family = "placeholder" # This is a placeholder - in reality, you would reference an existing task definition
  # The actual task definition ARN would be: {task_arn}
  # Since this is just for reference, we're creating a placeholder task definition
  
  # In a real scenario, you would not create this resource but refer to an existing one
  # This is just for demonstration purposes
  container_definitions = jsonencode([{{
    name  = "placeholder"
    image = "placeholder"
  }}])
  
  # Required fields for Fargate
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = var.role_arn
  task_role_arn            = var.role_arn
}}

resource "aws_sfn_state_machine" "ecs_state_machine" {{
  name     = var.name
  role_arn = var.role_arn
  definition = jsonencode({{
    Comment        = "{description}",
    StartAt        = "RunTask",
    TimeoutSeconds = var.timeout_seconds,
    States = {{
      RunTask = {{
        Type     = "Task",
        Resource = "arn:aws:states:::ecs:runTask.sync",
        Parameters = {{
          LaunchType     = "FARGATE",
          Cluster        = var.ecs_cluster_arn,
          TaskDefinition = "{task_arn}",  # Use the actual task ARN
          NetworkConfiguration = {{
            AwsvpcConfiguration = {{
              Subnets        = var.subnet_ids,
              AssignPublicIp = "ENABLED",
              SecurityGroups = var.security_group_ids
            }}
          }}
        }},
        Retry = [{{
          ErrorEquals     = ["States.TaskFailed"],
          IntervalSeconds = var.retry_interval_seconds,
          MaxAttempts     = var.retry_attempts,
          BackoffRate     = var.retry_backoff_rate
        }}],
        End = true
      }}
    }}
  }})
}}

resource "aws_cloudwatch_event_rule" "schedule_rule" {{
  name                = "${{var.name}}-schedule-rule"
  schedule_expression = var.schedule_expression
}}

resource "aws_cloudwatch_event_target" "state_machine_target" {{
  rule     = aws_cloudwatch_event_rule.schedule_rule.name
  arn      = aws_sfn_state_machine.ecs_state_machine.arn
  role_arn = var.role_arn
}}
'''

    # Write Terraform file
    output_file = os.path.join(output_dir, 'main.tf')
    with open(output_file, 'w') as file:
        file.write(terraform_content)
    
    print(f"Successfully generated Terraform files in {output_dir}")
    print(f"Main Terraform file: {output_file}")
    
    # Also generate a SAM template.yaml file
    generate_sam_template(config, task_arn, output_dir, cluster_arn, subnet_ids, security_group_ids)

def generate_sam_template(config, task_arn, output_dir, cluster_arn, subnet_ids, security_group_ids):
    """Generate AWS SAM template.yaml file."""
    name = config.get('name', 'default-workflow')
    description = config.get('description', '')
    role_arn = config.get('role_arn', '')
    
    execution_config = config.get('execution', {})
    timeout_seconds = execution_config.get('timeoutSeconds', 3600)
    
    retry_policy = config.get('retryPolicy', {})
    max_attempts = retry_policy.get('maxAttempts', 3)
    backoff_rate = retry_policy.get('backoffRate', 2.0)
    interval_seconds = retry_policy.get('intervalSeconds', 60)
    
    schedule = config.get('schedule', '')
    
    # Create SAM template with parameters that can be overridden
    sam_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Transform": "AWS::Serverless-2016-10-31",
        "Description": description,
        "Parameters": {
            "ClusterArn": {
                "Type": "String",
                "Description": "ARN of the ECS cluster",
                "Default": cluster_arn
            },
            "SubnetIds": {
                "Type": "CommaDelimitedList",
                "Description": "List of subnet IDs for the ECS task",
                "Default": ','.join(subnet_ids)
            },
            "SecurityGroupIds": {
                "Type": "CommaDelimitedList",
                "Description": "List of security group IDs for the ECS task",
                "Default": ','.join(security_group_ids)
            },
            "TaskRoleArn": {
                "Type": "String",
                "Description": "IAM role ARN for the ECS task execution",
                "Default": role_arn
            }
        },
        "Resources": {
            "StepFunction": {
                "Type": "AWS::StepFunctions::StateMachine",
                "Properties": {
                    "StateMachineName": name,
                    "RoleArn": {"Ref": "TaskRoleArn"},
                    "Definition": {
                        "Comment": description,
                        "StartAt": "RunTask",
                        "TimeoutSeconds": timeout_seconds,
                        "States": {
                            "RunTask": {
                                "Type": "Task",
                                "Resource": "arn:aws:states:::ecs:runTask.sync",
                                "Parameters": {
                                    "LaunchType": "FARGATE",
                                    "Cluster": {"Ref": "ClusterArn"},
                                    "TaskDefinition": task_arn,
                                    "NetworkConfiguration": {
                                        "AwsvpcConfiguration": {
                                            "Subnets": {"Ref": "SubnetIds"},
                                            "AssignPublicIp": "ENABLED",
                                            "SecurityGroups": {"Ref": "SecurityGroupIds"}
                                        }
                                    }
                                },
                                "Retry": [{
                                    "ErrorEquals": ["States.TaskFailed"],
                                    "IntervalSeconds": interval_seconds,
                                    "MaxAttempts": max_attempts,
                                    "BackoffRate": backoff_rate
                                }],
                                "End": True
                            }
                        }
                    }
                }
            },
            "ScheduleRule": {
                "Type": "AWS::Events::Rule",
                "Properties": {
                    "Name": f"{name}-schedule-rule",
                    "ScheduleExpression": schedule,
                    "Targets": [{
                        "Id": "StepFunctionTarget",
                        "Arn": {"Fn::GetAtt": ["StepFunction", "Arn"]},
                        "RoleArn": {"Ref": "TaskRoleArn"}
                    }]
                }
            }
        },
        "Outputs": {
            "StateMachineArn": {
                "Description": "ARN of the created Step Function",
                "Value": {"Fn::GetAtt": ["StepFunction", "Arn"]}
            }
        }
    }
    
    # Write SAM template
    sam_output_file = os.path.join(output_dir, 'template.yaml')
    with open(sam_output_file, 'w') as file:
        yaml.dump(sam_template, file, default_flow_style=False)
    
    print(f"Successfully generated SAM template: {sam_output_file}")

def main():
    args = parse_arguments()
    config = load_config(args.config)
    generate_terraform(config, args.task_arn, args.output_dir, args.cluster_arn, args.subnet_ids, args.security_group_ids)
    print("Done! Files are ready for deployment.")

if __name__ == "__main__":
    main()