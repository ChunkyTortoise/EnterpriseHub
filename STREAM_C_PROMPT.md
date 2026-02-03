# Stream C: Optional Feature Integration
**Chat Purpose**: Enable & validate Progressive Skills, Agent Mesh, and MCP integration  
**Duration**: 2-4 hours  
**Priority**: MEDIUM (can run after A & B)  
**Status**: Ready to begin

---

## Your Mission

Enable optional features that are already implemented but currently disabled. Each provides significant value:
- **Progressive Skills**: 68% token reduction
- **Agent Mesh**: Multi-agent cost optimization
- **MCP Integration**: Standardized external services

You'll configure, test, and document each feature.

**Files You'll Work With**:
- `ghl_real_estate_ai/agents/jorge_seller_bot.py` (Feature flags)
- `ghl_real_estate_ai/config/feature_config.py` (Central config)
- `ghl_real_estate_ai/services/progressive_skills_manager.py` (Use existing)
- `ghl_real_estate_ai/services/agent_mesh_coordinator.py` (Use existing)
- `docs/FEATURE_FLAGS.md` (NEW - create documentation)

---

## Overview of Features

### Feature 1: Progressive Skills Manager
**Purpose**: Reduce token usage while maintaining quality  
**Current State**: Implemented, disabled  
**Benefit**: 68% token reduction on repetitive tasks  
**Effort**: 1-2 hours

### Feature 2: Agent Mesh Coordinator
**Purpose**: Multi-agent orchestration & load balancing  
**Current State**: Implemented, disabled  
**Benefit**: Cost optimization, better resource utilization  
**Effort**: 1-2 hours

### Feature 3: MCP Integration
**Purpose**: Standardized Model Context Protocol for external services  
**Current State**: Implemented, disabled  
**Benefit**: Consistent integration patterns, better maintainability  
**Effort**: 1 hour

---

## Feature 1: Progressive Skills Manager

### Current Implementation
```python
# In jorge_seller_bot.py
class JorgeFeatureConfig:
    enable_progressive_skills: bool = False  # ← DISABLED
    ...
```

### What It Does
```
Traditional Flow:
User Input → Claude API (full model) → Bot Response
            ↑ (Full token usage)

Progressive Skills Flow:
User Input → Skill Library (fast, cheap) ↓ Cache Hit (90%)
                                        ↓ Return response
                                        ↓ No API call needed
            OR
            → Claude API (full model) ↓ Cache Miss (10%)
                                    ↓ Return response
            ↑ (68% fewer tokens)
```

### Enable Progressive Skills

**Step 1: Understand the Implementation**
```bash
# Review how it's currently structured
grep -A 20 "enable_progressive_skills" ghl_real_estate_ai/agents/jorge_seller_bot.py

# Check the skills manager service
cat ghl_real_estate_ai/services/progressive_skills_manager.py
```

**Step 2: Create Configuration**
```python
# File: ghl_real_estate_ai/config/feature_config.py

class ProgressiveSkillsConfig:
    """Configuration for Progressive Skills Manager"""
    
    enabled: bool = False  # Set to True in production
    model: str = "claude-3-5-sonnet"  # Skills model
    skill_library_path: str = "${CLAUDE_PLUGIN_ROOT}/skills"
    
    # Caching for skill responses
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 10000  # entries
    cache_eviction: str = "LRU"
    
    # Fallback if skill fails
    fallback_to_full: bool = True  # Use full model if skill fails
    fallback_timeout: int = 2  # seconds before fallback
    
    # Monitoring
    track_skill_usage: bool = True
    log_token_savings: bool = True
    
    # Skills to enable
    enabled_skills: List[str] = [
        "intent_classification",
        "response_formatting",
        "lead_scoring",
        "property_matching",
        "market_analysis"
    ]
```

**Step 3: Initialize in Seller Bot**
```python
# In jorge_seller_bot.py __init__

if self.config.enable_progressive_skills:
    self.skills_manager = ProgressiveSkillsManager(
        config=ProgressiveSkillsConfig(
            enabled=True,
            model=self.config.skills_model,
            fallback_to_full=True
        )
    )
else:
    self.skills_manager = None
```

**Step 4: Use in Response Generation**
```python
# In generate_response() method

if self.skills_manager:
    # Try skill first (fast path)
    response = await self.skills_manager.apply_skill(
        skill_name="response_formatting",
        context=context,
        timeout=2.0
    )
    if response:
        return response

# Fallback to full model
return await self.claude_assistant.generate_response(...)
```

