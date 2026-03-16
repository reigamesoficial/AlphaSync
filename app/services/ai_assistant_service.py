"""
AI Assistant Service — AlphaSync

Responsabilidades:
  1. Humanizar as respostas do bot (tornar mais naturais, sem alterar lógica).
  2. Interpretar mensagens complexas do cliente para mapear ao step correto.
  3. Guiar o cliente dentro do fluxo quando estiver confuso.

Regras de segurança:
  - A IA nunca altera valores, medidas ou cálculos.
  - A IA nunca decide etapas do fluxo.
  - A IA nunca acessa dados de outra empresa.
  - Degrada graciosamente: se falhar ou key não estiver configurada,
    retorna o texto original sem exceção.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("alphasync.ai")

_OPENAI_AVAILABLE = False
try:
    from openai import OpenAI  # noqa: F401
    _OPENAI_AVAILABLE = True
except ImportError:
    pass


def _get_client():
    if not _OPENAI_AVAILABLE:
        return None
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _build_company_context(company_ctx: dict[str, Any]) -> str:
    lines = []
    company_name = company_ctx.get("company_name") or "a empresa"
    bot_name = company_ctx.get("bot_name") or "Assistente"
    service_domain = company_ctx.get("service_domain") or "serviços gerais"
    tone = company_ctx.get("tone") or "amigável e profissional"

    lines.append(f"Empresa: {company_name}")
    lines.append(f"Nome do bot: {bot_name}")
    lines.append(f"Segmento: {service_domain}")
    lines.append(f"Tom de comunicação: {tone}")
    return "\n".join(lines)


def humanize_bot_response(
    text: str,
    *,
    company_ctx: dict[str, Any] | None = None,
    current_step: str | None = None,
) -> str:
    """
    Reformula o texto do bot para soar mais natural e amigável.
    Retorna o texto original se a IA não estiver disponível ou falhar.

    Regras aplicadas ao modelo:
      - Manter exatamente o mesmo conteúdo e instruções ao cliente.
      - Não inventar informações.
      - Não alterar números, valores ou medidas.
      - Não remover opções de menu (listas numeradas, botões, etc.).
      - Ser conciso: não ultrapassar 20% a mais de caracteres que o original.
    """
    if not text or not text.strip():
        return text

    client = _get_client()
    if client is None:
        return text

    ctx = company_ctx or {}
    company_block = _build_company_context(ctx)

    system_prompt = f"""Você é o assistente de atendimento de uma empresa.
{company_block}

Sua tarefa: reformular a mensagem do bot para soar mais natural e amigável, 
mantendo EXATAMENTE o mesmo conteúdo, instruções e opções de menu.

