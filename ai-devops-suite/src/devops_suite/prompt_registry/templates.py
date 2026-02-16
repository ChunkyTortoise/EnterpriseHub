"""Jinja2-based prompt template management with variable validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from jinja2 import Environment, TemplateSyntaxError, UndefinedError, meta


@dataclass
class TemplateInfo:
    template_id: str
    name: str
    content: str
    variables: list[str]
    description: str = ""


class PromptTemplateManager:
    """Manages Jinja2-based prompt templates with variable extraction and validation."""

    def __init__(self) -> None:
        self._env = Environment()
        self._templates: dict[str, TemplateInfo] = {}

    def register(self, template_id: str, name: str, content: str,
                 description: str = "") -> TemplateInfo:
        variables = self.extract_variables(content)
        info = TemplateInfo(
            template_id=template_id, name=name, content=content,
            variables=variables, description=description,
        )
        self._templates[template_id] = info
        return info

    def render(self, template_id: str, variables: dict[str, str]) -> str:
        info = self._templates.get(template_id)
        if not info:
            raise KeyError(f"Template '{template_id}' not found")
        template = self._env.from_string(info.content)
        try:
            return template.render(**variables)
        except UndefinedError as e:
            raise ValueError(f"Missing variable: {e}")

    def validate(self, template_id: str, variables: dict[str, str]) -> list[str]:
        info = self._templates.get(template_id)
        if not info:
            return [f"Template '{template_id}' not found"]
        errors = []
        for var in info.variables:
            if var not in variables:
                errors.append(f"Missing required variable: {var}")
        return errors

    def extract_variables(self, content: str) -> list[str]:
        try:
            ast = self._env.parse(content)
            return sorted(meta.find_undeclared_variables(ast))
        except TemplateSyntaxError:
            # Fallback to regex
            return sorted(set(re.findall(r"\{\{\s*(\w+)\s*\}\}", content)))

    def get_template(self, template_id: str) -> TemplateInfo | None:
        return self._templates.get(template_id)

    def list_templates(self) -> list[TemplateInfo]:
        return list(self._templates.values())

    def delete_template(self, template_id: str) -> bool:
        return self._templates.pop(template_id, None) is not None