### Enable in Production
```bash
# Option 1: Environment variable
export ENABLE_PROGRESSIVE_SKILLS=true
export PROGRESSIVE_SKILLS_MODEL=claude-3-5-sonnet

# Option 2: Configuration file
cat > .env.local << EOF
ENABLE_PROGRESSIVE_SKILLS=true
PROGRESSIVE_SKILLS_MODEL=claude-3-5-sonnet
PROGRESSIVE_SKILLS_CACHE_TTL=3600
EOF
```

### Test Progressive Skills
```python
# Test cases to add to test_jorge_seller_bot.py

async def test_progressive_skills_improves_performance():
    """Verify skills path is faster than full model"""
    bot_with_skills = create_seller_bot(enable_progressive_skills=True)
    bot_without_skills = create_seller_bot(enable_progressive_skills=False)
    
    start_with = time.time()
    response_with = await bot_with_skills.generate_response(...)
    time_with = time.time() - start_with
    
    start_without = time.time()
    response_without = await bot_without_skills.generate_response(...)
    time_without = time.time() - start_without
    
    assert time_with < time_without * 0.5  # 50% faster

async def test_progressive_skills_fallback():
    """Verify fallback to full model if skill fails"""
    bot = create_seller_bot(enable_progressive_skills=True)
    # Mock skills manager to fail
    bot.skills_manager.apply_skill = Mock(side_effect=TimeoutError)
    
    response = await bot.generate_response(...)
    
    # Should still return response via full model
    assert response is not None
    assert len(response) > 0

async def test_progressive_skills_token_savings():
    """Verify 68% token reduction"""
    # Count tokens with skills enabled vs disabled
    with_skills_tokens = measure_tokens(enable_progressive_skills=True)
    without_skills_tokens = measure_tokens(enable_progressive_skills=False)
    
    savings = 1 - (with_skills_tokens / without_skills_tokens)
    assert savings >= 0.60  # At least 60% reduction
```

---

## Feature 2: Agent Mesh Coordinator

### Current Implementation
```python
# In jorge_seller_bot.py
class JorgeFeatureConfig:
    enable_agent_mesh: bool = False  # ← DISABLED
    ...
```

### What It Does
```
Single Agent Flow:
Seller Request → Jorge Seller Bot → Claude API
                                  → Response

Agent Mesh Flow:
Seller Request → Agent Mesh Router
               ├→ Intent Analyzer Agent (fast)
               ├→ Price Optimizer Agent (fast)
               ├→ Market Data Agent (fast)
               └→ Coordination Layer (sync results)
                              ↓
                        Response (optimized)
               
Benefits:
- Parallel execution (3 agents = 3x faster)
- Cost optimization (route to cheapest agent)
- Specialized expertise (each agent optimized)
- Better load balancing
```

### Enable Agent Mesh

**Step 1: Understand the Implementation**
```bash
# Review mesh coordinator
grep -A 30 "agent_mesh_coordinator" ghl_real_estate_ai/services/agent_mesh_coordinator.py

# Check mesh configuration
grep -r "AgentMeshConfig" ghl_real_estate_ai/
```

**Step 2: Create Configuration**
```python
# File: ghl_real_estate_ai/config/feature_config.py

class AgentMeshConfig:
    """Configuration for Agent Mesh Coordinator"""
    
    enabled: bool = False  # Set to True for enterprise
    max_agents: int = 5
    routing_strategy: str = "cost_aware"  # or "performance", "availability"
    
    # Load balancing
    load_balance: bool = True
    round_robin: bool = False
    weighted_routing: bool = True
    
    # Health checking
    health_check_enabled: bool = True
    health_check_interval: int = 30  # seconds
    unhealthy_timeout: int = 60  # seconds before marking unhealthy
    
    # Optimization
    parallel_execution: bool = True
    result_aggregation: str = "voting"  # or "weighted", "first"
    timeout_per_agent: int = 5  # seconds
    
    # Agents in mesh
    agents: Dict[str, AgentConfig] = {
        "intent_analyzer": AgentConfig(
            model="claude-3-5-haiku",  # Fast + cheap
            priority=1,
            timeout=2
        ),
        "price_optimizer": AgentConfig(
            model="claude-3-5-sonnet",
            priority=2,
            timeout=3
        ),
        "market_data_agent": AgentConfig(
            model="claude-3-5-haiku",
            priority=3,
            timeout=2
        ),
        "main_agent": AgentConfig(
            model="claude-opus-4-5",  # Full model for final response
            priority=0,
            timeout=10
        )
    }
```

