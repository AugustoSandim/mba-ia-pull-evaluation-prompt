"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    @pytest.fixture(scope="class")
    def prompt_data(self):
        prompts = load_prompts("prompts/bug_to_user_story_v2.yml")
        assert prompts is not None, "Arquivo de prompt v2 não pôde ser carregado"
        assert "bug_to_user_story_v2" in prompts, "Chave 'bug_to_user_story_v2' não encontrada no YAML"
        return prompts["bug_to_user_story_v2"]

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompts = load_prompts("prompts/bug_to_user_story_v2.yml")
        assert "bug_to_user_story_v2" in prompts

        prompt = prompts["bug_to_user_story_v2"]
        assert "system_prompt" in prompt
        assert isinstance(prompt["system_prompt"], str)
        assert prompt["system_prompt"].strip() != ""

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data["system_prompt"].lower()
        role_keywords = [
            "você é",
            "product manager",
            "especialista",
            "persona",
        ]
        assert any(keyword in system_prompt for keyword in role_keywords)

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data["system_prompt"].lower()
        expects_markdown = "markdown" in system_prompt
        expects_user_story = "como " in system_prompt and "eu quero" in system_prompt and "para que" in system_prompt
        assert expects_markdown or expects_user_story

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data["system_prompt"].lower()
        few_shot_markers = [
            "few-shot",
            "exemplo",
            "entrada:",
            "saída esperada:",
        ]
        matches = sum(1 for marker in few_shot_markers if marker in system_prompt)
        assert matches >= 3

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        full_prompt_text = f"{prompt_data.get('system_prompt', '')}\n{prompt_data.get('user_prompt', '')}"
        assert "[TODO]" not in full_prompt_text
        assert "TODO" not in full_prompt_text

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list)
        assert len(techniques) >= 2

        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, f"Estrutura inválida: {errors}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])