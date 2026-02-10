import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Test script to validate the railway-deploy skill.

This validates Railway deployment configuration and readiness.
"""

import subprocess
import sys
import os
import json
from pathlib import Path


def check_item(description: str, condition: bool, details: str = "") -> bool:
    """Check a deployment item and display result."""
    status = "✅" if condition else "❌"
    print(f"{status} {description}")
    if details and not condition:
        print(f"   → {details}")
    return condition


def run_command(command: str) -> tuple[bool, str]:
    """Run a command and return success status with output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd="/Users/cave/enterprisehub"
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def validate_railway_config(config_path: str, service_type: str) -> dict:
    """Validate Railway configuration file."""
    results = {}

    if not Path(config_path).exists():
        return {"exists": False}

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        results["exists"] = True
        results["valid_json"] = True

        # Check required sections
        results["has_build"] = "build" in config
        results["has_deploy"] = "deploy" in config

        if "deploy" in config:
            deploy = config["deploy"]
            results["has_start_command"] = "startCommand" in deploy
            results["has_health_check"] = "healthcheckPath" in deploy
            results["has_restart_policy"] = "restartPolicyType" in deploy

            # Check health check path
            if "healthcheckPath" in deploy:
                if service_type == "fastapi":
                    results["correct_health_path"] = deploy["healthcheckPath"] == "/health"
                elif service_type == "streamlit":
                    results["correct_health_path"] = deploy["healthcheckPath"] == "/_stcore/health"
                else:
                    results["correct_health_path"] = True

            # Check start command
            if "startCommand" in deploy:
                cmd = deploy["startCommand"]
                if service_type == "fastapi":
                    results["correct_start_cmd"] = "uvicorn" in cmd and "api.main:app" in cmd
                elif service_type == "streamlit":
                    results["correct_start_cmd"] = "streamlit run" in cmd
                else:
                    results["correct_start_cmd"] = True

        return results

    except json.JSONDecodeError:
        return {"exists": True, "valid_json": False}
    except Exception:
        return {"exists": True, "valid_json": False}


def check_dockerfile(dockerfile_path: str) -> dict:
    """Check Dockerfile configuration."""
    results = {}

    if not Path(dockerfile_path).exists():
        return {"exists": False}

    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()

        results["exists"] = True
        results["has_python_base"] = "FROM python:" in content
        results["has_workdir"] = "WORKDIR" in content
        results["has_expose"] = "EXPOSE" in content
        results["has_healthcheck"] = "HEALTHCHECK" in content
        results["has_cmd"] = "CMD" in content
        results["multistage"] = "FROM python:" in content and "as builder" in content
        results["optimized_layers"] = "COPY requirements.txt" in content

        return results

    except Exception:
        return {"exists": True, "valid": False}


