import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.animation import Animation
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

import webbrowser
from kivy.properties import StringProperty, DictProperty

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests
import json
from kivy.utils import platform

if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    from jnius import autoclass

import firebase_admin
from firebase_admin import credentials, firestore

from firebase_config import FIREBASE_WEB_API_KEY, ADMIN_EMAIL, FIREBASE_CREDENTIALS_PATH, SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT, APP_ICON_PATH

try:
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Conexão com Firebase bem-sucedida!")
except Exception as e:
    print(f"ERRO AO CONECTAR COM FIREBASE: {e}")
    db = None

signup_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
login_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
update_url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FIREBASE_WEB_API_KEY}"
delete_url = f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={FIREBASE_WEB_API_KEY}"

Builder.load_file('app_theme.kv')

class LoginScreen(Screen):
    def on_enter(self, *args):
        self.ids.animated_background.start_animation()

    def do_login(self):
        email = self.ids.login_email.text
        password = self.ids.login_password.text
        App.get_running_app().login(email, password)

    def on_leave(self, *args):
        self.ids.animated_background.stop_animation()

class RegisterScreen(Screen):
    def on_enter(self, *args):
        self.ids.animated_background.start_animation()

    def do_register(self):
        email = self.ids.register_email.text
        password = self.ids.register_password.text
        App.get_running_app().sign_up(email, password)

    def on_leave(self, *args):
        self.ids.animated_background.stop_animation()

class AnimatedBackground(Widget):
    pass

class DashboardScreen(Screen):
    def on_enter(self, *args):
        app = App.get_running_app()
        if app.user_email:
            self.ids.welcome_label.text = f"Bem-vindo, {app.user_email}"

class BotListScreen(Screen):
    def on_enter(self, *args):
        self.fetch_and_display_bots()

    def fetch_and_display_bots(self):
        if not db:
            print("Firebase não conectado. Não é possível buscar bots.")
            return
        
        self.all_bots_data = []
        bots_ref = db.collection('bots').stream()
        for bot_doc in bots_ref:
            bot_data = bot_doc.to_dict()
            bot_data['doc_id'] = bot_doc.id
            self.all_bots_data.append(bot_data)

        self.filter_bots('')

    def filter_bots(self, search_text):
        bot_list_layout = self.ids.bot_list_layout
        bot_list_layout.clear_widgets()
        search_text = search_text.lower()

        for bot_data in self.all_bots_data:
            if search_text in bot_data.get('nome', '').lower():
                card = Factory.BotCard()
                card.doc_id = bot_data.get('doc_id')
                card.ids.bot_name.text = bot_data.get('nome', 'Nome não encontrado')
                card.ids.bot_info.text = f"Versão {bot_data.get('versao', 'N/A')} | Por: {bot_data.get('autor', 'N/A')}"
                card.download_link = bot_data.get('link', '')
                card.ids.install_button.file_name = bot_data.get('link', '').split('/')[-1]
                
                if App.get_running_app().user_email == ADMIN_EMAIL:
                    card.ids.admin_actions.width = 150
                    card.ids.admin_actions.opacity = 1
                    card.ids.install_button.size_hint_x = 0.2
                else:
                    card.ids.admin_actions.width = 0
                    card.ids.admin_actions.opacity = 0

                bot_list_layout.add_widget(card)
                Animation(opacity=1, duration=0.3).start(card)

        if not bot_list_layout.children:
            bot_list_layout.add_widget(Label(text='Nenhum bot encontrado.', color=App.get_running_app().theme.text_secondary))

