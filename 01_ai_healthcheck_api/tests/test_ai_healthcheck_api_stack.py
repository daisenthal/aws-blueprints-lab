import sys, os
from pathlib import Path

# Get repo root and current blueprint dir
current_dir = Path(__file__).resolve().parent
blueprint_dir = current_dir.parent
repo_root = blueprint_dir.parent

# Add both blueprint folder and repo root to sys.path
sys.path.append(str(blueprint_dir))
sys.path.append(str(repo_root))

import aws_cdk as core
import aws_cdk.assertions as assertions

from ai_healthcheck_api.ai_healthcheck_api_stack import AiHealthcheckApiStack

def test_resources_created():
    app = core.App()
    stack = AiHealthcheckApiStack(app, "TestAIHealthcheckApiStack")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 1)
    template.resource_count_is("AWS::DynamoDB::Table", 1)
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)
    
    
    

