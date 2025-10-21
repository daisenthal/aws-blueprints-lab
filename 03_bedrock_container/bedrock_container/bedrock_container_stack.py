from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct
from utils.outputs import standard_outputs


class BedrockContainerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table
        table = dynamodb.Table(
            self, "BedrockContainerResults",
            table_name="BedrockContainerResults",
            partition_key={"name": "id", "type": dynamodb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY,
        )
        
      
        log_group = logs.LogGroup(
            self, "HealthcheckLogGroup",
            log_group_name="/aws/lambda/bedrock-container",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        fn = _lambda.DockerImageFunction(
            self, "BedrockContainerLambda",
            function_name="bedrock-container",
            code=_lambda.DockerImageCode.from_image_asset("03_bedrock_container/lambda"),
            memory_size=1024,
            timeout=Duration.seconds(60),
            environment={
                "RESULTS_TABLE": table.table_name,
                "MODEL_ID": "amazon.titan-text-lite-v1",
                "REGION": "us-east-1",
                "USE_MOCK_BEDROCK": "false",
            },
            log_group=log_group,
        )
            
    
        
       

        # Permissions
        table.grant_write_data(fn)
        fn.add_to_role_policy(
            iam.PolicyStatement(actions=["bedrock:InvokeModel"], resources=["*"])
        )

        # API Gateway
        api = apigw.LambdaRestApi(
            self, "BedrockContainerAPI",
            rest_api_name="Bedrock Container",
            handler=fn,
            proxy=False,
        )
        api.apply_removal_policy(RemovalPolicy.DESTROY)
        
        analyze = api.root.add_resource("analyze")
        analyze.add_method("POST")
        
         # ✅ Add a clean, stable output
        standard_outputs(self, api=api, lambda_fn=fn, table=table)
