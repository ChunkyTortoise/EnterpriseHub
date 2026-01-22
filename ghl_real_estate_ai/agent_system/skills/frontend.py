"""
Frontend Engineering Skills.
Enables agents to generate UI components, dashboards, and visualizations.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import skill
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

import subprocess
import signal
import time

UI_ROOT = Path("enterprise-ui")
_PREVIEW_PROCESS = None

@skill(name="manage_preview", tags=["frontend", "preview", "dev-server"])
def manage_preview(action: str = "start", port: int = 3001) -> str:
    """
    Manages the Next.js development server for UI previews.
    
    Args:
        action: 'start', 'stop', or 'status'
        port: The port to run the server on
        
    Returns:
        Status message.
    """
    global _PREVIEW_PROCESS
    
    if action == "start":
        if _PREVIEW_PROCESS and _PREVIEW_PROCESS.poll() is None:
            return f"Preview server already running at http://localhost:{port}"
        
        try:
            # Start Next.js dev server in background
            _PREVIEW_PROCESS = subprocess.Popen(
                ["npm", "run", "dev", "--", "-p", str(port)],
                cwd=UI_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            # Give it a moment to start
            time.sleep(2)
            return f"Preview server started at http://localhost:{port}"
        except Exception as e:
            return f"Failed to start preview server: {e}"
            
    elif action == "stop":
        if _PREVIEW_PROCESS:
            os.killpg(os.getpgid(_PREVIEW_PROCESS.pid), signal.SIGTERM)
            _PREVIEW_PROCESS = None
            return "Preview server stopped."
        return "Preview server not running."
        
    elif action == "status":
        if _PREVIEW_PROCESS and _PREVIEW_PROCESS.poll() is None:
            return f"Preview server running (PID: {_PREVIEW_PROCESS.pid})"
        return "Preview server not running."
    
    return "Invalid action. Use 'start', 'stop', or 'status'."

@skill(name="capture_preview_screenshot", tags=["frontend", "testing", "visual"])
def capture_preview_screenshot(path: str = "/", output_filename: str = "preview.png") -> str:
    """
    Captures a screenshot of the running preview server.
    
    Args:
        path: The route to capture (e.g., '/dashboard')
        output_filename: Name of the file to save (in public/screenshots)
        
    Returns:
        Path to the saved screenshot or error message.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "Playwright not installed. Cannot capture screenshot."

    target_url = f"http://localhost:3001{path}"
    screenshot_dir = UI_ROOT / "public" / "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    output_path = screenshot_dir / output_filename

    try:
        with sync_playwright() as p:
            # Launch browser (headless)
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Navigate and wait for network idle to ensure hydration
            page.goto(target_url, wait_until="networkidle")
            
            # Take screenshot
            page.screenshot(path=str(output_path), full_page=True)
            browser.close()
            
        logger.info(f"Screenshot captured: {output_path}")
        return str(output_path)
    except Exception as e:
        error_msg = f"Failed to capture screenshot: {e}"
        logger.error(error_msg)
        return error_msg

@skill(name="generate_ui_component", tags=["frontend", "ui", "react"])
def generate_ui_component(component_name: str, jsx_code: str, sub_dir: str = "components") -> str:
    """
    Generates a React/Next.js component in the enterprise-ui directory.
    
    Args:
        component_name: Name of the component (e.g., 'KpiCard')
        jsx_code: The full JSX/TSX code for the component
        sub_dir: Sub-directory within src/ (e.g., 'components', 'app')
        
    Returns:
        The relative path to the generated file.
    """
    target_dir = UI_ROOT / "src" / sub_dir
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = target_dir / f"{component_name}.tsx"
    
    try:
        with open(file_path, "w") as f:
            f.write(jsx_code)
        logger.info(f"Generated UI component: {file_path}")
        return str(file_path.relative_to(UI_ROOT))
    except Exception as e:
        error_msg = f"Failed to generate UI component {component_name}: {e}"
        logger.error(error_msg)
        return error_msg

@skill(name="build_dashboard_page", tags=["frontend", "dashboard", "nextjs"])
def build_dashboard_page(page_name: str, components: List[str], layout_type: str = "grid") -> str:
    """
    Constructs a dashboard page by assembling multiple generated components.
    
    Args:
        page_name: Name of the page (e.g., 'executive-metrics')
        components: List of component names to include
        layout_type: The layout pattern to use ('grid', 'flex', 'sidebar')
        
    Returns:
        The relative path to the generated page.
    """
    target_dir = UI_ROOT / "src" / "app" / page_name
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = target_dir / "page.tsx"
    
    # Simple template for a dashboard page
    imports = "\n".join([f"import {{{c}}} from '@/components/{c}';" for c in components])
    
    component_calls = "\n          ".join([f"<{c} />" for c in components])
    
    content = f"""
import React from 'react';
{imports}

export default function {page_name.capitalize().replace('-', '')}Page() {{
  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold tracking-tight">{page_name.replace('-', ' ').capitalize()}</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {component_calls}
      </div>
    </div>
  );
}}
"""
    
    try:
        with open(file_path, "w") as f:
            f.write(content)
        logger.info(f"Built dashboard page: {file_path}")
        return str(file_path.relative_to(UI_ROOT))
    except Exception as e:
        error_msg = f"Failed to build dashboard page {page_name}: {e}"
        logger.error(error_msg)
        return error_msg

@skill(name="inject_visualization", tags=["frontend", "viz", "charts"])
def inject_visualization(component_name: str, data_source: str, chart_type: str = "bar") -> str:
    """
    Creates a Tremor or Recharts visualization component.
    
    Args:
        component_name: Name of the chart component
        data_source: Description or URL of the data source
        chart_type: Type of chart ('bar', 'line', 'area', 'donut')
        
    Returns:
        The generated JSX code for the visualization.
    """
    # This is a mock implementation that returns a template.
    # In a real scenario, the agent would use this to get a base and then refine it.
    
    templates = {
        "bar": f"""
import {{ Card, Title, BarChart, Text }} from "@tremor/react";

const data = [
  {{ name: "Topic A", value: 400 }},
  {{ name: "Topic B", value: 300 }},
  {{ name: "Topic C", value: 200 }},
];

export const {component_name} = () => (
  <Card>
    <Title>{component_name}</Title>
    <Text>Data source: {data_source}</Text>
    <BarChart
      className="mt-6"
      data={{data}}
      index="name"
      categories={{["value"]}}
      colors={{["blue"]}}
    />
  </Card>
);
""",
        "kpi": f"""
import {{ Card, Metric, Text, Flex, BadgeDelta }} from "@tremor/react";

export const {component_name} = () => (
  <Card className="max-w-xs mx-auto">
    <Text>{component_name}</Text>
    <Flex justifyContent="start" alignItems="baseline" className="space-x-3 truncate">
      <Metric>$ 34,743</Metric>
      <Text>from $ 31,223</Text>
    </Flex>
    <Flex justifyContent="start" className="mt-4 space-x-2">
      <BadgeDelta deltaType="moderateIncrease" />
      <Text className="truncate">12.3% increase</Text>
    </Flex>
  </Card>
);
"""
    }
    
    return templates.get(chart_type, templates["bar"])
