# Design Document

## Overview

O design proposto cria um sistema híbrido de armazenamento que funciona primariamente com arquivos locais, mas pode opcionalmente usar Supabase quando configurado. O sistema será estruturado em camadas com uma abstração de dados que permite alternar entre diferentes backends de armazenamento de forma transparente.

A arquitetura manterá a compatibilidade total com o código existente, mas adicionará robustez ao sistema local e melhor organização dos dados.

## Architecture

### Camada de Abstração de Dados
```
┌─────────────────────────────────────┐
│           Streamlit UI              │
├─────────────────────────────────────┤
│        Business Logic Layer        │
├─────────────────────────────────────┤
│       Data Abstraction Layer       │
├─────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐   │
│  │ Local Store │  │ Supabase    │   │
│  │ (Primary)   │  │ (Optional)  │   │
│  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────┘
```

### Estrutura de Diretórios Local
```
data/
├── users/
│   ├── users.json                 # Credenciais e metadados dos usuários
│   └── [email_hash]/
│       ├── profile.json           # Configurações do usuário
│       ├── uploads/
│       │   ├── metadata.json      # Histórico de uploads
│       │   └── files/
│       │       ├── 2024-01-15_baseKelm.csv
│       │       └── 2024-01-20_survey_data.csv
│       └── preferences/
│           └── settings.json      # Metas, filtros salvos, etc.
├── shared/
│   ├── default_data.csv          # baseKelm.csv como padrão
│   └── system_config.json        # Configurações globais
└── backups/
    └── [timestamp]/              # Backups automáticos
```

## Components and Interfaces

### 1. DataManager (Abstração Principal)
```python
class DataManager:
    def __init__(self, use_supabase: bool = False)
    def authenticate_user(email: str, password: str) -> UserSession
    def register_user(email: str, password: str) -> bool
    def save_upload(user_session: UserSession, file_data: pd.DataFrame, filename: str) -> UploadRecord
    def get_user_uploads(user_session: UserSession) -> List[UploadRecord]
    def load_upload_data(user_session: UserSession, upload_id: str) -> pd.DataFrame
    def save_user_preferences(user_session: UserSession, preferences: dict) -> bool
    def get_user_preferences(user_session: UserSession) -> dict
```

### 2. LocalStorageManager
```python
class LocalStorageManager:
    def __init__(self, base_path: str = "data")
    def _get_user_hash(email: str) -> str  # Hash do email para privacidade
    def _ensure_user_directory(user_hash: str) -> str
    def save_user_credentials(email: str, password_hash: str) -> bool
    def verify_user_credentials(email: str, password: str) -> bool
    def save_file_upload(user_hash: str, df: pd.DataFrame, filename: str) -> str
    def get_upload_metadata(user_hash: str) -> List[dict]
    def load_upload_file(user_hash: str, file_id: str) -> pd.DataFrame
```

### 3. UserSession
```python
@dataclass
class UserSession:
    email: str
    user_hash: str
    logged_in: bool
    preferences: dict
    created_at: datetime
```

### 4. UploadRecord
```python
@dataclass
class UploadRecord:
    id: str
    filename: str
    original_filename: str
    upload_date: datetime
    n_rows: int
    n_cols: int
    file_path: str
    user_hash: str
```

### 5. ConfigManager
```python
class ConfigManager:
    def __init__(self, config_path: str = "config")
    def get_dimensions() -> dict
    def get_likert_mapping() -> dict
    def get_satisfaction_mapping() -> dict
    def get_profile_fields() -> dict
    def update_user_goal(user_hash: str, goal: float) -> bool
    def get_user_goal(user_hash: str) -> float
```

## Data Models

### users.json
```json
{
  "users": {
    "hash_of_email": {
      "email": "user@example.com",
      "password_hash": "bcrypt_hash",
      "created_at": "2024-01-15T10:30:00Z",
      "last_login": "2024-01-20T14:20:00Z"
    }
  }
}
```

