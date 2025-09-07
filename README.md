# 📊 Dashboard de Qualidade - SEFAZ

Um dashboard interativo desenvolvido em **Streamlit** para análise de dados de satisfação de usuários de sistemas governamentais, com foco em três dimensões principais de qualidade.

## 🎯 Sobre o Projeto

Este dashboard foi desenvolvido para analisar pesquisas de satisfação utilizando escala Likert, oferecendo insights automáticos e sugestões de ações para melhoria contínua dos serviços públicos.

### 📈 Dimensões Analisadas

- **Qualidade do Sistema** (10 itens)
  - Funcionamento sem falhas
  - Acessibilidade
  - Facilidade de uso
  - Disponibilidade
  - Desempenho
  - Segurança e privacidade
  - Navegação intuitiva
  - Instruções úteis

- **Qualidade da Informação** (7 itens)
  - Clareza das informações
  - Precisão dos dados
  - Utilidade para solicitações
  - Completude das informações
  - Prazos e taxas informados
  - Atualização dos dados

- **Qualidade da Operação** (9 itens)
  - Suporte técnico eficiente
  - Resolução de problemas
  - Tempo de conclusão
  - Atendimento às expectativas
  - Identificação automática de dados
  - Confiabilidade dos serviços
  - Interações em tempo real

## ⚙️ Funcionalidades Principais

### 📊 Dashboard Interativo
- **Radar chart** por dimensões de qualidade
- **Métricas de satisfação** geral
- **Insights automáticos** com sugestões de ação
- **Filtros dinâmicos** por perfil do usuário

### 📤 Gestão de Dados
- Upload de arquivos CSV com diferentes delimitadores
- Validação e processamento automático
- Dados de exemplo incluídos para testes
- Histórico de uploads por usuário

### 🔍 Análise Detalhada
- Filtros por perfil (idade, sexo, escolaridade, servidor público)
- Análise de correlações entre itens
- Sugestões de ações coordenadas
- Metas personalizáveis por dimensão

### 👤 Sistema de Usuários
- Autenticação local com fallback automático
- Preferências personalizadas persistentes
- Sistema híbrido (Local Storage + Supabase opcional)

## 🏗️ Arquitetura

```
📁 SEFAZ/
├── 📄 app.py                    # Aplicação principal Streamlit
├── 📄 requirements.txt         # Dependências Python
├── 📄 supabase_schema.sql      # Schema do banco (opcional)
├── 📁 core/                    # Módulos principais
│   ├── 📄 data_manager.py      # Gerenciador híbrido de dados
│   ├── 📄 local_storage.py     # Armazenamento local
│   ├── 📄 models.py            # Modelos de dados
│   └── 📄 utils.py             # Utilitários
├── 📁 config/                  # Configurações
│   └── 📄 items_mapping.json   # Mapeamento de itens e dimensões
├── 📁 data/                    # Dados locais
│   ├── 📁 users/               # Dados de usuários
│   └── 📁 shared/              # Configurações compartilhadas
├── 📁 sample_data/             # Dados de exemplo
│   └── 📄 baseKelm.csv         # Dataset de demonstração
└── 📁 tests/                   # Testes automatizados
    ├── 📄 test_data_manager.py
    ├── 📄 test_local_storage.py
    └── 📄 test_integration.py
```

## 🚀 Como Executar

### 1. Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)

### 2. Instalação
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/sefa-dashboard.git
cd sefa-dashboard

# Instale as dependências
pip install -r requirements.txt
```

### 3. Execução
```bash
# Execute o dashboard
streamlit run app.py
```

O dashboard estará disponível em: `http://localhost:8501`

### 4. Modo Demo
- Use qualquer email/senha para testar
- Os dados de exemplo estão incluídos
- Não é necessário configuração adicional

## 🔐 Configuração Avançada (Supabase)

Para funcionalidades completas com persistência em nuvem:

### 1. Criar Projeto Supabase
- Acesse [supabase.com](https://supabase.com)
- Crie um novo projeto
- Copie `SUPABASE_URL` e `SUPABASE_ANON_KEY`

### 2. Configurar Variáveis
```bash
# Crie um arquivo .env
SUPABASE_URL=sua_url_aqui
SUPABASE_ANON_KEY=sua_chave_aqui
DEFAULT_GOAL=4.0
STORAGE_ROOT=data
```

### 3. Executar Schema
- Execute o arquivo `supabase_schema.sql` no SQL Editor do Supabase

## 🧪 Dados de Exemplo

O projeto inclui um dataset de demonstração (`sample_data/baseKelm.csv`) com:
- **338 respostas** de usuários
- **26 itens** de avaliação
- **Perfil demográfico** completo
- **Escala Likert** de 1 a 5

## 🛠️ Tecnologias Utilizadas

- **Frontend:** Streamlit
- **Backend:** Python + Pandas
- **Visualização:** Plotly
- **Banco de Dados:** Supabase (opcional) + Local Storage
- **Autenticação:** Sistema híbrido com fallback
- **Validação:** Pydantic

## 📊 Recursos de Análise

### Insights Automáticos
- **Prioritários:** Itens muito abaixo da meta (< 50% da meta)
- **Ações necessárias:** Itens abaixo da meta (< meta)
- **Bons desempenhos:** Itens que atendem ou superam a meta

### Sugestões Inteligentes
- Ações baseadas em correlações entre itens
- Sugestões específicas por tipo de problema
- Sequências de ação coordenadas por dimensão

### Filtros Avançados
- Por faixa etária
- Por sexo
- Por nível de escolaridade
- Por tipo de usuário (servidor público)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para dúvidas ou sugestões, abra uma issue no repositório ou entre em contato através do email: [seu-email@exemplo.com]

---

**Desenvolvido com ❤️ para melhorar a qualidade dos serviços públicos**
