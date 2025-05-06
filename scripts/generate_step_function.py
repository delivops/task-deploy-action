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
    return parser.parse_args()

def load_config(config_path):
    """Load YAML configuration file."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)


def generate_sam_template(config, task_arn):
    """Generate AWS SAM template.yaml file."""
    name = config.get('name', 'default-workflow')
    description = config.get('description', '')
    
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
                "Default": ''
            },
            "SubnetIds": {
                "Type": "CommaDelimitedList",
                "Description": "List of subnet IDs for the ECS task",
                "Default": ','
            },
            "SecurityGroupIds": {
                "Type": "CommaDelimitedList",
                "Description": "List of security group IDs for the ECS task",
                "Default": ','
            },
            "TaskRoleArn": {
                "Type": "String",
                "Description": "IAM role ARN for the ECS task execution",
                "Default": ''
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
    sam_output_file = 'template.yaml'
    with open(sam_output_file, 'w') as file:
        yaml.dump(sam_template, file, default_flow_style=False)
    print(f"Successfully generated SAM template: {sam_output_file}")


def main():
    args = parse_arguments()
    config = load_config(args.config)

    generate_sam_template(config, args.task_arn)
    print("Done! Files are ready for deployment.")

if __name__ == "__main__":
    main()