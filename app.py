#!/usr/bin/env python3
import aws_cdk as cdk
from cdk_pipeline_stack import BlueprintPipelineStack

app = cdk.App()


# Pipeline for automation
BlueprintPipelineStack(
    app,
    "BlueprintPipelineStack",
    repo_owner="daisenthal",
    repo_name="aws-blueprints",
    branch="main",
)

app.synth()