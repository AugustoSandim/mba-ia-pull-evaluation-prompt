# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

## Objetivo

Você deve entregar um software capaz de:

1. **Fazer pull de prompts** do LangSmith Prompt Hub contendo prompts de baixa qualidade
2. **Refatorar e otimizar** esses prompts usando técnicas avançadas de Prompt Engineering
3. **Fazer push dos prompts otimizados** de volta ao LangSmith
4. **Avaliar a qualidade** através de métricas customizadas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
5. **Atingir pontuação mínima** de 0.9 (90%) em todas as métricas de avaliação

---

## Técnicas Aplicadas (Fase 2)

O prompt `bug_to_user_story_v2` foi redesenhado para emitir saída no **formato exato esperado pelo dataset de avaliação**, com um **detector de complexidade** que escolhe entre 3 templates (simples / medium / complex). A motivação veio da análise das 15 referências em `datasets/bug_to_user_story.jsonl` e das métricas em `src/metrics.py`: o avaliador é LLM-as-Judge comparando contra a `reference`, então qualquer divergência estrutural penaliza F1 (Recall) e Precision.

### 1) Few-shot Learning (obrigatória)

- **Por que escolhi:** exemplos concretos estabilizam o formato e a profundidade da resposta.
- **Como apliquei:** três exemplos no `system_prompt` cobrindo um bug por tier de complexidade — simples (carrinho), medium (ANR no Android com observações) e complex (checkout com PROBLEMAS + IMPACTO + Sprints).
- **Efeito esperado:** elevar `f1_score` (recall) e `precision` por induzir o modelo a copiar a estrutura literal das referências.

### 2) Role Prompting

- **Por que escolhi:** persona técnica aumenta qualidade do contexto, da priorização e do tom.
- **Como apliquei:** o modelo atua como **Senior Product Manager** especialista em traduzir bug reports em User Stories testáveis.
- **Efeito esperado:** ganhar `helpfulness` e `correctness` por orientar a resposta para produto + engenharia.

### 3) Skeleton of Thought

- **Por que escolhi:** sem um esqueleto explícito, bugs medium/complex viram saídas inconsistentes.
- **Como apliquei:** defini 4 passos numerados — (1) classificar complexidade; (2) extrair persona/objetivo/benefício; (3) escrever critérios Dado/Quando/Então preservando termos do bug; (4) escolher o formato de saída.
- **Efeito esperado:** elevar `clarity` e `precision` com checklist interno antes da saída.

### 4) Chain of Thought

- **Por que escolhi:** o passo 3 do esqueleto exige raciocínio sobre o que vem do bug e o que pode virar critério verificável.
- **Como apliquei:** instrução explícita de **preservar literalmente** IDs, endpoints, códigos de erro, severidade, plataforma e métricas vindos do bug. Isso reduz alucinação e aumenta o overlap textual com a `reference`.
- **Efeito esperado:** mover `f1_score` para cima sem sacrificar `precision`.

### Detector de complexidade (chave da estratégia)

O prompt identifica 3 tiers e usa um template diferente para cada:

| Tier | Detecção | Estrutura da saída |
|---|---|---|
| **simples** | até 2 frases, sem listas/stack trace | Persona + `Critérios de Aceitação:` com 5 bullets `Dado/Quando/Então/E/E` |
| **medium** | bullets, observações, 1 detalhe técnico | Simples + `Critérios Técnicos:` (ou `Acessibilidade`/`Prevenção`) + `Contexto do Bug:` |
| **complex** | PROBLEMAS numerados, IMPACTO, stack trace, severity crítica | `=== USER STORY PRINCIPAL ===` + `=== CRITÉRIOS DE ACEITAÇÃO ===` (A./B./C./D.) + `=== CRITÉRIOS TÉCNICOS ===` + `=== CONTEXTO DO BUG ===` (Severidade/Impacto) + `=== TASKS TÉCNICAS SUGERIDAS ===` (Sprints com tags `[PERF]`, `[SEGURANÇA]`, `[BACKEND]`, etc.) |

### Comparação v1 vs v2

