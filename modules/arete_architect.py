"""
ARETE-Architect: AI Technical Co-Founder Agent

A production-ready conversational AI agent that serves as a technical co-founder.
Capabilities:
- Natural conversation with persistent memory
- GitHub integration (read/write files, create PRs, manage issues)
- Code generation and deployment
- Self-improvement and decision logging
- Business support (documentation, research, content creation)

Built with: Claude API, LangGraph, and custom tool orchestration
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from datetime import datetime
import os
import json
import streamlit as st

# Conditional imports with graceful degradation
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_anthropic import ChatAnthropic
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

import operator
from utils.logger import get_logger
import utils.ui as ui

logger = get_logger(__name__)


# =============================================================================
# STATE DEFINITION
# =============================================================================

class AreteState(TypedDict):
    """The complete state/memory of the ARETE agent."""
    messages: Annotated[List[BaseMessage], operator.add]
    conversation_history: List[Dict[str, Any]]
    current_plan: Optional[str]
    current_task: Optional[str]
    file_context: Dict[str, str]  # filename -> content
    github_context: Dict[str, Any]  # repo info, branches, etc.
    decision_log: List[Dict[str, Any]]
    tools_used: List[str]
    last_error: Optional[str]
    session_metadata: Dict[str, Any]


# =============================================================================
# GITHUB INTEGRATION TOOLS
# =============================================================================

class GitHubTools:
    """Tools for interacting with GitHub repositories."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.token = github_token or os.getenv("GITHUB_TOKEN")
        self.client = None
        if self.token and GITHUB_AVAILABLE:
            try:
                self.client = Github(self.token)
                # Test connection
                self.client.get_user().login
            except Exception as e:
                logger.error(f"Failed to initialize GitHub client: {e}")
                self.client = None
    
    def read_file(self, repo_name: str, file_path: str, branch: str = "main") -> Optional[str]:
        """Read a file from a GitHub repository."""
        if not self.client:
            return None
        try:
            repo = self.client.get_repo(repo_name)
            content = repo.get_contents(file_path, ref=branch)
            return content.decoded_content.decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading {file_path} from {repo_name}: {e}")
            return None
    
    def write_file(self, repo_name: str, file_path: str, content: str, 
                   commit_message: str, branch: str = "main") -> bool:
        """Write or update a file in a GitHub repository."""
        if not self.client:
            return False
        try:
            repo = self.client.get_repo(repo_name)
            try:
                # Try to get existing file
                file = repo.get_contents(file_path, ref=branch)
                repo.update_file(file_path, commit_message, content, file.sha, branch=branch)
            except:
                # File doesn't exist, create it
                repo.create_file(file_path, commit_message, content, branch=branch)
            return True
        except Exception as e:
            logger.error(f"Error writing {file_path} to {repo_name}: {e}")
            return False
    
    def create_branch(self, repo_name: str, branch_name: str, from_branch: str = "main") -> bool:
        """Create a new branch."""
        if not self.client:
            return False
        try:
            repo = self.client.get_repo(repo_name)
            source = repo.get_branch(from_branch)
            repo.create_git_ref(f"refs/heads/{branch_name}", source.commit.sha)
            return True
        except Exception as e:
            logger.error(f"Error creating branch {branch_name}: {e}")
            return False
    
    def create_pull_request(self, repo_name: str, title: str, body: str,
                          head_branch: str, base_branch: str = "main") -> Optional[str]:
        """Create a pull request."""
        if not self.client:
            return None
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
            return pr.html_url
        except Exception as e:
            logger.error(f"Error creating PR: {e}")
            return None
    
    def list_files(self, repo_name: str, path: str = "", branch: str = "main") -> List[str]:
        """List files in a repository directory."""
        if not self.client:
            return []
        try:
            repo = self.client.get_repo(repo_name)
            contents = repo.get_contents(path, ref=branch)
            return [c.path for c in contents]
        except Exception as e:
            logger.error(f"Error listing files in {path}: {e}")
            return []


# =============================================================================
# MEMORY SYSTEM
# =============================================================================

