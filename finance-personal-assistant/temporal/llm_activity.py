"""Bedrock text formatting Activity for the finance Workflow."""

import os

import boto3
from temporalio import activity

from .models import BedrockInvocationRequest


@activity.defn
def invoke_bedrock_model(request: BedrockInvocationRequest) -> str:
    """Format a report with Bedrock's Converse API."""
    region = request.region_name or os.environ.get("AWS_REGION", "us-west-2")
    activity.logger.info("Invoking Bedrock model %s in %s", request.model_id, region)

    if request.messages:
        messages = []
        for message in request.messages:
            if any(block.type != "text" for block in message.content):
                raise ValueError("Only text message content is supported")
            messages.append({
                "role": message.role,
                "content": [{"text": block.text} for block in message.content],
            })
    elif request.prompt:
        messages = [{"role": "user", "content": [{"text": request.prompt}]}]
    else:
        raise ValueError("Either 'prompt' or 'messages' must be provided")

    inference_config = {"maxTokens": request.max_tokens}
    if request.temperature is not None:
        inference_config["temperature"] = request.temperature
    arguments = {
        "modelId": request.model_id,
        "messages": messages,
        "inferenceConfig": inference_config,
    }
    if request.system_prompt:
        arguments["system"] = [{"text": request.system_prompt}]

    response = boto3.client("bedrock-runtime", region_name=region).converse(**arguments)
    blocks = response["output"]["message"]["content"]
    result = "".join(block["text"] for block in blocks if "text" in block)
    if not result:
        raise RuntimeError("Bedrock returned no text content")
    activity.logger.info("Bedrock model invocation completed")
    return result