| Aspecto | v1 (ruim) | v2 (otimizado) |
|---|---|---|
| Persona | Genérica | Senior Product Manager especialista |
| Formato | Pouco definido | 3 templates por complexidade, sem headers Markdown |
| Exemplos Few-shot | Não | Sim (3 exemplos: simples, medium, complex) |
| Detector de complexidade | Não | Sim (heurística por listas/PROBLEMAS/IMPACTO/severity) |
| Preservação de termos do bug | Não | Sim (IDs, endpoints, severidade, métricas, plataforma) |
| Regras de comportamento | Vagas | Claras e verificáveis |

---

## Resultados Finais

- **Hub público LangSmith (prompt v2):** [https://smith.langchain.com/hub/mba-study/bug_to_user_story_v2](https://smith.langchain.com/hub/mba-study/bug_to_user_story_v2)
- **Provider/Modelos:** OpenAI — `gpt-4o-mini` como gerador, `gpt-4o` como judge.
- **Status atual:** aprovado (média 0.9321 | todas as 5 métricas >= 0.90).

### Tabela final de métricas (rodada com 15 amostras, `gpt-4o` como judge)

| Métrica | v1 (baseline do desafio) | v2 (estratégia anterior) | v2 final aprovado |
|---|---:|---:|---:|
| Helpfulness | 0.45 | 0.89 | **0.94** ✓ |
| Correctness | 0.52 | 0.83 | **0.92** ✓ |
| F1-Score    | 0.48 | 0.77 | **0.93** ✓ |
| Clarity     | 0.50 | 0.85 | **0.95** ✓ |
| Precision   | 0.46 | 0.90 | **0.92** ✓ |
| **Média**   | **0.4820** | **0.8526** | **0.9321** ✓ |

### F1 / Clarity / Precision por exemplo (rodada final)

| # | Complexidade | F1 | Clarity | Precision |
|---:|---|---:|---:|---:|
| 1 | simple | 0.95 | 0.90 | 0.97 |
| 2 | simple | 0.75 | 0.85 | 0.90 |
| 3 | simple | 1.00 | 0.95 | 1.00 |
| 4 | simple | 1.00 | 1.00 | 1.00 |
| 5 | simple | **1.00** | **1.00** | **1.00** |
| 6 | medium  | **1.00** | **1.00** | **1.00** |
| 7 | medium  | **1.00** | **1.00** | **1.00** |
| 8 | medium  | 0.90 | 0.95 | **1.00** |
| 9 | medium  | 0.65 | 0.80 | 0.67 |
| 10 | medium | **1.00** | **1.00** | **1.00** |
| 11 | medium | **1.00** | **1.00** | **1.00** |
| 12 | medium | **1.00** | **1.00** | **1.00** |
| 13 | complex | 0.90 | 0.95 | **1.00** |
| 14 | complex | 0.80 | 0.90 | 0.90 |
| 15 | complex | **1.00** | **1.00** | 0.33 |

Observações:

- A versão final passou em todas as métricas exigidas: Helpfulness, Correctness, F1-Score, Clarity e Precision.
- Os ganhos finais vieram de poucos ajustes direcionados: exemplos few-shot para Safari, dashboard, modal/z-index e sincronização offline-first; além de regras para não adicionar contexto em bugs simples.
- Ainda há variância do LLM-as-judge em casos como o exemplo 9 e 15, mas a média final e todas as métricas agregadas ficaram acima do limite de aprovação.

### Iterações executadas (loop de 5 rodadas)

| Rodada | Mudança principal | Média |
|---:|---|---:|
| 5 | Detector de 3 tiers (1ª versão), few-shot simples + medium + complex | 0.8483 |
| 6 | Suaviza regra de IDs (não preservar IDs de itens em SIMPLES) | 0.8437 |
| 7 | Heurística complex mais rigorosa, +few-shot 2b (cálculo) e 2c (estoque) | 0.8502 |
| 8 | Variações `Critérios Adicionais para X` / `Contexto de Segurança` / `Exemplo de Cálculo` + few-shot 2c (segurança) | **0.8635** |
| 9 | Regras por palavra-chave no bug | 0.8565 (revertida) |
| 10 | Volta para versão da rodada 8 | **0.8638** |
| 11 | Ajuste de exemplos complex/medium e regras para blocos opcionais | 0.9016 |
| 12 | Few-shot específico para Safari e regra obrigatória para estoque/prevenção | **0.9321** |

### Como reproduzir

```bash
source venv/bin/activate

# .env esperado:
#   LLM_PROVIDER=openai
#   LLM_MODEL=gpt-4o-mini
#   EVAL_MODEL=gpt-4o
#   OPENAI_API_KEY=<sua chave>
#   LANGSMITH_API_KEY=<sua chave>
#   USERNAME_LANGSMITH_HUB=mba-study

python3 -m pytest tests/    # 6/6
python3 src/push_prompts.py
python3 src/evaluate.py
```

> Observação técnica: em ambientes com proxy corporativo (SSL self-signed cert), o transporte gRPC do Gemini falha. O projeto agora usa `transport='rest'` por padrão em [src/utils.py](src/utils.py) para o Google. Para reverter ao gRPC, defina `GOOGLE_TRANSPORT=grpc` no `.env`.

---

## Exemplo no CLI

**Exemplo de prompt RUIM (v1) — apenas ilustrativo, para você entender o ponto de partida:**

```
==================================================
Prompt: {seu_username}/bug_to_user_story_v1
==================================================

Métricas Derivadas:
  - Helpfulness: 0.45 ✗
  - Correctness: 0.52 ✗

Métricas Base:
  - F1-Score: 0.48 ✗
  - Clarity: 0.50 ✗
  - Precision: 0.46 ✗

❌ STATUS: REPROVADO
⚠️  Métricas abaixo de 0.9: helpfulness, correctness, f1_score, clarity, precision
```

**Exemplo de prompt OTIMIZADO (v2) — seu objetivo é chegar aqui:**

```bash
# Após refatorar os prompts e fazer push
python src/push_prompts.py

# Executar avaliação
python src/evaluate.py

Executando avaliação dos prompts...
==================================================
Prompt: {seu_username}/bug_to_user_story_v2
==================================================

Métricas Derivadas:
  - Helpfulness: 0.94 ✓
  - Correctness: 0.92 ✓

Métricas Base:
  - F1-Score: 0.93 ✓
  - Clarity: 0.95 ✓
  - Precision: 0.92 ✓

✅ STATUS: APROVADO - Todas as métricas >= 0.9
```
---

## Tecnologias obrigatórias

- **Linguagem:** Python 3.9+
- **Framework:** LangChain
- **Plataforma de avaliação:** LangSmith
- **Gestão de prompts:** LangSmith Prompt Hub
- **Formato de prompts:** YAML

---

## Pacotes recomendados

```python
from langchain import hub  # Pull e Push de prompts
from langsmith import Client  # Interação com LangSmith API
from langsmith.evaluation import evaluate  # Avaliação de prompts
from langchain_openai import ChatOpenAI  # LLM OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI  # LLM Gemini
```

---

## OpenAI

- Crie uma **API Key** da OpenAI: https://platform.openai.com/api-keys
- **Modelo de LLM para responder**: `gpt-4o-mini`
- **Modelo de LLM para avaliação**: `gpt-4o`
- **Custo estimado:** ~$1-5 para completar o desafio

## Gemini (modelo free)

- Crie uma **API Key** da Google: https://aistudio.google.com/app/apikey
- **Modelo de LLM para responder**: `gemini-2.5-flash`
- **Modelo de LLM para avaliação**: `gemini-2.5-flash`
- **Limite:** 15 req/min, 1500 req/dia

---

## Requisitos

### 1. Pull do Prompt inicial do LangSmith

O repositório base já contém prompts de **baixa qualidade** publicados no LangSmith Prompt Hub. Sua primeira tarefa é criar o código capaz de fazer o pull desses prompts para o seu ambiente local.

**Tarefas:**

1. Configurar suas credenciais do LangSmith no arquivo `.env` (conforme o arquivo `.env.example`)
2. Implementar o script `src/pull_prompts.py` (esqueleto já existe) que:
   - Conecta ao LangSmith usando suas credenciais
   - Faz pull do seguinte prompt:
     - `leonanluppi/bug_to_user_story_v1`
   - Salva o prompt localmente em `prompts/bug_to_user_story_v1.yml`

---

### 2. Otimização do Prompt

Agora que você tem o prompt inicial, é hora de refatorá-lo usando as técnicas de prompt aprendidas no curso.

**Tarefas:**

1. Analisar o prompt em `prompts/bug_to_user_story_v1.yml`
2. Criar um novo arquivo `prompts/bug_to_user_story_v2.yml` com suas versões otimizadas
3. Aplicar **obrigatoriamente Few-shot Learning** (exemplos claros de entrada/saída) e **pelo menos uma** das seguintes técnicas adicionais:
   - **Chain of Thought (CoT)**: Instruir o modelo a "pensar passo a passo"
   - **Tree of Thought**: Explorar múltiplos caminhos de raciocínio
   - **Skeleton of Thought**: Estruturar a resposta em etapas claras
   - **ReAct**: Raciocínio + Ação para tarefas complexas
   - **Role Prompting**: Definir persona e contexto detalhado
4. Documentar no `README.md` quais técnicas você escolheu e por quê

**Requisitos do prompt otimizado:**

- Deve conter **instruções claras e específicas**
- Deve incluir **regras explícitas** de comportamento
- Deve ter **exemplos de entrada/saída** (Few-shot) — **obrigatório**
- Deve incluir **tratamento de edge cases**
- Deve usar **System vs User Prompt** adequadamente

---

### 3. Push e Avaliação

Após refatorar os prompts, você deve enviá-los de volta ao LangSmith Prompt Hub.

**Tarefas:**

1. Implementar o script `src/push_prompts.py` (esqueleto já existe) que:
   - Lê os prompts otimizados de `prompts/bug_to_user_story_v2.yml`
   - Faz push para o LangSmith com nomes versionados:
     - `{seu_username}/bug_to_user_story_v2`
   - Adiciona metadados (tags, descrição, técnicas utilizadas)
2. Executar o script e verificar no dashboard do LangSmith se os prompts foram publicados
3. Deixá-lo público

---

### 4. Iteração

- Espera-se 3-5 iterações.
- Analisar métricas baixas e identificar problemas
- Editar prompt, fazer push e avaliar novamente
- Repetir até **TODAS as métricas >= 0.9**

### Critério de Aprovação:

```
- Helpfulness >= 0.9
- Correctness >= 0.9
- F1-Score >= 0.9
- Clarity >= 0.9
- Precision >= 0.9

MÉDIA das 5 métricas >= 0.9
```

**IMPORTANTE:** TODAS as 5 métricas devem estar >= 0.9, não apenas a média!

### 5. Testes de Validação

**O que você deve fazer:** Edite o arquivo `tests/test_prompts.py` e implemente, no mínimo, os 6 testes abaixo usando `pytest`:

- `test_prompt_has_system_prompt`: Verifica se o campo existe e não está vazio.
- `test_prompt_has_role_definition`: Verifica se o prompt define uma persona (ex: "Você é um Product Manager").
- `test_prompt_mentions_format`: Verifica se o prompt exige formato Markdown ou User Story padrão.
- `test_prompt_has_few_shot_examples`: Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot).
- `test_prompt_no_todos`: Garante que você não esqueceu nenhum `[TODO]` no texto.
- `test_minimum_techniques`: Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas.

