# RPA OpenPort - CODEBA (Porto de Ilhéus)

Este repositório contém uma automação robótica de processos (RPA) desenvolvida em Python e Selenium para agilizar o faturamento mensal de consumo de água e energia elétrica das empresas operadoras no Porto de Ilhéus através do portal **OpenPort** da CODEBA.

---

## 📂 Estrutura da Documentação

Para entender e usar o sistema, consulte os seguintes guias:

* **[Sobre o Programa](sobre_o_programa.md):** Apresentação das funcionalidades completas, validações de dados e fluxo do robô.
* **[Guia Passo a Passo de Execução](passo_a_passo.md):** Como configurar o ambiente Python, instalar dependências, ajustar configurações e rodar a automação.
* **[Memória de Desenvolvimento](memory.md):** Mapeamento técnico do sistema, seletores, comportamento AJAX de popups e histórico de correções de bugs.

---

## ⚡ Como Começar (Resumo)

### 1. Requisitos
- Python 3.10 ou superior
- Google Chrome instalado

### 2. Instalação
```bash
pip install -r requirements.txt
```

### 3. Configuração
1. Copie o arquivo de exemplo de configurações:
   ```bash
   cp config.example.py config.py
   ```
2. Abra o arquivo `config.py` e preencha com o seu CPF, senha, caminho da planilha Excel de leituras e os CNPJs das prestadoras.

### 4. Execução
```bash
python rpa_rsp.py
```

---

## 📝 Licença

Este projeto é de uso interno para otimização de faturamento da CODEBA.
