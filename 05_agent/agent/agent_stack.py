import json

from aws_cdk import (
    Stack, Duration, RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as ddb,
    aws_iam as iam,
)
from constructs import Construct

class AgentSkeletonStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # DynamoDB "memory"
        table = ddb.Table(
            self, "AgentMemory",
            partition_key={"name": "session_id", "type": ddb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY
        )

        # --- Tool Lambdas ---
        get_metrics = _lambda.Function(
            self, "GetMetricsFn",
            function_name="GetMetricsFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_metrics.handler",
            code=_lambda.Code.from_asset("lambda")
        )

        summarize = _lambda.Function(
            self, "SummarizeFn",
            function_name="SummarizeFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="summarize.handler",
            code=_lambda.Code.from_asset("lambda")
        )
        
        send_alert = _lambda.Function(
            self, "SendAlertFn",
            function_name="SendAlertFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="send_alert.handler",
            code=_lambda.Code.from_asset("lambda")
        )

       # --- Agent Router Lambda ---
        router = _lambda.Function(
            self, "AgentRouterFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="router.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": table.table_name,
                "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
                "TOOLS": json.dumps({
                    "get_customer_metrics": get_metrics.function_arn,
                    "summarize_metrics": summarize.function_arn,
                    "send_alert": send_alert.function_arn
                })
            },
            timeout=Duration.seconds(30)
        )
        table.grant_read_write_data(router)
        
        get_metrics.grant_invoke(router)
        summarize.grant_invoke(router)
        send_alert.grant_invoke(router)
        

        # Bedrock invoke permission
        router.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["*"]
        ))

        # API Gateway
        api = apigw.LambdaRestApi(
            self, "AgentAPI",
            handler=router,
            proxy=False
        )
        api.root.add_resource("agent").add_method("POST")
