
import os
import csv
import string
import secrets
from datetime import datetime
import PySimpleGUI as sg

# === Configuração ===
LENGTH = 5
CHARSET = string.digits + string.ascii_uppercase + string.ascii_lowercase
sysrand = secrets.SystemRandom()

def gerar_senha(require_all=False):
    """Gera uma senha de 5 caracteres. Se require_all=True, garante A/a/0-9."""
    if not require_all:
        return ''.join(secrets.choice(CHARSET) for _ in range(LENGTH))
    partes = [
        secrets.choice(string.digits),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
    ]
    while len(partes) < LENGTH:
        partes.append(secrets.choice(CHARSET))
    sysrand.shuffle(partes)
    return ''.join(partes)

def gerar_lista(qtd, unique=False, require_all=False):
    """Gera 'qtd' senhas. Se unique=True, evita repetições."""
    if qtd < 1 or qtd > 10000:
        raise ValueError("Informe um número entre 1 e 10.000.")
    if not unique:
        return [gerar_senha(require_all=require_all) for _ in range(qtd)]
    senhas = set()
    # Para grandes quantidades, poderia usar um limite de tentativas, mas com 62^5 combinações é tranquilo.
    while len(senhas) < qtd:
        senhas.add(gerar_senha(require_all=require_all))
    return list(senhas)

def salvar_csv(caminho, senhas):
    """Salva CSV com cabeçalho 'senha'."""
    with open(caminho, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['senha'])
        for s in senhas:
            w.writerow([s])

def abrir_pasta_do_arquivo(caminho):
    """Tenta abrir a pasta no sistema operacional."""
    try:
        pasta = os.path.dirname(os.path.abspath(caminho))
        if os.name == 'nt':  # Windows
            os.startfile(pasta)
        elif os.name == 'posix':  # Linux/Mac
            import subprocess, sys
            if sys.platform == 'darwin':
                subprocess.run(['open', pasta])
            else:
                subprocess.run(['xdg-open', pasta])
    except Exception:
        pass


# === GUI ===

import PySimpleGUI as sg

def set_theme_safe(name="SystemDefault"):
    try:
        if hasattr(sg, "theme") and callable(getattr(sg, "theme")):
            sg.theme(name)
            return
        if hasattr(sg, "ChangeLookAndFeel") and callable(getattr(sg, "ChangeLookAndFeel")):
            sg.ChangeLookAndFeel(name)
            return
    except Exception:
        pass
    # Sem API de tema: seguir sem aplicar tema global

set_theme_safe("SystemDefault")

layout = [
    [sg.Text("Gerador de Senhas (5 caracteres)", font=("Segoe UI", 12, "bold"))],
    [
        sg.Text("Quantidade (1–10.000):"),
        sg.Input(default_text="100", size=(8,1), key="-QTD-")
    ],
    [sg.Checkbox("Evitar repetições (senhas únicas)", default=True, key="-UNQ-")],
    [sg.Checkbox("Exigir ao menos 1 maiúscula, 1 minúscula e 1 número", default=False, key="-REQ-")],
    [sg.Button("Gerar", key="-GERAR-", bind_return_key=True),
     sg.Button("Salvar CSV...", key="-SALVAR-"),
     sg.Button("Abrir pasta", key="-ABRIR-"),
     sg.Button("Limpar", key="-LIMPAR-"),
     sg.Button("Sair")],
    [sg.Text("Resultado:")],
    [sg.Multiline("", size=(60,15), key="-OUT-", disabled=True, autoscroll=True, font=("Consolas", 10))]
]

window = sg.Window("Gerador de Senhas (5)", layout)
senhas_atuais = []
ultimo_arquivo = None

while True:
    event, values = window.read()
    if event in (sg.WINDOW_CLOSED, "Sair"):
        break

    if event == "-GERAR-":
        try:
            qtd = int(str(values["-QTD-"]).strip())
        except (ValueError, TypeError):
            sg.popup_error("A quantidade precisa ser um número inteiro entre 1 e 10.000.")
            continue
        try:
            senhas_atuais = gerar_lista(
                qtd, unique=values["-UNQ-"], require_all=values["-REQ-"]
            )
        except Exception as e:
            sg.popup_error(f"Erro ao gerar: {e}")
            continue

        window["-OUT-"].update("")
        window["-OUT-"].print(f"Gerado: {len(senhas_atuais)} senhas.\n")
        for s in senhas_atuais:
            window["-OUT-"].print(s)
        ultimo_arquivo = None

    if event == "-SALVAR-":
        if not senhas_atuais:
            sg.popup("Nada para salvar. Gere as senhas primeiro.")
            continue
        nome_sugerido = f"senhas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        caminho = sg.popup_get_file(
            "Escolha onde salvar",
            save_as=True,
            default_extension=".csv",
            file_types=(("CSV", "*.csv"),),
            default_path=nome_sugerido,
            no_window=True
        )
        if not caminho:
            continue
        try:
            salvar_csv(caminho, senhas_atuais)
            ultimo_arquivo = caminho
            sg.popup(f"Arquivo salvo:\n{os.path.basename(caminho)}")
        except Exception as e:
            sg.popup_error(f"Erro ao salvar: {e}")

    if event == "-ABRIR-":
        if ultimo_arquivo:
            abrir_pasta_do_arquivo(ultimo_arquivo)
        else:
            sg.popup("Nenhum arquivo salvo ainda.")

    if event == "-LIMPAR-":
        window["-OUT-"].update("")
        senhas_atuais = []
        ultimo_arquivo = None

window.close()

