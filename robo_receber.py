from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

from tecnicon_comum import (
    PORTAL_URL,
    abrir_csv_resultado,
    clicar_financas,
    clicar_texto_exato,
    esperar_loader_sumir,
    login_manual,
    selecionar_estoque,
    setar_input_por_id,
)

DOWNLOAD_DIR = Path(__file__).resolve().parent / "CSV_RECEBER"


def abrir_relatorio_receber(page):
    clicar_financas(page)

    nome = "Contas a Pagar e Contas a Receber Pendentes por Período"
    print(f"[RELATÓRIO] Abrindo: {nome}")
    if not clicar_texto_exato(page, nome):
        raise RuntimeError(f"Relatório não encontrado: {nome}")

    # O relatório antigo usa perfis salvos.
    print("[PERFIL] Procurando MARLON4...")
    perfil = page.get_by_text("MARLON4", exact=True)
    if perfil.count():
        perfil.first.click(timeout=30000, force=True)
        esperar_loader_sumir(page, 300000)
        time.sleep(3)

    return True


def abrir_parametros(page):
    for texto in ["Parâmetros de entrada", "Parâmetros"]:
        try:
            loc = page.get_by_text(texto, exact=False)
            if loc.count():
                loc.first.click(timeout=30000, force=True)
                time.sleep(2)
                return True
        except Exception:
            pass
    return False


def processar_receber(page, data_ini, data_fim):
    s_ini = data_ini.strftime("%d/%m/%Y")
    s_fim = data_fim.strftime("%d/%m/%Y")

    if not abrir_parametros(page):
        raise RuntimeError("Não foi possível abrir os parâmetros do relatório de receber.")

    # O relatório de receber usa DATAINICIAL / DATAFINAL.
    for _ in range(3):
        try:
            setar_input_por_id(page, "DATAINICIAL", s_ini)
            setar_input_por_id(page, "DATAFINAL", s_fim)
            time.sleep(1)

            ini = page.evaluate("document.getElementById('DATAINICIAL')?.value || ''")
            fim = page.evaluate("document.getElementById('DATAFINAL')?.value || ''")
            if ini == s_ini and fim == s_fim:
                break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError(f"O Tecnicon não confirmou as datas {s_ini} até {s_fim}.")

    print(f"[PROCESSAR] Receber: {s_ini} até {s_fim}")

    btns = [
        "[title='Processar Cubo']",
        "[title='Processar Cubo' i]",
        ".fa-play",
        "button:has-text('Processar Cubo')",
    ]
    for sel in btns:
        try:
            b = page.locator(sel).first
            if b.count():
                b.click(timeout=10000, force=True)
                break
        except Exception:
            continue
    else:
        page.evaluate(
            "document.querySelector(\"[title*='Processar Cubo' i], .fa-play\")?.click()"
        )

    esperar_loader_sumir(page, 180000)
    time.sleep(5)

    nome = f"receber_{data_ini:%Y%m%d}_{data_fim:%Y%m%d}.csv"
    return abrir_csv_resultado(page, DOWNLOAD_DIR / nome)


def gerar_dias_uteis(ini, fim):
    atual = ini
    while atual <= fim:
        if atual.weekday() < 5:
            yield atual
        atual += timedelta(days=1)


def iniciar(data_inicio, data_fim):
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            page.goto(PORTAL_URL, wait_until="domcontentloaded", timeout=120000)
            login_manual(page)
            selecionar_estoque(page)
            abrir_relatorio_receber(page)

            ini = datetime.strptime(data_inicio, "%d/%m/%Y")
            fim = datetime.strptime(data_fim, "%d/%m/%Y")

            # Mantém a proteção que já funcionou no relatório de receber:
            # um dia útil por vez.
            for dia in gerar_dias_uteis(ini, fim):
                for tentativa in range(1, 4):
                    try:
                        processar_receber(page, dia, dia)
                        print(f"[OK] Receber {dia:%d/%m/%Y}")
                        break
                    except Exception as e:
                        print(f"[TENTATIVA {tentativa}/3] {dia:%d/%m/%Y}: {e}")
                        if tentativa == 3:
                            print(f"[ERRO] Não baixou {dia:%d/%m/%Y}")
                        else:
                            time.sleep(3)

            print("\n[FINALIZADO] Robô de contas a receber concluído.")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python robo_receber.py DD/MM/AAAA DD/MM/AAAA")
        raise SystemExit(1)
    iniciar(sys.argv[1], sys.argv[2])