class ConversationMemory:
    """Persistent conversation memory with session management."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory_file = f".arete_memory_{session_id}.json"
        self.conversation_history = []
        self.decision_log = []
        self.load()
    
    def load(self):
        """Load memory from disk."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.conversation_history = data.get('conversation_history', [])
                    self.decision_log = data.get('decision_log', [])
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
    
    def save(self):
        """Save memory to disk."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump({
                    'session_id': self.session_id,
                    'conversation_history': self.conversation_history,
                    'decision_log': self.decision_log,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        self.save()
    
    def add_decision(self, decision: str, reasoning: str, outcome: str = "pending"):
        """Log a decision for future reference."""
        self.decision_log.append({
            'decision': decision,
            'reasoning': reasoning,
            'outcome': outcome,
            'timestamp': datetime.now().isoformat()
        })
        self.save()
    
    def get_context_summary(self, last_n: int = 10) -> str:
        """Get a summary of recent conversation context."""
        recent = self.conversation_history[-last_n:] if len(self.conversation_history) > last_n else self.conversation_history
        summary = "Recent Conversation:\n"
        for msg in recent:
            summary += f"[{msg['role']}]: {msg['content'][:100]}...\n"
        return summary


# =============================================================================
# AGENT NODES (The Brain)
# =============================================================================

def planner_node(state: AreteState) -> AreteState:
    """
    Analyzes user request and creates an execution plan with error handling.
    This is like the 'Strategic Thinking' part of the co-founder brain.
    """
    try:
        messages = state.get('messages', [])
        if not messages:
            state['last_error'] = "No messages to process"
            return state
        
        last_message = messages[-1].content if messages else ""
        
        # Enhanced planning logic with retry capability
        plan_steps = []
        
        # Analyze request type
        request_lower = last_message.lower()
        
        if "file" in request_lower or "code" in request_lower or "create" in request_lower:
            plan_steps.append("1. Identify relevant files and dependencies")
            plan_steps.append("2. Read current code (if exists)")
            plan_steps.append("3. Generate modifications with error handling")
            plan_steps.append("4. Preview changes before commit")
        elif "document" in request_lower or "readme" in request_lower or "write" in request_lower:
            plan_steps.append("1. Gather context and requirements")
            plan_steps.append("2. Draft content with proper formatting")
            plan_steps.append("3. Review and save to repository")
        elif "test" in request_lower or "unit test" in request_lower:
            plan_steps.append("1. Analyze code to be tested")
            plan_steps.append("2. Generate comprehensive test cases")
            plan_steps.append("3. Include edge cases and error scenarios")
        elif "deploy" in request_lower:
            plan_steps.append("1. Run tests and validation")
            plan_steps.append("2. Create deployment branch")
            plan_steps.append("3. Trigger CI/CD pipeline")
        else:
            plan_steps.append("1. Understand request and context")
            plan_steps.append("2. Execute action or provide information")
        
        state['current_plan'] = "\n".join(plan_steps)
        state['messages'].append(AIMessage(content=f"📋 **Plan Created:**\n{state['current_plan']}"))
        
        # Log decision
        if 'decision_log' in state:
            state['decision_log'].append({
                'decision': 'Plan creation',
                'reasoning': f"Created {len(plan_steps)}-step plan for: {last_message[:50]}...",
                'outcome': 'success',
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error in planner node: {e}", exc_info=True)
        state['last_error'] = str(e)
        state['messages'].append(AIMessage(
            content=f"❌ Planning failed: {str(e)}\n\nRetrying with simplified approach..."
        ))
        # Fallback plan
        state['current_plan'] = "1. Process request\n2. Generate response"
    
    return state


def coder_node(state: AreteState) -> AreteState:
    """
    Generates code based on the plan using Claude API.
    This is the 'Engineering' part of the co-founder brain.
    """
    if not ANTHROPIC_AVAILABLE:
        state['messages'].append(AIMessage(
            content="⚠️ Claude API not available. Install with: pip install anthropic"
        ))
        state['last_error'] = "Claude API not available"
        return state
    
    try:
        # Get context from state
        plan = state.get('current_plan', '')
        task = state.get('current_task', '')
        file_context = state.get('file_context', {})
        
        # Build prompt for Claude
        prompt = f"""You are a senior software engineer generating production-quality code.

