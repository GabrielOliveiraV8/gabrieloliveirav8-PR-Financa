from __future__ import annotations

import re
import sys
import time
from datetime import datetime
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
)

DOWNLOAD_DIR = Path(__file__).resolve().parent / "CSV_PREVISAO_SAIDA"


def abrir_relatorio_saida(page):
    clicar_financas(page)

    # Caminho visto nas telas enviadas:
    # Finanças -> Contas a Pagar -> Relatórios -> A Pagar a Vencer
    # -> A Pagar/Vencer por Vencimento.
    for texto in [
        "Contas a Pagar",
        "Relatórios",
        "A Pagar a Vencer",
        "A Pagar/Vencer por Vencimento",
    ]:
        print(f"[NAVEGAÇÃO] Procurando: {texto}")
        if not clicar_texto_exato(page, texto):
            # Alguns desses itens são apenas pastas e podem já estar abertas.
            if texto in {"Relatórios", "A Pagar a Vencer"}:
                continue
            raise RuntimeError(f"Não encontrei o item: {texto}")

    print("[OK] Relatório de previsão de saída aberto.")
    return True


def abrir_parametros_saida(page):
    # Nesta tela os parâmetros já aparecem abertos.
    # Se houver botão Ações/Parâmetros, tenta abrir.
    for texto in ["Parâmetros", "Ações"]:
        try:
            loc = page.get_by_text(texto, exact=True)
            if loc.count():
                loc.first.click(timeout=5000, force=True)
                time.sleep(1)
        except Exception:
            pass


def encontrar_inputs_visiveis(page):
    arr = []
    inputs = page.locator("input")
    for i in range(inputs.count()):
        try:
            x = inputs.nth(i)
            if x.is_visible() and x.is_editable():
                arr.append(x)
        except Exception:
            pass
    return arr


def preencher_datas_saida(page, ini, fim):
    s_ini = ini.strftime("%d/%m/%Y")
    s_fim = fim.strftime("%d/%m/%Y")

    print(f"[PARÂMETROS] Vencimento: {s_ini} até {s_fim}")

    # Pelo layout enviado, os primeiros campos de data editáveis da tela
    # são Vencimento Inicial e Vencimento Final.
    inputs = encontrar_inputs_visiveis(page)

    # Primeiro tenta pelo texto do rótulo e pelo input seguinte.
    def por_rotulo(rotulo, valor):
        label = page.get_by_text(rotulo, exact=False).last
        if not label.count():
            return False

        for expr in [
            "xpath=following::input[1]",
            "xpath=ancestor::*[self::div or self::td][1]//input[1]",
            "xpath=parent::*//input[1]",
        ]:
            try:
                inp = label.locator(expr)
                if inp.count() and inp.first.is_visible():
                    inp.first.fill(valor)
                    inp.first.dispatch_event("change")
                    return True
            except Exception:
                continue
        return False

    ok1 = por_rotulo("Vencimento Inicial", s_ini)
    ok2 = por_rotulo("Vencimento Final", s_fim)

    # Fallback pelo conjunto de inputs visíveis.
    if not (ok1 and ok2):
        inputs = encontrar_inputs_visiveis(page)
        candidatos = []
        for inp in inputs:
            try:
                val = inp.input_value()
                ph = (inp.get_attribute("placeholder") or "").lower()
                typ = (inp.get_attribute("type") or "").lower()
                if typ in ("date", "text") and ("data" in ph or "/" in val or val == ""):
                    candidatos.append(inp)
            except Exception:
                pass

        # Na tela do relatório, os dois primeiros campos são os vencimentos.
        if len(candidatos) >= 2:
            try:
                candidatos[0].fill(s_ini)
                candidatos[0].dispatch_event("change")
                candidatos[1].fill(s_fim)
                candidatos[1].dispatch_event("change")
                ok1 = ok2 = True
            except Exception:
                pass

    if not (ok1 and ok2):
        raise RuntimeError("Não consegui preencher Vencimento Inicial/Final.")

    time.sleep(1)