class MyBotsScreen(Screen):
    def on_enter(self):
        self.list_local_bots()

    def get_bots_dir(self):
        if platform == 'android':
            return os.path.join(primary_external_storage_path(), 'Android', 'Media', 'com.BotDeploy')
        else:
            return os.path.join(os.path.expanduser('~'), 'Downloads', 'BotDeploy')

    def list_local_bots(self):
        my_bots_list = self.ids.my_bots_list
        my_bots_list.clear_widgets()
        bots_dir = self.get_bots_dir()

        if not os.path.exists(bots_dir):
            my_bots_list.add_widget(Label(text='Nenhum bot baixado ainda.', color=App.get_running_app().theme.text_secondary))
            return

        files = [f for f in os.listdir(bots_dir) if f.endswith('.py')]
        if not files:
            my_bots_list.add_widget(Label(text='Nenhum bot baixado ainda.', color=App.get_running_app().theme.text_secondary))
            return

        for file_name in files:
            card = Factory.MyBotCard()
            card.file_path = os.path.join(bots_dir, file_name)
            card.ids.my_bot_name.text = file_name
            my_bots_list.add_widget(card)

class ProfileScreen(Screen):
    pass

class AboutScreen(Screen):
    pass

class InstallScreen(Screen):
    pass

class AdminScreen(Screen):
    def on_enter(self, *args):
        self.fetch_publication_requests()

    def publish_bot_directly(self):
        bot_name = self.ids.admin_bot_name.text
        bot_version = self.ids.admin_bot_version.text
        bot_link = self.ids.admin_bot_link.text
        
        if not all([bot_name, bot_version, bot_link]):
            App.get_running_app().show_popup("Erro", "Todos os campos são obrigatórios.")
            return
        
        App.get_running_app().add_new_bot(bot_name, bot_version, bot_link)
        self.ids.admin_bot_name.text = ""
        self.ids.admin_bot_version.text = ""

    def fetch_publication_requests(self):
        if not db:
            print("Firebase não conectado. Não é possível buscar solicitações.")
            return

        pending_layout = self.ids.pending_list_layout
        reviewing_layout = self.ids.reviewing_list_layout
        pending_layout.clear_widgets()
        reviewing_layout.clear_widgets()

        pending_ref = db.collection('publication_requests').where('status', '==', 'pending_payment').stream()
        for doc in pending_ref:
            request_data = doc.to_dict()
            card = Factory.RequestCard()
            Animation(opacity=1, duration=0.3).start(card)
            card.doc_id = doc.id
            card.ids.request_bot_name.text = request_data.get('bot_name', 'Nome não encontrado')
            card.ids.request_user_email.text = f"Enviado por: {request_data.get('requester_email', 'Email não encontrado')}"
            pending_layout.add_widget(card)

        reviewing_ref = db.collection('publication_requests').where('status', '==', 'reviewing').stream()
        for doc in reviewing_ref:
            request_data = doc.to_dict()
            card = Factory.RequestCard()
            Animation(opacity=1, duration=0.3).start(card)
            card.doc_id = doc.id
            card.is_reviewing = True
            card.ids.request_bot_name.text = request_data.get('bot_name', 'Nome não encontrado')
            card.ids.request_user_email.text = f"Enviado por: {request_data.get('requester_email', 'Email não encontrado')}"
            reviewing_layout.add_widget(card)

        if not pending_layout.children:
            pending_layout.add_widget(Label(text='Nenhuma solicitação pendente.', color=App.get_running_app().theme.text_secondary))
        
        if not reviewing_layout.children:
            reviewing_layout.add_widget(Label(text='Nenhuma solicitação em revisão.', color=App.get_running_app().theme.text_secondary))

class PublishScreen(Screen):
    def submit_publication_request(self):
        bot_name = self.ids.bot_name_input.text
        bot_desc = self.ids.bot_desc_input.text
        bot_link = self.ids.bot_link_input.text

        if not all([bot_name, bot_desc, bot_link]):
            App.get_running_app().show_popup("Erro", "Todos os campos são obrigatórios.")
            return
        
        App.get_running_app().request_publication(bot_name, bot_desc, bot_link)

class WindowManager(ScreenManager):
    pass

