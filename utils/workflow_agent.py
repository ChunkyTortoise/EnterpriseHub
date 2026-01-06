"""
Workflow Agent - Dynamic Workflow Architecture Generator
Uses AI-powered logic to convert user process descriptions into structured automation nodes.
"""
from typing import List, Dict, Any
import re

class WorkflowAgent:
    """
    Generates workflow automation architectures from natural language descriptions.
    Uses pattern matching and keyword analysis to identify automation components.
    """
    
    # Trigger patterns
    TRIGGER_PATTERNS = {
        'email': ['email', 'gmail', 'outlook', 'inbox', 'message'],
        'form': ['form', 'submission', 'typeform', 'google form', 'jotform'],
        'webhook': ['webhook', 'api call', 'http', 'post request'],
        'schedule': ['daily', 'weekly', 'monthly', 'scheduled', 'every morning', 'cron'],
        'database': ['new row', 'database', 'airtable', 'spreadsheet', 'google sheets'],
        'social': ['tweet', 'facebook', 'instagram', 'linkedin post', 'social media'],
        'payment': ['stripe', 'payment', 'purchase', 'transaction', 'paypal']
    }
    
    # Processing patterns
    PROCESSING_PATTERNS = {
        'data_extraction': ['extract', 'parse', 'read', 'scan', 'ocr', 'pdf'],
        'ai_analysis': ['analyze', 'classify', 'summarize', 'generate', 'ai', 'gpt', 'claude'],
        'validation': ['validate', 'check', 'verify', 'confirm', 'ensure'],
        'transformation': ['transform', 'convert', 'format', 'map', 'restructure'],
        'enrichment': ['enrich', 'lookup', 'fetch', 'augment', 'append data'],
        'calculation': ['calculate', 'compute', 'sum', 'total', 'math']
    }
    
    # Action patterns
    ACTION_PATTERNS = {
        'storage': ['save', 'store', 'upload', 'google drive', 'dropbox', 's3', 'cloud storage'],
        'database_write': ['update', 'insert', 'write to', 'add to database', 'crm'],
        'notification': ['notify', 'alert', 'slack', 'email', 'sms', 'send message'],
        'api_call': ['api', 'integrate', 'connect to', 'post to', 'update in'],
        'document': ['create document', 'generate pdf', 'create report', 'export'],
        'approval': ['approve', 'review', 'human approval', 'manual check']
    }
    
    # Tool/Service recommendations
    TOOL_RECOMMENDATIONS = {
        'email': 'Gmail/Outlook API',
        'form': 'Webhook Integration',
        'data_extraction': 'Claude 3.5 Vision',
        'ai_analysis': 'Claude 3.5 Sonnet',
        'storage': 'Cloud Storage API (S3/GCS)',
        'database_write': 'API Integration',
        'notification': 'Slack/Email/SMS Gateway',
        'document': 'Document Generation API',
        'validation': 'Custom Logic Node',
        'calculation': 'JavaScript/Python Node'
    }
    
    def __init__(self):
        pass
    
    def analyze_process(self, process_description: str) -> Dict[str, Any]:
        """
        Analyzes a process description and returns structured workflow data.
        
        Args:
            process_description: Natural language description of manual process
            
        Returns:
            Dict containing nodes, estimated complexity, and recommendations
        """
        process_lower = process_description.lower()
        
        # Identify components
        trigger = self._identify_trigger(process_lower)
        processing_steps = self._identify_processing(process_lower)
        actions = self._identify_actions(process_lower)
        
        # Build nodes
        nodes = self._build_node_structure(trigger, processing_steps, actions)
        
        # Calculate estimates
        complexity = self._estimate_complexity(nodes)
        time_estimate = self._estimate_build_time(complexity, len(nodes))
        efficiency_gain = self._estimate_efficiency(process_lower, len(nodes))
        
        return {
            'nodes': nodes,
            'complexity': complexity,
            'build_time_hours': time_estimate,
            'efficiency_gain_percent': efficiency_gain,
            'total_nodes': len(nodes),
            'recommendations': self._generate_recommendations(nodes)
        }
    
    def _identify_trigger(self, text: str) -> str:
        """Identifies the trigger type from text."""
        for trigger_type, keywords in self.TRIGGER_PATTERNS.items():
            if any(keyword in text for keyword in keywords):
                return trigger_type
        return 'webhook'  # Default fallback
    
    def _identify_processing(self, text: str) -> List[str]:
        """Identifies processing steps from text."""
        steps = []
        for step_type, keywords in self.PROCESSING_PATTERNS.items():
            if any(keyword in text for keyword in keywords):
                steps.append(step_type)
        return steps if steps else ['ai_analysis']  # Default
    
    def _identify_actions(self, text: str) -> List[str]:
        """Identifies action steps from text."""
        actions = []
        for action_type, keywords in self.ACTION_PATTERNS.items():
            if any(keyword in text for keyword in keywords):
                actions.append(action_type)
        return actions if actions else ['notification']  # Default
    
    def _build_node_structure(self, trigger: str, processing: List[str], actions: List[str]) -> List[Dict[str, str]]:
        """Builds the complete node structure."""
        nodes = []
        
        # Trigger node
        nodes.append({
            'type': 'trigger',
            'label': self._get_node_label('trigger', trigger),
            'tool': self.TOOL_RECOMMENDATIONS.get(trigger, 'Webhook'),
            'description': f'Listens for {trigger} events'
        })
        
        # Processing nodes
        for i, step in enumerate(processing, 1):
            nodes.append({
                'type': 'processing',
                'label': self._get_node_label('processing', step),
                'tool': self.TOOL_RECOMMENDATIONS.get(step, 'Custom Logic'),
                'description': f'Performs {step.replace("_", " ")}'
            })
        
        # Action nodes
        for action in actions:
            nodes.append({
                'type': 'action',
                'label': self._get_node_label('action', action),
                'tool': self.TOOL_RECOMMENDATIONS.get(action, 'API Integration'),
                'description': f'Executes {action.replace("_", " ")}'
            })
        
        # Always add a success notification
        if not any(n['type'] == 'notification' for n in nodes):
            nodes.append({
                'type': 'notification',
                'label': 'Success Confirmation',
                'tool': 'Slack/Email',
                'description': 'Confirms workflow completion'
            })
        
        return nodes
    
    def _get_node_label(self, category: str, node_type: str) -> str:
        """Generates human-readable label for node."""
        labels = {
            'trigger': {
                'email': 'Email Listener',
                'form': 'Form Submission',
                'webhook': 'Webhook/API',
                'schedule': 'Scheduled Trigger',
                'database': 'Database Watch',
                'social': 'Social Media Monitor',
                'payment': 'Payment Event'
            },
            'processing': {
                'data_extraction': 'Data Extraction (AI Vision)',
                'ai_analysis': 'AI Analysis & Classification',
                'validation': 'Data Validation',
                'transformation': 'Data Transformation',
                'enrichment': 'Data Enrichment',
                'calculation': 'Business Logic'
            },
            'action': {
                'storage': 'Cloud Storage',
                'database_write': 'Database Update',
                'notification': 'Notification',
                'api_call': 'External API Call',
                'document': 'Document Generation',
                'approval': 'Human Approval Gate'
            }
        }
        return labels.get(category, {}).get(node_type, node_type.replace('_', ' ').title())
    
    def _estimate_complexity(self, nodes: List[Dict]) -> str:
        """Estimates workflow complexity."""
        node_count = len(nodes)
        has_ai = any('AI' in n['label'] for n in nodes)
        has_approval = any('approval' in n['type'].lower() for n in nodes)
        
        if node_count <= 3 and not has_ai:
            return 'Simple'
        elif node_count <= 5 or (node_count <= 4 and has_ai):
            return 'Moderate'
        elif node_count <= 7 or has_approval:
            return 'Complex'
        else:
            return 'Advanced'
    
    def _estimate_build_time(self, complexity: str, node_count: int) -> str:
        """Estimates build time range."""
        base_hours = {
            'Simple': (2, 4),
            'Moderate': (4, 8),
            'Complex': (8, 16),
            'Advanced': (16, 32)
        }
        hours = base_hours.get(complexity, (8, 12))
        return f"{hours[0]}-{hours[1]}"
    
    def _estimate_efficiency(self, text: str, node_count: int) -> int:
        """Estimates efficiency gain percentage."""
        # Base efficiency from automation depth
        base_efficiency = min(95, 60 + (node_count * 5))
        
        # Boost for AI components
        if 'ai' in text or 'analyze' in text or 'classify' in text:
            base_efficiency = min(98, base_efficiency + 10)
        
        # Boost for manual elimination
        if 'manual' in text or 'manually' in text:
            base_efficiency = min(99, base_efficiency + 15)
        
        return base_efficiency
    
    def _generate_recommendations(self, nodes: List[Dict]) -> List[str]:
        """Generates implementation recommendations."""
        recommendations = []
        
        # Check for AI nodes
        if any('AI' in n['label'] for n in nodes):
            recommendations.append("Consider using Claude 3.5 Sonnet for advanced reasoning tasks")
        
        # Check for data extraction
        if any('extraction' in n['description'].lower() for n in nodes):
            recommendations.append("Use Claude Vision API for OCR and document parsing")
        
        # Check for notifications
        if any('notification' in n['type'].lower() for n in nodes):
            recommendations.append("Implement error handling and retry logic for notifications")
        
        # Check for external APIs
        if any('api' in n['tool'].lower() for n in nodes):
            recommendations.append("Add rate limiting and timeout handling for external API calls")
        
        # General recommendations
        if len(nodes) > 5:
            recommendations.append("Consider breaking this into sub-workflows for better maintainability")
        
        recommendations.append("Implement comprehensive logging for debugging and audit trails")
        recommendations.append("Set up monitoring alerts for workflow failures")
        
        return recommendations

