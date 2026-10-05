# PR Finança — 2 robôs Tecnicon

Este pacote separa a coleta em dois robôs:

1. `robo_receber.py`
   - Mantém o fluxo do relatório que já funcionava.
   - Abre **BA > Finanças > Contas a Pagar e Contas a Receber Pendentes por Período**.
   - Usa o perfil **MARLON4**, quando disponível.
   - Baixa um dia útil por vez para evitar o problema de sessão do Tecnicon.
   - Salva em `CSV_RECEBER`.

2. `robo_previsao_saida.py`
   - Abre **ERP > Finanças > Contas a Pagar > Relatórios > A Pagar a Vencer > A Pagar/Vencer por Vencimento**.
   - Preenche **Vencimento Inicial** e **Vencimento Final**.
   - Mantém/ativa **Vencimento Programado**.
   - Mantém/ativa **Imprimir Previsão de Saída**.
   - Seleciona filiais 1 até 3.
   - Clica em **Imprimir**.
   - Escolhe **CSV** na tela seguinte e gera o arquivo.
   - Salva em `CSV_PREVISAO_SAIDA`.

## Instalação

```bash
pip install playwright
python -m playwright install chromium
```

## Executar o robô de receber

```bash
python robo_receber.py 01/10/2026 31/10/2026
```

## Executar o robô de previsão de saída

```bash
python robo_previsao_saida.py 01/10/2026 30/11/2026
```

### Importante

- O login continua sendo manual.
- Usuário e senha não ficam gravados no código.
- O segundo robô foi montado com base nas telas enviadas, especialmente no relatório
  **A Pagar/Vencer por Vencimento** e na opção **Imprimir Previsão de Saída**.
- Como o HTML do Tecnicon pode variar entre perfis/versões, o segundo robô usa vários
  fallbacks de localização. O primeiro teste deve ser feito com um período pequeno.
