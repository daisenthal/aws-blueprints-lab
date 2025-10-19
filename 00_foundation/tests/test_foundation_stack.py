import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # adds foundation/ to path

import aws_cdk as core
import aws_cdk.assertions as assertions
from foundation.foundation_stack import FoundationStack



def test_lambda_created():
    app = core.App()
    stack = FoundationStack(app, "TestStack")
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::Lambda::Function", 1)
