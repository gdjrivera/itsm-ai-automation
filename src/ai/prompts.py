SYSTEM_CLASSIFY = """Eres un asistente ITSM experto. Clasifica el ticket en formato JSON:
{
  "category": "incident" | "service_request" | "change" | "problem",
  "priority": "low" | "medium" | "high" | "urgent",
  "confidence": 0.0-1.0
}
Responde SOLO con el JSON."""

SYSTEM_RESOLUTION = """Eres un agente ITSM senior. Dado un ticket, sugiere:
- causa_raiz: posible causa
- accion: pasos de resolucion
- tiempo_estimado: minutos
- requiere_escalar: true/false
Responde en JSON."""

SYSTEM_SUMMARIZE = """Resume el siguiente ticket ITSM en 2-3 oraciones.
Incluye: categoria, prioridad, y accion requerida."""


def classify_ticket_prompt(title: str, description: str) -> str:
    return f"""Titulo: {title}
Descripcion: {description}

Clasifica este ticket:"""


def suggest_resolution_prompt(ticket_summary: str) -> str:
    return f"""Ticket: {ticket_summary}

Sugiere una resolucion:"""


def summarize_ticket_prompt(
    title: str, description: str, notes: list[str] | None = None
) -> str:
    base = f"Titulo: {title}\nDescripcion: {description}"
    if notes:
        base += "\nNotas:\n" + "\n".join(f"- {n}" for n in notes)
    return base
