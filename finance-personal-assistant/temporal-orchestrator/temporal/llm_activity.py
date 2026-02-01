import json
import boto3
from temporalio import activity
from .models import BedrockInvocationRequest


@activity.defn
async def invoke_bedrock_model(request: BedrockInvocationRequest) -> str:
    """
    Generic activity that invokes a Bedrock model with a prompt.
    
    Args:
        request: BedrockInvocationRequest containing prompt/messages, system prompt, and model configuration
        
    Returns:
        The model's response as a string
    """
    activity.logger.info(f"Invoking Bedrock model: {request.model_id}")
    
    # Initialize Bedrock runtime client
    bedrock_runtime = boto3.client('bedrock-runtime', region_name=request.region_name)
    
    # Build messages array
    if request.messages:
        # Use provided messages (conversation history)
        messages = [
            {
                "role": msg.role,
                "content": [{"type": content.type, "text": content.text} for content in msg.content]
            }
            for msg in request.messages
        ]
    elif request.prompt:
        # Use simple prompt (backward compatibility)
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": request.prompt
                    }
                ]
            }
        ]
    else:
        raise ValueError("Either 'prompt' or 'messages' must be provided")
    
    # Prepare the request body for Claude models
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": request.max_tokens,
        "messages": messages
    }
    
    # Add system prompt if provided
    if request.system_prompt:
        request_body["system"] = request.system_prompt
    
    # Add temperature if provided
    if request.temperature is not None:
        request_body["temperature"] = request.temperature
    
    try:
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=request.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # Extract the text from Claude's response
        response_text = ""
        if 'content' in response_body:
            for content_block in response_body['content']:
                if content_block.get('type') == 'text':
                    response_text += content_block.get('text', '')
        
        activity.logger.info("✅ Bedrock model invocation completed")
        return response_text
        
    except Exception as e:
        activity.logger.error(f"Error invoking Bedrock model: {str(e)}")
        raise

