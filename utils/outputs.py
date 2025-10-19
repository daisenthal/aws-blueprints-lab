from aws_cdk import CfnOutput

def standard_outputs(stack, api=None, lambda_fn=None, table=None, repo=None):
    """
    Creates standardized CloudFormation outputs for CDK stacks.
    Each parameter is optional; only defined resources are exported.
    """
    if api:
        CfnOutput(
            stack,
            "APIEndpoint",
            value=api.url,
            export_name=f"{stack.stack_name}-APIEndpoint"
        )

    if lambda_fn:
        CfnOutput(
            stack,
            "LambdaArn",
            value=lambda_fn.function_arn,
            export_name=f"{stack.stack_name}-LambdaArn"
        )

    if table:
        CfnOutput(
            stack,
            "TableName",
            value=table.table_name,
            export_name=f"{stack.stack_name}-TableName"
        )

    if repo:
        CfnOutput(
            stack,
            "EcrRepositoryUri",
            value=repo.repository_uri,
            export_name=f"{stack.stack_name}-EcrRepositoryUri"
        )