Regras estritas:
- Não altere números, valores monetários ou medidas.
- Não remova nenhuma opção de lista ou botão (ex: "1) Confirmar" deve permanecer).
- Não adicione informações que não estão no texto original.
- Não faça o texto mais longo que 20% do original.
- Responda apenas com o texto reformulado, sem explicações.
- Se o texto já estiver bom, retorne-o como está.
- Mantenha emojis se existirem; não adicione emojis excessivos."""

    user_prompt = f"Reformule esta mensagem do bot:\n\n{text}"
    if current_step:
        user_prompt += f"\n\n(Contexto: etapa atual do fluxo = {current_step})"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=600,
            temperature=0.4,
        )
        result = response.choices[0].message.content or ""
        result = result.strip()
        if result:
            return result
        return text
    except Exception as exc:
        logger.warning("AI humanize_bot_response failed: %s", exc)
        return text


def interpret_client_message(
    message: str,
    *,
    current_step: str,
    company_ctx: dict[str, Any] | None = None,
    extra_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Interpreta uma mensagem complexa do cliente e tenta extrair informações
    relevantes para o step atual do fluxo.

    Retorna um dict com:
      - "interpreted_text": str — texto normalizado/limpo para processar
      - "confidence": "high" | "medium" | "low"
      - "notes": str — o que a IA entendeu (para log)

    Se falhar, retorna {"interpreted_text": message, "confidence": "low", "notes": "fallback"}.

    Uso no fluxo:
      - Passar o resultado["interpreted_text"] para a lógica determinística.
      - A lógica determinística decide o que fazer; a IA apenas normaliza a entrada.
    """
    fallback = {"interpreted_text": message, "confidence": "low", "notes": "ai_unavailable"}

    if not message or not message.strip():
        return fallback

    client = _get_client()
    if client is None:
        return fallback

    ctx = company_ctx or {}
    extra = extra_context or {}

    step_hints = {
        "customer_name": "O cliente deve informar o nome completo.",
        "address_lookup": "O cliente deve informar o endereço completo de instalação.",
        "manual_measurements": (
            "O cliente deve informar medidas no formato: quantidade tipo largura x altura.\n"
            "Exemplo: '1 sacada 1,20 x 1,40' ou '2 janelas 1,00 x 1,20'.\n"
            "Extraia e normalize para esse formato se o cliente enviou de forma diferente."
        ),
        "network_color": (
            "O cliente deve escolher uma cor de rede. "
            "Cores possíveis: " + ", ".join(extra.get("colors", ["branca", "preta", "areia", "cinza"])) + "."
        ),
        "mesh_type": (
            "O cliente deve escolher um tipo de malha. "
            "Malhas possíveis: " + ", ".join(extra.get("meshes", ["3x3", "5x5", "10x10"])) + "."
        ),
        "plant_choice": "O cliente deve escolher uma planta/tipo de apartamento da lista apresentada.",
        "quote_confirm": "O cliente deve confirmar ou alterar o orçamento.",
    }
    hint = step_hints.get(current_step, f"Etapa atual: {current_step}.")

    system_prompt = f"""Você é um assistente especializado em interpretar mensagens de clientes
em um chatbot de atendimento de instalações.

Contexto da empresa:
{_build_company_context(ctx)}

Sua tarefa: analisar a mensagem do cliente e extrair a informação relevante 
para a etapa atual do fluxo de atendimento.

Etapa atual: {current_step}
{hint}

Responda APENAS em JSON no formato:
{{
  "interpreted_text": "texto normalizado que o sistema consegue processar",
  "confidence": "high|medium|low",
  "notes": "breve explicação do que você entendeu"
}}

Regras:
- "interpreted_text" deve ser algo que o sistema consegue processar diretamente.
- Se a mensagem já estiver clara, repita-a em "interpreted_text".
- Se não conseguir interpretar, use a mensagem original.
- Não invente informações que o cliente não forneceu.
- confidence="high" quando tem certeza, "medium" quando razoável, "low" quando incerto."""

    try:
        import json

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Mensagem do cliente: {message}"},
            ],
            max_tokens=300,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        parsed = json.loads(raw)
        return {
            "interpreted_text": str(parsed.get("interpreted_text") or message),
            "confidence": str(parsed.get("confidence") or "low"),
            "notes": str(parsed.get("notes") or ""),
        }
    except Exception as exc:
        logger.warning("AI interpret_client_message failed: %s", exc)
        return fallback


def explain_step_to_client(
    current_step: str,
    *,
    company_ctx: dict[str, Any] | None = None,
    extra_context: dict[str, Any] | None = None,
) -> str | None:
    """
    Gera uma mensagem explicando ao cliente o que ele precisa enviar na etapa atual,
    quando ele parecer confuso (mensagem inválida repetida).

    Retorna None se a IA não estiver disponível.
    """
    client = _get_client()
    if client is None:
        return None

    ctx = company_ctx or {}
    extra = extra_context or {}

    step_descriptions = {
        "customer_name": "nome completo do cliente",
        "address_lookup": "endereço completo de instalação (rua, número, bairro, cidade)",
        "manual_measurements": "medidas das áreas (ex: 1 sacada 1,20 x 1,40)",
        "network_color": "cor da rede escolhida",
        "mesh_type": "tipo de malha (ex: 3x3, 5x5)",
        "plant_choice": "escolha da planta/tipo de imóvel",
        "quote_confirm": "confirmação ou alteração do orçamento",
    }
    desc = step_descriptions.get(current_step, current_step)

    system_prompt = f"""Você é um assistente de atendimento amigável.
{_build_company_context(ctx)}

Gere uma mensagem curta e amigável explicando ao cliente o que ele precisa enviar.
O cliente parece confuso na etapa: {current_step}.
O que precisamos: {desc}.

Seja direto, amigável e dê um exemplo prático quando fizer sentido.
Máximo de 3 linhas. Responda apenas com o texto da mensagem."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}],
            max_tokens=200,
            temperature=0.5,
        )
        result = (response.choices[0].message.content or "").strip()
        return result or None
    except Exception as exc:
        logger.warning("AI explain_step_to_client failed: %s", exc)
        return None