### uploads/metadata.json
```json
{
  "uploads": [
    {
      "id": "uuid4_string",
      "filename": "2024-01-15_baseKelm.csv",
      "original_filename": "baseKelm.csv",
      "upload_date": "2024-01-15T10:30:00Z",
      "n_rows": 338,
      "n_cols": 31,
      "file_path": "files/2024-01-15_baseKelm.csv"
    }
  ]
}
```

### preferences/settings.json
```json
{
  "goal": 4.0,
  "default_filters": {
    "age_range": [18, 65],
    "sex": "Todos",
    "education": "Todos",
    "public_servant": "Todos"
  },
  "ui_preferences": {
    "theme": "default",
    "chart_colors": ["#1f77b4", "#ff7f0e", "#2ca02c"]
  },
  "last_updated": "2024-01-20T14:20:00Z"
}
```

## Error Handling

### Estratégia de Fallback
1. **Supabase Indisponível**: Sistema automaticamente usa armazenamento local
2. **Arquivo Corrompido**: Sistema tenta recuperar de backup automático
3. **Permissões de Escrita**: Sistema alerta usuário e sugere soluções
4. **Espaço em Disco**: Sistema implementa limpeza automática de arquivos antigos

### Tratamento de Erros por Componente
```python
class DataManagerError(Exception):
    pass

class AuthenticationError(DataManagerError):
    pass

class StorageError(DataManagerError):
    pass

class FileCorruptionError(StorageError):
    pass
```

## Testing Strategy

### Testes Unitários
- **LocalStorageManager**: Testes de CRUD para todos os métodos
- **DataManager**: Testes de integração entre local e Supabase
- **ConfigManager**: Testes de carregamento e validação de configurações
- **UserSession**: Testes de serialização e validação

### Testes de Integração
- **Fluxo Completo de Upload**: Do upload até visualização
- **Autenticação Híbrida**: Local vs Supabase
- **Migração de Dados**: De local para Supabase e vice-versa
- **Recuperação de Falhas**: Testes de resiliência

### Testes de Performance
- **Carregamento de Arquivos Grandes**: CSV com 10k+ linhas
- **Múltiplos Usuários**: Simulação de uso concorrente
- **Backup e Restauração**: Tempo de operações de backup

### Estrutura de Testes
```
tests/
├── unit/
│   ├── test_local_storage.py
│   ├── test_data_manager.py
│   └── test_config_manager.py
├── integration/
│   ├── test_upload_flow.py
│   ├── test_auth_flow.py
│   └── test_data_migration.py
├── fixtures/
│   ├── sample_data.csv
│   └── test_config.json
└── conftest.py
```

## Migration Strategy

### Dados Existentes
1. **Detecção Automática**: Sistema detecta se há dados no Supabase
2. **Migração Opcional**: Usuário pode escolher migrar dados para local
3. **Sincronização**: Opção de manter ambos sincronizados

### Compatibilidade
- **Código Existente**: Mantém 100% de compatibilidade
- **Session State**: Migração transparente do session state atual
- **Configurações**: Preserva todas as configurações existentes

## Security Considerations

### Armazenamento Local
- **Hash de Emails**: Emails são hasheados para privacidade
- **Senhas**: Bcrypt para hash de senhas
- **Arquivos**: Permissões restritas nos diretórios de dados

### Backup e Recuperação
- **Backups Automáticos**: Backup diário dos dados críticos
- **Criptografia**: Opção de criptografar backups
- **Recuperação**: Sistema de recuperação automática de falhas

## Performance Optimizations

### Caching
- **Streamlit Cache**: Cache de dados carregados
- **Lazy Loading**: Carregamento sob demanda de uploads antigos
- **Compression**: Compressão de arquivos CSV grandes

### Memory Management
- **Chunked Processing**: Processamento em chunks para arquivos grandes
- **Garbage Collection**: Limpeza automática de dados não utilizados
- **Session Cleanup**: Limpeza de sessões expiradas