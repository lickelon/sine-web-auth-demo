from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parents[1] / "templates")
)


def render_template(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    status_code: int = 200,
):
    merged_context: dict[str, Any] = {}
    if context:
        merged_context.update(context)
    return templates.TemplateResponse(
        request,
        template_name,
        merged_context,
        status_code=status_code,
    )
