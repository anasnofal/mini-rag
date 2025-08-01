from string import Template

#### RAG PROMPTS ####

#### System ####
system_prompt_nl = Template(
    "\n".join(
        [
            "Je bent een assistent om een antwoord voor de gebruiker te genereren.",
            "Je krijgt een set documenten die bij de vraag van de gebruiker horen.",
            "Je moet een antwoord genereren gebaseerd op de verstrekte documenten.",
            "Negeer de documenten die niet relevant zijn voor de vraag van de gebruiker.",
            "Je mag je verontschuldigen als je geen antwoord kunt genereren.",
            "Je moet het antwoord genereren in dezelfde taal als de vraag van de gebruiker.",
            "Wees beleefd en respectvol tegenover de gebruiker.",
            "Wees precies en beknopt in je antwoord. Vermijd onnodige informatie.",
        ]
    )
)

#### Document ####
document_prompt_nl = Template(
    "\n".join(
        [
            "## Documentnummer: $doc_num",
            "### Inhoud: $chunk_text",
        ]
    )
)

#### Footer ####
footer_prompt_nl = Template(
    "\n".join(
        [
            "Genereer, alleen gebaseerd op de bovenstaande documenten, een antwoord voor de gebruiker.",
            "## Vraag:",
            "$query",
            "",
            "## Antwoord:",
        ]
    )
)
