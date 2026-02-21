"""SMB case study: clinic intake triage and appointment follow-up."""

import asyncio

from agentforge import DAG, Agent, AgentInput, DAGConfig, ExecutionEngine


async def main() -> None:
    intake = Agent(
        name="intake_triage",
        instructions="Categorize patient intake messages by urgency.",
        llm="mock/mock-v1",
    )
    reminders = Agent(
        name="appointment_followup",
        instructions="Generate concise appointment follow-up messages.",
        llm="mock/mock-v1",
    )

    dag = DAG(config=DAGConfig(name="clinic-intake"))
    dag.add_node("intake", intake)
    dag.add_node("reminders", reminders)
    dag.add_edge("intake", "reminders")

    result = await ExecutionEngine().execute(
        dag,
        input=AgentInput(
            messages=[
                {"role": "user", "content": "Patient has severe tooth pain, needs earliest slot"}
            ]
        ),
    )
    print(result.outputs["reminders"].content)


if __name__ == "__main__":
    asyncio.run(main())