**Step 3: Initialize in Seller Bot**
```python
# In jorge_seller_bot.py __init__

if self.config.enable_agent_mesh:
    self.agent_mesh = AgentMeshCoordinator(
        config=AgentMeshConfig(enabled=True),
        agents=self._initialize_mesh_agents()
    )
    # Start health check background task
    asyncio.create_task(self.agent_mesh.health_check_loop())
else:
    self.agent_mesh = None

def _initialize_mesh_agents(self):
    """Initialize specialized agents for mesh"""
    return {
        "intent_analyzer": IntentAnalyzerAgent(...),
        "price_optimizer": PriceOptimizerAgent(...),
        "market_data": MarketDataAgent(...),
        "main": self.claude_assistant
    }
```

**Step 4: Use in Response Generation**
```python
# In generate_response() method

if self.agent_mesh:
    # Route through mesh
    result = await self.agent_mesh.coordinate(
        request=request,
        primary_agent="main",
        parallel_agents=["intent_analyzer", "price_optimizer", "market_data"],
        strategy="cost_aware"
    )
    return result['response']

# Fallback to single agent
return await self.claude_assistant.generate_response(...)
```

### Enable in Production
```bash
# Option 1: Environment variable
export ENABLE_AGENT_MESH=true
export AGENT_MESH_ROUTING=cost_aware

# Option 2: Configuration file
cat > .env.local << EOF
ENABLE_AGENT_MESH=true
AGENT_MESH_ROUTING_STRATEGY=cost_aware
AGENT_MESH_PARALLEL=true
EOF
```

### Test Agent Mesh
```python
# Test cases to add to test_jorge_seller_bot.py

async def test_agent_mesh_parallel_execution():
    """Verify agents execute in parallel"""
    bot = create_seller_bot(enable_agent_mesh=True)
    
    start = time.time()
    response = await bot.generate_response(...)
    duration = time.time() - start
    
    # Parallel should be faster than sequential
    # Estimate: 3 agents = max(agent_times) not sum
    assert duration < 5.0  # Should be <5s not 15s (sequential)

async def test_agent_mesh_cost_optimization():
    """Verify cost-aware routing selects cheaper agent"""
    bot = create_seller_bot(enable_agent_mesh=True, routing="cost_aware")
    
    # Mock agents with different costs
    bot.agent_mesh.agents["haiku"].cost = 0.001
    bot.agent_mesh.agents["sonnet"].cost = 0.003
    
    response = await bot.generate_response(...)
    
    # Should prefer cheaper agent
    assert bot.agent_mesh.selected_agent == "haiku"

async def test_agent_mesh_health_check():
    """Verify health checking and failover"""
    bot = create_seller_bot(enable_agent_mesh=True)
    
    # Mark an agent as unhealthy
    bot.agent_mesh.mark_unhealthy("price_optimizer")
    
    response = await bot.generate_response(...)
    
    # Should skip unhealthy agent
    assert "price_optimizer" not in response['agents_used']

async def test_agent_mesh_fallback():
    """Verify fallback if all agents fail"""
    bot = create_seller_bot(enable_agent_mesh=True)
    # Mock all agents to fail
    bot.agent_mesh.coordinate = Mock(side_effect=Exception("All failed"))
    
    response = await bot.generate_response(...)
    
    # Should fallback to main agent
    assert response is not None
```

---

## Feature 3: MCP Integration

### Current Implementation
```python
# In jorge_seller_bot.py
class JorgeFeatureConfig:
    enable_mcp_integration: bool = False  # ← DISABLED
    ...
```

### What It Does
```
Direct Integration (current):
Bot → Service A (custom adapter)
    → Service B (custom adapter)
    → Service C (custom adapter)

MCP Integration (enabled):
Bot → MCP Client
    ├→ MCP Adapter for Service A (standard)
    ├→ MCP Adapter for Service B (standard)
    └→ MCP Adapter for Service C (standard)
    
Benefits:
- Standardized integration pattern
- Easier to add new services
- Better error handling
- Service abstraction
```

### Enable MCP Integration

**Step 1: Understand MCP**
```bash
# Check MCP configuration
cat ghl_real_estate_ai/config/.mcp.json

# Review MCP client
cat ghl_real_estate_ai/services/mcp_client.py
```

