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

        # --- Agent Router Lambda ---
        router = _lambda.Function(
            self, "AgentRouterFn",
            function_name="AgentRouterFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="router.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": table.table_name,
                "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
                "TOOLS": '{"get_customer_metrics":"<lambda_arn1>", "summarize_metrics":"<lambda_arn2>"}'
            },
            timeout=Duration.seconds(30)
        )
        table.grant_read_write_data(router)

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
