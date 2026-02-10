"""Agentic RAG pipeline orchestrator.

Coordinates query planning, tool execution, reflection/self-correction,
and answer synthesis into a multi-step reasoning pipeline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.agents.query_planner import QueryPlan, QueryPlanner, StepStatus
from src.agents.reflection import (
    AnswerQualityAssessment,
    ConfidenceScore,
    ConfidenceScorer,
    CorrectionStrategy,
    ReflectionEngine,
)
from src.agents.tool_registry import ToolRegistry, ToolResult
from src.agents.memory import ConversationMemory
from src.core.exceptions import RetrievalError
from src.retrieval.contextual_compression import ContextualCompressor


@dataclass
class AgenticRAGConfig:
    max_iterations: int = 3
    quality_threshold: float = 0.7
    enable_reflection: bool = True
    enable_compression: bool = True
    enable_self_query: bool = True
    top_k: int = 10
    enable_memory: bool = True
    memory_max_tokens: int = 1200
    memory_summary_tokens: int = 300


class ExecutionStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_number: int = Field(..., ge=1)
    description: str
    tool_name: str
    tool_result: Optional[ToolResult] = None
    duration_ms: float = Field(default=0.0, ge=0.0)
    status: str = "pending"


class ExecutionTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    steps: List[ExecutionStep] = Field(default_factory=list)
    total_duration_ms: float = Field(default=0.0, ge=0.0)
    iterations_used: int = Field(default=1, ge=1)


class AgenticRAGResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str
    confidence: ConfidenceScore
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    trace: ExecutionTrace
    quality: Optional[AnswerQualityAssessment] = None


class AgenticRAG:
    def __init__(
        self,
        config: Optional[AgenticRAGConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
        query_planner: Optional[QueryPlanner] = None,
        reflection_engine: Optional[ReflectionEngine] = None,
        compressor: Optional[ContextualCompressor] = None,
        memory: Optional[ConversationMemory] = None,
    ) -> None:
        self.config = config or AgenticRAGConfig()
        self.tool_registry = tool_registry or ToolRegistry()
        self.query_planner = query_planner or QueryPlanner()
        self.reflection_engine = reflection_engine or ReflectionEngine()
        self.compressor = compressor
        self._confidence_scorer = ConfidenceScorer()
        self._initialized = False
        self.memory = memory or ConversationMemory(
            max_tokens=self.config.memory_max_tokens,
            summary_tokens=self.config.memory_summary_tokens,
        )

    async def initialize(self) -> None:
        self._initialized = True

    async def close(self) -> None:
        self._initialized = False

    async def query(self, query_text: str) -> AgenticRAGResponse:
        if not query_text or not query_text.strip():
            raise ValueError("Query text cannot be empty")
        start_time = time.time()
        try:
            memory_context = ""
            if self.config.enable_memory and self.memory:
                memory_context = self.memory.get_context()
                self.memory.add_message("user", query_text)
            response = await self._run_pipeline(query_text, start_time, memory_context=memory_context)
            if self.config.enable_memory and self.memory:
                self.memory.add_message("assistant", response.answer)
            return response
        except ValueError:
            raise
        except Exception as exc:
            raise RetrievalError(
                message=f"Agentic RAG pipeline failed: {exc}",
                details={"query": query_text},
            ) from exc

    async def _run_pipeline(self, query_text: str, start_time: float, memory_context: str = "") -> AgenticRAGResponse:
        context_query = self._build_context_query(query_text, memory_context)
        plan = self.query_planner.create_plan(context_query)
        all_tool_results: List[ToolResult] = []
        execution_steps: List[ExecutionStep] = []
        iteration = 1
        await self._execute_plan(plan, all_tool_results, execution_steps)
        answer = self._synthesize_answer(query_text, all_tool_results)
        quality: Optional[AnswerQualityAssessment] = None
        if self.config.enable_reflection:
            while iteration <= self.config.max_iterations:
                confidence = self._confidence_scorer.calculate(
                    all_tool_results, plan.intent_analysis.intent, iteration, answer,
                )
                quality = self.reflection_engine.assess_quality(
                    answer=answer, query=query_text, tool_results=all_tool_results,
                    query_plan=plan, iteration_count=iteration,
                )
                if not self.reflection_engine.should_iterate(quality, iteration, confidence):
                    break
                corrections = self.reflection_engine.generate_correction_strategies(quality)
                if not corrections:
                    break
                new_results = await self._apply_corrections(context_query, corrections, execution_steps)
                all_tool_results.extend(new_results)
                answer = self._synthesize_answer(query_text, all_tool_results)
                iteration += 1
        confidence = self._confidence_scorer.calculate(
            all_tool_results, plan.intent_analysis.intent, iteration, answer,
        )
        sources = self._collect_sources(all_tool_results)
        total_duration = (time.time() - start_time) * 1000
        trace = ExecutionTrace(
            steps=execution_steps, total_duration_ms=total_duration, iterations_used=iteration,
        )
        return AgenticRAGResponse(
            answer=answer, confidence=confidence, sources=sources, trace=trace, quality=quality,
        )

    def _build_context_query(self, query_text: str, memory_context: str) -> str:
        if memory_context:
            return f"{query_text}\n\nConversation context:\n{memory_context}"
        return query_text

    async def _execute_plan(self, plan: QueryPlan, all_tool_results: List[ToolResult], execution_steps: List[ExecutionStep]) -> None:
        while not plan.is_complete():
            ready_steps = plan.get_ready_steps()
            if not ready_steps:
                break
            for step in ready_steps:
                plan.update_step_status(step.id, StepStatus.IN_PROGRESS)
                step_start = time.time()
                tool_name = step.tool_selection.tool_name
                params = dict(step.tool_selection.parameters)
                if tool_name in ("vector_search", "web_search"):
                    params["query"] = step.sub_query
                elif tool_name == "calculator":
                    params["expression"] = step.sub_query
                result = await self.tool_registry.execute(tool_name, **params)
                step_duration = (time.time() - step_start) * 1000
                all_tool_results.append(result)
                status = StepStatus.COMPLETED if result.success else StepStatus.FAILED
                plan.update_step_status(step.id, status, result.model_dump() if result.data else None)
                execution_steps.append(ExecutionStep(
                    step_number=step.step_number, description=step.description,
                    tool_name=tool_name, tool_result=result,
                    duration_ms=step_duration, status=status.value,
                ))

    async def _apply_corrections(self, query: str, corrections: List[CorrectionStrategy], execution_steps: List[ExecutionStep]) -> List[ToolResult]:
        new_results: List[ToolResult] = []
        for correction in corrections[:2]:
            tool_name = "vector_search"
            if correction.action_type in ("expand_search", "verify_sources", "fill_gap", "refine_query"):
                refined_query = f"{query} {correction.description}"
                result = await self.tool_registry.execute(tool_name, query=refined_query, top_k=self.config.top_k)
            elif correction.action_type == "update_search":
                result = await self.tool_registry.execute("web_search", query=query, num_results=5)
                tool_name = "web_search"
            else:
                continue
            new_results.append(result)
            execution_steps.append(ExecutionStep(
                step_number=len(execution_steps) + 1,
                description=f"Correction: {correction.description[:80]}",
                tool_name=tool_name, tool_result=result,
                duration_ms=result.execution_time_ms,
                status="completed" if result.success else "failed",
            ))
        return new_results

    def _synthesize_answer(self, query: str, tool_results: List[ToolResult]) -> str:
        if not tool_results:
            return "No information available to answer this query."
        parts: List[str] = []
        for result in tool_results:
            if not result.success:
                continue
            if isinstance(result.data, dict):
                if "results" in result.data:
                    for item in result.data["results"]:
                        if isinstance(item, dict):
                            content = item.get("content", item.get("snippet", ""))
                            if content:
                                parts.append(str(content))
                elif "result" in result.data:
                    parts.append(f"Calculation result: {result.data['result']}")
        if not parts:
            return "No relevant information found for the query."
        seen: set[str] = set()
        unique_parts: List[str] = []
        for part in parts:
            if part not in seen:
                seen.add(part)
                unique_parts.append(part)
        return " ".join(unique_parts)

    def _collect_sources(self, tool_results: List[ToolResult]) -> List[Dict[str, Any]]:
        sources: List[Dict[str, Any]] = []
        for result in tool_results:
            if not result.success or not result.data:
                continue
            if isinstance(result.data, dict) and "results" in result.data:
                for item in result.data["results"]:
                    if isinstance(item, dict):
                        metadata = item.get("metadata", {}) if isinstance(item.get("metadata", {}), dict) else {}
                        custom = metadata.get("custom", {}) if isinstance(metadata.get("custom", {}), dict) else {}
                        offset_start = item.get("offset_start") or custom.get("offset_start")
                        offset_end = item.get("offset_end") or custom.get("offset_end")
                        page_number = item.get("page_number") or custom.get("page_number") or custom.get("page")
                        sources.append({
                            "tool": result.tool_name,
                            "content": item.get("content", item.get("snippet", "")),
                            "score": item.get("score", 0),
                            "metadata": metadata,
                            "citation": {
                                "document_id": item.get("document_id"),
                                "chunk_id": item.get("id"),
                                "offset_start": offset_start,
                                "offset_end": offset_end,
                                "page_number": page_number,
                                "source": item.get("source") or metadata.get("source"),
                            },
                        })
        return sources
