from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as ddb,
)
from constructs import Construct
from utils.outputs import standard_outputs

class AiHealthcheckApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        table = ddb.Table(
            self, "AIHealthcheckResults",
            table_name="AIHealthcheckResults",
            partition_key={"name": "id", "type": ddb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY,  # optional for dev
        )

        fn = _lambda.Function(
            self, "AIHealthcheckLambda",
            function_name="ai-healthcheck-lambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={"RESULTS_TABLE": table.table_name},
        )

        table.grant_write_data(fn)

        api = apigw.LambdaRestApi(
            self, "AIHealthcheckAPI",
            rest_api_name="AI Healthcheck Service",
            handler=fn,
            proxy=False
        )

        analyze = api.root.add_resource("analyze")
        analyze.add_method("POST")  # POST /analyze
        
         # ✅ Add a clean, stable output
        standard_outputs(self, api=api, lambda_fn=fn, table=table)
