# Guia de Contribuição — Leilão de Química 🧪🎲

Obrigado pelo interesse em aprimorar o **Leilão de Química**! Este projeto segue uma arquitetura rigorosa orientada por especificações (**Spec-Driven Architecture**), onde nenhum dado científico é duplicado e toda questão de cálculo é provada matematicamente via `SymPy`.

---

## Como Adicionar uma Nova Questão

1. **Verifique a Base de Conhecimento (`SPEC-00-fundamentos`):**
   - Certifique-se de que os conceitos (`concepts.yaml`), fórmulas (`formulas.yaml`), elementos (`elements.yaml`) e unidades (`units.yaml`) necessários já estão cadastrados em `specs/SPEC-00-fundamentos/knowledge/`.
   - Todo distrator conceitual deve apontar para um erro comum documentado (`mistake_ref`) no conceito correspondente.

2. **Escreva a Questão no Padrão Binário A ou B (`SPEC-01-questoes`):**
   - Adicione a questão em um dos arquivos YAML dentro de `specs/SPEC-01-questoes/questions/` (Nível 1, Nível 2 ou Nível 3).
   - Toda questão deve possuir exatamente **duas alternativas (`A` e `B`)**: uma cientificamente correta e outra construída sobre uma **concepção alternativa plausível** (sem respostas absurdas ou óbvias).
   - Se a questão envolver cálculo numérico, inclua o bloco `calc` (ou `steps`) referenciando a fórmula da base (`CHEM-FRM-...`) para que o validador recalcule o gabarito automaticamente.

3. **Rode os Validadores e Testes:**
   ```bash
   python specs/SPEC-00-fundamentos/validate_knowledge.py
   python specs/SPEC-01-questoes/validate_questions.py
   python specs/SPEC-02-mecanica/validate_rules.py
   ```

4. **Regenere os Arquivos HTML de Impressão (`001` a `023`):**
   ```bash
   python specs/SPEC-03-gerador/deck_builder.py
   python -m pytest specs/SPEC-03-gerador
   ```
   Isso atualizará automaticamente o baralho duplex, o Guia do Mestre, a Folha do Aluno e o Manual do Professor em `specs/SPEC-04-impressao/`.
