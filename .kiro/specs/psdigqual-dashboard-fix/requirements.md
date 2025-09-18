# Requirements Document

## Introduction

O projeto PSDigQual é uma plataforma web para análise da qualidade dos serviços públicos digitais baseada em questionários Likert. Atualmente, o sistema apresenta problemas críticos no carregamento de bases de dados e na apresentação dos dashboards. Esta especificação visa resolver esses problemas e implementar dashboards independentes para cada tipo de questionário (8 questões do Portal da Transparência e 20+ questões do questionário completo).

## Requirements

### Requirement 1

**User Story:** Como usuário do sistema, eu quero que os arquivos CSV sejam carregados corretamente independente do encoding, para que eu possa visualizar os dados sem caracteres corrompidos.

#### Acceptance Criteria

1. WHEN um arquivo CSV é carregado THEN o sistema SHALL detectar automaticamente o encoding (UTF-8, ISO-8859-1, Windows-1252)
2. WHEN caracteres especiais estão presentes THEN o sistema SHALL converter corretamente acentos e cedilhas
3. WHEN o processamento de encoding falha THEN o sistema SHALL tentar múltiplos encodings automaticamente
4. WHEN todos os encodings falharem THEN o sistema SHALL exibir uma mensagem de erro clara com sugestões

### Requirement 2

**User Story:** Como usuário, eu quero que o sistema identifique automaticamente o tipo de questionário (8 ou 20+ questões), para que os dados sejam processados corretamente.

#### Acceptance Criteria

1. WHEN um arquivo CSV é carregado THEN o sistema SHALL analisar os cabeçalhos para determinar o tipo de questionário
2. WHEN o arquivo contém questões específicas do Portal da Transparência THEN o sistema SHALL classificá-lo como "transparency"
3. WHEN o arquivo contém mais de 12 colunas de questões THEN o sistema SHALL classificá-lo como "complete"
4. WHEN a detecção automática é ambígua THEN o sistema SHALL usar critérios de fallback baseados no número de colunas

### Requirement 3

**User Story:** Como usuário, eu quero visualizar dashboards independentes para cada tipo de questionário, para que eu possa analisar os dados de forma adequada ao contexto.

#### Acceptance Criteria

1. WHEN dados do questionário de transparência são carregados THEN o sistema SHALL exibir apenas as 8 questões relevantes
2. WHEN dados do questionário completo são carregados THEN o sistema SHALL exibir todas as dimensões (QS, QI, QO)
3. WHEN múltiplos tipos de dados estão presentes THEN o sistema SHALL permitir filtrar por tipo de questionário
4. WHEN nenhum dado está carregado THEN o sistema SHALL exibir dados de exemplo apropriados

### Requirement 4

**User Story:** Como usuário, eu quero que os KPIs e gráficos sejam calculados corretamente, para que eu possa tomar decisões baseadas em dados precisos.

#### Acceptance Criteria

1. WHEN dados são processados THEN o sistema SHALL calcular médias por questão corretamente
2. WHEN médias por dimensão são calculadas THEN o sistema SHALL agrupar questões pelas dimensões corretas (QS, QI, QO)
3. WHEN classificações são geradas THEN o sistema SHALL categorizar questões como críticas (<3.0), neutras (3.0-meta) ou positivas (≥meta)
4. WHEN dados demográficos estão presentes THEN o sistema SHALL extrair e processar informações de perfil

### Requirement 5

**User Story:** Como usuário, eu quero que o sistema limpe automaticamente os dados inválidos, para que apenas respostas válidas sejam consideradas nas análises.

#### Acceptance Criteria

1. WHEN linhas vazias estão presentes THEN o sistema SHALL removê-las automaticamente
2. WHEN respostas Likert são encontradas THEN o sistema SHALL convertê-las para escala numérica (1-5)
3. WHEN uma linha tem menos de 30% de respostas válidas THEN o sistema SHALL excluí-la da análise
4. WHEN dados inválidos são encontrados THEN o sistema SHALL reportar estatísticas de limpeza

### Requirement 6

**User Story:** Como usuário, eu quero feedback detalhado sobre o processamento dos dados, para que eu possa entender o que aconteceu durante o carregamento.

#### Acceptance Criteria

1. WHEN um arquivo é processado THEN o sistema SHALL exibir número de registros válidos e inválidos
2. WHEN o tipo de questionário é detectado THEN o sistema SHALL informar o tipo identificado
3. WHEN erros ocorrem THEN o sistema SHALL exibir mensagens de erro específicas e acionáveis
4. WHEN o processamento é bem-sucedido THEN o sistema SHALL mostrar resumo detalhado dos dados carregados

### Requirement 7

**User Story:** Como usuário, eu quero que os gráficos e visualizações sejam atualizados automaticamente quando novos dados são carregados, para que eu veja sempre informações atuais.

#### Acceptance Criteria

1. WHEN novos dados são carregados THEN todos os gráficos SHALL ser atualizados automaticamente
2. WHEN filtros são aplicados THEN as visualizações SHALL refletir os filtros imediatamente
3. WHEN metas são alteradas THEN as classificações e cores dos gráficos SHALL ser recalculadas
4. WHEN dados são resetados THEN o sistema SHALL voltar aos dados de exemplo padrão

### Requirement 8

**User Story:** Como usuário, eu quero que o sistema mantenha a compatibilidade com os dados existentes, para que eu possa continuar usando arquivos já criados.

#### Acceptance Criteria

1. WHEN arquivos CSV existentes são carregados THEN o sistema SHALL processá-los sem quebrar funcionalidades
2. WHEN estruturas de dados antigas são encontradas THEN o sistema SHALL convertê-las para o novo formato
3. WHEN mapeamentos de questões são atualizados THEN o sistema SHALL manter compatibilidade com versões anteriores
4. WHEN dados de exemplo são usados THEN eles SHALL representar cenários realistas de uso