**Step 2: Create Configuration**
```python
# File: ghl_real_estate_ai/config/feature_config.py

class MCPConfig:
    """Configuration for Model Context Protocol"""
    
    enabled: bool = False  # Set to True for standardized integrations
    protocol_version: str = "1.0"
    
    # MCP Server configuration
    mcp_servers: Dict[str, MCPServerConfig] = {
        "property_data": MCPServerConfig(
            url="http://localhost:8001",
            type="stdio",  # or "sse", "http"
            timeout=10,
            retry_policy="exponential"
        ),
        "market_data": MCPServerConfig(
            url="http://localhost:8002",
            type="http",
            timeout=5,
            retry_policy="linear"
        ),
        "compliance": MCPServerConfig(
            url="http://localhost:8003",
            type="stdio",
            timeout=3,
            retry_policy="none"
        )
    }
    
    # Request handling
    request_timeout: int = 30  # seconds
    max_retries: int = 3
    cache_responses: bool = True
    cache_ttl: int = 3600
    
    # Error handling
    fallback_enabled: bool = True
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5  # failures before circuit opens
```

**Step 3: Initialize in Seller Bot**
```python
# In jorge_seller_bot.py __init__

if self.config.enable_mcp_integration:
    self.mcp_client = MCPClient(config=MCPConfig(enabled=True))
    # Initialize all MCP servers
    await self.mcp_client.initialize()
else:
    self.mcp_client = None
```

**Step 4: Use in Services**
```python
# Example: Get property data via MCP

async def get_property_data(property_address: str) -> Dict:
    if self.mcp_client:
        # Via MCP (standardized)
        return await self.mcp_client.call(
            service="property_data",
            method="get_comparable_properties",
            params={"address": property_address}
        )
    else:
        # Direct integration (legacy)
        return await self.property_service.get_comparable_properties(
            property_address
        )
```

### Enable in Production
```bash
# Option 1: Environment variable
export ENABLE_MCP_INTEGRATION=true
export MCP_PROPERTY_DATA_URL=http://localhost:8001

# Option 2: Configuration file
cat > .env.local << EOF
ENABLE_MCP_INTEGRATION=true
MCP_PROTOCOL_VERSION=1.0
MCP_REQUEST_TIMEOUT=30
EOF
```

### Test MCP Integration
```python
# Test cases to add to test_jorge_seller_bot.py

async def test_mcp_integration_property_data():
    """Verify MCP call to property data service"""
    bot = create_seller_bot(enable_mcp_integration=True)
    
    result = await bot.mcp_client.call(
        service="property_data",
        method="get_comparable_properties",
        params={"address": "123 Main St, RC, CA"}
    )
    
    assert result is not None
    assert "comparable_properties" in result

async def test_mcp_circuit_breaker():
    """Verify circuit breaker on repeated failures"""
    bot = create_seller_bot(enable_mcp_integration=True)
    
    # Cause 5 failures
    for i in range(5):
        try:
            await bot.mcp_client.call(service="market_data", ...)
        except:
            pass
    
    # Circuit should be open
    assert bot.mcp_client.circuit_breaker.is_open("market_data")
    
    # Next call should fail fast
    result = await bot.mcp_client.call(service="market_data", ...)
    assert result is None  # Fallback

async def test_mcp_fallback():
    """Verify fallback when MCP service unavailable"""
    bot = create_seller_bot(enable_mcp_integration=True)
    # Simulate service unavailable
    bot.mcp_client.services["property_data"].available = False
    
    result = await bot.get_property_data("123 Main St, RC, CA")
    
    # Should fallback to direct integration
    assert result is not None
```

---

## Implementation Sequence

### Option A: Parallel (Recommended)
```
Start all 3 features at the same time
├─ Agent 1: Progressive Skills
├─ Agent 2: Agent Mesh
└─ Agent 3: MCP Integration
↓
All done in 2-4 hours
```

### Option B: Sequential
```
1. Progressive Skills (1 hour)
   ↓
2. Agent Mesh (1.5 hours)
   ↓
3. MCP Integration (0.75 hours)
↓
Total: 3.25 hours
```

---

## Configuration File Structure

