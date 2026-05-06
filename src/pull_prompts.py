"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def _extract_template(message_prompt_template) -> str:
    """Extrai template textual de mensagens do ChatPromptTemplate."""
    prompt_obj = getattr(message_prompt_template, "prompt", None)
    if prompt_obj is None:
        return ""

    return getattr(prompt_obj, "template", "") or ""


def pull_prompts_from_langsmith():
    """Faz pull do prompt base e salva no YAML local."""
    prompt_name = "leonanluppi/bug_to_user_story_v1"
    output_path = "prompts/bug_to_user_story_v1.yml"

    try:
        print(f"Puxando prompt do LangSmith Hub: {prompt_name}")
        prompt_obj = hub.pull(prompt_name)

        messages = getattr(prompt_obj, "messages", [])
        system_prompt = ""
        user_prompt = "{bug_report}"

        for message in messages:
            message_type = message.__class__.__name__.lower()
            template = _extract_template(message)

            if not template:
                continue

            if "system" in message_type and not system_prompt:
                system_prompt = template
            elif ("human" in message_type or "user" in message_type) and user_prompt == "{bug_report}":
                user_prompt = template

        if not system_prompt:
            raise ValueError("Não foi possível extrair system_prompt do prompt puxado")

        prompt_payload = {
            "bug_to_user_story_v1": {
                "description": "Prompt para converter relatos de bugs em User Stories",
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "version": "v1",
                "source_prompt": prompt_name,
                "tags": ["bug-analysis", "user-story", "product-management"],
            }
        }

        if not save_yaml(prompt_payload, output_path):
            return False

        print(f"✓ Prompt salvo em: {output_path}")
        return True
    except Exception as exc:
        print(f"❌ Erro ao fazer pull do prompt: {exc}")
        return False


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    success = pull_prompts_from_langsmith()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
