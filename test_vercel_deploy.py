#!/usr/bin/env python3
"""
Test script to validate the vercel-deploy skill.

This validates Vercel deployment setup and readiness for frontend applications.
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


def check_package_json(package_path: str) -> dict:
    """Validate package.json configuration."""
    results = {}

    if not Path(package_path).exists():
        return {"exists": False}

    try:
        with open(package_path, 'r') as f:
            pkg = json.load(f)

        results["exists"] = True
        results["valid_json"] = True

        # Check required scripts
        scripts = pkg.get("scripts", {})
        results["has_build"] = "build" in scripts
        results["has_dev"] = "dev" in scripts
        results["has_start"] = "start" in scripts

        # Check if it's a Next.js project
        deps = pkg.get("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}

        results["is_nextjs"] = "next" in all_deps
        results["is_react"] = "react" in deps
        results["is_vite"] = "vite" in all_deps

        # Check Node.js version
        engines = pkg.get("engines", {})
        results["has_node_version"] = "node" in engines

        return results

    except json.JSONDecodeError:
        return {"exists": True, "valid_json": False}
    except Exception:
        return {"exists": True, "valid_json": False}


def check_vercel_config(config_path: str) -> dict:
    """Check vercel.json configuration."""
    results = {}

    if not Path(config_path).exists():
        return {"exists": False}

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        results["exists"] = True
        results["valid_json"] = True
        results["has_builds"] = "builds" in config
        results["has_routes"] = "routes" in config
        results["has_env"] = "env" in config
        results["version_2"] = config.get("version") == 2

        return results

    except json.JSONDecodeError:
        return {"exists": True, "valid_json": False}
    except Exception:
        return {"exists": True, "valid_json": False}


def main():
    """Run Vercel deployment validation."""
    print("🚀 Vercel Deployment Skill Validation")
    print("=" * 50)
    print("Validating Vercel deployment readiness")
    print()

    passed = 0
    total = 0

    # === VERCEL CLI CHECK ===
    print("🔧 VERCEL CLI SETUP")
    print("-" * 25)

    total += 1
    # Check Vercel CLI availability
    success, _ = run_command("which vercel")
    if not success:
        success, _ = run_command("npm list -g vercel")
    passed += check_item(
        "Vercel CLI available",
        success,
        "Run: npm install -g vercel"
    )

    # === FRONTEND PROJECT ANALYSIS ===
    print("\n📱 FRONTEND PROJECT ANALYSIS")
    print("-" * 35)

    # Check for frontend directory
    total += 1
    frontend_exists = Path("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend").exists()
    passed += check_item(
        "Frontend directory exists",
        frontend_exists,
        "No dedicated frontend directory found"
    )

    if frontend_exists:
        # Validate package.json
        total += 1
        pkg_config = check_package_json("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/package.json")
        passed += check_item(
            "Frontend has package.json",
            pkg_config.get("exists", False),
            "Missing package.json in frontend directory"
        )

        if pkg_config.get("exists"):
            total += 1
            passed += check_item(
                "package.json is valid JSON",
                pkg_config.get("valid_json", False),
                "Invalid JSON in package.json"
            )

            total += 1
            passed += check_item(
                "Has build script",
                pkg_config.get("has_build", False),
                "Missing 'build' script in package.json"
            )

            total += 1
            passed += check_item(
                "Has development script",
                pkg_config.get("has_dev", False),
                "Missing 'dev' script in package.json"
            )

            total += 1
            passed += check_item(
                "React application detected",
                pkg_config.get("is_react", False),
                "No React dependency found"
            )

            total += 1
            framework_detected = pkg_config.get("is_nextjs", False) or pkg_config.get("is_vite", False)
            passed += check_item(
                "Supported framework detected (Next.js/Vite)",
                framework_detected,
                "Consider using Next.js or Vite for better Vercel integration"
            )

            total += 1
            passed += check_item(
                "Node.js version specified",
                pkg_config.get("has_node_version", False),
                "Add 'engines.node' to package.json for consistent builds"
            )

    # === VERCEL CONFIGURATION ===
    print("\n⚙️ VERCEL CONFIGURATION")
    print("-" * 30)

    total += 1
    vercel_config = check_vercel_config("/Users/cave/enterprisehub/vercel.json")
    if not vercel_config.get("exists"):
        vercel_config = check_vercel_config("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/vercel.json")

    passed += check_item(
        "Vercel configuration file exists",
        vercel_config.get("exists", False),
        "Create vercel.json for custom deployment configuration"
    )

    if vercel_config.get("exists"):
        total += 1
        passed += check_item(
            "Vercel config is valid JSON",
            vercel_config.get("valid_json", False),
            "Fix JSON syntax in vercel.json"
        )

        total += 1
        passed += check_item(
            "Uses Vercel platform version 2",
            vercel_config.get("version_2", False),
            "Update to Vercel platform version 2"
        )

    # === DEPLOYMENT ENVIRONMENT ===
    print("\n🌍 DEPLOYMENT ENVIRONMENT")
    print("-" * 35)

    total += 1
    # Check for environment configuration
    env_example_exists = (
        Path("/Users/cave/enterprisehub/.env.example").exists() or
        Path("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/.env.example").exists()
    )
    passed += check_item(
        "Environment variables documented",
        env_example_exists,
        "Create .env.example to document required environment variables"
    )

    total += 1
    # Check for .gitignore
    success, _ = run_command("grep -q '\\.env' .gitignore")
    passed += check_item(
        "Environment files in .gitignore",
        success,
        "Add .env* to .gitignore to prevent secret exposure"
    )

    total += 1
    # Check for API endpoints (serverless functions)
    api_dir_exists = (
        Path("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/api").exists() or
        Path("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/pages/api").exists()
    )
    passed += check_item(
        "API routes/serverless functions available",
        api_dir_exists,
        "Consider adding API routes for serverless functions"
    )

    # === BUILD OPTIMIZATION ===
    print("\n⚡ BUILD OPTIMIZATION")
    print("-" * 30)

    if frontend_exists:
        total += 1
        # Check for build configuration
        next_config_exists = Path("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/next.config.js").exists()
        vite_config_exists = Path("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/vite.config.js").exists()
        build_config_exists = next_config_exists or vite_config_exists

        passed += check_item(
            "Build configuration file present",
            build_config_exists,
            "Add next.config.js or vite.config.js for build optimization"
        )

        total += 1
        # Check for TypeScript
        ts_config_exists = Path("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/tsconfig.json").exists()
        passed += check_item(
            "TypeScript configuration",
            ts_config_exists,
            "Consider adding TypeScript for better development experience"
        )

        total += 1
        # Check for Tailwind CSS
        success, _ = run_command("test -f ghl_real_estate_ai/frontend/tailwind.config.js")
        passed += check_item(
            "CSS framework configured",
            success,
            "Tailwind CSS or similar framework already configured"
        )

    # === SECURITY AND PERFORMANCE ===
    print("\n🔒 SECURITY & PERFORMANCE")
    print("-" * 35)

    total += 1
    # Check for security headers
    security_config = False
    if vercel_config.get("exists"):
        try:
            config_path = "/Users/cave/enterprisehub/vercel.json"
            if not Path(config_path).exists():
                config_path = "/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/vercel.json"

            with open(config_path, 'r') as f:
                config = json.load(f)
                security_config = "headers" in config
        except:
            pass

    passed += check_item(
        "Security headers configured",
        security_config,
        "Add security headers to vercel.json for better security"
    )

    total += 1
    # Check for analytics
    analytics_configured = False
    if frontend_exists and pkg_config.get("exists"):
        try:
            with open("/Users/cave/enterprisehub/ghl_real_estate_ai/frontend/package.json", 'r') as f:
                pkg = json.load(f)
                deps = pkg.get("dependencies", {})
                analytics_configured = "@vercel/analytics" in deps
        except:
            pass

    passed += check_item(
        "Analytics integration ready",
        analytics_configured,
        "Consider adding @vercel/analytics for performance monitoring"
    )

    # === DEPLOYMENT STRATEGY ===
    print("\n🎯 DEPLOYMENT STRATEGY")
    print("-" * 30)

    total += 1
    # Check for GitHub Actions or CI/CD
    github_workflow = Path("/Users/cave/enterprisehub/.github/workflows").exists()
    passed += check_item(
        "CI/CD pipeline configured",
        github_workflow,
        "Consider adding GitHub Actions for automated deployments"
    )

    total += 1
    # Check project type compatibility
    is_suitable_for_vercel = (
        frontend_exists and
        pkg_config.get("is_react", False) and
        (pkg_config.get("is_nextjs", False) or pkg_config.get("is_vite", False))
    )
    passed += check_item(
        "Project suitable for Vercel",
        is_suitable_for_vercel,
        "Project structure is compatible with Vercel deployment"
    )

    # === FINAL ASSESSMENT ===
    print("\n" + "=" * 50)
    print("🎯 VERCEL DEPLOYMENT READINESS")
    print("=" * 50)

    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"Validation Items Passed: {passed}/{total}")
    print(f"Deployment Readiness: {success_rate:.1f}%")

    # Special assessment for this Python-heavy project
    project_type = "Python Backend with React Components"

    if success_rate >= 80:
        print("✅ GOOD VERCEL SETUP - Frontend components ready")
        recommendation = "Frontend components can be deployed to Vercel. Consider separating frontend for better optimization."
        status = 0
    elif success_rate >= 60:
        print("⚠️ PARTIAL VERCEL READINESS - Some setup needed")
        recommendation = "Complete frontend configuration for Vercel deployment."
        status = 1
    else:
        print("❌ LIMITED VERCEL COMPATIBILITY - Major setup required")
        recommendation = "This project is primarily Python backend. Consider Vercel for frontend components only."
        status = 1

    print(f"Project Type: {project_type}")
    print(f"Recommendation: {recommendation}")

    # Vercel deployment guidance
    print("\n🚀 VERCEL DEPLOYMENT GUIDANCE:")
    print("-" * 40)

    if frontend_exists:
        print("""# Deploy frontend components to Vercel
cd ghl_real_estate_ai/frontend

# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --prod

# Monitor deployment
vercel logs

# Alternative: Configure for automatic GitHub deployment
# 1. Connect GitHub repo to Vercel
# 2. Set build command: npm run build
# 3. Set output directory: dist/ or .next/""")
    else:
        print("""# This project is primarily a Python backend
# For Vercel deployment, consider:

1. Extract React components to dedicated frontend project
2. Create Next.js or Vite project structure
3. Configure API routes to connect to Python backend
4. Use Vercel for frontend, Railway for backend

# Example frontend setup:
npx create-next-app@latest ghl-frontend
# or
npm create vite@latest ghl-frontend -- --template react-ts""")

    return status


if __name__ == "__main__":
    sys.exit(main())