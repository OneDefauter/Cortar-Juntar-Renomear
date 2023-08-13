import hashlib
import os
import shutil
import subprocess
import requests
import win32con
import win32api
import platform
import pickle
import winsound
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

# Obtém o nome do sistema operacional
sistema_operacional = platform.system()
if sistema_operacional != 'Windows':
    os.exit()

def is_program_installed():
    program_name = "magick" # Nome do programa
    # Verificar se o executável do programa está no PATH
    executable_path = shutil.which(program_name)
    if executable_path:
        print(f"{program_name} está instalado.")
    else:
        print(f"{program_name} não está instalado.")
        if messagebox.askyesno("ImageMagick não está instalado", "ImageMagick não foi encontrado.\nDeseja baixar e instalar agora?"):
            url = "https://github.com/OneDefauter/Menu_/releases/download/Req/ImageMagick-7.1.1-15-Q16-HDRI-x64-dll.exe"
            filename = "ImageMagick-7.1.1-15-Q16-HDRI-x64-dll.exe"
    
            response = requests.get(url)
            with open(filename, "wb") as f:
                f.write(response.content)
    
            atributos_atuais = win32api.GetFileAttributes(filename)
            win32api.SetFileAttributes(filename, atributos_atuais | win32con.FILE_ATTRIBUTE_HIDDEN)
    
            try:
                subprocess.run([filename, '/silent'], check=True)
                os.remove(filename)
                print(f"{program_name} foi instalado.")
            except subprocess.CalledProcessError as e:
                if e.returncode == 1602:
                    print("A instalação foi cancelada pelo usuário.")
                    os.exit()
        else:
            sys.exit()
is_program_installed()

current_version = "v1.0"  # Versão atual do seu aplicativo

