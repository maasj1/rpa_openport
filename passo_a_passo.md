# Guia Passo a Passo de Execução - RPA RSP OpenPort

Este guia contém as instruções necessárias para configurar o ambiente e executar o robô de processamento de RSPs e Apontamentos de Consumo.

---

## Passo 1: Preparação do Ambiente

### 1. Instalar o Python
Certifique-se de ter o Python 3.10 ou superior instalado na sua máquina. Você pode validar abrindo o terminal (PowerShell ou CMD) e executando:
```powershell
python --version
```

### 2. Instalar as Dependências
Navegue até a pasta do projeto e instale as bibliotecas necessárias declaradas no arquivo `requirements.txt`:
```powershell
pip install -r requirements.txt
```
> [!NOTE]
> Se você estiver em uma rede corporativa com restrições e timeouts para baixar bibliotecas do PyPI padrão, utilize o mirror interno ou adicione parâmetros de timeout ao pip:
> `pip install -r requirements.txt --timeout 120`

---

## Passo 2: Configuração dos Parâmetros

As configurações gerais da execução do robô ficam concentradas no arquivo [config.py](file:///c:/Users/marcelo.augusto/Documents/New%20OpenCode%20Project/rpa_openport/config.py). Abra-o e valide os seguintes dados:

1. **Credenciais do OpenPort:**
   ```python
   USUARIO = "03746413583"
   SENHA = "..." # Senha do portal
   ```
2. **Caminho da Planilha:**
   ```python
   CAMINHO_PLANILHA = r"Y:\COBRANÇA MENSAL\PLANILHA 25 - 26 CONSUMO ÁGUA E ENERGIA.xls"
   ABA_PLANILHA = "CONTAINERS" # Nome exato da aba no Excel
   ```
3. **Mapeamento de Empresas e CNPJs:**
   Verifique se as empresas que constam nos cabeçalhos da planilha estão listadas corretamente no dicionário `EMPRESAS` com seus CNPJs atualizados.

---

## Passo 3: Executar o RPA

Com a planilha no caminho especificado e o portal de login ativo, execute o script principal através do terminal:

```powershell
python rpa_rsp.py
```

### O que o robô fará ao iniciar:
1. Abrirá uma janela automatizada do Google Chrome.
2. Realizará o login no portal OpenPort da CODEBA de forma automática.
3. Carregará a planilha Excel e localizará automaticamente a **última linha de dados válida** (a mais recente, correspondente ao mês a ser cobrado).
4. Para cada empresa/serviço presente nessa linha, criará a Capa da RSP, vinculará o Serviço, aprovará/liberará a requisição, e efetuará o lançamento/apontamento de consumo com **período mensal** (dia 01 até o último dia do mês).
5. Fechará o navegador ao terminar.

---

## Passo 4: Analisar os Resultados

Após a conclusão da execução, você pode conferir o status através das seguintes saídas:

1. **Planilha de Sucessos:** 
   O robô gera uma planilha consolidada com todas as RSPs que foram lançadas e apontadas com sucesso. Ela é salva na pasta do projeto com o padrão:
   `logs/sucessos_rsp_AAAAMMDD_HHMMSS.xlsx`

2. **Planilha de Erros:**
   Caso algum registro apresente falhas ao longo do processo (ex: CNPJ não cadastrado ou oscilação de rede), o robô cria um relatório detalhado contendo a linha correspondente do Excel e o motivo do erro na pasta:
   `logs/erros_rsp_AAAAMMDD_HHMMSS.xlsx`

3. **Arquivo de Logs Geral:**
   O histórico completo e técnico da execução detalhando cada passo do robô fica salvo em:
   `logs/rpa_rsp.log`

---

## 🛠️ Resolução de Problemas Comuns (Troubleshooting)

* **O robô trava após abrir o Chrome:** Certifique-se de que não existem sessões do Chrome antigas ou congeladas presas em segundo plano no Gerenciador de Tarefas do Windows.
* **Erro de conexão com o banco ou lentidão na resposta do site:** O sistema OpenPort às vezes apresenta instabilidades de lentidão. O robô possui retentativas automáticas (`MAX_TENTATIVAS = 3`), mas em casos extremos de queda do portal, o robô interromperá o processamento gerando o relatório de erro com a última linha processada para que você possa continuar dali posteriormente.
* **Erros de "Element Not Found" na tela 6060:** Confirme se o usuário de login possui as permissões ativas de aprovação e de lançamento de apontamentos. O robô assume que as RSPs são auto-aprovadas no momento da liberação.
