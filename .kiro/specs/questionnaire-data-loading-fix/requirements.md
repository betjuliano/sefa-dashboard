# Requirements Document

## Introduction

O sistema de dashboard de qualidade está enfrentando problemas no carregamento e processamento das questões dos questionários base20 e base8. Os problemas incluem inconsistências no mapeamento de questões, erros na conversão de escalas Likert, e falhas na normalização de dados entre os diferentes conjuntos de questões. Esta especificação visa resolver esses problemas criando um sistema robusto de carregamento e processamento de dados que funcione consistentemente para ambos os conjuntos de questões.

## Requirements

### Requirement 1

**User Story:** Como um usuário do sistema, eu quero que o carregamento das questões funcione corretamente para ambos os conjuntos (base20 e base8), para que eu possa analisar os dados sem erros.

#### Acceptance Criteria

1. WHEN o sistema carrega dados do base20 THEN o sistema SHALL mapear corretamente todas as 20 questões para suas respectivas dimensões (QS, QI, QO)
2. WHEN o sistema carrega dados do base8 THEN o sistema SHALL mapear corretamente todas as 8 questões para suas respectivas dimensões
3. WHEN há inconsistências nos nomes das questões THEN o sistema SHALL normalizar automaticamente os textos removendo acentos e padronizando a formatação
4. WHEN o sistema encontra questões não mapeadas THEN o sistema SHALL registrar um log de aviso e continuar o processamento com as questões disponíveis

### Requirement 2

**User Story:** Como um analista de dados, eu quero que as escalas Likert sejam convertidas corretamente para valores numéricos, para que as análises estatísticas sejam precisas.

#### Acceptance Criteria

1. WHEN o sistema processa respostas "Discordo Totalmente" THEN o sistema SHALL converter para valor numérico 1
2. WHEN o sistema processa respostas "Discordo" THEN o sistema SHALL converter para valor numérico 2
3. WHEN o sistema processa respostas "Não sei" ou "Neutro" THEN o sistema SHALL converter para valor numérico 3
4. WHEN o sistema processa respostas "Concordo" THEN o sistema SHALL converter para valor numérico 4
5. WHEN o sistema processa respostas "Concordo Totalmente" THEN o sistema SHALL converter para valor numérico 5
6. WHEN o sistema encontra valores inválidos ou vazios THEN o sistema SHALL tratar como NaN e continuar o processamento

### Requirement 3

**User Story:** Como um desenvolvedor do sistema, eu quero que os códigos das questões (QS1, QI1, QO1, etc.) sejam mapeados corretamente, para que as análises por dimensão funcionem adequadamente.

#### Acceptance Criteria

1. WHEN o sistema processa questões de Qualidade do Sistema THEN o sistema SHALL atribuir códigos QS1 a QS10 conforme especificado
2. WHEN o sistema processa questões de Qualidade da Informação THEN o sistema SHALL atribuir códigos QI1 a QI7 conforme especificado  
3. WHEN o sistema processa questões de Qualidade da Operação THEN o sistema SHALL atribuir códigos QO1 a QO7 conforme especificado
4. WHEN há diferenças entre base20 e base8 THEN o sistema SHALL usar o mapeamento apropriado para cada conjunto

### Requirement 4

**User Story:** Como um usuário do sistema, eu quero que as questões de perfil (idade, sexo, escolaridade, servidor público) sejam processadas corretamente, para que os filtros funcionem adequadamente.

#### Acceptance Criteria

1. WHEN o sistema processa dados de perfil THEN o sistema SHALL identificar corretamente as colunas de idade, sexo, escolaridade e servidor público
2. WHEN há variações nos nomes das colunas de perfil THEN o sistema SHALL normalizar automaticamente os nomes
3. WHEN o sistema processa a questão de satisfação THEN o sistema SHALL mapear corretamente para a escala numérica de 1 a 5
4. WHEN há dados de perfil ausentes THEN o sistema SHALL continuar o processamento sem falhar

### Requirement 5

**User Story:** Como um administrador do sistema, eu quero que os arquivos de configuração sejam validados e corrigidos automaticamente, para que não haja inconsistências entre os mapeamentos.

#### Acceptance Criteria

1. WHEN o sistema inicia THEN o sistema SHALL validar a consistência dos arquivos items_mapping.json e items_mapping_8q.json
2. WHEN há questões duplicadas ou inconsistentes THEN o sistema SHALL reportar os problemas e sugerir correções
3. WHEN há questões ausentes no mapeamento THEN o sistema SHALL identificar e reportar as questões não mapeadas
4. WHEN o sistema detecta problemas de codificação THEN o sistema SHALL aplicar normalização automática de texto

### Requirement 6

**User Story:** Como um usuário final, eu quero que o sistema forneça feedback claro sobre problemas de carregamento, para que eu possa entender e resolver questões com os dados.

#### Acceptance Criteria

1. WHEN há erros no carregamento de dados THEN o sistema SHALL exibir mensagens de erro claras e específicas
2. WHEN há questões não encontradas THEN o sistema SHALL listar quais questões estão ausentes
3. WHEN há problemas de conversão de dados THEN o sistema SHALL indicar quais linhas ou colunas têm problemas
4. WHEN o carregamento é bem-sucedido THEN o sistema SHALL confirmar quantas questões foram carregadas e processadas corretamente