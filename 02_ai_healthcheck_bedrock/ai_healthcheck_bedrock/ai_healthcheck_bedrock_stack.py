from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct
from utils.outputs import standard_outputs


class AiHealthcheckBedrockStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table
        table = dynamodb.Table(
            self, "AIHealthcheckResults",
            table_name="AIHealthcheckResults",
            partition_key={"name": "id", "type": dynamodb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        log_group = logs.LogGroup(
        self, "BedrockLogGroup",
        log_group_name="/aws/lambda/ai-healthcheck-lambda-bedrock",
        retention=logs.RetentionDays.ONE_WEEK,
        removal_policy=RemovalPolicy.DESTROY,
    )
        

        # Lambda with Bedrock access
        fn = _lambda.Function(
            self, "AIHealthcheckLambda",
            function_name="ai-healthcheck-lambda-bedrock", 
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "RESULTS_TABLE": table.table_name,
                "MODEL_ID": "amazon.titan-text-lite-v1",
                "REGION": "us-east-1",
                "USE_MOCK_BEDROCK": "false",
            },
        )
        
        fn.node.add_dependency(log_group)  # ensure log group exists first

        # Permissions
        table.grant_write_data(fn)
        fn.add_to_role_policy(
            iam.PolicyStatement(actions=["bedrock:InvokeModel"], resources=["*"])
        )

        # API Gateway
        api = apigw.LambdaRestApi(
            self, "AIHealthcheckBedrockAPI",
            rest_api_name="AI Healthcheck (Bedrock)",
            handler=fn,
            proxy=False,
        )
        api.apply_removal_policy(RemovalPolicy.DESTROY)
        
        analyze = api.root.add_resource("analyze")
        analyze.add_method("POST")
        
         # ✅ Add a clean, stable output
        standard_outputs(self, api=api, lambda_fn=fn, table=table)