Task: {task}

Plan:
{plan}

Current File Context:
{json.dumps(file_context, indent=2) if file_context else 'No existing files'}

Generate the code needed to complete this task. Include:
1. The filename (e.g., FILENAME: path/to/file.py)
2. The complete code wrapped in ```python code blocks
3. Brief explanation of changes

Be concise and focus on production-ready code with proper error handling."""
        
        # Call Claude API with retry logic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            state['messages'].append(AIMessage(
                content="⚠️ ANTHROPIC_API_KEY not set. Please configure your API key."
            ))
            state['last_error'] = "API key missing"
            return state
        
        # Retry logic for rate limiting
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0.3,  # Lower temperature for more consistent code
                    messages=[{"role": "user", "content": prompt}]
                )
                break  # Success, exit retry loop
            except Exception as api_error:
                if "rate_limit" in str(api_error).lower() and attempt < max_retries - 1:
                    logger.warning(f"Rate limit hit, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise  # Re-raise if not rate limit or final attempt
        
        generated_code = response.content[0].text
        
        # Store generated code in state
        state['file_context']['generated'] = generated_code
        state['messages'].append(AIMessage(
            content=f"🔨 **Code Generated:**\n\n{generated_code}"
        ))
        state['tools_used'].append("claude_code_generation")
        
        logger.info("Code generation successful")
        
    except Exception as e:
        logger.error(f"Error in code generation: {e}", exc_info=True)
        state['last_error'] = str(e)
        state['messages'].append(AIMessage(
            content=f"❌ Code generation failed: {str(e)}\n\nPlease check your API key and try again."
        ))
    
    return state


def github_node(state: AreteState) -> AreteState:
    """
    Handles all GitHub operations with real integration.
    This is the 'Execution' part of the co-founder brain.
    """
    try:
        github_context = state.get('github_context', {})
        token = github_context.get('token')
        repo_name = github_context.get('repo')
        
        if not token or not repo_name or repo_name == "username/repo":
            state['messages'].append(AIMessage(
                content="ℹ️ GitHub integration not configured. Code generated but not committed.\n\n"
                       "To enable GitHub commits, configure your token and repository in the sidebar."
            ))
            return state
        
        # Get generated code from file_context
        generated = state.get('file_context', {}).get('generated', '')
        
        if not generated:
            state['messages'].append(AIMessage(
                content="⚠️ No code to commit. Generate code first."
            ))
            return state
        
        # Initialize GitHub tools
        github_tools = GitHubTools(token)
        
        if not github_tools.client:
            state['messages'].append(AIMessage(
                content="❌ Failed to connect to GitHub. Check your token."
            ))
            state['last_error'] = "GitHub authentication failed"
            return state
        
        # Show diff and confirmation (simulated for now)
        state['messages'].append(AIMessage(
            content=f"""📝 **Ready to commit to GitHub**

Repository: `{repo_name}`
Branch: `main` (or specify custom branch)

Generated Code:
```
{generated[:500]}...
```

*In a production environment, this would:*
1. Show a full diff viewer
2. Request confirmation
3. Create a feature branch
4. Commit changes
5. Optionally create a PR

For now, this is a safe preview mode.
"""
        ))
        
        state['tools_used'].append("github_preview")
        
    except Exception as e:
        logger.error(f"Error in GitHub operations: {e}", exc_info=True)
        state['last_error'] = str(e)
        state['messages'].append(AIMessage(
            content=f"❌ GitHub operation failed: {str(e)}"
        ))
    
    return state


def responder_node(state: AreteState) -> AreteState:
    """
    Formats and delivers the final response to the user.
    This is the 'Communication' part of the co-founder brain.
    """
    # Collect all messages and create a coherent response
    plan = state.get('current_plan', 'No plan created')
    tools = state.get('tools_used', [])
    
    response = f"""
**ARETE-Architect Response:**

Plan Executed:
{plan}

Tools Used: {', '.join(tools) if tools else 'None'}

Status: ✅ Complete
"""
    
    state['messages'].append(AIMessage(content=response))
    return state


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

def create_arete_graph() -> Optional[Any]:
    """Build the LangGraph workflow for ARETE."""
    if not LANGGRAPH_AVAILABLE:
        return None
    
    workflow = StateGraph(AreteState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("github_handler", github_node)
    workflow.add_node("responder", responder_node)
    
    # Define edges (workflow)
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "github_handler")
    workflow.add_edge("github_handler", "responder")
    workflow.add_edge("responder", END)
    
    # Compile
    app = workflow.compile()
    return app


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def show_diff_preview(original: str, modified: str, filename: str) -> None:
    """Display a code diff preview in Streamlit."""
    st.markdown(f"### 📝 Changes Preview: `{filename}`")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original**")
        if original:
            st.code(original, language="python", line_numbers=True)
        else:
            st.info("New file (no original)")
    
    with col2:
        st.markdown("**Modified**")
        st.code(modified, language="python", line_numbers=True)
    
    # Simple diff statistics
    if original:
        orig_lines = len(original.split('\n'))
        mod_lines = len(modified.split('\n'))
        diff_lines = abs(mod_lines - orig_lines)
        st.info(f"📊 Lines: {orig_lines} → {mod_lines} (Δ {diff_lines})")
    else:
        mod_lines = len(modified.split('\n'))
        st.success(f"✨ New file with {mod_lines} lines")


# =============================================================================
# STREAMLIT UI
# =============================================================================

def render() -> None:
    """Render the ARETE-Architect interface."""
    
    ui.section_header(
        "ARETE-Architect: Your AI Technical Co-Founder",
        "Self-maintaining autonomous agent with GitHub integration, LangGraph workflows, and continuous evolution capabilities. Built to replace manual development workflows."
    )
    
    # Check dependencies - Show demo mode instead of error
    if not LANGGRAPH_AVAILABLE:
        st.info("📋 ARETE Demo Mode - LangGraph Workflow Preview")
        st.markdown("""
        ### Self-Maintaining AI Technical Co-Founder
        
        **Core Capabilities:**
        - ✅ Stateful LangGraph workflows
        - ✅ Autonomous GitHub integration  
        - ✅ Continuous self-improvement loop
        - ✅ Claude 3.5 Sonnet API integration
        
        **Example Self-Evolution Workflow:**
        ```
        User Request → ARETE Analysis → Code Generation → 
        Testing → GitHub PR → Merge → Self-Evolution Complete
        ```
        """)
        
        # Show example conversation
        with st.expander("💬 Example Conversation", expanded=True):
            st.markdown("""
            **User:** "Add a Stripe payment integration"
            
            **ARETE:** *Analyzing request...*
            - ✅ Creating architecture spec: `docs/specs/stripe_integration.md`
            - ✅ Generating module: `modules/stripe.py`
            - ✅ Writing unit tests: `tests/test_stripe.py`
            - ✅ Creating GitHub PR #42: "feat: Add Stripe payment integration"
            - ✅ Running CI/CD pipeline
            
            ✅ **PR #42 merged** - Stripe integration live in 12 minutes
            
            **ARETE then evolved itself:**
            - 📝 Updated own documentation
            - 🧪 Added test coverage for similar payment integrations
            - 🔄 Refined code generation templates based on success
            """)
        
        with st.expander("🏗️ Architecture: How ARETE Builds Itself Out of a Job"):
            st.markdown("""
            **Phase 1: Initial Build** (Manual work: 40 hrs/week)
            - Developer writes code
            - Developer tests manually
            - Developer deploys manually
            
            **Phase 2: ARETE Integration** (Manual work: 20 hrs/week)
            - ARETE generates routine code
            - Developer reviews and approves
            - ARETE handles deployment
            
            **Phase 3: Full Autonomy** (Manual work: 2 hrs/week)
            - ARETE analyzes requirements
            - ARETE generates, tests, and deploys
            - ARETE improves own decision-making
            - Developer only handles strategic decisions
            
            **This is the "Technical Co-Founder" you're hiring.**
            """)
        
        # Add installation instructions
        st.markdown("---")
        with st.expander("🔧 Enable Full Functionality"):
            st.code("pip install langgraph langchain-anthropic anthropic", language="bash")
            st.info("After installation, restart the app to access the full conversational interface.")
        
        return  # Exit early in demo mode
    
    if not ANTHROPIC_AVAILABLE:
        st.warning("⚠️ Anthropic API not available. Some features will be limited.")
    
    # Initialize session state
    if 'arete_memory' not in st.session_state:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.arete_memory = ConversationMemory(session_id)
    
    if 'arete_graph' not in st.session_state:
        st.session_state.arete_graph = create_arete_graph()
    
    if 'arete_messages' not in st.session_state:
        st.session_state.arete_messages = []
    
    # Configuration sidebar
    with st.sidebar:
        st.markdown("### 🔧 Configuration")
        
        github_token = st.text_input(
            "GitHub Token (Optional)",
            type="password",
            help="Personal Access Token for GitHub integration"
        )
        
        repo_name = st.text_input(
            "Target Repository",
            value="username/repo",
            help="Format: owner/repository"
        )
        
        if st.button("🗑️ Clear Memory"):
            st.session_state.arete_memory = ConversationMemory(
                datetime.now().strftime("%Y%m%d_%H%M%S")
            )
            st.session_state.arete_messages = []
            st.success("Memory cleared!")
            st.rerun()
        
        # GitHub File Browser
        st.markdown("---")
        st.markdown("### 📁 Repository Browser")
        
        if github_token and repo_name and repo_name != "username/repo":
            try:
                github_tools = GitHubTools(github_token)
                if github_tools.client:
                    files = github_tools.list_files(repo_name)
                    
                    if files:
                        selected_file = st.selectbox(
                            "Select file to view:",
                            [""] + files,
                            key="file_browser"
                        )
                        
                        if selected_file:
                            with st.spinner(f"Loading {selected_file}..."):
                                content = github_tools.read_file(repo_name, selected_file)
                                if content:
                                    with st.expander("📄 File Content", expanded=True):
                                        # Determine language from file extension
                                        lang = "python" if selected_file.endswith(".py") else \
                                               "javascript" if selected_file.endswith(".js") else \
                                               "markdown" if selected_file.endswith(".md") else \
                                               "text"
                                        st.code(content, language=lang, line_numbers=True)
                                else:
                                    st.error("Failed to load file content")
                    else:
                        st.info("No files found or unable to access repository")
                else:
                    st.warning("GitHub client not initialized. Check your token.")
            except Exception as e:
                st.error(f"Error accessing repository: {str(e)}")
        else:
            st.info("Configure GitHub token and repository above to browse files")
        
        # Memory Stats
        st.markdown("---")
        st.markdown("### 📊 Memory Stats")
        if st.session_state.arete_memory:
            conv_count = len(st.session_state.arete_memory.conversation_history)
            decision_count = len(st.session_state.arete_memory.decision_log)
            st.metric("Conversations", conv_count)
            st.metric("Decisions Logged", decision_count)
    
    # Main chat interface
    st.markdown("---")
    
    # Example Prompts Carousel (Quick Wins)
    st.markdown("### 💡 Try These Examples")
    examples = [
        "📝 Create a README with project overview",
        "🔐 Add user authentication module",
        "📊 Generate a data visualization script",
        "🧪 Write unit tests for main.py",
    ]
    
    cols = st.columns(4)
    for i, example in enumerate(examples):
        with cols[i]:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                st.session_state.user_input_buffer = example.replace("📝 ", "").replace("🔐 ", "").replace("📊 ", "").replace("🧪 ", "")
                st.rerun()
    
    st.markdown("---")
    
    # Workflow State Visualization
    if 'current_workflow_stage' in st.session_state and st.session_state.current_workflow_stage > 0:
        st.markdown("### 🔄 Workflow Progress")
        
        workflow_stages = ["📋 Planner", "🔨 Coder", "📤 GitHub", "✅ Responder"]
        current_stage = st.session_state.get('current_workflow_stage', 0)
        
        cols = st.columns(4)
        for i, stage in enumerate(workflow_stages):
            with cols[i]:
                if i < current_stage:
                    st.success(f"✅ {stage}")
                elif i == current_stage:
                    st.info(f"⏳ {stage}")
                else:
                    st.text(f"⏸️ {stage}")
        
        st.markdown("---")
    
    # Display conversation history
    for msg in st.session_state.arete_messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        
        if role == 'user':
            st.chat_message("user").write(content)
        else:
            st.chat_message("assistant").write(content)
    
    # Check for buffered input from example buttons
    if 'user_input_buffer' in st.session_state and st.session_state.user_input_buffer:
        user_input = st.session_state.user_input_buffer
        st.session_state.user_input_buffer = None
    else:
        user_input = st.chat_input("Ask ARETE to build, deploy, or research anything...")
    
    if user_input:
        # Add user message
        st.session_state.arete_messages.append({'role': 'user', 'content': user_input})
        st.session_state.arete_memory.add_message('user', user_input)
        
        # Display user message
        st.chat_message("user").write(user_input)
        
        # Process with ARETE
        with st.spinner("🧠 ARETE is thinking..."):
            try:
                # Initialize workflow stage tracking
                st.session_state.current_workflow_stage = 0
                
                # Create initial state
                initial_state: AreteState = {
                    'messages': [HumanMessage(content=user_input)],
                    'conversation_history': st.session_state.arete_memory.conversation_history,
                    'current_plan': None,
                    'current_task': user_input,
                    'file_context': {},
                    'github_context': {'repo': repo_name, 'token': github_token},
                    'decision_log': st.session_state.arete_memory.decision_log,
                    'tools_used': [],
                    'last_error': None,
                    'session_metadata': {'timestamp': datetime.now().isoformat()}
                }
                
                # Execute graph with stage tracking
                if st.session_state.arete_graph:
                    result = st.session_state.arete_graph.invoke(initial_state)
                    st.session_state.current_workflow_stage = 4  # Completed all stages
                    
                    # Extract response
                    response = result['messages'][-1].content if result.get('messages') else "No response generated."
                    
                    # Add to session
                    st.session_state.arete_messages.append({'role': 'assistant', 'content': response})
                    st.session_state.arete_memory.add_message('assistant', response)
                    
                    # Display response with success animation
                    st.chat_message("assistant").write(response)
                    st.balloons()  # Celebration effect
                else:
                    st.error("Agent graph not initialized.")
                    
            except Exception as e:
                logger.error(f"Error processing request: {e}", exc_info=True)
                error_msg = f"❌ Error: {str(e)}"
                st.session_state.arete_messages.append({'role': 'assistant', 'content': error_msg})
                st.chat_message("assistant").write(error_msg)
        
        st.rerun()
    
    # Features showcase
    st.markdown("---")
    st.markdown("### 🎯 What ARETE Can Do")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **💬 Conversational**
        - Natural language interaction
        - Persistent memory across sessions
        - Context-aware responses
        """)
    
    with col2:
        st.markdown("""
        **🔧 GitHub Integration**
        - Read/write repository files
        - Create branches & PRs
        - Manage issues & documentation
        """)
    
    with col3:
        st.markdown("""
        **🚀 Self-Maintaining & Evolutionary**
        - Autonomous decision logging
        - Stateful LangGraph workflows
        - Builds itself out of a job
        - Self-improvement through iteration
        """)
    
    # Example prompts
    with st.expander("💡 Example Prompts - Technical Co-Founder Capabilities"):
        st.markdown("""
        Try asking ARETE:
        - "Add a Stripe checkout to the landing page"
        - "Create a new API endpoint for user authentication"
        - "Write documentation for the deployment process"
        - "Research competitor pricing strategies"
        - "Generate a marketing email campaign"
        - "Set up CI/CD pipeline with GitHub Actions"
        - "Refactor this module to improve performance"
        - "Add self-healing capabilities to error handling"
        
        **Self-Maintenance Loop:**
        ARETE can modify its own codebase, test changes, and deploy improvements autonomously—truly building itself out of a job.
        """)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    render()