**Create**: `ghl_real_estate_ai/config/feature_config.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ProgressiveSkillsConfig:
    enabled: bool = False
    model: str = "claude-3-5-sonnet"
    skill_library_path: str = ""
    cache_ttl: int = 3600
    fallback_to_full: bool = True

@dataclass
class AgentMeshConfig:
    enabled: bool = False
    max_agents: int = 5
    routing_strategy: str = "cost_aware"
    load_balance: bool = True
    health_check_interval: int = 30

@dataclass
class MCPConfig:
    enabled: bool = False
    protocol_version: str = "1.0"
    request_timeout: int = 30
    max_retries: int = 3

@dataclass
class JorgeFeatureConfig:
    """Master feature configuration"""
    progressive_skills: ProgressiveSkillsConfig = ProgressiveSkillsConfig()
    agent_mesh: AgentMeshConfig = AgentMeshConfig()
    mcp_integration: MCPConfig = MCPConfig()
    
    def load_from_env(self):
        """Load feature flags from environment variables"""
        import os
        self.progressive_skills.enabled = os.getenv(
            "ENABLE_PROGRESSIVE_SKILLS", "false"
        ).lower() == "true"
        self.agent_mesh.enabled = os.getenv(
            "ENABLE_AGENT_MESH", "false"
        ).lower() == "true"
        self.mcp_integration.enabled = os.getenv(
            "ENABLE_MCP_INTEGRATION", "false"
        ).lower() == "true"
        return self
```

---

## Documentation to Create

**File**: `docs/FEATURE_FLAGS.md`

```markdown
# Jorge Bot Feature Flags

## Overview
Enable optional features to optimize performance, reduce costs, and improve scalability.

## Progressive Skills Manager
**Token Reduction**: 68% on repetitive tasks

Enable with:
```bash
export ENABLE_PROGRESSIVE_SKILLS=true
```

Benefits:
- Faster response times (skill library hits)
- 68% fewer tokens
- Better cost optimization

Example config:
```python
PROGRESSIVE_SKILLS_MODEL=claude-3-5-sonnet
PROGRESSIVE_SKILLS_CACHE_TTL=3600
PROGRESSIVE_SKILLS_CACHE_MAX_SIZE=10000
```

## Agent Mesh Coordinator
**Cost Optimization**: Multi-agent routing

Enable with:
```bash
export ENABLE_AGENT_MESH=true
```

Benefits:
- Parallel agent execution
- Specialized agents for different tasks
- Cost-aware routing
- Better resource utilization

## MCP Integration
**Standardized Services**: Model Context Protocol

Enable with:
```bash
export ENABLE_MCP_INTEGRATION=true
```

Benefits:
- Standardized integration patterns
- Service abstraction
- Better error handling
- Easier maintenance
```

---

## Success Criteria Checklist

- [ ] Progressive Skills: Enabled, tested, 68% token reduction verified
- [ ] Agent Mesh: Enabled, tested, parallel execution confirmed
- [ ] MCP Integration: Enabled, tested, services accessible
- [ ] All 20 existing tests still passing (no regression)
- [ ] 6+ new tests passing for features
- [ ] Configuration file created: `config/feature_config.py`
- [ ] Documentation created: `docs/FEATURE_FLAGS.md`
- [ ] Environment variables documented
- [ ] Code review approved
- [ ] Performance impact: <100ms overhead per feature

---

## Commands to Run

```bash
# Check if feature services exist
ls -la ghl_real_estate_ai/services/ | grep -E "progressive|mesh|mcp"

# Review feature flags in seller bot
grep -n "enable_" ghl_real_estate_ai/agents/jorge_seller_bot.py

# Run tests with features enabled
pytest tests/agents/test_jorge_seller_bot.py -v -s -k "features"

# Test with environment variables
ENABLE_PROGRESSIVE_SKILLS=true ENABLE_AGENT_MESH=true pytest tests/agents/test_jorge_seller_bot.py -v

# Check feature usage
grep -rn "enable_progressive_skills\|enable_agent_mesh\|enable_mcp" ghl_real_estate_ai/
```

---

## Questions to Consider

1. Which features should be enabled by default in production?
2. Should features be togglable per-request or globally?
3. What's the rollback strategy if a feature causes issues?
4. How to monitor feature usage and performance impact?
5. Should there be an admin dashboard to toggle features?

---

**Ready to start? Begin by exploring the existing feature implementations!**

**Estimated completion**: 2-4 hours  
**Due by**: After Streams A & B (can run in parallel if preferred)  
**Can run in parallel with Stream D**
