"""
RPA - Requisição de Serviços Portuárias (RSP)
Sistema OpenPort - CODEBA Ilhéus

Automatiza a criação de RSPs no sistema OpenPort lendo a planilha
hierárquica de consumo (aba "containers") e preenchendo as telas
6050 (Capa) e 6060 (Apontamento).
"""

import sys
import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
)

from config import (
    URL_BASE, USUARIO, SENHA, TELA_CAPA, TELA_APONTAMENTO,
    SERVICOS, MESES, TIMEOUT_PADRAO, MAX_TENTATIVAS,
    INTERVALO_TENTATIVA, CAMINHO_PLANILHA
)
from ler_excel import ler_planilha, gerar_resumo


class RPAAberturaRSP:

    def __init__(self):
        self.driver = None
        self.wait = None
        self.erros = []
        self.sucessos = []
        self._configurar_logging()

    def _configurar_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        data_execucao = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"rpa_rsp_{data_execucao}.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Log de execução: {log_file}")

    def _iniciar_navegador(self):
        self.logger.info("Iniciando navegador Chrome...")

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": str(Path.cwd()),
            "download.prompt_for_download": False,
        })

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, TIMEOUT_PADRAO)

        self.logger.info("Navegador iniciado com sucesso!")

    def _login(self):
        self.logger.info("Acessando página de login...")
        self.driver.get(URL_BASE)
        time.sleep(2)

        self.logger.info("Preenchendo credenciais...")
        campo_usuario = self.wait.until(
            EC.presence_of_element_located((By.ID, "User"))
        )
        campo_usuario.clear()
        campo_usuario.send_keys(USUARIO)

        campo_senha = self.driver.find_element(By.ID, "Pass")
        campo_senha.clear()
        campo_senha.send_keys(SENHA)

        self.logger.info("Clicando em 'Entrar'...")
        botao_entrar = self.driver.find_element(By.ID, "Entrar")
        botao_entrar.click()

        time.sleep(3)

        try:
            # Aguarda a caixa de código de tela aparecer (confirma que o login foi bem-sucedido)
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div/div[1]/div/div[3]/form/div/span[1]/input[2]")
                )
            )
            self.logger.info("Login realizado com sucesso!")
            return True
        except TimeoutException:
            self.logger.error("Falha no login - timeout ao aguardar caixa de código de tela")
            return False

    def _navegar_para_tela(self, codigo_tela):
        self.logger.info(f"Navegando para tela {codigo_tela}...")

        try:
            try:
                campo_codigo = self.wait.until(
                    EC.presence_of_element_located((By.ID, "txtMenuAccess"))
                )
            except TimeoutException:
                campo_codigo = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "/html/body/div/div[1]/div/div[3]/form/div/span[1]/input[2]")
                    )
                )
            
            campo_codigo.clear()
            campo_codigo.send_keys(codigo_tela)
            campo_codigo.send_keys(Keys.RETURN)

            time.sleep(3)
            self.logger.info(f"Tela {codigo_tela} acessada com sucesso!")
            return True
        except TimeoutException:
            self.logger.error(f"Falha ao navegar para tela {codigo_tela}")
            return False

    def _clicar_novo(self):
        self.logger.info("Clicando em 'Novo'...")

        # Garantir que estamos no frame principal
        self.driver.switch_to.default_content()

        # Aguardar a tela carregar completamente
        time.sleep(5)

        # Lista de estratégias para encontrar o botão "Novo" no frame principal
        estrategias = [
            (By.ID, "INSERIR"),
            (By.ID, "btnNovo"),
            (By.XPATH, "//*[contains(text(), 'Novo')]"),
            (By.XPATH, "//label[contains(text(), 'Novo')]"),
            (By.XPATH, "//input[@value='Novo']"),
            (By.XPATH, "//a[contains(text(), 'Novo')]"),
            (By.XPATH, "//span[contains(text(), 'Novo')]"),
            (By.CSS_SELECTOR, "[id*='Novo']"),
        ]

        # Tentar no frame principal primeiro
        for by, seletor in estrategias:
            try:
                elemento = self.driver.find_element(by, seletor)
                self.logger.info(f"Botão 'Novo' encontrado no frame principal: {by}='{seletor}' (tag={elemento.tag_name})")
                elemento.click()
                time.sleep(2)
                self.logger.info("Botão 'Novo' clicado com sucesso!")
                return True
            except Exception:
                continue

        # Se não encontrou no frame principal, tentar dentro dos iframes
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for i, iframe in enumerate(iframes):
            try:
                self.driver.switch_to.frame(iframe)
                self.logger.info(f"Buscando 'Novo' dentro do iframe {i}...")

                # Esperar o iframe carregar
                time.sleep(5)

                for by, seletor in estrategias:
                    try:
                        elemento = self.driver.find_element(by, seletor)
                        self.logger.info(f"Botão 'Novo' encontrado no iframe {i}: {by}='{seletor}' (tag={elemento.tag_name})")
                        elemento.click()
                        time.sleep(2)
                        self.logger.info("Botão 'Novo' clicado com sucesso!")
                        return True
                    except Exception:
                        continue

                # Voltar ao frame principal para tentar o próximo iframe
                self.driver.switch_to.default_content()
            except Exception:
                self.driver.switch_to.default_content()
                continue

        # Se nada funcionou, logar os elementos visíveis para debug
        self.driver.switch_to.default_content()
        self.logger.error("Não foi possível encontrar o botão 'Novo' com nenhuma estratégia")
        try:
            todos = self.driver.find_elements(By.XPATH, "//*[string-length(text()) > 0 and string-length(text()) < 30]")
            textos = [f"<{e.tag_name} id='{e.get_attribute('id')}'>{e.text}" for e in todos[:30] if e.text.strip()]
            self.logger.info(f"Elementos visíveis no frame principal: {textos}")
        except Exception:
            pass
        return False

    def _preencher_campo(self, elemento_id, valor, timeout=TIMEOUT_PADRAO):
        try:
            wait = WebDriverWait(self.driver, timeout)
            campo = wait.until(
                EC.presence_of_element_located((By.ID, elemento_id))
            )
            campo.clear()
            time.sleep(0.3)
            campo.send_keys(str(valor))
            return True
        except TimeoutException:
            try:
                campo = self.driver.find_element(By.XPATH, f"//input[@id='{elemento_id}']")
                campo.clear()
                campo.send_keys(str(valor))
                return True
            except Exception:
                self.logger.error(f"Falha ao preencher campo {elemento_id}")
                return False

    def _preencher_campo_com_enter(self, elemento_id, valor, timeout=TIMEOUT_PADRAO):
        """Preenche um campo e pressiona Enter para confirmar busca/seleção."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            campo = wait.until(
                EC.presence_of_element_located((By.ID, elemento_id))
            )
            campo.clear()
            time.sleep(0.3)
            campo.send_keys(str(valor))
            time.sleep(0.5)
            campo.send_keys(Keys.RETURN)
            time.sleep(1)
            return True
        except TimeoutException:
            try:
                campo = self.driver.find_element(By.XPATH, f"//input[@id='{elemento_id}']")
                campo.clear()
                campo.send_keys(str(valor))
                campo.send_keys(Keys.RETURN)
                time.sleep(1)
                return True
            except Exception:
                self.logger.error(f"Falha ao preencher campo {elemento_id}")
                return False

    def _obter_observacao(self, tipo_servico, empresa, data):
        mes = MESES[data.month]
        servico = SERVICOS[tipo_servico]
        texto = servico["texto_obs"]
        return f"referente ao {texto} da empresa {empresa} - mês de {mes}"

    def _criar_capa_rsp(self, registro):
        empresa = registro["empresa"]
        cnpj = registro["cnpj"]
        data = registro["data"]
        tipo_servico = registro["tipo_servico"]

        self.logger.info(f"Criando capa RSP para {empresa} ({cnpj})...")

        if not self._navegar_para_tela(TELA_CAPA):
            raise Exception("Falha ao navegar para tela 6050")

        if not self._clicar_novo():
            raise Exception("Falha ao clicar em Novo na tela 6050")

        servico = SERVICOS[tipo_servico]
        data_str = data.strftime("%d/%m/%Y")

        self.logger.info("Preenchendo campos da capa...")

        if not self._preencher_campo_com_enter("NUM_OPERADOR_2", cnpj):
            self._preencher_campo_com_enter("NUM_OPERADOR", cnpj)
 
        time.sleep(1)
 
        if not self._preencher_campo_com_enter("NUM_EMPRESA_FATURAR_2", cnpj):
            self._preencher_campo_com_enter("NUM_EMPRESA_FATURAR", cnpj)
 
        time.sleep(1)
 
        if not self._preencher_campo("DAT_REQUISICAO", data_str):
            self._preencher_campo("DAT_REQUISICAO_2", data_str)
 
        time.sleep(1)

        self.logger.info("Salvando capa RSP...")
        if not self._salvar():
            raise Exception("Falha ao salvar capa RSP")

        # Obter número da RSP gerada
        numero_rsp = self._obter_numero_rsp()
        self.logger.info(f"Capa RSP criada! Número: {numero_rsp}")

        if numero_rsp == "N/A" or not numero_rsp:
            # Tentar ler novamente com fallback
            try:
                campo_num = self.driver.find_element(By.ID, "NUM_REQUISICAO")
                numero_rsp = campo_num.text.strip()
                self.logger.info(f"Fallback número RSP: {numero_rsp}")
            except Exception:
                pass

        if not numero_rsp or numero_rsp == "N/A":
            raise Exception("Não foi possível identificar o número da RSP gerada")

        # 2. Adicionar o Serviço no popup
        self.logger.info(f"Adicionando serviço '{servico['codigo']}'...")
        main_window = self.driver.current_window_handle
        
        try:
            self.driver.find_element(By.XPATH, "//img[@alt='Inserir']").click()
            time.sleep(4)
            
            # Mudar para popup
            popup_handle = None
            for h in self.driver.window_handles:
                if h != main_window:
                    popup_handle = h
                    self.driver.switch_to.window(h)
                    break
                    
            if not popup_handle:
                raise Exception("Popup de serviço não abriu")
                
            # Preencher serviço e enviar TAB para autocomplete
            input_serv = self.driver.find_element(By.ID, "NUM_SERVICO_FAT_2")
            input_serv.clear()
            input_serv.send_keys(servico["codigo"])
            input_serv.send_keys(Keys.TAB)
            time.sleep(3)
            
            # Gravar serviço
            self.driver.find_element(By.ID, "GRAVAR").click()
            time.sleep(3)
            
            # Fechar popup
            self.driver.close()
        except Exception as e:
            self.logger.error(f"Erro ao adicionar serviço no popup: {e}")
            raise e
        finally:
            self.driver.switch_to.window(main_window)
            time.sleep(2)

        # 3. Liberar/Aprovar RSP
        self.logger.info("Liberando/Aprovando requisição...")
        try:
            self.driver.find_element(By.ID, "LIBERACAO").click()
            time.sleep(2)
            # Tratar os dois alertas sequenciais (confirmação e aprovação)
            for i in range(2):
                try:
                    alert = self.driver.switch_to.alert
                    self.logger.info(f"Alerta {i+1} aceito: {alert.text}")
                    alert.accept()
                    time.sleep(2)
                except Exception:
                    pass
        except Exception as e:
            self.logger.warning(f"Aviso ao liberar RSP: {e}")

        return numero_rsp

    def _criar_apontamento(self, registro, numero_rsp):
        empresa = registro["empresa"]
        tipo_servico = registro["tipo_servico"]
        consumo = registro["consumo"]
        data_inicio = registro["data_inicio"]
        data_fim = registro["data_fim"]

        self.logger.info(f"Criando apontamento para RSP {numero_rsp} da empresa {empresa}...")

        if not self._navegar_para_tela(TELA_APONTAMENTO):
            raise Exception("Falha ao navegar para tela 6060")

        # Buscar pela requisição
        try:
            input_req = self.wait.until(EC.presence_of_element_located((By.ID, "sqlNUM_REQUISICAO")))
            input_req.clear()
            input_req.send_keys(numero_rsp)
            
            self.driver.find_element(By.ID, "BPESQUISAR").click()
            time.sleep(4)
        except Exception as e:
            self.logger.error(f"Erro ao buscar RSP {numero_rsp} na tela 6060: {e}")
            raise e

        # Clicar em Modificar na linha encontrada
        try:
            btn_modificar = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Modificar']")))
            btn_modificar.click()
            time.sleep(4)
        except Exception as e:
            self.logger.error(f"Não encontrou registro para modificar na tela 6060: {e}")
            raise e

        servico = SERVICOS[tipo_servico]
        observacao = self._obter_observacao(tipo_servico, empresa, registro["data"])

        # Clicar em Inserir Apontamento (valores)
        self.logger.info("Abrindo popup de apontamento de valores...")
        main_window = self.driver.current_window_handle
        
        try:
            self.driver.find_element(By.XPATH, "//img[@alt='Inserir']").click()
            time.sleep(4)
            
            # Mudar para popup
            popup_handle = None
            for h in self.driver.window_handles:
                if h != main_window:
                    popup_handle = h
                    self.driver.switch_to.window(h)
                    break
                    
            if not popup_handle:
                raise Exception("Popup de valores do apontamento não abriu")

            # Preencher campos de valores
            consumo_str = registro["consumo_formatado"]
            
            self.driver.find_element(By.ID, "QTD_APONTAMENTO").clear()
            self.driver.find_element(By.ID, "QTD_APONTAMENTO").send_keys(consumo_str)
            
            # Preencher Unidade
            try:
                select_unidade = self.driver.find_element(By.ID, "NUM_UND_MED")
                select_unidade.send_keys(servico["unidade"])
            except Exception:
                pass
                
            # Preencher Datas e Horas
            self.driver.find_element(By.ID, "DAT_INICIAL").clear()
            self.driver.find_element(By.ID, "DAT_INICIAL").send_keys(data_inicio.strftime("%d/%m/%Y"))
            self.driver.find_element(By.ID, "DAT_INICIAL_2").clear()
            self.driver.find_element(By.ID, "DAT_INICIAL_2").send_keys(data_inicio.strftime("%H:%M"))
            
            self.driver.find_element(By.ID, "DAT_FINAL").clear()
            self.driver.find_element(By.ID, "DAT_FINAL").send_keys(data_fim.strftime("%d/%m/%Y"))
            self.driver.find_element(By.ID, "DAT_FINAL_2").clear()
            self.driver.find_element(By.ID, "DAT_FINAL_2").send_keys(data_fim.strftime("%H:%M"))
            
            # Observação
            self.driver.find_element(By.ID, "DCR_OBSERVACAO").clear()
            self.driver.find_element(By.ID, "DCR_OBSERVACAO").send_keys(observacao)
            time.sleep(1)

            # Gravar valores
            self.driver.find_element(By.ID, "GRAVAR").click()
            time.sleep(3)
            
            self.driver.close()
        except Exception as e:
            self.logger.error(f"Erro ao preencher popup de apontamento de valores: {e}")
            raise e
        finally:
            self.driver.switch_to.window(main_window)
            time.sleep(2)

        # Gerar Protocolo do Apontamento
        self.logger.info("Gerando protocolo do apontamento...")
        main_window = self.driver.current_window_handle
        try:
            self.driver.find_element(By.ID, "GERARPROTOCOLO").click()
            time.sleep(3)

            # Fechar a página em branco que abre após gerar protocolo
            for h in self.driver.window_handles:
                if h != main_window:
                    self.driver.switch_to.window(h)
                    self.driver.close()
                    self.logger.info("Página do protocolo fechada.")
                    break

            self.driver.switch_to.window(main_window)
            time.sleep(1)
        except Exception as e:
            self.logger.warning(f"Aviso ao gerar protocolo: {e}")
            # Garantir retorno à janela principal
            try:
                self.driver.switch_to.window(main_window)
            except Exception:
                pass

        self.logger.info("Apontamento criado e protocolo gerado com sucesso!")

    def _salvar(self):
        for tentativa in range(MAX_TENTATIVAS):
            try:
                botao = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "GRAVAR"))
                )
                botao.click()
                time.sleep(2)
                return True
            except (TimeoutException, ElementClickInterceptedException):
                try:
                    self.driver.find_element(By.XPATH, "//button[contains(text(), 'Salvar')]").click()
                    time.sleep(2)
                    return True
                except Exception:
                    try:
                        self.driver.find_element(By.XPATH, "//input[@value='Salvar']").click()
                        time.sleep(2)
                        return True
                    except Exception:
                        if tentativa < MAX_TENTATIVAS - 1:
                            self.logger.warning(f"Tentativa {tentativa + 1} de salvar falhou, retry...")
                            time.sleep(INTERVALO_TENTATIVA)
                        else:
                            self.logger.error("Todas as tentativas de salvar falharam")
                            return False
        return False

    def _obter_numero_rsp(self):
        time.sleep(1)
        for campo_id in ("NUM_REQUISICAO", "txtNumero", "Numero", "txtRSP", "RSP"):
            try:
                campo = self.driver.find_element(By.ID, campo_id)
                valor = campo.get_attribute("value")
                if valor:
                    return valor
            except Exception:
                continue
        self.logger.warning("Não foi possível obter número da RSP")
        return "N/A"

    def _gerar_relatorio(self):
        self.logger.info("Gerando relatório Excel...")

        for tentativa in range(MAX_TENTATIVAS):
            try:
                botao = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "btnRelatorio"))
                )
                botao.click()
                time.sleep(3)
                self.logger.info("Relatório gerado com sucesso!")
                return True
            except (TimeoutException, ElementClickInterceptedException):
                try:
                    self.driver.find_element(
                        By.XPATH, "//button[contains(text(), 'Relatório') or contains(text(), 'Relatorio')]"
                    ).click()
                    time.sleep(3)
                    self.logger.info("Relatório gerado com sucesso!")
                    return True
                except Exception:
                    try:
                        self.driver.find_element(
                            By.XPATH, "//button[contains(text(), 'Gerar')]"
                        ).click()
                        time.sleep(3)
                        self.logger.info("Relatório gerado com sucesso!")
                        return True
                    except Exception:
                        if tentativa < MAX_TENTATIVAS - 1:
                            self.logger.warning(f"Tentativa {tentativa + 1} de gerar relatório falhou, retry...")
                            time.sleep(INTERVALO_TENTATIVA)
                        else:
                            self.logger.error("Todas as tentativas de gerar relatório falharam")
                            return False
        return False

    def _salvar_screenshot(self, contexto):
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho = log_dir / f"erro_{contexto}_{ts}.png"
            self.driver.save_screenshot(str(caminho))
            self.logger.info(f"Screenshot salvo: {caminho}")
        except Exception as e:
            self.logger.warning(f"Não foi possível salvar screenshot: {e}")

    def _voltar_estado_estavel(self):
        """Tenta recuperar para um estado estável sem perder a sessão."""
        try:
            # Tenta localizar a caixa de código de tela (sessão ainda ativa)
            campo = self.driver.find_element(
                By.XPATH, "/html/body/div/div[1]/div/div[3]/form/div/span[1]/input[2]"
            )
            # Se encontrou, a sessão está ativa — limpa o campo
            campo.clear()
            time.sleep(1)
            self.logger.info("Sessão ainda ativa, estado recuperado.")
        except Exception:
            # Sessão perdida — fazer login novamente
            self.logger.warning("Sessão perdida, realizando login novamente...")
            try:
                self._login()
            except Exception as e:
                self.logger.error(f"Falha ao refazer login: {e}")

    def _gerar_relatorio_erros(self):
        if not self.erros:
            self.logger.info("Nenhum erro registrado durante a execução.")
            return

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho = log_dir / f"erros_rsp_{ts}.xlsx"

        df = pd.DataFrame(self.erros)
        df.to_excel(caminho, index=False, sheet_name="Erros")

        self.logger.info(f"=== RELATÓRIO DE ERROS SALVO EM: {caminho} ===")

    def _gerar_relatorio_sucesso(self):
        if not self.sucessos:
            return

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho = log_dir / f"sucessos_rsp_{ts}.xlsx"

        df = pd.DataFrame(self.sucessos)
        df.to_excel(caminho, index=False, sheet_name="Sucessos")

        self.logger.info(f"Relatório de sucessos salvo em: {caminho}")

    def executar(self):
        self.logger.info("=" * 60)
        self.logger.info("INÍCIO DA EXECUÇÃO - RPA RSP OpenPort")
        self.logger.info("=" * 60)

        try:
            registros = ler_planilha()

            if not registros:
                self.logger.info("Nenhum registro para processar. Finalizando.")
                return

            self.logger.info(gerar_resumo(registros))

            self._iniciar_navegador()

            if not self._login():
                raise Exception("Falha na autenticação do OpenPort")

            total = len(registros)
            for idx, registro in enumerate(registros):
                self.logger.info("-" * 50)
                self.logger.info(
                    f"Processando {idx + 1}/{total}: "
                    f"{registro['empresa']} | {registro['tipo_servico']} | "
                    f"consumo={registro['consumo']}"
                )

                try:
                    numero_rsp = self._criar_capa_rsp(registro)

                    self._criar_apontamento(registro, numero_rsp)

                    self._gerar_relatorio()

                    self.sucessos.append({
                        "linha_planilha": registro["linha_planilha"],
                        "empresa": registro["empresa"],
                        "cnpj": registro["cnpj"],
                        "data": registro["data"].strftime("%d/%m/%Y"),
                        "tipo_servico": registro["tipo_servico"],
                        "consumo": registro["consumo"],
                        "numero_rsp": numero_rsp,
                        "status": "SUCESSO",
                    })

                    self.logger.info(
                        f"RSP criada com sucesso! "
                        f"Empresa: {registro['empresa']} | "
                        f"Serviço: {registro['tipo_servico']} | "
                        f"Número: {numero_rsp}"
                    )

                except Exception as e:
                    erro_msg = str(e)
                    self.logger.error(f"ERRO ao processar RSP: {erro_msg}")

                    self.erros.append({
                        "linha_planilha": registro["linha_planilha"],
                        "empresa": registro["empresa"],
                        "cnpj": registro["cnpj"],
                        "data": registro["data"].strftime("%d/%m/%Y"),
                        "tipo_servico": registro["tipo_servico"],
                        "consumo": registro["consumo"],
                        "erro": erro_msg,
                        "status": "FALHA",
                    })

                    self._salvar_screenshot(
                        f"linha{registro['linha_planilha']}_{registro['empresa']}"
                    )

                    self._voltar_estado_estavel()

            self._gerar_relatorio_erros()
            self._gerar_relatorio_sucesso()

            self.logger.info("=" * 60)
            self.logger.info("EXECUÇÃO FINALIZADA")
            self.logger.info(f"Total processado: {total}")
            self.logger.info(f"Sucessos: {len(self.sucessos)}")
            self.logger.info(f"Erros: {len(self.erros)}")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Erro fatal na execução: {e}")
            raise

        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Navegador fechado.")


def main():
    rpa = RPAAberturaRSP()

    try:
        rpa.executar()
    except KeyboardInterrupt:
        print("\nExecução interrompida pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\nErro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
