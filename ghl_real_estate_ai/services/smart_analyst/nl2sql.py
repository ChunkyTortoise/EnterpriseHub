"""Natural language to SQL generator for Smart Analyst."""
from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import create_engine, inspect, text

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.core.llm_client import get_llm_client
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class NL2SQLGenerator:
    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url or settings.database_url
        self.llm_client = get_llm_client()

    def get_schema(self) -> Dict[str, List[str]]:
        if not self.database_url:
            return {}
        try:
            engine = create_engine(self.database_url)
            inspector = inspect(engine)
            schema: Dict[str, List[str]] = {}
            for table in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns(table)]
                schema[table] = columns
            return schema
        except Exception as exc:
            logger.error(f"NL2SQL schema inspection failed: {exc}")
            return {}

    async def generate_sql(self, question: str, schema: Optional[Dict[str, List[str]]] = None) -> str:
        schema = schema or self.get_schema()
        prompt = f"""
        You are a SQL generator. Create a single SELECT query based on the question.
        Use only the tables/columns provided. Do not generate write queries.

        Schema: {schema}
        Question: {question}
        """
        if hasattr(self.llm_client, "agenerate"):
            response = await self.llm_client.agenerate(prompt=prompt, max_tokens=300, temperature=0.1)
        else:
            response = self.llm_client.generate(prompt=prompt, max_tokens=300, temperature=0.1)
        sql = response.content.strip() if response and response.content else ""
        if sql.startswith("```"):
            sql = sql.split("```", 2)[1].strip()
        sql = sql.strip().rstrip(";")

        if not sql.lower().startswith("select") and not sql.lower().startswith("with"):
            raise ValueError("Generated SQL is not a SELECT query")

        return sql + ";"
