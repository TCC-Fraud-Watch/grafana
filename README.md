# 📊 Grafana - Fraud Watch

Repositório destinado ao gerenciamento, provisionamento e deploy de dashboards no Grafana para a plataforma Fraud Watch.

## 📋 Visão Geral

Este projeto automatiza a criação, validação e deploy de dashboards Grafana usando:
- **Docker** para containerização
- **CloudFormation** para infraestrutura como código (IaC)
- **GitHub Actions** para CI/CD
- **uv** para gerenciamento rápido de dependências Python
- **Playwright** para scraping de dados
- **AWS** para hospedagem e armazenamento

---

## 🚀 Quick Start

### Pré-requisitos
- Python 3.12+
- Docker & Docker Compose
- AWS CLI configurado
- uv (gerenciador de pacotes Python)

### Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/TCC-Fraud-Watch/grafana.git
cd grafana
```

2. Instale as dependências com `uv`:
```bash
python -m pip install --upgrade uv
uv sync --no-dev
```

3. (Opcional) Instale dependências de desenvolvimento:
```bash
uv sync
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas credenciais AWS
```

5. Suba o Grafana localmente:
```bash
docker-compose up -d
```

6. Acesse: http://localhost:3000 (usuário: `admin`, senha: `admin`)

---

## 📁 Estrutura do Projeto

```
grafana/
├── .github/
│   └── workflows/
│       ├── deploy.yml           # Pipeline principal de CI/CD
│       ├── validation.yml       # Validação em Pull Requests
│       ├── get_aws_access.py    # Script para obter credenciais AWS
│       └── scraping.py          # Script de scraping de dados
├── grafana/
│   ├── dashboards/
│   │   └── init.json            # Dashboard inicial de exemplo
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yaml  # Configuração de provisioning
│       └── datasources/
│           └── datasources.yaml # Configuração de datasources
├── infra/
│   └── grafana.yaml             # Template CloudFormation para deploy
├── docker-compose.yaml          # Configuração Docker local
├── pyproject.toml               # Dependências e configuração do projeto
├── grafana.ini                  # Configuração do Grafana
├── .gitignore                   # Arquivos ignorados pelo Git
└── README.md                    # Este arquivo
```

---

## 🔧 Configuração

### Docker Compose

Execute localmente:
```bash
docker-compose up -d
```

Acesse em: `http://localhost:3000`

Parar os serviços:
```bash
docker-compose down
```

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz:
```env
# AWS Credentials (obtidas automaticamente no CI/CD)
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_SESSION_TOKEN=xxx

# Grafana
GRAFANA_ADMIN_PASSWORD=admin
GF_SECURITY_ADMIN_USER=admin

# Email para notificações
SMTP_FROM_ADDRESS=noreply@fraudwatch.com
```

### Secrets do GitHub

Configure os seguintes secrets em **Settings → Secrets and variables → Actions**:

| Secret | Descrição |
|--------|-----------|
| `EMAIL` | Email para autenticação AWS |
| `PASSWORD` | Senha para autenticação AWS |
| `GRAFANA_KEY` | Chave PEM para acesso EC2 |
| `AWS_ACCESS_KEY_ID` | Credencial AWS |
| `AWS_SECRET_ACCESS_KEY` | Credencial AWS |
| `AWS_SESSION_TOKEN` | Token de sessão AWS (temporário) |

---

## 📊 Dashboards

### Dashboard Inicial
- **Arquivo:** `grafana/dashboards/init.json`
- **Panels inclusos:**
  - Série Temporal (timeseries)
  - Stat Gauge (métrica principal)
  - Gráfico de Barras
  - Tabela de Dados

### Criando Novos Dashboards

1. Crie/edite no Grafana UI
2. Exporte como JSON: **Dashboard → Menu → Export JSON model**
3. Salve em `grafana/dashboards/`
4. Commit e push (será automaticamente provisionado)

### Provisioning Automático

Os dashboards em `grafana/dashboards/` são automaticamente provisionados via `grafana/provisioning/dashboards/dashboards.yaml`.

---

## 🔄 Pipeline CI/CD

### Workflow: Deploy

Acionado por **push em `main`** ou manualmente via **workflow_dispatch**.

**Jobs executados:**

