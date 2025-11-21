provider "aws" {
  region = "us-west-2"
}

resource "aws_s3_bucket" "model_train_bucket" {
  bucket = "model-train-control-system-bucket"
  acl    = "private"
}

resource "aws_lambda_function" "central_api" {
  function_name = "central_api"
  handler       = "app.main"
  runtime       = "python3.8"
  s3_bucket     = aws_s3_bucket.model_train_bucket.bucket
  s3_key        = "central_api.zip"
  environment = {
    MQTT_BROKER_URL = "mqtt://your-broker-url"
  }
}

resource "aws_lambda_function" "pi_controller" {
  function_name = "pi_controller"
  handler       = "app.main"
  runtime       = "python3.8"
  s3_bucket     = aws_s3_bucket.model_train_bucket.bucket
  s3_key        = "pi_controller.zip"
}

resource "aws_api_gateway_rest_api" "api" {
  name        = "Model Train Control API"
  description = "API for controlling model trains"
}

resource "aws_api_gateway_resource" "trains" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "trains"
}

resource "aws_api_gateway_method" "get_trains" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.trains.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "post_command" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.trains.id
  http_method   = "POST"
  authorization = "NONE"
}

output "api_endpoint" {
  value = "${aws_api_gateway_rest_api.api.execution_arn}/trains"
}