def generate_workflow_visualization_html(nodes: List[Dict[str, str]]) -> str:
    """
    Generates HTML visualization of workflow nodes with arrows.
    
    Args:
        nodes: List of node dictionaries
        
    Returns:
        HTML string with styled workflow diagram
    """
    html = "<div style='font-family: system-ui;'>"
    
    for i, node in enumerate(nodes):
        # Determine color based on type
        colors = {
            'trigger': {'bg': '#EEF2FF', 'border': '#6366F1', 'icon': '▶️'},
            'processing': {'bg': '#FEF3C7', 'border': '#F59E0B', 'icon': '⚙️'},
            'action': {'bg': '#D1FAE5', 'border': '#10B981', 'icon': '✓'},
            'notification': {'bg': '#E0E7FF', 'border': '#6366F1', 'icon': '🔔'}
        }
        
        color_scheme = colors.get(node['type'], colors['processing'])
        
        # Node card
        html += f"""
        <div style='
            background: {color_scheme['bg']}; 
            padding: 16px; 
            border-radius: 12px; 
            margin: 12px 0; 
            border-left: 5px solid {color_scheme['border']};
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        '>
            <div style='display: flex; align-items: center; gap: 12px;'>
                <span style='font-size: 1.5rem;'>{color_scheme['icon']}</span>
                <div style='flex: 1;'>
                    <div style='font-weight: 700; font-size: 1rem; color: #1e293b;'>
                        {node['label']}
                    </div>
                    <div style='font-size: 0.85rem; color: #64748b; margin-top: 4px;'>
                        {node['description']}
                    </div>
                    <div style='
                        display: inline-block;
                        margin-top: 8px;
                        padding: 4px 12px;
                        background: white;
                        border-radius: 6px;
                        font-size: 0.75rem;
                        font-weight: 600;
                        color: {color_scheme['border']};
                    '>
                        🔧 {node['tool']}
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Arrow connector (except for last node)
        if i < len(nodes) - 1:
            html += """
            <div style='text-align: center; margin: 8px 0;'>
                <span style='font-size: 1.5rem; color: #94A3B8;'>⬇️</span>
            </div>
            """
    
    html += "</div>"
    return html
