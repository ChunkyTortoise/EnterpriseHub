"""SMB case study: local services lead qualification and follow-up."""

import asyncio

from agentforge import DAG, Agent, AgentInput, DAGConfig, ExecutionEngine


async def main() -> None:
    qualifier = Agent(
        name="lead_qualifier",
        instructions="Classify inbound local service leads as hot/warm/cold.",
        llm="mock/mock-v1",
    )
    followup = Agent(
        name="followup_writer",
        instructions="Draft a short follow-up asking for booking availability.",
        llm="mock/mock-v1",
    )

    dag = DAG(config=DAGConfig(name="local-services"))
    dag.add_node("qualifier", qualifier)
    dag.add_node("followup", followup)
    dag.add_edge("qualifier", "followup")

    result = await ExecutionEngine().execute(
        dag,
        input=AgentInput(
            messages=[{"role": "user", "content": "Need weekly lawn care quote, start this week"}]
        ),
    )
    print(result.outputs["followup"].content)


if __name__ == "__main__":
    asyncio.run(main())
