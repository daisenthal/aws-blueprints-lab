#!/usr/bin/env python3
import os

import aws_cdk as cdk

import sys, os
from pathlib import Path

# Add repo root (parent of current folder) to sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_root))

from ai_healthcheck_api.ai_healthcheck_api_stack import AiHealthcheckApiStack


app = cdk.App()
AiHealthcheckApiStack(app, "AiHealthcheckApiStack",
    )

app.synth()
