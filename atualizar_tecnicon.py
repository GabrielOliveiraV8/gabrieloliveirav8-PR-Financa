from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def rodar(script: str, ini: str, fim: str) -> int:
    caminho = BASE / script
    print("=" * 70)
    print(f"EXECUTANDO: {script} | {ini} até {fim}")
    print("=" * 70)
    proc = subprocess.run([sys.executable, str(caminho), ini, fim], cwd=str(BASE))
    return proc.returncode


def main():
    if len(sys.argv) < 3:
        print("Uso: python atualizar_tecnicon.py DD/MM/AAAA DD/MM/AAAA")
        raise SystemExit(1)

    ini, fim = sys.argv[1], sys.argv[2]

    # 1) Receber: baixa os dias úteis do período.
    rc1 = rodar("robo_receber.py", ini, fim)
    if rc1 != 0:
        print("[ATENÇÃO] O robô de receber terminou com erro.")

    # 2) Previsão de saída: gera o relatório A Pagar/Vencer por Vencimento.
    rc2 = rodar("robo_previsao_saida.py", ini, fim)
    if rc2 != 0:
        print("[ATENÇÃO] O robô de previsão de saída terminou com erro.")

    print("\n[ATUALIZAÇÃO] Os robôs terminaram.")
    print("[ATUALIZAÇÃO] O Streamlit pode ler automaticamente a pasta CSV_RECEBER.")
    raise SystemExit(0 if rc1 == 0 and rc2 == 0 else 1)


if __name__ == "__main__":
    main()
