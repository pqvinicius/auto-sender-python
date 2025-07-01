# =============================================================================
# IMPORTAÇÕES NECESSÁRIAS
# =============================================================================
import tkinter as tk
from tkinter import ttk 
import subprocess
import sys
from pathlib import Path


def executar_script(nome_do_script):
    """
    Executa um script Python em um novo processo de terminal,
    garantindo que o ambiente virtual correto seja usado.
    """
    try:
        python_executable = Path(sys.executable)
        
       
        script_path = Path(__file__).resolve().parent / 'src' / nome_do_script
        
        if not script_path.exists():
            print(f"ERRO: O script '{nome_do_script}' não foi encontrado na pasta 'src/'.")
         
            tk.messagebox.showerror("Erro de Script", f"O arquivo de script '{nome_do_script}' não foi encontrado!")
            return

        print(f"▶️  Iniciando a execução de: {nome_do_script}")
     
        subprocess.Popen([str(python_executable), str(script_path)])

    except Exception as e:
        print(f"ERRO ao tentar executar o script '{nome_do_script}': {e}")
        tk.messagebox.showerror("Erro de Execução", f"Falha ao iniciar o script:\n{e}")

# =============================================================================
# CRIAÇÃO DA INTERFACE GRÁFICA (GUI)
# =============================================================================

root = tk.Tk()
root.title("Central de Automação de Vendas")
root.geometry("400x350") 
root.resizable(False, False) 


style = ttk.Style()
style.configure('TButton', font=('Helvetica', 12), padding=10)


main_frame = ttk.Frame(root, padding="20 20 20 20")
main_frame.pack(expand=True, fill='both')

title_label = ttk.Label(
    main_frame, 
    text="Central de Automação ", 
    font=("Helvetica", 18, "bold")
)
title_label.pack(pady=(0, 20))

button_relatorios = ttk.Button(
    main_frame, 
    text="📊 Enviar Relatórios Diários", 
    command=lambda: executar_script('EnviarMensagemVendedores.py')
)
button_relatorios.pack(fill='x', pady=5) # fill='x' faz o botão ocupar toda a largura

button_parabens = ttk.Button(
    main_frame, 
    text="🎉 Enviar Parabéns por Meta", 
    command=lambda: executar_script('EnviarParabens.py')
)
button_parabens.pack(fill='x', pady=5)

button_lembretes = ttk.Button(
    main_frame, 
    text="🔔 Enviar Lembretes de Meta", 
    command=lambda: executar_script('EnviarLembreteMeta.py')
)
button_lembretes.pack(fill='x', pady=5)

button_sair = ttk.Button(
    main_frame, 
    text="Sair", 
    command=root.destroy
)
button_sair.pack(side='bottom', pady=(20, 0))


root.mainloop()