# Sobre o Programa - RPA RSP OpenPort

O **RPA RSP OpenPort** é um assistente virtual e robô de automação (RPA - Robotic Process Automation) desenvolvido em Python utilizando a biblioteca **Selenium** para interagir diretamente com o portal web **OpenPort (CODEBA - Porto de Ilhéus)**.

Seu objetivo principal é automatizar o lançamento mensal de consumo de água e energia elétrica das empresas operadoras do porto a partir de uma planilha Excel consolidada, eliminando o preenchimento manual lento e propício a erros humanos.

---

## 🎯 Problema que o Robô Resolve

Todos os meses, o setor financeiro e de faturamento do porto recebe uma planilha Excel contendo as leituras de consumo diárias ou acumuladas de água e energia para diversas empresas concessionárias (como *AIS*, *Base Liba*, *Intermarítima*, *Irmãos Brito*, etc.).

Manualmente, para cada registro de consumo, um operador precisa:
1. Entrar na tela **6050** do portal, preencher uma Capa de RSP para o CNPJ da empresa, datar e salvar.
2. Abrir um popup de serviços na aba inferior da RSP, inserir o serviço correto (Água ou Energia), aguardar o preenchimento Ajax e salvar.
3. Clicar em "Solicitar Liberação" na capa, aceitar as caixas de alerta do portal para aprovar a requisição.
4. Navegar para a tela **6060** (Apontamentos), buscar o número da RSP gerada e clicar para editar.
5. Clicar em "Inserir" na aba inferior de Apontamentos para abrir um segundo popup, digitar a quantidade consumida (m³ ou kW/h), as datas/horas de início e fim, as observações detalhadas de faturamento e salvar.
6. Clicar em "Concluir" na tela de apontamentos e confirmar o despacho.

Esse ciclo para dezenas ou centenas de linhas tomava horas de trabalho repetitivo. O robô executa cada ciclo completo em cerca de **45 a 60 segundos** com precisão absoluta.

---

## 🛠️ Principais Funcionalidades

### 1. Processamento Otimizado de Excel
* Lê arquivos de formatos legados `.xls` e arquivos modernos `.xlsx`.
* Mapeia automaticamente as colunas da planilha baseado em coordenadas configuráveis (linhas, colunas de início e fim para cada Prestadora).
* Identifica automaticamente se a coluna corresponde a consumo de **Água** ou **Energia**, aplicando as regras de negócio de cada uma.
* **Processamento da Última Linha:** Localiza automaticamente a última linha de dados válida na planilha e processa somente ela. Isso garante que cobranças de meses anteriores (já lançadas) não sejam reprocessadas, mantendo o foco exclusivamente no mês vigente.

### 2. Validação e Formatação de Dados
* **Formatação Inteligente de Consumo:** Números inteiros (ex: `152`) são enviados ao portal sem casas decimais (`"152"`). Números fracionários (ex: `0,23` m³ de água) são enviados com vírgula como separador decimal (`"0,23"`). Isso evita que o OpenPort interprete incorretamente os separadores de milhar e decimal.
* **Datas Mensais Automáticas:** As cobranças são mensais, portanto a data de início é sempre **dia 01 do mês** e a data final é sempre o **último dia do mês** (28, 29, 30 ou 31 conforme o caso), calculado dinamicamente.

### 3. Fluxo de Execução E2E Autônomo
* **Autenticação:** Realiza login automático com tratamento de sessões expiradas.
* **Criação de Capa (Tela 6050):** Cria a requisição vinculando o CNPJ correto do Prestador e do Tomador do serviço, com a respectiva data de competência.
* **Associação de Serviços via AJAX:** Controla a abertura e preenchimento de popups dinâmicos. Envia o sinalizador de `TAB` para disparar as consultas internas do portal de forma a evitar exceções no banco de dados.
* **Auto-Aprovação Dinâmica:** Simula o clique de liberação e gerencia de forma inteligente a resposta de múltiplos popups nativos de alerta do JavaScript de confirmação e sucesso.
* **Apontamento de Consumo (Tela 6060):** Localiza a RSP previamente autorizada, preenche as datas de início e término do mês completo, quantidade consumida e monta uma observação descritiva dinâmica contendo a competência e o nome da empresa.
* **Despacho Automático:** Conclui a ordem de serviço no banco de dados, deixando-a pronta para faturamento direto.

### 4. Mecanismos de Resiliência
* **Resolução Nativa de Drivers:** Não depende de softwares ou dependências externas para rodar o ChromeDriver do Chrome. O gerenciamento é feito de forma transparente e em segundo plano pelo Selenium Manager.
* **Tratamento de Janelas Modais:** Gerenciamento robusto de alternância de janelas ativa/filha (`window handles`), garantindo o fechamento e retorno limpo das modais para a janela pai de controle, impedindo bloqueios de tela.
* **Sistema de Retry:** Realiza tentativas automáticas ao tentar interagir com botões ou campos de texto se houver oscilação de rede ou lentidão no carregamento das páginas web.
* **Relatórios Automatizados:** Gera arquivos Excel distintos com o status de cada execução para auditoria operacional.