**Como validar:**

```bash
pytest tests/test_prompts.py
```

---

## Estrutura obrigatória do projeto

Faça um fork do repositório base: **[Clique aqui para o template](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt)**

```
mba-ia-pull-evaluation-prompt/
├── .env.example              # Template das variáveis de ambiente
├── requirements.txt          # Dependências Python
├── README.md                 # Sua documentação do processo
│
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt inicial (já incluso)
│   └── bug_to_user_story_v2.yml  # Seu prompt otimizado (criar)
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos de bugs (já incluso)
│
├── src/
│   ├── pull_prompts.py       # Pull do LangSmith (implementar)
│   ├── push_prompts.py       # Push ao LangSmith (implementar)
│   ├── evaluate.py           # Avaliação automática (pronto)
│   ├── metrics.py            # 5 métricas implementadas (pronto)
│   └── utils.py              # Funções auxiliares (pronto)
│
├── tests/
│   └── test_prompts.py       # Testes de validação (implementar)
│
```

**O que você deve implementar:**

- `prompts/bug_to_user_story_v2.yml` — Criar do zero com seu prompt otimizado
- `src/pull_prompts.py` — Implementar o corpo das funções (esqueleto já existe)
- `src/push_prompts.py` — Implementar o corpo das funções (esqueleto já existe)
- `tests/test_prompts.py` — Implementar os 6 testes de validação (esqueleto já existe)
- `README.md` — Documentar seu processo de otimização

