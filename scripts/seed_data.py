"""Sample tickets to test the pipeline locally."""

SAMPLE_TICKETS = [
    {
        "title": "VPN no conecta desde casa",
        "description": "Usuario reporta que desde el día de ayer no puede conectar a la VPN corporativa. "
        "Recibe error 800. Ya reinició el equipo y el router.",
        "source": "freshservice",
    },
    {
        "title": "Solicitud de licencia Adobe Creative Cloud",
        "description": "Nuevo diseñador necesita licencia de Adobe CC para empezar el lunes. "
        "Enviar a user@company.com",
        "source": "freshservice",
    },
    {
        "title": "Outlook no envía correos",
        "description": "Desde las 14hs no puede enviar correos. Recibe mensaje de "
        "que el servidor SMTP no responde. Recibir sí funciona.",
        "source": "zendesk",
    },
    {
        "title": "Acceso denegado a carpeta compartida",
        "description": "Al intentar acceder a \\\\server\\finanzas\\ da acceso denegado. "
        "Usuario pertenece al grupo Contabilidad.",
        "source": "zendesk",
    },
]


def print_samples() -> None:
    for i, t in enumerate(SAMPLE_TICKETS, 1):
        print(f"{i}. [{t['source']}] {t['title']}")


if __name__ == "__main__":
    print_samples()
