"""SMB case study: legal/accounting client intake and document request flow."""

import asyncio

from agentforge import DAG, Agent, AgentInput, DAGConfig, ExecutionEngine


async def main() -> None:
    intake = Agent(
        name="client_intake",
        instructions="Summarize new client requests and required documents.",
        llm="mock/mock-v1",
    )
    checklist = Agent(
        name="document_checklist",
        instructions="Draft a clear next-step checklist for the client.",
        llm="mock/mock-v1",
    )

    dag = DAG(config=DAGConfig(name="legal-accounting"))
    dag.add_node("intake", intake)
    dag.add_node("checklist", checklist)
    dag.add_edge("intake", "checklist")

    result = await ExecutionEngine().execute(
        dag,
        input=AgentInput(
            messages=[
                {"role": "user", "content": "Need business LLC formation and bookkeeping setup"}
            ]
        ),
    )
    print(result.outputs["checklist"].content)


if __name__ == "__main__":
    asyncio.run(main())
