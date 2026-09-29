# PR Finança

Versão revisada conforme o modelo Excel enviado pelo usuário.

## Regras desta versão

- A linha 3 do Excel é a apresentação do dia: `dd/mm - Dia-da-semana`.
- As tabelas pequenas de `CONTAS À PAGAR` usam a referência da linha 3 para mostrar a data com o dia da semana.
- A linha 4 permanece como data técnica para as fórmulas do resumo.
- `CONTAS À PAGAR` no resumo inclui fornecedores + impostos.
- Impostos **não possuem bloco/planilha separada**.
- Nas tabelas pequenas de cada data, impostos aparecem junto com os fornecedores, mantendo `Duplicata | Nome | Valor`, com `[IMPOSTO]` no início do nome para identificação.
- Cliente continua separado de fornecedor: cliente entra em `CONTAS À RECEBER` e recebe regra D+ da carteira; fornecedor e imposto usam a data original de saída.
- Carteiras novas são detectadas automaticamente e, enquanto não houver D+ cadastrado, usam D+1 provisoriamente e são sinalizadas no painel.
