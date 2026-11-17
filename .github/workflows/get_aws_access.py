"""Obtém credenciais temporárias da AWS pelo portal AWS Academy.

O fluxo usa Playwright para autenticar no portal, iniciar/verificar a conta
informada e ler as credenciais temporárias exibidas na página. Ao executar o
arquivo diretamente, exige as variáveis de ambiente ``EMAIL`` e ``PASSWORD``
e acrescenta as credenciais coletadas ao arquivo local ``creds.txt``.

As credenciais e capturas de tela podem conter informações sensíveis. Não
versione esses arquivos nem publique as capturas geradas pelo script.
"""
import logging
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis de ambiente do arquivo .env, se existir

logging.basicConfig(level=logging.INFO)


class AWS:
    """Automatiza a autenticação e a consulta de credenciais no AWS Academy.

    Args:
        email: E-mail usado para autenticação no portal.
        password: Senha da conta do portal.
        headless: Se ``True``, executa o Chromium sem janela visível.

    Attributes:
        page: Página Playwright utilizada durante a automação.
        screenshots: Diretório relativo usado para salvar capturas de tela.

    A inicialização abre o navegador e tenta concluir o login imediatamente.
    """

    def __init__(self, email: str, password: str, headless=True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.screenshots = "screenshots"

        logging.info("[+] Navegador iniciado")
        self._login(email, password)

    def _login(self, email: str, password: str):
        """Autentica no portal e salva capturas das etapas do login.

        Raises:
            RuntimeError: Se a URL de login concluído não for alcançada.
        """
        logging.info("[*] Fazendo login...")
        self.page.goto("https://www.awsacademy.com/vforcesite/LMS_Login")

        self.page.click('body > div.splash-body > a:nth-child(1) > button')
        self.page.screenshot(path=f"{self.screenshots}/1-click_start.png")

        self.page.fill("#username", email)
        self.page.fill("#password", password)
        self.page.screenshot(path=f"{self.screenshots}/2-send_data.png")

        self.page.click(
            '#react-router-portals > div > span > span > div > div > main '
            '> span > div.css-1itq1yq-view > span > form > span > '
            'span.css-x4jjeu-view--flex-flex > button')

        try:
            self.page.wait_for_url(
                "https://awsacademy.instructure.com/?login_success=1", timeout=15000)
            logging.info("[+] Login concluído com sucesso")
            self.page.screenshot(
                path=f"{self.screenshots}/3-conclude_login.png")
        except Exception as exc:
            logging.error(
                "[!] Falha no login: credenciais inválidas ou página não carregou corretamente")
            self.page.screenshot(path=f"{self.screenshots}/3-login_error.png")
            raise RuntimeError(
                "Login falhou! Verifique suas credenciais ou se o site mudou o layout.") from exc

    def configure_aws(self, conta: str):
        """Abre o laboratório da conta e retorna o texto das credenciais.

        Args:
            conta: Identificador do curso/conta no AWS Academy.

        Returns:
            Texto exibido pelo portal contendo as credenciais temporárias.

        A conta é iniciada se o indicador de status não estiver verde. Uma
        captura de tela é salva em cada etapa principal da consulta.
        """
        logging.info("[+] Entrando na AWS")
        self.page.goto(
            f"https://awsacademy.instructure.com/courses/{conta}/modules/items/18151799")
        self.page.wait_for_load_state("domcontentloaded", timeout=0)
        self.page.screenshot(path=f"{self.screenshots}/4-configure_aws.png")

        logging.info('[*] Verificando status da conta')
        frame_locator = self.page.frame_locator('iframe.tool_launch')
        locator = frame_locator.locator('#vmstatus')
        locator.wait_for(state='attached', timeout=30000)
        classe = locator.get_attribute('class')
        self.page.screenshot(
            path=f"{self.screenshots}/5-configure_aws_status.png")

        if 'led-green' not in classe:
            logging.info('[*] Inicia a conta da AWS')
            frame_locator.locator('#launchclabsbtn').click()
            frame_locator.locator('#vmstatus.led-green').wait_for(timeout=0)

        logging.info("[*] Coletando informações da AWS")
        # mostrar informações aws
        frame_locator.locator('#detailbtn2').click()
        frame_locator.locator('#clikeyboxbtn').click()
        self.page.screenshot(
            path=f"{self.screenshots}/6-show_aws_credentials.png")

        # coletar texto
        text_locator = frame_locator.locator('#clikeybox > pre > span')
        text_locator.wait_for(state='attached', timeout=0)
        return text_locator.text_content()

    @staticmethod
    def get_secrets(info_raw: str):
        """Extrai as três credenciais AWS do texto retornado pelo portal.

        Args:
            info_raw: Texto com as credenciais no formato apresentado pelo
                AWS Academy.

        Returns:
            Tupla ``(access_key_id, secret_access_key, session_token)``.
        """
        info = info_raw.split()

        aws_access_key_id = info[1].split('=')[1]
        aws_secret_access_key = info[2].split('=')[1]
        aws_session_token = info[3].split('=', 1)[1]
        logging.info('[+] Dados coletados')
        return aws_access_key_id, aws_secret_access_key, aws_session_token


def set_github_env(aws_access_key_id: str, aws_secret_access_key: str, aws_session_token: str):
    """Acrescenta as credenciais ao arquivo local ``creds.txt``.

    Apesar do nome, esta função não configura o ambiente do GitHub Actions;
    ela apenas grava três atribuições ``CHAVE=valor`` no diretório atual.
    Proteja o arquivo, pois ele contém credenciais temporárias utilizáveis.
    """
    with open('creds.txt', 'a') as env_file:
        env_file.write(f"AWS_ACCESS_KEY_ID={aws_access_key_id}\n")
        env_file.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}\n")
        env_file.write(f"AWS_SESSION_TOKEN={aws_session_token}\n")


if __name__ == "__main__":
    # As variáveis EMAIL e PASSWORD devem ser fornecidas pelo ambiente.
    import os

    email = os.getenv("EMAIL")
    senha = os.getenv("PASSWORD")
    CONTA = "183880"

    aws = AWS(email, senha)
    page = aws.page
    try:
        info_raw = aws.configure_aws(CONTA)
        aws_access_key_id, aws_secret_access_key, aws_session_token = aws.get_secrets(
            info_raw)
        set_github_env(aws_access_key_id,
                       aws_secret_access_key, aws_session_token)
    except Exception as error:
        SCREENSHOT_DIR = "screenshots"
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        timestamp = int(time.time())
        path = os.path.join(
            SCREENSHOT_DIR, f"screenshot_error_{timestamp}.png")
        page.screenshot(path=path)
        logging.info("Screenshot salvo em: %s", path)
        raise Exception(error) from error
