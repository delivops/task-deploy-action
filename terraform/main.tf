
# Generated Step Functions and CloudWatch Events for app
# Description: Retrieves Tableau users views data

variable "name" {
  description = "Name of the Step Function state machine"
  default     = "app"
}

variable "role_arn" {
  description = "IAM Role ARN for the Step Function"
  default     = "arn:aws:iam::123456789012:role/ecsTaskExecutionRole"
}

variable "timeout_seconds" {
  description = "Timeout for the state machine execution in seconds"
  default     = 3600
}

variable "retry_attempts" {
  description = "Maximum retry attempts for the task"
  default     = 3
}

variable "retry_interval_seconds" {
  description = "Interval between retry attempts in seconds"
  default     = 60
}

variable "retry_backoff_rate" {
  description = "Backoff rate for retries"
  default     = 2.0
}

variable "schedule_expression" {
  description = "CloudWatch Events schedule expression"
  default     = "cron(20 4,6 * * ? *)"
}

variable "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs for the ECS task"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security Group IDs for the ECS task"
  type        = list(string)
  default     = []
}

resource "aws_ecs_task_definition" "this" {
  family = "placeholder" # This is a placeholder - in reality, you would reference an existing task definition
  # The actual task definition ARN would be: 123
  # Since this is just for reference, we're creating a placeholder task definition
  
  # In a real scenario, you would not create this resource but refer to an existing one
  # This is just for demonstration purposes
  container_definitions = jsonencode([{
    name  = "placeholder"
    image = "placeholder"
  }])
  
  # Required fields for Fargate
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = var.role_arn
  task_role_arn            = var.role_arn
}

resource "aws_sfn_state_machine" "ecs_state_machine" {
  name     = var.name
  role_arn = var.role_arn
  definition = jsonencode({
    Comment        = "Retrieves Tableau users views data",
    StartAt        = "RunTask",
    TimeoutSeconds = var.timeout_seconds,
    States = {
      RunTask = {
        Type     = "Task",
        Resource = "arn:aws:states:::ecs:runTask.sync",
        Parameters = {
          LaunchType     = "FARGATE",
          Cluster        = var.ecs_cluster_arn,
          TaskDefinition = "123",  # Use the actual task ARN
          NetworkConfiguration = {
            AwsvpcConfiguration = {
              Subnets        = var.subnet_ids,
              AssignPublicIp = "ENABLED",
              SecurityGroups = var.security_group_ids
            }
          }
        },
        Retry = [{
          ErrorEquals     = ["States.TaskFailed"],
          IntervalSeconds = var.retry_interval_seconds,
          MaxAttempts     = var.retry_attempts,
          BackoffRate     = var.retry_backoff_rate
        }],
        End = true
      }
    }
  })
}

resource "aws_cloudwatch_event_rule" "schedule_rule" {
  name                = "${var.name}-schedule-rule"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "state_machine_target" {
  rule     = aws_cloudwatch_event_rule.schedule_rule.name
  arn      = aws_sfn_state_machine.ecs_state_machine.arn
  role_arn = var.role_arn
}
