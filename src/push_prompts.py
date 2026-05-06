"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
        full_prompt_name = f"{username}/{prompt_name}" if username else prompt_name
        print(f"Publicando prompt: {full_prompt_name}")

        chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_data["system_prompt"]),
                ("human", prompt_data.get("user_prompt", "{bug_report}")),
            ]
        )

        commit_message = (
            f"{prompt_data.get('description', 'Prompt otimizado')} "
            f"| Técnicas: {', '.join(prompt_data.get('techniques_applied', []))}"
        )
        tags = prompt_data.get("tags", [])

        # Compatibilidade com assinaturas diferentes do hub.push entre versões.
        visibility = "público"
        try:
            try:
                hub.push(
                    full_prompt_name,
                    object=chat_prompt,
                    new_repo_is_public=True,
                    description=prompt_data.get("description", ""),
                    tags=tags,
                    commit_message=commit_message,
                )
            except TypeError:
                hub.push(full_prompt_name, object=chat_prompt, new_repo_is_public=True)
        except Exception as public_exc:
            error_text = str(public_exc).lower()
            if "cannot create a prompt for another tenant" in error_text:
                fallback_name = prompt_name
                print(
                    "⚠️  USERNAME_LANGSMITH_HUB não pertence ao tenant atual. "
                    f"Repetindo push sem namespace: {fallback_name}"
                )
                hub.push(fallback_name, object=chat_prompt, new_repo_is_public=False)
                visibility = "privado"
            elif "cannot create a public prompt" in error_text and "hub handle" in error_text:
                print("⚠️  Handle público ainda não inicializado. Publicando prompt como PRIVADO para não bloquear a avaliação.")
                try:
                    hub.push(full_prompt_name, object=chat_prompt, new_repo_is_public=False)
                except Exception as private_exc:
                    private_error = str(private_exc).lower()
                    if "cannot create a prompt for another tenant" in private_error:
                        fallback_name = prompt_name
                        print(
                            "⚠️  USERNAME_LANGSMITH_HUB não pertence ao tenant atual. "
                            f"Repetindo push sem namespace: {fallback_name}"
                        )
                        hub.push(fallback_name, object=chat_prompt, new_repo_is_public=False)
                    else:
                        raise
                visibility = "privado"
            else:
                raise

        print(f"✓ Push concluído com sucesso (repositório {visibility})")
        return True
    except Exception as exc:
        error_text = str(exc).lower()
        if "nothing to commit" in error_text:
            print("✓ Prompt já estava atualizado no LangSmith (sem alterações para commit)")
            return True

        print(f"❌ Erro ao publicar prompt: {exc}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ["description", "system_prompt", "user_prompt", "version", "techniques_applied"]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    if not prompt_data.get("system_prompt", "").strip():
        errors.append("system_prompt está vazio")

    if not prompt_data.get("user_prompt", "").strip():
        errors.append("user_prompt está vazio")

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append("O prompt deve listar ao menos 2 técnicas em techniques_applied")

    full_text = f"{prompt_data.get('system_prompt', '')}\n{prompt_data.get('user_prompt', '')}"
    if "[TODO]" in full_text or "TODO" in full_text:
        errors.append("Prompt contém TODO pendente")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    yaml_data = load_yaml("prompts/bug_to_user_story_v2.yml")
    if not yaml_data or "bug_to_user_story_v2" not in yaml_data:
        print("❌ Estrutura inválida em prompts/bug_to_user_story_v2.yml")
        print("   Esperado: chave raiz 'bug_to_user_story_v2'")
        return 1

    prompt_name = "bug_to_user_story_v2"
    prompt_data = yaml_data[prompt_name]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido. Corrija os erros abaixo:")
        for error in errors:
            print(f"   - {error}")
        return 1

    success = push_prompt_to_langsmith(prompt_name, prompt_data)
    if success:
        username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
        published_name = f"{username}/{prompt_name}" if username else prompt_name
        print(f"\n✅ Prompt publicado: {published_name}")
        print("Próximo passo: python src/evaluate.py")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