def marcar_previsao_saida(page):
    print("[PARÂMETROS] Garantindo 'Vencimento Programado' e 'Imprimir Previsão de Saída'.")

    # Localiza a caixa pelo texto e tenta clicar no checkbox/label correspondente.
    def marcar(texto):
        labels = page.get_by_text(texto, exact=False)
        if not labels.count():
            return False

        for i in range(labels.count()):
            lab = labels.nth(i)
            try:
                # O clique no texto costuma acionar o checkbox do Tecnicon.
                lab.click(timeout=5000, force=True)
                time.sleep(0.3)
                return True
            except Exception:
                continue
        return False

    # Pela captura, ambos já aparecem marcados. O robô tenta preservar isso.
    # Se o clique simples for necessário em outra versão do HTML, ele ainda funciona.
    #
    # Primeiro inspeciona checkboxes visíveis e procura o texto próximo.
    marcado_saida = False
    try:
        textos = page.get_by_text("Imprimir Previsão de Saída", exact=False)
        if textos.count():
            lab = textos.last
            for expr in [
                "xpath=preceding::input[@type='checkbox'][1]",
                "xpath=following::input[@type='checkbox'][1]",
                "xpath=ancestor::*[self::div or self::td][1]//input[@type='checkbox']",
            ]:
                try:
                    chk = lab.locator(expr)
                    if chk.count():
                        if not chk.first.is_checked():
                            chk.first.check(force=True)
                        marcado_saida = chk.first.is_checked()
                        break
                except Exception:
                    continue
    except Exception:
        pass

    # Fallback: clique no texto somente se não conseguiu localizar o input.
    if not marcado_saida:
        marcar("Imprimir Previsão de Saída")

    # Vencimento Programado deve permanecer marcado.
    try:
        textos = page.get_by_text("Vencimento Programado", exact=False)
        if textos.count():
            lab = textos.last
            for expr in [
                "xpath=preceding::input[@type='checkbox'][1]",
                "xpath=following::input[@type='checkbox'][1]",
                "xpath=ancestor::*[self::div or self::td][1]//input[@type='checkbox']",
            ]:
                try:
                    chk = lab.locator(expr)
                    if chk.count():
                        if not chk.first.is_checked():
                            chk.first.check(force=True)
                        break
                except Exception:
                    continue
    except Exception:
        pass


def selecionar_filiais(page, filial_ini="1", filial_fim="3"):
    print(f"[FILIAIS] Selecionando filiais {filial_ini} até {filial_fim}.")

    botao = page.get_by_text("Selecionar filial", exact=False)
    if not botao.count():
        return False

    botao.last.click(timeout=15000, force=True)
    time.sleep(1)

    # Modal visto na captura: Filial inicial / Filial final / OK.
    campos = []
    for i in range(page.locator("input").count()):
        try:
            x = page.locator("input").nth(i)
            if x.is_visible() and x.is_editable():
                campos.append(x)
        except Exception:
            pass

    # Procura por rótulos para evitar depender da posição.
    def preencher(rotulo, valor):
        lab = page.get_by_text(rotulo, exact=False).last
        if not lab.count():
            return False
        try:
            inp = lab.locator("xpath=following::input[1]")
            if inp.count():
                inp.first.fill(valor)
                return True
        except Exception:
            pass
        return False

    ok1 = preencher("Filial inicial", filial_ini)
    ok2 = preencher("Filial final", filial_fim)

    if not (ok1 and ok2) and len(campos) >= 2:
        campos[-2].fill(filial_ini)
        campos[-1].fill(filial_fim)

    ok = page.get_by_role("button", name="OK")
    if ok.count():
        ok.last.click(timeout=10000, force=True)
    else:
        page.get_by_text("OK", exact=True).last.click(timeout=10000, force=True)

    time.sleep(1)
    return True


def clicar_imprimir(page):
    btn = page.get_by_role("button", name="Imprimir")
    if not btn.count():
        btn = page.get_by_text("Imprimir", exact=True)
    if not btn.count():
        raise RuntimeError("Botão Imprimir não encontrado.")
    btn.last.click(timeout=30000, force=True)
    time.sleep(2)
    esperar_loader_sumir(page, 180000)


def escolher_csv(page):
    # Tela seguinte mostrada na captura:
    # Tipo de Visualização: PDF / Texto / CSV
    print("[EXPORTAÇÃO] Selecionando CSV...")
    csv = page.get_by_text("CSV", exact=True)
    if csv.count():
        try:
            csv.last.click(timeout=10000, force=True)
        except Exception:
            pass
    else:
        # Tenta radio/label.
        for inp in page.locator("input[type='radio']").all():
            try:
                if inp.is_visible():
                    label_text = ""
                    parent = inp.locator("xpath=..")
                    if parent.count():
                        label_text = parent.inner_text().upper()
                    if "CSV" in label_text:
                        inp.check(force=True)
                        break
            except Exception:
                continue

    visualizar = page.get_by_text("Visualizar", exact=True)
    if visualizar.count():
        visualizar.last.click(timeout=30000, force=True)
        time.sleep(2)
        esperar_loader_sumir(page, 120000)


def executar(ini, fim):
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            page.goto(PORTAL_URL, wait_until="domcontentloaded", timeout=120000)
            login_manual(page)
            selecionar_estoque(page)

            abrir_relatorio_saida(page)
            abrir_parametros_saida(page)

            preencher_datas_saida(page, ini, fim)
            marcar_previsao_saida(page)
            selecionar_filiais(page, "1", "3")

            print("[PROCESSAR] Gerando previsão de saída...")
            clicar_imprimir(page)
            escolher_csv(page)

            nome = f"previsao_saida_{ini:%Y%m%d}_{fim:%Y%m%d}.csv"
            abrir_csv_resultado(page, DOWNLOAD_DIR / nome)

            print("\n[FINALIZADO] Robô de previsão de saída concluído.")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python robo_previsao_saida.py DD/MM/AAAA DD/MM/AAAA")
        raise SystemExit(1)

    ini = datetime.strptime(sys.argv[1], "%d/%m/%Y")
    fim = datetime.strptime(sys.argv[2], "%d/%m/%Y")
    executar(ini, fim)
