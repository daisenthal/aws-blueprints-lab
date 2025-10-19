from aws_cdk import (
    # Duration,
    Stack,
    aws_lambda as _lambda,
)
from constructs import Construct

class FoundationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        _lambda.Function(
            self, "HelloHandler",
            function_name="foundation-hello-lambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda"),
        )