def main():
    """Run Railway deployment validation."""
    print("🚂 Railway Deployment Skill Validation")
    print("=" * 50)
    print("Validating Railway deployment configuration")
    print()

    passed = 0
    total = 0

    # === RAILWAY CLI CHECK ===
    print("🔧 RAILWAY CLI SETUP")
    print("-" * 25)

    total += 1
    # Check Railway CLI availability
    success, _ = run_command("which railway")
    if not success:
        success, _ = run_command("npm list -g @railway/cli")
    passed += check_item(
        "Railway CLI available",
        success,
        "Run: npm install -g @railway/cli"
    )

    # === CONFIGURATION VALIDATION ===
    print("\n⚙️ CONFIGURATION VALIDATION")
    print("-" * 35)

    # FastAPI service configuration
    total += 1
    fastapi_config = validate_railway_config(
        "/Users/cave/enterprisehub/ghl_real_estate_ai/railway.json",
        "fastapi"
    )
    passed += check_item(
        "FastAPI service has railway.json",
        fastapi_config.get("exists", False),
        "Missing railway.json in FastAPI service"
    )

    if fastapi_config.get("exists"):
        total += 1
        passed += check_item(
            "FastAPI railway.json is valid JSON",
            fastapi_config.get("valid_json", False),
            "Invalid JSON in railway.json"
        )

        total += 1
        passed += check_item(
            "FastAPI has correct health check path (/health)",
            fastapi_config.get("correct_health_path", False),
            "Health check should be '/health' for FastAPI"
        )

        total += 1
        passed += check_item(
            "FastAPI has correct start command",
            fastapi_config.get("correct_start_cmd", False),
            "Start command should use uvicorn with api.main:app"
        )

        total += 1
        passed += check_item(
            "FastAPI has restart policy",
            fastapi_config.get("has_restart_policy", False),
            "Missing restart policy configuration"
        )

    # Root Streamlit configuration
    total += 1
    streamlit_config = validate_railway_config(
        "/Users/cave/enterprisehub/railway.json",
        "streamlit"
    )
    passed += check_item(
        "Streamlit service has railway.json",
        streamlit_config.get("exists", False),
        "Missing railway.json for Streamlit service"
    )

    if streamlit_config.get("exists"):
        total += 1
        passed += check_item(
            "Streamlit has correct health check path",
            streamlit_config.get("correct_health_path", False),
            "Health check should be '/_stcore/health' for Streamlit"
        )

        total += 1
        passed += check_item(
            "Streamlit has correct start command",
            streamlit_config.get("correct_start_cmd", False),
            "Start command should use 'streamlit run'"
        )

    # === DOCKERFILE VALIDATION ===
    print("\n🐳 DOCKERFILE VALIDATION")
    print("-" * 30)

    # FastAPI Dockerfile
    total += 1
    fastapi_docker = check_dockerfile("/Users/cave/enterprisehub/ghl_real_estate_ai/Dockerfile")
    passed += check_item(
        "FastAPI service has Dockerfile",
        fastapi_docker.get("exists", False),
        "Missing Dockerfile in FastAPI service"
    )

    if fastapi_docker.get("exists"):
        total += 1
        passed += check_item(
            "FastAPI Dockerfile has Python base image",
            fastapi_docker.get("has_python_base", False),
            "Missing Python base image"
        )

        total += 1
        passed += check_item(
            "FastAPI Dockerfile has health check",
            fastapi_docker.get("has_healthcheck", False),
            "Missing HEALTHCHECK instruction"
        )

        total += 1
        passed += check_item(
            "FastAPI Dockerfile is optimized (multi-stage)",
            fastapi_docker.get("multistage", False),
            "Consider multi-stage build for smaller images"
        )

        total += 1
        passed += check_item(
            "FastAPI Dockerfile has layer optimization",
            fastapi_docker.get("optimized_layers", False),
            "Copy requirements.txt before application code for better caching"
        )

    # === ENVIRONMENT VARIABLES ===
    print("\n🔐 ENVIRONMENT CONFIGURATION")
    print("-" * 40)

    total += 1
    # Check for requirements.txt
    success, _ = run_command("test -f ghl_real_estate_ai/requirements.txt")
    passed += check_item(
        "FastAPI service has requirements.txt",
        success,
        "Missing requirements.txt for dependency management"
    )

    total += 1
    # Check for environment example
    success, _ = run_command("test -f .env.example -o -f ghl_real_estate_ai/.env.example")
    passed += check_item(
        "Environment variables documented",
        success,
        "Create .env.example to document required variables"
    )

    # === DEPLOYMENT READINESS ===
    print("\n🚀 DEPLOYMENT READINESS")
    print("-" * 30)

    total += 1
    # Check if health endpoint works
    success, _ = run_command("""
    ./.venv/bin/python -c "
import sys
sys.path.append('ghl_real_estate_ai')
try:
    from fastapi.testclient import TestClient
    from api.routes.health import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    print('SUCCESS')
except Exception as e:
    print(f'FAILED: {e}')
    sys.exit(1)
" 2>/dev/null | grep -q SUCCESS""")
    passed += check_item(
        "Health endpoint responds correctly",
        success,
        "Health endpoint not working - required for Railway health checks"
    )

    total += 1
    # Check if PORT environment variable is handled
    success, _ = run_command("grep -r 'PORT' ghl_real_estate_ai/railway.json")
    passed += check_item(
        "PORT environment variable configured",
        success,
        "Railway requires $PORT variable in start command"
    )

    total += 1
    # Check for production-ready logging
    success, _ = run_command("grep -r 'logging\\|logger' ghl_real_estate_ai/api/ | head -1")
    passed += check_item(
        "Logging configured for production",
        success,
        "Add structured logging for Railway deployment monitoring"
    )

    # === SECURITY CHECKS ===
    print("\n🛡️ SECURITY VALIDATION")
    print("-" * 25)

    total += 1
    # Check for .env in .gitignore
    success, _ = run_command("grep -q '\\.env' .gitignore")
    passed += check_item(
        "Environment files in .gitignore",
        success,
        "Add .env to .gitignore to prevent secret exposure"
    )

    total += 1
    # Check for secret management
    success, _ = run_command("grep -r 'os.getenv\\|os.environ' ghl_real_estate_ai/")
    passed += check_item(
        "Environment variables used for config",
        success,
        "Use environment variables for sensitive configuration"
    )

    # === FINAL REPORT ===
    print("\n" + "=" * 50)
    print("🎯 RAILWAY DEPLOYMENT READINESS")
    print("=" * 50)

    success_rate = (passed / total) * 100
    print(f"Validation Items Passed: {passed}/{total}")
    print(f"Deployment Readiness: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 READY TO DEPLOY - Excellent Railway configuration!")
        recommendation = "Project is ready for Railway deployment. Use 'railway up' to deploy."
        status = 0
    elif success_rate >= 80:
        print("✅ MOSTLY READY - Minor configuration needed")
        recommendation = "Address remaining items then deploy to Railway."
        status = 0
    elif success_rate >= 70:
        print("⚠️ NEEDS CONFIGURATION - Several items require attention")
        recommendation = "Complete configuration before Railway deployment."
        status = 1
    else:
        print("❌ NOT READY - Major setup needed")
        recommendation = "Significant Railway configuration work required."
        status = 1

    print(f"\nRecommendation: {recommendation}")

    # Railway deployment commands
    print("\n🚂 RAILWAY DEPLOYMENT COMMANDS:")
    print("-" * 40)
    print("""# Login to Railway
railway login

# Deploy FastAPI service
cd ghl_real_estate_ai && railway up

# Deploy Streamlit frontend
railway up --service frontend

# Monitor deployment
railway logs --follow

# Check status
railway status""")

    return status


if __name__ == "__main__":
    sys.exit(main())