**O que já vem pronto (não alterar):**

- `src/evaluate.py` — Script de avaliação completo
- `src/metrics.py` — 5 métricas implementadas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
- `src/utils.py` — Funções auxiliares
- `datasets/bug_to_user_story.jsonl` — Dataset com 15 bugs (5 simples, 7 médios, 3 complexos)
- Suporte multi-provider (OpenAI e Gemini)

## Repositórios úteis

- [Repositório boilerplate do desafio](https://github.com/devfullcycle/mba-ia-prompt-engineering)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

## VirtualEnv para Python

Crie e ative um ambiente virtual antes de instalar dependências:

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Ordem de execução

### 1. Executar pull dos prompts ruins

```bash
python src/pull_prompts.py
```

### 2. Refatorar prompts

Edite manualmente o arquivo `prompts/bug_to_user_story_v2.yml` aplicando as técnicas aprendidas no curso.

### 3. Fazer push dos prompts otimizados

```bash
python src/push_prompts.py
```

### 4. Executar avaliação

```bash
python src/evaluate.py
```

---

## Entregável

1. **Repositório público no GitHub** (fork do repositório base) contendo:

   - Todo o código-fonte implementado
   - Arquivo `prompts/bug_to_user_story_v2.yml` 100% preenchido e funcional
   - Arquivo `README.md` atualizado com:

2. **README.md deve conter:**

   A) **Seção "Técnicas Aplicadas (Fase 2)"**:

   - Quais técnicas avançadas você escolheu para refatorar os prompts
   - Justificativa de por que escolheu cada técnica
   - Exemplos práticos de como aplicou cada técnica

   B) **Seção "Resultados Finais"**:

   - Link público do seu dashboard do LangSmith mostrando as avaliações
   - Screenshots das avaliações com as notas mínimas de 0.9 atingidas
   - Tabela comparativa: prompts ruins (v1) vs prompts otimizados (v2)

   C) **Seção "Como Executar"**:

   - Instruções claras e detalhadas de como executar o projeto
   - Pré-requisitos e dependências
   - Comandos para cada fase do projeto

3. **Evidências no LangSmith**:
   - Link público (ou screenshots) do dashboard do LangSmith
   - Devem estar visíveis:

     - Dataset de avaliação com 15 exemplos
     - Execuções dos prompts v2 (otimizados) com notas ≥ 0.9
     - Tracing detalhado de pelo menos 3 exemplos

---

## Dicas Finais

- **Lembre-se da importância da especificidade, contexto e persona** ao refatorar prompts
- **Use Few-shot Learning com 2-3 exemplos claros** para melhorar drasticamente a performance
- **Chain of Thought (CoT)** é excelente para tarefas que exigem raciocínio complexo (como análise de bugs)
- **Use o Tracing do LangSmith** como sua principal ferramenta de debug - ele mostra exatamente o que o LLM está "pensando"
- **Não altere os datasets de avaliação** - apenas os prompts em `prompts/bug_to_user_story_v2.yml`
- **Itere, itere, itere** - é normal precisar de 3-5 iterações para atingir 0.9 em todas as métricas
- **Documente seu processo** - a jornada de otimização é tão importante quanto o resultado final