class BotDownloaderApp(App):
    icon = APP_ICON_PATH
    
    theme_name = StringProperty('dark')
    theme = DictProperty()

    def on_start(self):
        self.themes = {
            'dark': {
                'primary': get_color_from_hex('#25CD9D'), 'primary_hex': '#25CD9D',
                'secondary': get_color_from_hex('#3A5A59'),
                'background': get_color_from_hex('#0B1B27'),
                'card_bg': get_color_from_hex('#102331'),
                'text_main': get_color_from_hex('#FBFBFB'),
                'text_secondary': get_color_from_hex('#989C9F'),
            },
            'light': {
                'primary': get_color_from_hex('#1E88E5'), 'primary_hex': '#1E88E5',
                'secondary': get_color_from_hex('#B0BEC5'),
                'background': get_color_from_hex('#F5F5F5'),
                'card_bg': get_color_from_hex('#FFFFFF'),
                'text_main': get_color_from_hex('#212121'),
                'text_secondary': get_color_from_hex('#757575'),
            }
        }
        self.theme = self.themes[self.theme_name]
    
    def build(self):
        self.user_token = None
        self.user_email = None
        self.last_downloaded_path = None

        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

        Window.clearcolor = self.themes['dark']['background']
        return WindowManager()

    def toggle_theme(self):
        self.theme_name = 'light' if self.theme_name == 'dark' else 'dark'
        self.theme = self.themes[self.theme_name]

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message, halign='center'),
                      size_hint=(0.8, 0.3))
        popup.open()

    def sign_up(self, email, password):
        signup_data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        try:
            response = requests.post(signup_url, data=signup_data)
            response.raise_for_status()
            self.show_popup("Sucesso", "Conta criada com sucesso!\nFaça o login.")
            self.root.current = 'login'
        except requests.exceptions.HTTPError as e:
            error_json = e.response.json()
            error_message = error_json.get("error", {}).get("message", "ERRO DESCONHECIDO")
            self.show_popup("Erro de Registro", error_message)

    def login(self, email, password):
        login_data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        try:
            response = requests.post(login_url, data=login_data)
            response.raise_for_status()
            data = response.json()
            self.user_token = data['idToken']
            self.user_email = data['email']

            if self.user_email == ADMIN_EMAIL:
                self.root.current = 'admin'
            else:
                self.root.current = 'dashboard'

        except requests.exceptions.HTTPError as e:
            error_json = e.response.json()
            error_message = error_json.get("error", {}).get("message", "EMAIL_OR_PASSWORD_INVALID")
            self.show_popup("Erro de Login", "Email ou senha inválidos.")

    def review_request(self, doc_id):
        if not db: return
        try:
            db.collection('publication_requests').document(doc_id).update({'status': 'reviewing'})
            self.root.get_screen('admin').fetch_publication_requests()
            self.show_request_details(doc_id)
        except Exception as e:
            self.show_popup("Erro", f"Não foi possível iniciar a revisão.\n{e}")

    def show_request_details(self, doc_id):
        if not db:
            self.show_popup("Erro", "Banco de dados não conectado.")
            return
        
        try:
            request_ref = db.collection('publication_requests').document(doc_id)
            request_data = request_ref.get().to_dict()

            if not request_data:
                self.show_popup("Erro", "Solicitação não encontrada.")
                return

            content = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
            
            details_text = (
                f"[b]Nome do Bot:[/b] {request_data.get('bot_name', 'N/A')}\n\n"
                f"[b]Enviado por:[/b] {request_data.get('requester_email', 'N/A')}\n\n"
                f"[b]Descrição:[/b]\n{request_data.get('bot_description', 'N/A')}\n\n"
                f"[b]Link do Arquivo:[/b]\n{request_data.get('bot_link', 'N/A')}"
            )

            details_label = Label(text=details_text, markup=True, halign='left', valign='top')
            details_label.bind(size=details_label.setter('text_size'))
            content.add_widget(details_label)

            popup = Popup(title="Detalhes da Solicitação", content=content, size_hint=(0.9, 0.6))
            popup.open()
        except Exception as e:
            self.show_popup("Erro", f"Não foi possível carregar os detalhes.\n{e}")

    def delete_bot(self, doc_id):
        content = BoxLayout(orientation='vertical', spacing='10dp')
        content.add_widget(Label(text='Você tem certeza que deseja excluir este bot permanentemente?', color=self.theme['text_main']))
        confirm_button = Factory.AdminButton(text='Sim, Excluir', bg_color=(0.9, 0.2, 0.2, 1))
        cancel_button = Factory.AdminButton(text='Cancelar', bg_color=(0.5, 0.5, 0.5, 1))
        
        buttons_layout = BoxLayout(spacing='10dp', size_hint_y=None, height='40dp')
        buttons_layout.add_widget(cancel_button)
        buttons_layout.add_widget(confirm_button)
        content.add_widget(buttons_layout)

        popup = Popup(title='Confirmar Exclusão', content=content, size_hint=(0.8, 0.4))

        def _delete_confirmed(instance):
            popup.dismiss()
            if not db: return
            try:
                db.collection('bots').document(doc_id).delete()
                self.show_popup("Sucesso", "Bot excluído.")
                self.root.get_screen('bot_list').fetch_and_display_bots()
            except Exception as e:
                self.show_popup("Erro", f"Não foi possível excluir o bot.\n{e}")

        confirm_button.bind(on_release=_delete_confirmed)
        cancel_button.bind(on_release=popup.dismiss)
        popup.open()

    def edit_bot(self, doc_id):
        if not db: return
        bot_data = db.collection('bots').document(doc_id).get().to_dict()
        if not bot_data: return

        content = BoxLayout(orientation='vertical', spacing='10dp', padding='10dp')
        name_input = Factory.StyledTextInput(text=bot_data.get('nome', ''), hint_text='Nome do Bot')
        version_input = Factory.StyledTextInput(text=bot_data.get('versao', ''), hint_text='Versão')
        link_input = Factory.StyledTextInput(text=bot_data.get('link', ''), hint_text='Link do arquivo .py')
        save_button = Factory.StyledButton(text='Salvar Alterações')

        content.add_widget(name_input); content.add_widget(version_input); content.add_widget(link_input); content.add_widget(save_button)
        popup = Popup(title='Editar Bot', content=content, size_hint=(0.9, 0.6))

        def _save_changes(instance):
            new_data = {
                'nome': name_input.text,
                'versao': version_input.text,
                'link': link_input.text
            }
            try:
                db.collection('bots').document(doc_id).update(new_data)
                popup.dismiss()
                self.show_popup("Sucesso", "Bot atualizado.")
                self.root.get_screen('bot_list').fetch_and_display_bots()
            except Exception as e:
                self.show_popup("Erro", f"Não foi possível salvar as alterações.\n{e}")

        save_button.bind(on_release=_save_changes)
        popup.open()

    def send_approval_email(self, recipient_email, bot_name):
        try:
            message = MIMEMultipart()
            message["From"] = SENDER_EMAIL
            message["To"] = recipient_email
            message["Subject"] = f"Seu Bot Foi Aprovado: {bot_name}"

            body = f"""
            Olá,

            Boas notícias! Seu bot "{bot_name}" foi aprovado e já está listado em nosso aplicativo.

            Obrigado por sua contribuição!

            Atenciosamente,
            Equipe BotDeploy
            """
            message.attach(MIMEText(body, "plain"))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
            
            print(f"E-mail de aprovação enviado para {recipient_email}")
        except Exception as e:
            print(f"FALHA AO ENVIAR E-MAIL: {e}")

    def send_rejection_email(self, recipient_email, bot_name, reason):
        try:
            message = MIMEMultipart()
            message["From"] = SENDER_EMAIL
            message["To"] = recipient_email
            message["Subject"] = f"Sua solicitação para o bot {bot_name} foi revisada"

            body = f"""
            Olá,

            Agradecemos pelo envio do seu bot "{bot_name}". Após uma revisão, decidimos não publicá-lo no momento.

            Motivo: {reason}

            Sinta-se à vontade para fazer ajustes e submeter novamente.
            """
            message.attach(MIMEText(body, "plain"))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(); server.login(SENDER_EMAIL, SENDER_PASSWORD); server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
            print(f"E-mail de rejeição enviado para {recipient_email}")
        except Exception as e:
            print(f"FALHA AO ENVIAR E-MAIL DE REJEIÇÃO: {e}")

    def logout(self):
        self.user_token = None
        self.user_email = None
        self.last_downloaded_path = None
        self.root.current = 'login'

    def approve_request(self, doc_id):
        if not db: return
        try:
            request_ref = db.collection('publication_requests').document(doc_id)
            request_data = request_ref.get().to_dict()

            if not request_data:
                self.show_popup("Erro", "Solicitação não encontrada.")
                return

            db.collection('bots').add({
                'nome': request_data.get('bot_name'),
                'versao': '1.0',
                'link': request_data.get('bot_link'),
                'autor': request_data.get('requester_email')
            })

            self.send_approval_email(request_data.get('requester_email'), request_data.get('bot_name'))
            request_ref.delete()
            self.show_popup("Sucesso", f"Bot '{request_data.get('bot_name')}' aprovado e publicado!")
            self.root.get_screen('admin').fetch_publication_requests()
        except Exception as e:
            self.show_popup("Erro", f"Não foi possível aprovar a solicitação.\n{e}")
    
    def reject_request(self, doc_id):
        content = BoxLayout(orientation='vertical', spacing='10dp')
        reason_input = Factory.StyledTextInput(hint_text='Motivo da rejeição...', size_hint_y=None, height='80dp')
        submit_button = Factory.StyledButton(text='Enviar Rejeição')
        content.add_widget(reason_input)
        content.add_widget(submit_button)

        popup = Popup(title='Motivo da Rejeição', content=content, size_hint=(0.8, 0.4))

        def process_rejection(instance):
            reason = reason_input.text
            if not reason:
                self.show_popup("Erro", "O motivo é obrigatório.")
                return
            popup.dismiss()
            self._process_rejection(doc_id, reason)
        
        submit_button.bind(on_release=process_rejection)
        popup.open()

    def _process_rejection(self, doc_id, reason):
        if not db: return
        try:
            request_ref = db.collection('publication_requests').document(doc_id)
            request_data = request_ref.get().to_dict()
            
            self.send_rejection_email(request_data.get('requester_email'), request_data.get('bot_name'), reason)
            request_ref.delete()
            self.show_popup("Sucesso", "A solicitação foi rejeitada.")
            self.root.get_screen('admin').fetch_publication_requests()
        except Exception as e:
            self.show_popup("Erro", f"Não foi possível rejeitar a solicitação.\n{e}")

    def add_new_bot(self, name, version, link):
        if not db: return
        try:
            db.collection('bots').add({
                'nome': name,
                'versao': version,
                'link': link,
                'autor': 'Admin'
            })
            self.show_popup("Sucesso", f"Bot '{name}' publicado!")
        except Exception as e:
            self.show_popup("Erro", f"Não foi possível publicar o bot.\n{e}")

    def request_publication(self, name, description, link):
        if not db:
            self.show_popup("Erro", "Não foi possível conectar ao banco de dados.")
            return
        if not self.user_email:
            self.show_popup("Erro", "Você precisa estar logado.")
            return

        try:
            new_request_ref = db.collection('publication_requests').document()
            new_request_ref.set({
                'requester_email': self.user_email,
                'bot_name': name,
                'bot_description': description,
                'bot_link': link,
                'status': 'pending_payment',
                'request_date': firestore.SERVER_TIMESTAMP
            })
            self.show_popup("Sucesso!", "Sua solicitação foi enviada para revisão.")
            self.root.current = 'dashboard'
        except Exception as e:
            self.show_popup("Erro", f"Não foi possível enviar a solicitação.\n{e}")

    def delete_local_bot(self, file_path):
        try:
            os.remove(file_path)
            self.show_popup("Sucesso", f"O arquivo {os.path.basename(file_path)} foi excluído.")
            self.root.get_screen('my_bots').list_local_bots()
        except Exception as e:
            self.show_popup("Erro", f"Não foi possível excluir o arquivo.\n{e}")

    def change_password(self, new_password):
        if len(new_password) < 6:
            self.show_popup("Erro", "A nova senha deve ter pelo menos 6 caracteres.")
            return
        
        update_data = json.dumps({"idToken": self.user_token, "password": new_password, "returnSecureToken": False})
        try:
            response = requests.post(update_url, data=update_data)
            response.raise_for_status()
            self.show_popup("Sucesso", "Sua senha foi alterada.")
        except Exception as e:
            self.show_popup("Erro", f"Não foi possível alterar a senha.\n{e}")

    def delete_account(self):
        content = BoxLayout(orientation='vertical', spacing='10dp')
        content.add_widget(Label(text='Esta ação é irreversível!\nVocê tem certeza que deseja excluir sua conta?', color=self.theme['text_main']))
        confirm_button = Factory.AdminButton(text='Sim, Excluir Minha Conta', bg_color=(0.9, 0.2, 0.2, 1))
        cancel_button = Factory.AdminButton(text='Cancelar', bg_color=(0.5, 0.5, 0.5, 1))
        
        buttons_layout = BoxLayout(spacing='10dp', size_hint_y=None, height='40dp')
        buttons_layout.add_widget(cancel_button)
        buttons_layout.add_widget(confirm_button)
        content.add_widget(buttons_layout)

        popup = Popup(title='Confirmar Exclusão de Conta', content=content, size_hint=(0.9, 0.4))

        def _delete_confirmed(instance):
            popup.dismiss()
            delete_data = json.dumps({"idToken": self.user_token})
            try:
                response = requests.post(delete_url, data=delete_data)
                response.raise_for_status()
                self.show_popup("Conta Excluída", "Sua conta foi excluída com sucesso.")
                self.logout()
            except Exception as e:
                self.show_popup("Erro", f"Não foi possível excluir a conta.\n{e}")

        confirm_button.bind(on_release=_delete_confirmed)
        cancel_button.bind(on_release=popup.dismiss)
        popup.open()

    def download_bot(self, download_link, button_instance):
        if not download_link:
            self.show_popup("Erro", "Link de download não encontrado.")
            return

            download_dir = os.path.join(primary_external_storage_path(), 'Android', 'Media', 'com.BotDeploy')
        else:
            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'BotDeploy')
        
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        file_path = os.path.join(download_dir, button_instance.file_name)

        try:
            button_instance.disabled = True
            button_instance.text = "Baixando..."

            response = requests.get(download_link, stream=True)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            button_instance.text = "Instalado"
            self.last_downloaded_path = file_path

            install_screen = self.root.get_screen('install')
            terminal_text = (
                f"SUCESSO!\nBot '{button_instance.file_name}' salvo em:\n{file_path}\n\n"
                f"Pronto para executar no Termux.\n\n"
                f"> Pressione o botão abaixo para iniciar."
            )
            install_screen.ids.terminal_output.text = terminal_text
            self.root.current = 'install'

        except Exception as e:
            button_instance.disabled = False
            button_instance.text = "Tentar Nov."
            self.show_popup("Erro no Download", str(e))
    
    def execute_in_termux(self):
        if platform != 'android':
            self.show_popup("Aviso", "Esta função só está disponível no Android.")
            return

        if not self.last_downloaded_path:
            self.show_popup("Erro", "Nenhum bot foi instalado ainda. Instale um primeiro.")
            return

        relative_path = os.path.relpath(self.last_downloaded_path, primary_external_storage_path())
        termux_path = os.path.join('~/storage/shared', relative_path)
        command_to_run = f"python {termux_path}"

        try:
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            context = autoclass('org.kivy.android.PythonActivity').mActivity

            intent = Intent(Intent.ACTION_RUN)
            intent.setData(Uri.parse(f"com.termux.file:{termux_path}"))
            intent.putExtra("com.termux.execute.command", command_to_run)
            context.startActivity(intent)
        except Exception as e:
            self.show_popup("Erro ao abrir o Termux", "Verifique se o Termux está instalado e se a permissão 'termux-setup-storage' foi concedida.\n\n" + str(e))

if __name__ == '__main__':
    BotDownloaderApp().run()
