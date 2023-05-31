resource "aws_iam_role" "idle_resource_lambda_role" {
  name = "${var.function_name}_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "lambda_elb_policy" {
  name = "${var.function_name}_policy"
  role = aws_iam_role.idle_resource_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
         "elasticloadbalancing:DescribeLoadBalancers",
          "elasticloadbalancing:DeleteLoadBalancer",
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      },
    ]
  })
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "lambda_function.py"
  output_path = "lambda_function.zip"
}

resource "aws_lambda_function" "idle_elb_instance_function" {
  filename      = "lambda_function.zip"  # replace with your zip file
  function_name = var.function_name
  role          = aws_iam_role.idle_resource_lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  timeout       = 40

  source_code_hash = data.archive_file.lambda.output_base64sha256

  runtime = "python3.8"  # replace with your runtime
}

resource "aws_cloudwatch_log_group" "idle_elb_instance_function_lg" {
  name = "/aws/lambda/${aws_lambda_function.idle_elb_instance_function.function_name}"
  retention_in_days = 14
}

# Create Event rule
resource "aws_cloudwatch_event_rule" "lambda_idle_resource_er" {
  name                = "lambda_idle_resource_er"
  description         = "Define Specific time"
  schedule_expression = "cron(0 20 * * ? *)"
}

resource "aws_cloudwatch_event_target" "invoke_lambda" {
  rule      = aws_cloudwatch_event_rule.lambda_idle_resource_er.name
  target_id = "invoke_lambda"
  arn       = aws_lambda_function.idle_elb_instance_function.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_invoke_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.idle_elb_instance_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_idle_resource_er.arn
}
