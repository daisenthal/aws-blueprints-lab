# 🧱 Day 0 – Foundation Stack (AWS CDK + Python)

## 🎯 Objective
Establish a reusable AWS CDK (Python) scaffold for all subsequent AI and data architecture blueprints.  
This serves as the “Hello World” baseline for deploying, testing, and tearing down infrastructure as code.

---

## 🧩 Components

| Layer | Service | Purpose |
|--------|----------|----------|
| **Application** | AWS Lambda (`foundation-hello-lambda`) | Minimal function responding `"Hello from Day 0 Lambda!"` |
| **IaC** | AWS CDK (Python) | Defines, synthesizes, and deploys infrastructure as code. |
| **Bootstrap** | CDKToolkit Stack | Provides S3 asset bucket, IAM roles, and SSM bootstrap versioning. |
| **Testing** | Pytest + CDK Assertions | Validates synthesized CloudFormation template (no AWS calls). |
| **Teardown** | `teardown.sh` | Standardized, non-interactive cleanup script per blueprint. |

---

## ⚙️ Deployment Flow

1. **Local Development**
   - Work within isolated `.venv` at repo root.  
   - Define stacks inside blueprint folder (e.g., `foundation/foundation_stack.py`).

2. **Synthesize**
   ```bash
   cdk synth
