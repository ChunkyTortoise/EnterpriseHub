# Agent Swarm Coordination Patterns

## Multi-Agent Portfolio Development

### Agent Specialization Strategy

#### Market Intelligence Agent
- **Focus**: Competitive analysis, market trends, opportunity identification
- **Model**: Sonnet (cost-effective for research)
- **Tools**: WebSearch, Read, Write
- **Context**: Fork (isolated market analysis)
- **Output**: Competitive positioning report, market opportunities

#### Technical Architecture Agent
- **Focus**: System design, scalability planning, technology optimization
- **Model**: Opus (complex architectural decisions)
- **Tools**: Read, Write, Task (code-architect)
- **Context**: Fork (isolated technical analysis)
- **Output**: Architecture recommendations, technology stack specification

#### Security Compliance Agent
- **Focus**: Enterprise security, vulnerability assessment, compliance validation
- **Model**: Sonnet (structured security analysis)
- **Tools**: Read, Bash (security scanning)
- **Context**: Fork (security-focused analysis)
- **Output**: Security assessment, compliance checklist

#### Performance Optimization Agent
- **Focus**: Scalability analysis, load testing, optimization strategies
- **Model**: Sonnet (performance analysis)
- **Tools**: Read, Bash (performance testing)
- **Context**: Fork (performance-focused analysis)
- **Output**: Performance recommendations, optimization plan

#### Client Materials Agent
- **Focus**: Professional deliverables, ROI analysis, client presentations
- **Model**: Opus (high-quality business materials)
- **Tools**: Write, Read
- **Context**: Fork (presentation-focused work)
- **Output**: Executive presentations, ROI documentation

### Coordination Patterns

#### Parallel Research Phase
```yaml
agents:
  - name: market-intelligence
    phase: discovery
    parallel: true
  - name: technical-architecture
    phase: discovery
    parallel: true
duration: 3-5 days
synchronization: findings-synthesis
```

#### Sequential Analysis Phase
```yaml
agents:
  - name: technical-architecture
    phase: architecture
    depends_on: discovery-complete
  - name: security-compliance
    phase: architecture
    depends_on: technical-architecture
  - name: performance-optimization
    phase: architecture
    depends_on: security-compliance
duration: 5-7 days
synchronization: architecture-review
```

#### Integrated Synthesis Phase
```yaml
agents:
  - name: all-agents
    phase: synthesis
    mode: collaborative
duration: 2-3 days
output: comprehensive-recommendations
```

### Context Forking Strategy

#### Isolation Benefits
- **Parallel Processing**: Agents work simultaneously without context pollution
- **Specialized Focus**: Each agent maintains domain-specific context
- **Resource Optimization**: Appropriate model selection per agent type
- **Quality Assurance**: Independent validation streams

#### Synchronization Points
- **Discovery Synthesis**: Combine market and technical insights
- **Architecture Review**: Validate technical decisions against business requirements
- **Quality Gates**: Ensure all agents meet portfolio standards
- **Final Integration**: Comprehensive deliverable compilation

### Agent Lifecycle Management

#### Initialization
```bash
# Deploy agent swarm for parallel analysis
./scripts/advanced/optimize_agent_swarm.sh {project_name} 5 enterprise
```

#### Monitoring
```bash
# Check agent coordination status
./scripts/advanced/monitor_agent_status.sh {project_name}
```

#### Optimization
```bash
# Optimize agent performance and resource usage
./scripts/advanced/optimize_agent_performance.sh {project_name}
```

### Quality Coordination

#### Cross-Agent Validation
- **Consistency Checks**: Ensure recommendations align across agents
- **Gap Analysis**: Identify missing considerations or conflicts
- **Integration Validation**: Verify combined recommendations are coherent
- **Business Alignment**: Ensure technical decisions support business goals

#### Automated Coordination Hooks
- **Agent Startup**: Validate agent configuration and context
- **Progress Checkpoints**: Monitor agent progress and synchronization
- **Quality Gates**: Ensure output quality before synthesis
- **Completion Validation**: Verify comprehensive coverage and integration

This pattern enables sophisticated portfolio development with multiple specialist perspectives while maintaining coordination and quality standards.