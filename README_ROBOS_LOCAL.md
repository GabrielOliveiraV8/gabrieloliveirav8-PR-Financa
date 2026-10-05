# Atualização automática pelo Tecnicon

O botão **🔄 Atualizar Tecnicon** do Streamlit agora chama os dois robôs:

1. **Receber** — baixa os dias úteis do período selecionado.
2. **Previsão de saída** — entra em **A Pagar/Vencer por Vencimento**, seleciona **Somente a Pagar**, mantém **Vencimento Programado** e **Imprimir Previsão de Saída**, seleciona as filiais 1 a 3 e gera o CSV.

Depois do download, o aplicativo lê automaticamente todos os CSVs existentes em `CSV_RECEBER`, sem precisar selecionar arquivo manualmente.

> O CSV da previsão de saída também é salvo em `CSV_PREVISAO_SAIDA`. A integração dele aos cálculos da previsão será feita depois de vermos o formato real que o Tecnicon gerar no primeiro teste. Não vamos inventar colunas nem misturar fornecedor/cliente incorretamente.

## Instalação no Windows

No terminal da pasta do sistema:

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

Execute:

```powershell
python -m streamlit run app.py
```

Na tela, escolha o período e clique em **🔄 Atualizar Tecnicon**.

Os navegadores abrirão para o login manual do Tecnicon. O robô não grava usuário nem senha.
