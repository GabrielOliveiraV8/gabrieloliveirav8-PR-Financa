from __future__ import annotations

import time
from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

PORTAL_URL = "https://soberana.2cloud.com.br/Tecnicon/Portal"


def esperar_loader_sumir(page, timeout=60000):
    try:
        loader = page.locator(".tloader-container")
        if loader.count():
            try:
                loader.first.wait_for(state="visible", timeout=2000)
            except PlaywrightTimeoutError:
                pass
            loader.first.wait_for(state="hidden", timeout=timeout)
        return True
    except Exception:
        return False


def login_manual(page):
    print("[LOGIN] Faça o login manualmente no Tecnicon.")
    print("[LOGIN] O robô não armazena usuário ou senha.")
    try:
        page.get_by_text("Selecione o Local", exact=False).wait_for(
            state="visible", timeout=300000
        )
    except PlaywrightTimeoutError:
        page.get_by_text("ESTOQUE", exact=True).first.wait_for(
            state="visible", timeout=30000
        )


def selecionar_estoque(page):
    print("[LOCAL] Selecionando ESTOQUE...")
    time.sleep(2)
    itens = page.get_by_text("ESTOQUE", exact=True)
    if not itens.count():
        itens = page.get_by_text("ESTOQUE")
    for i in range(itens.count()):
        try:
            itens.nth(i).click(timeout=10000)
            time.sleep(1.5)
            botao = page.get_by_role("button", name="Selecionar")
            if botao.count():
                botao.first.click(timeout=10000)
                esperar_loader_sumir(page, 30000)
                return
        except Exception:
            continue
    raise RuntimeError("Não foi possível selecionar ESTOQUE.")


def clicar_financas(page):
    print("[NAVEGAÇÃO] Abrindo BA > Finanças...")
    try:
        ba = page.get_by_role("heading", name="BA")
        if not ba.count():
            ba = page.get_by_text("BA", exact=True)
        ba.first.click(timeout=30000)
    except Exception:
        # Em algumas telas o BA é um item de menu.
        page.get_by_text("BA", exact=True).first.click(timeout=30000)

    time.sleep(2)
    esperar_loader_sumir(page, 20000)

    try:
        page.locator("#an113 i").first.click(timeout=15000, force=True)
    except Exception:
        page.evaluate("document.querySelector('#an113 i')?.click()")

    time.sleep(2)
    esperar_loader_sumir(page, 20000)

    fin = page.get_by_text("Finanças", exact=True)
    if not fin.count():
        raise RuntimeError("Menu Finanças não encontrado.")
    fin.first.click(timeout=30000, force=True)
    time.sleep(2)
    esperar_loader_sumir(page, 20000)


def clicar_texto_exato(page, texto, timeout=30000):
    loc = page.get_by_text(texto, exact=True)
    if not loc.count():
        loc = page.get_by_text(texto, exact=False)
    if not loc.count():
        return False
    loc.first.click(timeout=timeout, force=True)
    time.sleep(2)
    esperar_loader_sumir(page, 30000)
    return True


def abrir_csv_resultado(page, caminho_saida: Path):
    print("[CSV] Procurando botão CSV...")
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    if caminho_saida.exists():
        caminho_saida.unlink()

    with page.expect_download(timeout=180000) as info:
        botoes = page.locator(
            ".fa-file-csv, [title*='CSV' i], [aria-label*='CSV' i]"
        )
        if not botoes.count():
            botoes = page.get_by_text("CSV", exact=True)

        if not botoes.count():
            raise RuntimeError("Botão CSV não encontrado.")

        botoes.last.click(timeout=20000, force=True)

    download = info.value
    download.save_as(str(caminho_saida))

    for _ in range(60):
        if caminho_saida.exists() and caminho_saida.stat().st_size > 100:
            print(f"[OK] CSV salvo: {caminho_saida}")
            return str(caminho_saida)
        time.sleep(1)

    raise RuntimeError("O CSV não ficou estável no disco.")


def setar_input_por_id(page, element_id, valor):
    page.evaluate(
        """([id, valor]) => {
            const el = document.getElementById(id);
            if (!el) throw new Error("Campo não encontrado: " + id);
            el.value = valor;
            el.dispatchEvent(new Event("input", {bubbles:true}));
            el.dispatchEvent(new Event("change", {bubbles:true}));
            el.blur();
        }""",
        [element_id, valor],
    )


def garantir_checkbox(page, texto, marcado=True):
    """Tenta marcar/desmarcar um checkbox associado ao texto informado."""
    try:
        label = page.get_by_text(texto, exact=False).last
        if not label.count():
            return False

        # Tenta localizar input próximo do texto.
        candidatos = [
            label.locator("xpath=preceding::input[@type='checkbox'][1]"),
            label.locator("xpath=following::input[@type='checkbox'][1]"),
            label.locator("xpath=..").locator("input[type='checkbox']"),
            page.locator(f"input[type='checkbox']").filter(has=label),
        ]

        for chk in candidatos:
            try:
                if chk.count():
                    atual = chk.first.is_checked()
                    if atual != marcado:
                        chk.first.check(force=True) if marcado else chk.first.uncheck(force=True)
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def preencher_data_por_texto(page, texto_label, valor):
    """
    Procura o campo de data próximo ao texto do rótulo.
    O Tecnicon muda pequenos detalhes do HTML entre relatórios,
    por isso são usadas várias estratégias.
    """
    # Estratégia 1: label -> input dentro do mesmo container.
    label = page.get_by_text(texto_label, exact=False).last
    if label.count():
        for expr in [
            "xpath=ancestor::*[self::div or self::td][1]//input",
            "xpath=following::input[1]",
        ]:
            try:
                inp = label.locator(expr)
                if inp.count():
                    inp.first.fill(valor)
                    inp.first.dispatch_event("change")
                    return True
            except Exception:
                pass

    # Estratégia 2: campos visíveis de data.
    campos = page.locator("input")
    for i in range(campos.count()):
        try:
            inp = campos.nth(i)
            if inp.is_visible() and inp.is_editable():
                ph = (inp.get_attribute("placeholder") or "").lower()
                typ = (inp.get_attribute("type") or "").lower()
                if "date" in typ or "data" in ph:
                    # Não substitui indiscriminadamente campos já preenchidos.
                    continue
        except Exception:
            continue

    return False
