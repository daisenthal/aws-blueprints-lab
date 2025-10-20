from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cp_actions,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


class BlueprintPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, repo_owner, repo_name, branch="main", **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for artifacts
        artifact_bucket = s3.Bucket(
            self, "PipelineArtifacts",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=False,
        )

        # Source output artifact
        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        # Source stage (GitHub)
        source_action = cp_actions.CodeStarConnectionsSourceAction(
            action_name="GitHub_Source",
            owner=repo_owner,
            repo=repo_name,
            branch=branch,
            connection_arn="arn:aws:codeconnections:us-east-1:946486897374:connection/06727ba5-1a58-4cf7-89dd-ad6c8cc5c2bb",
            output=source_output,
        )

        # Build project (CodeBuild)
        build_project = codebuild.PipelineProject(
            self, "BlueprintBuild",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=True,
            ),
        )

        # Allow CodeBuild to deploy CDK
        build_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sts:AssumeRole",
                    "cloudformation:*",
                    "s3:*",
                    "lambda:*",
                    "apigateway:*",
                    "dynamodb:*",
                    "bedrock:*",
                ],
                resources=["*"],
            )
        )

        # Pipeline definition
        pipeline = codepipeline.Pipeline(
            self, "BlueprintPipeline",
            pipeline_name="AIHealthcheckPipeline",
            artifact_bucket=artifact_bucket,
            restart_execution_on_update=True,
        )

        pipeline.add_stage(stage_name="Source", actions=[source_action])
        pipeline.add_stage(
            stage_name="Build",
            actions=[
                cp_actions.CodeBuildAction(
                    action_name="Build_and_Deploy",
                    project=build_project,
                    input=source_output,
                    outputs=[build_output],
                )
            ],
        )