def check_for_updates_and_replace():
    repo_owner = "OneDefauter"  # Nome do proprietário do repositório
    repo_name = "Cortar Juntar Renomear"  # Nome do repositório
    current_exe_path = os.path.basename(__file__)  # Caminho para o arquivo instalado localmente
    print("Nome do seu arquivo:", current_exe_path)

    # Consultar a API do GitHub para obter as informações do repositório
    response = requests.get(f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest")
    if response.status_code == 200:
        release_info = response.json()
        latest_version = release_info["tag_name"]
        asset_url = release_info["assets"][0]["browser_download_url"]  # Pode ser necessário ajustar o índice se houver mais de um arquivo de download

        if latest_version != current_version:
            print("Há uma nova versão disponível:", latest_version)
            if messagebox.askyesno("Atualização", f"Versão atual: {current_version}\nVersão mais recente: {latest_version}"):
                download_and_replace(asset_url, current_exe_path)
                messagebox.showinfo("Bem-sucedido", "Atualização concluida.\nInicie o App novamente.")
                sys.exit()
        else:
            print("Você está usando a versão mais recente.")
    else:
        print("Não foi possível verificar as atualizações.")

def download_and_replace(url, destination):
    response = requests.get(url, stream=True)
    with open(destination, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    print("Substituição concluída.")

# Chamada da função para verificar atualizações e realizar substituição, se necessário
check_for_updates_and_replace()

class ImageJoinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Juntar Imagens")
        self.image_folder = None
        self.image_list = []
        self.backup_var = tk.BooleanVar(value=False)
        self.extension_var = tk.StringVar(value=".jpg")
        self.quality_var = tk.IntVar(value=80)
        self.join_direction_var = tk.StringVar(value="vertical")
        self.show_success_msg_var = tk.BooleanVar(value=True)
        self.show_rename_success_msg_var = tk.BooleanVar(value=True)
        
        # Bloquear redimensionamento da janela
        self.root.resizable(False, False)
            
        # Caminho para o diretório atual (onde o código está sendo executado)
        self.current_dir = os.getcwd()

        # Diretório onde o arquivo settings.pickle será salvo
        self.settings_dir = os.path.join(os.environ.get("HOMEDRIVE"), os.environ.get("HOMEPATH"), "Juntar Imagens")

        if not os.path.exists(self.settings_dir):
            os.mkdir(self.settings_dir)

        # Carregar configurações do usuário
        self.load_settings()

        self.create_widgets()

    def save_settings(self):
        settings = {
            "backup_var": self.backup_var.get(),
            "extension_var": self.extension_var.get(),
            "quality_var": self.quality_var.get(),
            "join_direction_var": self.join_direction_var.get(),
            "show_success_msg_var": self.show_success_msg_var.get(),
            "show_rename_success_msg_var": self.show_rename_success_msg_var.get(),
        }

        with open(f"{self.settings_dir}/settings.pickle", "wb") as file:
            pickle.dump(settings, file)

    def load_settings(self):
        try:
            with open(f"{self.settings_dir}/settings.pickle", "rb") as file:
                settings = pickle.load(file)

            self.backup_var.set(settings["backup_var"])
            self.extension_var.set(settings["extension_var"])
            self.quality_var.set(settings["quality_var"])
            self.join_direction_var.set(settings["join_direction_var"])
            self.show_success_msg_var.set(settings["show_success_msg_var"])
            self.show_rename_success_msg_var.set(settings["show_rename_success_msg_var"])

        except FileNotFoundError:
            # Usar valores padrão caso o arquivo de configurações não exista
            self.backup_var.set(False)
            self.extension_var.set(".jpg")
            self.quality_var.set(80)
            self.join_direction_var.set("vertical")
            self.show_success_msg_var.set(True)
            self.show_rename_success_msg_var.set(True)
        except (pickle.PickleError, KeyError):
            # Tratar qualquer erro de desserialização ou chave ausente
            print("Erro ao carregar as configurações. Usando valores padrão.")
            self.backup_var.set(False)
            self.extension_var.set(".jpg")
            self.quality_var.set(80)
            self.join_direction_var.set("vertical")
            self.show_success_msg_var.set(True)
            self.show_rename_success_msg_var.set(True)

    def create_widgets(self):
        # Botão para adicionar a pasta de imagens
        tk.Button(self.root, text="Adicionar Pasta", command=self.select_image_folder).grid(row=0, column=0, padx=10, pady=10)

        # Caixa para marcar ou desmarcar a opção de backup
        tk.Checkbutton(self.root, text="Fazer Backup", variable=self.backup_var).grid(row=0, column=1, padx=10, pady=10)

        # Lista com as extensões de saída disponíveis
        tk.Label(self.root, text="Extensão de Saída:").grid(row=1, column=0, padx=10, pady=5)
        extensions = [".png", ".jpg"]
        tk.OptionMenu(self.root, self.extension_var, *extensions).grid(row=1, column=1, padx=10, pady=5)

        # Escala para selecionar o nível da imagem
        tk.Label(self.root, text="Nível de Qualidade:").grid(row=2, column=0, padx=10, pady=5)
        tk.Scale(self.root, from_=1, to=100, variable=self.quality_var, orient=tk.HORIZONTAL).grid(row=2, column=1, padx=10, pady=5)

        # Lista para selecionar as imagens a serem juntadas
        self.image_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, width=100)
        self.image_listbox.grid(row=7, columnspan=2, padx=10, pady=5)

        # Botão para juntar as imagens
        tk.Button(self.root, text="Juntar Imagens", command=self.join_images).grid(row=8, columnspan=2, padx=10, pady=10)

        # Botão para renomear os arquivos da pasta
        tk.Button(self.root, text="Renomear", command=self.rename_files).grid(row=8, column=1, padx=10, pady=10, rowspan=5)

        # Botão para renomear os arquivos da pasta
        tk.Button(self.root, text="Atualizar lista", command=self.refresh_list).grid(row=8, column=0, padx=10, pady=10, rowspan=5)

        # Radiobuttons para escolher a direção de junção das imagens
        tk.Label(self.root, text="Direção da Junção:").grid(row=3, column=0, padx=10, pady=5)
        tk.Radiobutton(self.root, text="Vertical", variable=self.join_direction_var, value="vertical").grid(row=3, column=1, padx=10, pady=5)
        tk.Radiobutton(self.root, text="Horizontal", variable=self.join_direction_var, value="horizontal").grid(row=3, columnspan=2, padx=10, pady=5)

        # Checkbox para mostrar a mensagem de sucesso após a junção
        tk.Checkbutton(self.root, text="Mostrar mensagem de sucesso após juntar", variable=self.show_success_msg_var).grid(row=5, column=0, columnspan=2)

        # Checkbox para mostrar a mensagem de sucesso após a renomeação
        tk.Checkbutton(self.root, text="Mostrar mensagem de sucesso após renomear", variable=self.show_rename_success_msg_var).grid(row=6, column=0, columnspan=2)

    def refresh_list(self):
        self.load_image_list()

    def select_image_folder(self):
        self.image_folder = filedialog.askdirectory(title="Selecione a pasta de imagens")
        self.load_image_list()

    def load_image_list(self):
        if self.image_folder:
            image_files = sorted([f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            self.image_listbox.delete(0, tk.END)
            for image_file in image_files:
                self.image_listbox.insert(tk.END, image_file)

    def join_images(self):
        if not self.image_folder:
            messagebox.showerror("Erro", "Selecione uma pasta de imagens primeiro.")
            return

        selected_images = [self.image_listbox.get(i) for i in self.image_listbox.curselection()]
        if len(selected_images) < 2:
            messagebox.showerror("Erro", "Selecione pelo menos duas imagens para juntar.")
            return
        
        join_direction = self.join_direction_var.get()
        if join_direction == "horizontal":
            if len(selected_images) > 2:
                messagebox.showerror("Erro", "Você selecionou mais do que 2 no modo horizontal")
                return
        
        if join_direction == "vertical":
            sorted_selected_images = sorted(selected_images, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
        if join_direction == "horizontal":
            sorted_selected_images = sorted(selected_images, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)], reverse=True)

        input_images = [os.path.join(self.image_folder, image) for image in sorted_selected_images]
        output_folder = os.path.join(self.image_folder, "temp")
        backup = self.backup_var.get()
        extension = self.extension_var.get()
        quality = self.quality_var.get()

        # Verificar tamanhos das imagens de entrada
        max_width = 32000
        max_height = 32000
        for image_path in input_images:
            img = Image.open(image_path)
            width, height = img.size
            if width > max_width or height > max_height:
                messagebox.showerror("Erro", f"A imagem {os.path.basename(image_path)} excede o tamanho máximo permitido de 32000x32000 pixels.")
                return
        
        # Calcular o tamanho da imagem resultante
        output_width, output_height = self.calculate_output_dimensions(input_images, join_direction)
        if output_width > max_width or output_height > max_height:
            messagebox.showerror("Erro", "A imagem resultante da junção excede o tamanho máximo permitido de 32000x32000 pixels.")
            return

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        atributos_atuais = win32api.GetFileAttributes(output_folder)
        win32api.SetFileAttributes(output_folder, atributos_atuais | win32con.FILE_ATTRIBUTE_HIDDEN)

        # Obtendo o nome da primeira imagem selecionada
        first_image_name = sorted(selected_images)[0].split(".")[0]

        try:
            output_filename = os.path.join(output_folder, f"{first_image_name}{extension}")
            command = ["magick", "convert", "-quality", str(quality)]
            
            if join_direction == "vertical":
                command.append("-append")
            elif join_direction == "horizontal":
                command.append("+append")
            
            command += input_images + [output_filename]
            
            subprocess.run(command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if backup:
                backup_path = os.path.join(self.image_folder, "Backup")
                if not os.path.exists(backup_path):
                    os.makedirs(backup_path)

                output_folder = os.path.join(self.image_folder, "Backup")

                for image_file in selected_images:
                    source_path = os.path.join(self.image_folder, image_file)
                    backup_path = os.path.join(output_folder, image_file)
                    shutil.move(source_path, backup_path)
            else:
                for image_file in selected_images:
                    source_path = os.path.join(self.image_folder, image_file)
                    os.remove(source_path)
            
            shutil.move(output_filename, self.image_folder)
            output_folder2 = os.path.join(self.image_folder, "temp")
            os.removedirs(output_folder2)

            # Exibir a mensagem de sucesso apenas se a caixa de seleção estiver marcada
            if self.show_success_msg_var.get():
                messagebox.showinfo("Sucesso", "As imagens foram juntadas com sucesso!")
            else:
                winsound.Beep(1000, 500)  # O primeiro argumento é a frequência em Hz e o segundo é a duração em milissegundos

            self.load_image_list()  # Atualizar a lista de imagens após a junção
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao executar o ImageMagick: \n{e}")
        self.save_settings()

    def rename_files(self):
        if not self.image_folder:
            messagebox.showerror("Erro", "Selecione uma pasta de imagens primeiro.")
            return
        
        backup = self.backup_var.get()

        file_list = sorted([f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

        if backup:
            backup_path = os.path.join(self.image_folder, "Backup")
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            
            for image_file in file_list:
                source_path = os.path.join(self.image_folder, image_file)
                shutil.copy(source_path, backup_path)

        # Contador para numerar os arquivos
        count = 1

        for filename in file_list:
            base, ext = os.path.splitext(filename)
            new_filename = f"{base}__{ext}"
            os.rename(os.path.join(self.image_folder, filename), os.path.join(self.image_folder, new_filename))

        file_list = sorted([f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

        for filename in file_list:
            base, ext = os.path.splitext(filename)
            new_filename = f"{count:02d}{ext}"
            os.rename(os.path.join(self.image_folder, filename), os.path.join(self.image_folder, new_filename))
            count += 1

        messagebox.showinfo("Sucesso", "Os arquivos foram renomeados com sucesso!") if self.show_rename_success_msg_var.get() else winsound.Beep(1000, 500)  # O primeiro argumento é a frequência em Hz e o segundo é a duração em milissegundos
        self.load_image_list()  # Atualizar a lista de imagens após a renomeação

    def calculate_output_dimensions(self, input_images, join_direction):
        total_width = 0
        total_height = 0
        for image_path in input_images:
            img = Image.open(image_path)
            width, height = img.size
            total_width += width if join_direction == "horizontal" else 0
            total_height += height if join_direction == "vertical" else 0
        return total_width, total_height
    
class ImageCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cortar Imagens")
        self.image_folder = None
        self.image_list = []
        self.backup_var = tk.BooleanVar(value=False)
        self.extension_var = tk.StringVar(value=".jpg")
        self.quality_var = tk.IntVar(value=80)
        self.crop_altura_var = tk.IntVar(value=1000)
        self.show_success_msg_var = tk.BooleanVar(value=True)
        self.show_rename_success_msg_var = tk.BooleanVar(value=True)
        
        # Bloquear redimensionamento da janela
        self.root.resizable(False, False)
            
        # Caminho para o diretório atual (onde o código está sendo executado)
        self.current_dir = os.getcwd()

        # Diretório onde o arquivo settings.pickle será salvo
        self.settings_dir = os.path.join(os.environ.get("HOMEDRIVE"), os.environ.get("HOMEPATH"), "Cortar Imagens")

        if not os.path.exists(self.settings_dir):
            os.mkdir(self.settings_dir)

        # Carregar configurações do usuário
        self.load_settings()

        self.create_widgets()

    def save_settings(self):
        settings = {
            "backup_var": self.backup_var.get(),
            "extension_var": self.extension_var.get(),
            "quality_var": self.quality_var.get(),
            "crop_altura_var": self.crop_altura_var.get(),
            "show_success_msg_var": self.show_success_msg_var.get(),
            "show_rename_success_msg_var": self.show_rename_success_msg_var.get(),
        }

        with open(f"{self.settings_dir}/settings.pickle", "wb") as file:
            pickle.dump(settings, file)

    def load_settings(self):
        try:
            with open(f"{self.settings_dir}/settings.pickle", "rb") as file:
                settings = pickle.load(file)

            self.backup_var.set(settings["backup_var"])
            self.extension_var.set(settings["extension_var"])
            self.quality_var.set(settings["quality_var"])
            self.crop_altura_var.set(settings["crop_altura_var"])
            self.show_success_msg_var.set(settings["show_success_msg_var"])
            self.show_rename_success_msg_var.set(settings["show_rename_success_msg_var"])

        except FileNotFoundError:
            # Usar valores padrão caso o arquivo de configurações não exista
            self.backup_var.set(False)
            self.extension_var.set(".jpg")
            self.quality_var.set(80)
            self.crop_altura_var.set(1000)
            self.show_success_msg_var.set(True)
            self.show_rename_success_msg_var.set(True)
        except (pickle.PickleError, KeyError):
            # Tratar qualquer erro de desserialização ou chave ausente
            print("Erro ao carregar as configurações. Usando valores padrão.")
            self.backup_var.set(False)
            self.extension_var.set(".jpg")
            self.quality_var.set(80)
            self.crop_altura_var.set(1000)
            self.show_success_msg_var.set(True)
            self.show_rename_success_msg_var.set(True)

    def create_widgets(self):
        # Botão para adicionar a pasta de imagens
        tk.Button(self.root, text="Adicionar Pasta", command=self.select_image_folder).grid(row=0, column=0, padx=10, pady=10)

        # Caixa para marcar ou desmarcar a opção de backup
        tk.Checkbutton(self.root, text="Fazer Backup", variable=self.backup_var).grid(row=0, column=1, padx=10, pady=10)

        # Lista com as extensões de saída disponíveis
        tk.Label(self.root, text="Extensão de Saída:").grid(row=1, column=0, padx=10, pady=5)
        extensions = [".png", ".jpg"]
        tk.OptionMenu(self.root, self.extension_var, *extensions).grid(row=1, column=1, padx=10, pady=5)

        # Escala para selecionar o nível da imagem
        tk.Label(self.root, text="Nível de Qualidade:").grid(row=2, column=0, padx=10, pady=5)
        tk.Scale(self.root, from_=1, to=100, variable=self.quality_var, orient=tk.HORIZONTAL).grid(row=2, column=1, padx=10, pady=5)

        # Botão para juntar as imagens
        tk.Button(self.root, text="Cortar Imagens", command=self.crop_images).grid(row=8, column=1, padx=10, pady=10)

        # Botão para renomear os arquivos da pasta
        tk.Button(self.root, text="Renomear", command=self.rename_files).grid(row=8, column=0, padx=10, pady=10)

        # Checkbox para mostrar a mensagem de sucesso após cortar
        tk.Checkbutton(self.root, text="Mostrar mensagem de sucesso após cortar", variable=self.show_success_msg_var).grid(row=5, column=0, columnspan=2)

        # Checkbox para mostrar a mensagem de sucesso após a renomeação
        tk.Checkbutton(self.root, text="Mostrar mensagem de sucesso após renomear", variable=self.show_rename_success_msg_var).grid(row=6, column=0, columnspan=2)

        self.crop_altura_var = tk.StringVar()
        self.crop_altura_var.set("1000")
        tk.Label(self.root, text="Altura do Corte:").grid(row=3, column=0, padx=10, pady=5)
        tk.Entry(self.root, textvariable=self.crop_altura_var).grid(row=3, column=1, padx=10, pady=5)
        
        # Rótulo para mostrar o caminho completo da pasta de imagens
        self.image_folder_label = tk.Label(self.root, text="", wraplength=300, anchor="sw", justify="left")
        self.image_folder_label.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

    def select_image_folder(self):
        self.image_folder = filedialog.askdirectory(title="Selecione a pasta de imagens")
        self.load_image_list()
        
        # Atualizar o rótulo com o caminho completo da pasta de imagens
        self.image_folder_label.config(text=f"Pasta Selecionada:\n{self.image_folder}")

    def load_image_list(self):
        if self.image_folder:
            image_files = [f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    def crop_images(self):
        if not self.image_folder:
            messagebox.showerror("Erro", "Selecione uma pasta de imagens primeiro.")
            return

        image_files = [f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        input_images = [os.path.join(self.image_folder, image) for image in image_files]
        output_folder = os.path.join(self.image_folder, "temp")
        backup = self.backup_var.get()
        extension = self.extension_var.get()
        quality = self.quality_var.get()
        altura = int(self.crop_altura_var.get())

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        atributos_atuais = win32api.GetFileAttributes(output_folder)
        win32api.SetFileAttributes(output_folder, atributos_atuais | win32con.FILE_ATTRIBUTE_HIDDEN)


        try:
            output_filename = os.path.join(output_folder, f"0{extension}")
            command = ["magick", "convert", "-quality", str(quality), "-crop", f"32000x{altura}"]
            
            command += input_images + [output_filename]
            
            subprocess.run(command, check=True)

            if backup:
                backup_path = os.path.join(self.image_folder, "Backup")
                if not os.path.exists(backup_path):
                    os.makedirs(backup_path)

                for image_file in input_images:
                    shutil.move(image_file, backup_path)
            else:
                for image_file in input_images:
                    source_path = os.path.join(self.image_folder, image_file)
                    os.remove(source_path)

            # Contador para numerar os arquivos
            count = 1

            output_files = sorted([f for f in os.listdir(output_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

            for filename in output_files:
                base, ext = os.path.splitext(filename)
                new_filename = f"{count:02d}{ext}"
                os.rename(os.path.join(output_folder, filename), os.path.join(output_folder, new_filename))
                count += 1

            output_files = [f for f in os.listdir(output_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            for image in output_files:
                output_pathfile = os.path.join(output_folder, image)
                shutil.move(output_pathfile, self.image_folder)
            
            # shutil.move(output_filename, self.image_folder)
            output_folder2 = os.path.join(self.image_folder, "temp")
            os.removedirs(output_folder2)

            # Exibir a mensagem de sucesso apenas se a caixa de seleção estiver marcada
            if self.show_success_msg_var.get():
                messagebox.showinfo("Sucesso", "As imagens foram juntadas com sucesso!")
            else:
                winsound.Beep(1000, 500)  # O primeiro argumento é a frequência em Hz e o segundo é a duração em milissegundos

            self.load_image_list()  # Atualizar a lista de imagens após a junção
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao executar o ImageMagick: \n{e}")
        self.save_settings()

    def rename_files(self):
        if not self.image_folder:
            messagebox.showerror("Erro", "Selecione uma pasta de imagens primeiro.")
            return
        
        backup = self.backup_var.get()

        file_list = sorted([f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

        if backup:
            backup_path = os.path.join(self.image_folder, "Backup")
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            
            for image_file in file_list:
                source_path = os.path.join(self.image_folder, image_file)
                shutil.copy(source_path, backup_path)

        # Contador para numerar os arquivos
        count = 1

        for filename in file_list:
            base, ext = os.path.splitext(filename)
            new_filename = f"{base}__{ext}"
            os.rename(os.path.join(self.image_folder, filename), os.path.join(self.image_folder, new_filename))

        file_list = sorted([f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

        for filename in file_list:
            base, ext = os.path.splitext(filename)
            new_filename = f"{count:02d}{ext}"
            os.rename(os.path.join(self.image_folder, filename), os.path.join(self.image_folder, new_filename))
            count += 1

        messagebox.showinfo("Sucesso", "Os arquivos foram renomeados com sucesso!") if self.show_rename_success_msg_var.get() else winsound.Beep(1000, 500)  # O primeiro argumento é a frequência em Hz e o segundo é a duração em milissegundos
        self.load_image_list()  # Atualizar a lista de imagens após a renomeação

class ImageRenameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Renomear Imagens")
        self.image_folder = None
        
        # Bloquear redimensionamento da janela
        self.root.resizable(False, False)

        tk.Label(self.root, text="Selecione a pasta de imagens:").pack(pady=10)
        self.folder_label = tk.Label(self.root, text="")  # Defina o wraplength conforme necessário
        self.folder_label.pack()

        self.select_button = tk.Button(self.root, text="Selecionar Pasta", command=self.select_image_folder)
        self.select_button.pack()

        self.rename_button = tk.Button(self.root, text="Renomear Imagens", command=self.rename_files)
        self.rename_button.pack()

    def select_image_folder(self):
        self.image_folder = filedialog.askdirectory(title="Selecione a pasta de imagens")
        if self.image_folder:
            self.folder_label.config(text=f"Pasta selecionada:\n{self.image_folder}")
        else:
            self.folder_label.config(text="Nenhuma pasta selecionada")
            
    def rename_files(self, backup=False):
        if not self.image_folder:
            return
        
        file_list = sorted([f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

        if backup:
            backup_path = os.path.join(self.image_folder, "Backup")
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            
            for image_file in file_list:
                source_path = os.path.join(self.image_folder, image_file)
                shutil.copy(source_path, backup_path)

        # Contador para numerar os arquivos
        count = 1

        for filename in file_list:
            base, ext = os.path.splitext(filename)
            new_filename = f"{base}__{ext}"
            os.rename(os.path.join(self.image_folder, filename), os.path.join(self.image_folder, new_filename))

        file_list = sorted([f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

        for filename in file_list:
            base, ext = os.path.splitext(filename)
            new_filename = f"{count:02d}{ext}"
            os.rename(os.path.join(self.image_folder, filename), os.path.join(self.image_folder, new_filename))
            count += 1

        return True

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"App {current_version}")
        
        # Bloquear redimensionamento da janela
        self.root.resizable(False, False)

        # Configuração para centralizar a janela
        window_width = 166
        window_height = 133
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Botões
        btn_image_joiner = tk.Button(root, text="Juntar Imagens", command=self.open_image_joiner)
        btn_image_joiner.pack(pady=10)

        btn_image_cropper = tk.Button(root, text="Cortar Imagens", command=self.open_image_cropper)
        btn_image_cropper.pack(pady=10)

        btn_image_rename = tk.Button(root, text="Renomear Imagens", command=self.open_image_rename)
        btn_image_rename.pack(pady=10)

    def open_image_joiner(self):
        self.root.withdraw()  # Ocultar a janela principal
        top = tk.Toplevel()
        top.title("Juntar Imagens")
        app = ImageJoinerApp(top)
        self.center_joiner_window(top)
        top.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(top))

    def open_image_cropper(self):
        self.root.withdraw()  # Ocultar a janela principal
        top = tk.Toplevel()
        top.title("Cortar Imagens")
        app = ImageCropperApp(top)
        self.center_cropper_window(top)
        top.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(top))

    def open_image_rename(self):
        self.root.withdraw()  # Ocultar a janela principal
        top = tk.Toplevel()
        top.title("Renomear Imagens")
        app = ImageRenameApp(top)
        self.center_renamer_window(top)
        top.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(top))

    def center_joiner_window(self, window):
        window_width = 626  # Largura da janela secundária de ImageJoinerApp
        window_height = 476  # Altura da janela secundária de ImageJoinerApp
        self.center_window(window, window_width, window_height)

    def center_cropper_window(self, window):
        window_width = 275  # Largura da janela secundária de ImageCropperApp
        window_height = 339  # Altura da janela secundária de ImageCropperApp
        self.center_window(window, window_width, window_height)

    def center_renamer_window(self, window):
        window_width = 545  # Largura da janela secundária de ImageRenameApp
        window_height = 133 # Altura da janela secundária de ImageRenameApp
        self.center_window(window, window_width, window_height)

    def center_window(self, window, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def on_child_close(self, top):
        top.destroy()
        self.root.deiconify()  # Exibir a janela principal novamente

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