1. **validacao-codigo** 
   - Valida código com `pycodestyle` (PEP8)
   - Ignora linhas longas (E501)
   - Exclui ambientes virtuais

2. **configurar-credenciais**
   - Executa script de scraping (`get_aws_access.py`)
   - Obtém credenciais AWS temporárias
   - Faz upload de artefatos

3. **validar-credenciais**
   - Testa credenciais AWS
   - Valida acesso S3

4. **upload-to-s3**
   - Compacta código com timestamp
   - Faz upload para S3 (`sptech-bronze-jupyter/releases/`)
   - Mantém link `latest.zip`

5. **deploy-grafana-cloudformation** ⭐
   - Valida template CloudFormation
   - Deploy/atualiza stack `fraud-watch-grafana-stack`
   - Exibe URL da instância Grafana

### Workflow: Validation

Acionado por **Pull Requests** para `main`.

- Valida código (pycodestyle)
- Não faz deploy

---

## 🛠 Ferramentas de Desenvolvimento

### Validação Local

```bash
# Verificar PEP8
pycodestyle . --ignore=E501 --exclude=.venv,venv,env,infra

# Rodar testes
pytest

# Rodar flake8 (erros críticos)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,venv,env
```

### Gerenciamento de Dependências

```bash
# Sincronizar ambiente (sem dev-deps)
uv sync --no-dev

# Sincronizar com dev-deps
uv sync

# Instalar pacote específico
uv pip install <package>

# Gerar lock file
uv lock
```

---

## 📦 Dependências

### Runtime
- `uvicorn[standard]` ≥0.21.0 — Servidor ASGI
- `playwright` ≥1.40.0 — Automação de browser/scraping

### Development
- `pycodestyle` ≥2.14.0 — Validação de estilo PEP8
- `flake8` ≥6.0.0 — Linter avançado
- `pytest` ≥7.0 — Framework de testes

Veja `pyproject.toml` para versões exatas.

---

## 🚀 Deploy em Produção

### Opção 1: CloudFormation (Recomendado)

O deploy é automatizado via GitHub Actions. A stack CloudFormation cria:
- EC2 t2.micro (Amazon Linux 2023)
- Security Group (porta 3000 aberta)
- Docker + Docker Compose
- Clone automático do repositório
- Serviço Grafana rodando

**Acompanhar o deploy:**
```bash
aws cloudformation describe-stacks \
  --stack-name fraud-watch-grafana-stack \
  --region us-east-1 \
  --query 'Stacks[0].Outputs'
```

### Opção 2: Manual com Docker

```bash
# Em um EC2 ou servidor
docker pull grafana/grafana:latest
docker-compose up -d
```

---

## 🔐 Segurança

- ✅ Variáveis de ambiente em secrets do GitHub (não commitadas)
- ✅ Chave PEM (`GRAFANA_KEY`) armazenada como secret
- ✅ `.gitignore` exclui `.env`, `*.pem`, `__pycache__`, venvs
- ✅ CloudFormation com CAPABILITY_IAM controlado
- ✅ Validação de código em cada commit (CI/CD)

---

## 📝 Commits e Convenções

Use conventional commits:

```bash
git commit -m "feat: adicionar novo dashboard de vendas"
git commit -m "fix: corrigir query de datasource"
git commit -m "chore: atualizar dependências com uv"
git commit -m "docs: atualizar README"
```

---

## 🤝 Contribuindo

1. Crie uma branch: `git checkout -b feature/sua-feature`
2. Faça commits: `git commit -m "feat: descrição"`
3. Push: `git push origin feature/sua-feature`
4. Abra um Pull Request

**A CI/CD validará automaticamente seu código.**

---

## 📞 Suporte

Para dúvidas ou issues:
1. Abra uma issue no GitHub
2. Descreva o problema com logs/screenshots
3. Mencione sua versão do Python e SO

---

## 📄 Licença

Este projeto é parte da plataforma **Fraud watch**. Todos os direitos reservados.

---

## 📚 Referências

- [Grafana Docs](https://grafana.com/docs/)
- [Docker Compose](https://docs.docker.com/compose/)
- [AWS CloudFormation](https://aws.amazon.com/cloudformation/)
- [GitHub Actions](https://github.com/features/actions)
- [uv Package Manager](https://github.com/astral-sh/uv)
