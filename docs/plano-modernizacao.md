# Plano de modernização do PyCobrança

## Objetivo

Transformar o PyCobrança em uma evolução moderna do PyBoleto, preservando compatibilidade com usos existentes quando possível, incorporando recursos maduros da BrCobrança e criando uma camada de integração estável com a cobrança_api.

## Referências de origem

| Projeto | Papel na modernização | Pontos a aproveitar |
| --- | --- | --- |
| [Maxwbh/pyboleto](https://github.com/Maxwbh/pyboleto) | Base Python legada para geração de boletos de cobrança brasileiros. | Modelos existentes de boletos, bancos já implementados, exemplos, testes e API pública que precisa de plano de compatibilidade. |
| [Maxwbh/brcobranca](https://github.com/Maxwbh/brcobranca) | Referência funcional com melhorias já implementadas. | Suporte multi-banco, CNAB 240/400/444, PIX/Bolepix, PDFs via Prawn/RGhost, serialização JSON e registro programático de bancos. |
| [Maxwbh/cobranca-api](https://github.com/Maxwbh/cobranca-api) | Plataforma de integração e exposição de cobrança como serviço. | Contratos REST/OpenAPI, webhooks, geração de boletos registrados, PIX, CNAB offline, OFX e documentação operacional. |

## Diretrizes da branch HML

A branch `HML` será usada como trilha principal de homologação.

Regras propostas:

1. Toda melhoria relevante deve ser integrada primeiro em `HML`.
2. A branch deve receber cenários de testes automatizados e evidências manuais de homologação.
3. Alterações promovidas de `HML` para produção devem possuir checklist de bancos, formatos CNAB e endpoints impactados.
4. Quebras de compatibilidade com PyBoleto devem ser documentadas com migração clara.
5. Integrações com cobrança_api devem ser validadas contra contrato OpenAPI versionado.

## Escopo funcional da modernização

### 1. Compatibilidade com PyBoleto

- Mapear a API pública atual do PyBoleto.
- Definir nomes de módulos, classes e métodos que permanecerão compatíveis.
- Criar adaptadores/depreciações para chamadas legadas.
- Garantir geração de linha digitável, código de barras, datas, valores e carteiras já suportadas.
- Importar ou recriar fixtures de saída para comparar resultados antes e depois da migração.

### 2. Melhorias vindas da BrCobrança

- Implementar registro central de bancos e capacidades.
- Padronizar contratos para boleto, remessa, retorno, PIX e PDF.
- Priorizar suporte a CNAB 240 e CNAB 400, mantendo abertura para CNAB 444 quando aplicável.
- Adicionar suporte a PIX/Bolepix com `chave_pix`, `tipo_chave_pix`, `txid`, QR Code e EMV.
- Oferecer serialização `dict`/JSON para entidades principais.
- Separar regras bancárias de renderização de PDF.
- Preparar temas de PDF com logo, cores, fontes e campos customizados.

### 3. Integração com cobrança_api

- Definir cliente Python oficial para consumo da cobrança_api.
- Versionar schemas de entrada/saída compatíveis com OpenAPI.
- Implementar autenticação configurável por ambiente.
- Criar endpoints/serviços internos para:
  - emitir boleto;
  - gerar boleto híbrido com PIX;
  - gerar remessa CNAB;
  - processar retorno CNAB;
  - consultar liquidação/status;
  - processar OFX quando aplicável;
  - receber e validar webhooks.
- Criar testes de contrato para evitar divergência entre biblioteca e API.

## Arquitetura proposta

```text
pycobranca/
  banks/              # Regras específicas por banco
  boleto/             # Entidades e validações de boleto
  cnab/               # Remessa, retorno, layouts 240/400/444
  pix/                # EMV, QR Code, Bolepix
  pdf/                # Renderizadores e temas
  api/                # Cliente/integração com cobrança_api
  compatibility/      # Adaptadores de compatibilidade com PyBoleto
  tests/              # Testes unitários, fixtures e contratos
```

## Plano de execução

### Fase 0 — Preparação

- Criar branch `HML` para homologação.
- Definir governança de merge e checklist de aprovação.
- Catalogar bancos, carteiras, convênios e layouts suportados nos três projetos.
- Montar matriz de compatibilidade PyBoleto x BrCobrança x cobrança_api.

### Fase 1 — Núcleo Python moderno

- Definir empacotamento com `pyproject.toml`.
- Criar modelos tipados com validações explícitas.
- Separar domínio, bancos, CNAB, PIX, PDF e integração API.
- Configurar lint, formatação, testes e cobertura.

### Fase 2 — Migração de bancos e boletos

- Migrar bancos do PyBoleto com testes de regressão.
- Portar melhorias da BrCobrança por banco, priorizando os bancos usados pela cobrança_api.
- Validar linha digitável, fator de vencimento, dígitos verificadores e código de barras.
- Documentar parâmetros obrigatórios por banco.

### Fase 3 — CNAB e retorno

- Implementar geração de remessa CNAB 240/400.
- Implementar parser de retorno com normalização de eventos.
- Criar fixtures reais anonimizadas para cada banco suportado.
- Validar conciliação por nosso número, documento, valor, vencimento e ocorrência.

### Fase 4 — PIX/Bolepix

- Implementar geração EMV e QR Code.
- Integrar campos PIX ao boleto.
- Validar Bolepix nos bancos com suporte.
- Criar testes de payload, `txid`, chave PIX e vencimento.

### Fase 5 — PDF e temas

- Definir renderizador padrão Python.
- Avaliar dependências para PDF sem GhostScript.
- Criar templates de boleto tradicional, boleto híbrido e carnê.
- Criar snapshots/fixtures para evitar regressões visuais.

### Fase 6 — Integração cobrança_api

- Criar cliente Python e camada de configuração.
- Validar contratos com OpenAPI.
- Criar testes de integração em HML.
- Documentar exemplos de uso local, Docker e pipeline.

## Critérios de aceite para HML

- Testes unitários cobrindo regras críticas de boleto, CNAB e PIX.
- Testes de regressão com fixtures do PyBoleto.
- Testes de contrato com cobrança_api.
- Documentação de campos por banco.
- Exemplos executáveis para boleto simples, Bolepix, remessa e retorno.
- Checklist de homologação por banco aprovado.

## Riscos e mitigação

| Risco | Mitigação |
| --- | --- |
| Divergência entre regras bancárias de Python e Ruby. | Criar fixtures cruzadas e comparar saídas por banco/layout. |
| Quebra de usuários legados do PyBoleto. | Manter camada `compatibility` e avisos de depreciação versionados. |
| Dependências pesadas para PDF. | Priorizar renderização Python pura e deixar backends opcionais. |
| Diferenças entre ambientes HML e produção. | Usar configuração por ambiente, contratos OpenAPI e dados de homologação segregados. |
| Falta de dados reais para retorno/CNAB. | Manter fixtures anonimizadas e cenários mínimos por banco. |

## Checklist inicial

- [x] Criar branch `HML`.
- [x] Criar documentação inicial de modernização.
- [ ] Catalogar bancos suportados no PyBoleto.
- [ ] Catalogar melhorias da BrCobrança por módulo.
- [ ] Catalogar endpoints e schemas da cobrança_api.
- [ ] Definir arquitetura final do pacote Python.
- [ ] Criar suíte inicial de testes de regressão.

## Estratégia recomendada para renderização moderna do boleto

A decisão de arquitetura é adotar **ReportLab como renderizador padrão** do PyCobrança, mantendo **HTML+WeasyPrint** e **HTML+Playwright/Chromium** como backends opcionais por meio de uma interface de renderização plugável no código.

Essa escolha prioriza previsibilidade de impressão, velocidade, baixo acoplamento operacional e controle fino do layout bancário. O HTML continua importante para pré-visualização, temas modernos e experiências visuais mais ricas, mas não deve ser o backend padrão inicial de geração final em produção.

### Tabela de decisão

Pontuação: 1 = fraco, 3 = médio, 5 = forte.

| Modelo | Simples de implementar | Melhorias visuais | Fácil manutenção | Velocidade de renderização | Decisão |
| --- | ---: | ---: | ---: | ---: | --- |
| **ReportLab** | 4 | 3 | 4 | 5 | **Padrão do PyCobrança**. Melhor equilíbrio para boleto bancário, alto controle de coordenadas, boa performance e menos dependências de navegador. |
| **HTML + WeasyPrint** | 4 | 5 | 4 | 3 | Backend opcional para modelos mais modernos, temas e pré-visualização com CSS de impressão. Requer validação de dependências nativas em HML. |
| **HTML + Playwright/Chromium** | 3 | 5 | 3 | 2 | Backend opcional quando a fidelidade com navegador for prioridade. Mais pesado por depender de Chromium. |
| **PDF fixo/manual** | 2 | 1 | 1 | 5 | Não recomendado como modelo principal; dificulta evolução, parametrização e testes. |

### Decisão proposta

1. **ReportLab como backend padrão**
   - Gera PDF diretamente em Python, com controle preciso de posições, margens, códigos de barras, QR Code e blocos fixos do boleto.
   - É adequado para layouts bancários, onde previsibilidade de impressão e estabilidade são mais importantes que liberdade visual total.
   - Tende a ter melhor velocidade e menor custo operacional que um motor HTML completo, especialmente em lotes de 100 a 200 boletos.

2. **HTML/CSS como backend opcional para experiência visual**
   - Deve ser mantido via backends opcionais para templates modernos, prévia web e personalização visual.
   - Pode usar WeasyPrint quando o objetivo for CSS de impressão server-side.
   - Pode usar Playwright quando a prioridade for máxima fidelidade com renderização de navegador.

3. **Interface única de backends**
   - O domínio do boleto não deve conhecer ReportLab, WeasyPrint ou Playwright diretamente.
   - A aplicação deve escolher o backend por configuração, tenant, tipo de documento ou cenário de homologação.
   - Todos os backends devem receber o mesmo `BoletoViewModel` já validado.

4. **PDF como formato final de distribuição**
   - O PDF continua sendo o artefato final para impressão, envio e arquivamento.
   - O modelo não deve ser um PDF fixo editado manualmente; deve ser gerado por template/código versionado e testável.

### Arquitetura de renderização

```text
Dados validados do boleto
        |
        v
ViewModel de impressão
        |
        v
RenderBackend selecionado por configuração
        |-- ReportLabBackend    # padrão arquitetural
        |-- WeasyPrintBackend   # opcional HTML/CSS
        |-- PlaywrightBackend   # opcional Chromium
        |
        +--> Templates/componentes versionados
        |
        v
PDF final + metadados + testes de regressão
```

### Contrato sugerido para os backends

- Entrada: `BoletoViewModel`, tema, locale, assets permitidos e opções de página.
- Saída: bytes do PDF, metadados de geração e lista de avisos.
- Regras:
  - O backend não calcula código de barras, linha digitável, PIX ou valores.
  - O backend apenas renderiza dados já validados pelo domínio.
  - Todo acesso a assets deve ser explícito para evitar vazamento de arquivos locais.
  - O backend padrão deve ser `ReportLabBackend`.
  - Backends HTML devem ser opcionais e ativados por configuração.
  - Todos os backends devem passar pela mesma suíte de regressão de dados e layout.

### Critérios de escolha por cenário

| Cenário | Estratégia indicada | Motivo |
| --- | --- | --- |
| Boleto bancário padrão, alto volume ou lote assíncrono. | ReportLab | Melhor previsibilidade, controle de coordenadas e velocidade de renderização. |
| Boleto moderno com marca, tema e evolução visual frequente. | HTML/CSS + WeasyPrint | Facilita evolução visual, mantendo geração server-side. |
| Prévia web e PDF precisam ficar quase idênticos ao navegador. | HTML/CSS + Playwright | Usa motor Chromium e reduz diferença entre tela e PDF. |
| Layout fixo validado por banco. | ReportLab | Dá controle fino de posicionamento e reduz variação entre ambientes. |

### Requisitos de homologação para renderização

- Criar exemplos de boleto simples, Bolepix e carnê usando `ReportLabBackend`.
- Validar impressão em A4 com margens controladas.
- Validar leitura de código de barras e QR Code após geração do PDF.
- Criar testes de regressão visual por snapshot ou comparação estrutural do PDF.
- Rodar benchmark com lote mínimo de 100, 1.000 e 10.000 boletos em HML.
- Comparar ReportLab, WeasyPrint e Playwright usando o mesmo `BoletoViewModel`.
- Documentar fontes, logos e assets permitidos por tema.
- Validar acessibilidade básica apenas nas pré-visualizações HTML.

### Conclusão

A melhor estratégia para o PyCobrança é **ReportLab como renderizador padrão**, com backends opcionais HTML+WeasyPrint e HTML+Playwright para cenários em que o ganho visual justifique maior custo operacional. Essa decisão preserva velocidade, controle e estabilidade para boletos e lotes, sem bloquear evolução visual futura via interface plugável de backends.

## Arquitetura para processamento em lote e background

O PyCobrança e a cobrança_api devem tratar requisições com **100 a 200 boletos** como trabalhos assíncronos. A API não deve tentar renderizar todos os documentos ou gerar todos os arquivos CNAB dentro do ciclo síncrono HTTP, porque isso aumenta timeout, consumo de memória e risco de perda parcial do processamento.

### Estratégia recomendada para boletos em lote

1. **Recepção síncrona curta**
   - A API recebe uma lista de boletos, valida o envelope da requisição e cria um `job_id`.
   - A resposta inicial deve ser `202 Accepted`, contendo `job_id`, quantidade recebida, endpoint de consulta e, opcionalmente, uma estimativa inicial.
   - A validação profunda de regras bancárias, geração de linha digitável, PIX, PDF e persistência dos artefatos ocorre em background.

2. **Processamento assíncrono por itens**
   - Cada boleto vira um item rastreável dentro do job, com `item_id`, status, mensagens e artefatos.
   - A fila pode processar itens em paralelo com limite de concorrência por banco, carteira ou tenant.
   - Falha em um boleto não deve cancelar todo o lote, exceto quando o erro for estrutural no envelope da requisição.

3. **Retorno individual e consolidado**
   - O cliente deve poder consultar o job completo e também consultar um boleto específico.
   - PDFs individuais devem ser armazenados separadamente.
   - Quando solicitado, a API gera um artefato consolidado, como `.zip`, contendo PDFs, JSON de manifesto e relatório de erros.

4. **Download por manifesto**
   - O resultado do job deve incluir um manifesto com status por item, URLs temporárias, hashes, tamanho dos arquivos e mensagens de validação.
   - Para lotes grandes, o manifesto evita respostas HTTP pesadas e permite retentativa apenas dos itens com erro.

### Forma mais performática de retorno

A forma mais performática é **retornar imediatamente um `job_id` e processar em background**, disponibilizando resultados por consulta, webhook ou download de artefatos.

| Forma de retorno | Quando usar | Observação de performance |
| --- | --- | --- |
| `202 Accepted` + `job_id` | Padrão para 100 a 200 boletos. | Evita timeout HTTP e permite escala horizontal por workers. |
| Consulta paginada de itens | Acompanhar progresso e erros item a item. | Evita payloads grandes e permite atualizar telas administrativas. |
| Webhook de conclusão | Integração entre sistemas. | Reduz polling e melhora integração com cobrança_api. |
| Download individual | Segunda via, reprocessamento parcial ou erro pontual. | Melhor para consumo sob demanda. |
| Download consolidado `.zip` | Exportação operacional de lote concluído. | Mais eficiente que retornar PDFs em base64 no JSON. |
| PDF único com todos os boletos | Apenas quando houver exigência operacional. | Pode consumir muita memória; deve ser gerado como artefato separado em background. |

A recomendação é **não retornar PDFs em base64 dentro da resposta JSON** para lotes. Base64 aumenta o tamanho trafegado e dificulta streaming, cache e armazenamento. O ideal é persistir os arquivos em storage e retornar referências controladas por expiração e permissão.

### Estados do job

```text
received -> validating -> processing -> partially_completed
                              |              |
                              |              v
                              |          completed
                              |
                              v
                            failed
```

Estados por item:

- `pending`: item recebido e aguardando processamento.
- `validating`: validações bancárias e de domínio em execução.
- `rendering`: boleto, PIX, PDF ou CNAB sendo gerado.
- `completed`: artefatos gerados com sucesso.
- `failed`: erro individual com código e mensagem rastreável.
- `skipped`: item ignorado por regra explícita do lote.

### Arquitetura sugerida

```text
Cliente
  |
  v
cobrança_api /jobs/boletos
  |
  +--> valida envelope + cria job + responde 202
  |
  v
Banco transacional: job, itens, status e auditoria
  |
  v
Fila: boleto.render, boleto.pix, boleto.pdf, cnab.generate
  |
  v
Workers PyCobrança
  |-- validação de domínio
  |-- geração de boleto/PIX
  |-- renderização PDF
  |-- geração CNAB
  |
  v
Storage de artefatos: PDFs, ZIPs, CNAB, manifestos
  |
  v
Webhook / polling / download assinado
```

### Idempotência e rastreabilidade

- Toda requisição em lote deve aceitar uma `idempotency_key` por cliente/tenant.
- Cada item deve aceitar uma chave externa, como `external_id`, para evitar duplicidade.
- O job deve registrar versão do template, versão das regras bancárias, banco, carteira, convênio, tenant, usuário solicitante e ambiente.
- Reprocessamentos devem criar nova tentativa do item, mantendo histórico de erro e artefato anterior quando aplicável.

### Concorrência e limites

Para 100 a 200 boletos por requisição, o sistema deve limitar concorrência para proteger CPU, memória e serviços externos.

Regras sugeridas:

- Limite de tamanho do lote por endpoint, inicialmente 200 itens.
- Limite de jobs simultâneos por tenant.
- Limite de workers por tipo de tarefa: validação, PDF, PIX e CNAB.
- Fila separada para renderização de PDF, pois costuma ser CPU/memória intensiva.
- Timeout por item e timeout total do job.
- Retentativa com backoff apenas para falhas transitórias.

### Estratégia equivalente para CNAB

O CNAB deve seguir o mesmo padrão assíncrono, mas com uma diferença importante: **o agrupamento bancário precisa ser determinístico**.

1. A API recebe os títulos/boletos que devem compor uma remessa.
2. O job valida se todos pertencem ao mesmo banco, layout, convênio, carteira e conta, ou separa automaticamente em sublotes compatíveis.
3. Cada sublote gera um arquivo CNAB próprio.
4. O resultado final entrega um manifesto com arquivos CNAB, totais, quantidade de registros, hash e erros por item.

Critérios específicos para CNAB:

- Não misturar bancos, layouts, convênios ou contas incompatíveis no mesmo arquivo.
- Validar totais do header/trailer antes de disponibilizar o arquivo.
- Guardar o conteúdo CNAB gerado de forma imutável para auditoria.
- Permitir reprocessar apenas o sublote com erro.
- Gerar retorno normalizado quando houver upload/processamento de arquivos de retorno.

### Modelo de endpoints sugerido

```text
POST /jobs/boletos
GET  /jobs/boletos/{job_id}
GET  /jobs/boletos/{job_id}/items
GET  /jobs/boletos/{job_id}/items/{item_id}
GET  /jobs/boletos/{job_id}/artifacts

POST /jobs/cnab/remessas
GET  /jobs/cnab/remessas/{job_id}
GET  /jobs/cnab/remessas/{job_id}/files

POST /jobs/cnab/retornos
GET  /jobs/cnab/retornos/{job_id}
```

### Critérios de homologação para lotes

- Processar lote de 100 boletos com sucesso e falhas parciais controladas.
- Processar lote de 200 boletos sem timeout HTTP.
- Validar geração de PDFs individuais e `.zip` consolidado.
- Validar manifesto com status, hashes e URLs de artefatos.
- Validar webhook de conclusão e consulta por polling.
- Validar idempotência repetindo a mesma requisição.
- Validar CNAB com sublotes por banco/layout/convênio/conta.
- Medir tempo médio por item, tempo total do job, uso de CPU, memória e tamanho de storage.

## Separação de responsabilidades entre PyCobrança e cobrança_api

A divisão proposta — **PyCobrança responsável pela geração** e **cobrança_api responsável pela comunicação** — é o melhor cenário para iniciar a modernização, desde que exista um contrato claro entre as duas camadas. Essa separação mantém a biblioteca Python reutilizável, testável e independente de infraestrutura, enquanto a API concentra autenticação, filas, storage, webhooks, integrações externas e observabilidade.

### Desenho recomendado

```text
Aplicações clientes
        |
        v
cobrança_api
  |-- autenticação/autorização
  |-- contratos HTTP/OpenAPI
  |-- idempotência e jobs assíncronos
  |-- filas, storage, webhooks e auditoria
  |-- comunicação com bancos, gateways e sistemas externos
        |
        v
PyCobrança
  |-- validação de domínio do boleto
  |-- cálculo de linha digitável e código de barras
  |-- geração de PIX/Bolepix
  |-- geração e leitura de CNAB
  |-- renderização de PDF/HTML
  |-- serialização de artefatos e manifestos técnicos
```

### Responsabilidade do PyCobrança

O PyCobrança deve ser uma biblioteca/engine de domínio, sem depender de HTTP, banco de dados, filas ou credenciais de ambiente.

Responsabilidades:

- Validar dados bancários, beneficiário, pagador, valores, datas, carteira, convênio e regras por banco.
- Gerar linha digitável, código de barras, nosso número, instruções e campos específicos por banco.
- Gerar PIX/Bolepix, payload EMV e dados para QR Code.
- Gerar PDFs, HTML de pré-visualização e artefatos técnicos.
- Gerar remessa CNAB e interpretar retorno CNAB.
- Expor erros estruturados, determinísticos e fáceis de mapear pela API.
- Ser executável em testes unitários sem infraestrutura externa.

Não deve ser responsabilidade do PyCobrança:

- Autenticar clientes da API.
- Controlar permissões por tenant.
- Enfileirar jobs.
- Persistir arquivos em storage definitivo.
- Enviar webhooks.
- Chamar diretamente bancos, gateways ou serviços externos, salvo por interfaces opcionais muito bem isoladas.

### Responsabilidade da cobrança_api

A cobrança_api deve ser a camada de aplicação e comunicação.

Responsabilidades:

- Expor endpoints REST/OpenAPI para clientes.
- Validar autenticação, autorização, tenant e limites de uso.
- Criar jobs assíncronos, itens, tentativas e estados.
- Controlar idempotência por requisição e por item.
- Persistir status, auditoria, manifestos e artefatos em storage.
- Orquestrar workers que chamam o PyCobrança.
- Entregar resultados por polling, webhook, callback, download assinado ou integração interna.
- Realizar comunicação com bancos, provedores de registro, gateways, mensageria e sistemas externos.
- Traduzir erros técnicos do PyCobrança para respostas HTTP e eventos de domínio.

### Alternativas avaliadas

| Alternativa | Vantagem | Risco |
| --- | --- | --- |
| PyCobrança gera e cobrança_api comunica. | Melhor separação de domínio e infraestrutura; facilita testes e reuso. | Exige contrato bem definido entre biblioteca e API. |
| PyCobrança também comunica com bancos. | Pode parecer mais simples para scripts isolados. | Acopla domínio a credenciais, HTTP, retries e ambientes; dificulta homologação e segurança. |
| cobrança_api contém toda regra de geração. | Reduz um componente inicial. | Torna a API pesada, menos reutilizável e mais difícil de testar sem infraestrutura. |
| Criar um terceiro serviço exclusivo de geração. | Escala geração de forma independente. | Aumenta complexidade operacional; só vale se volume/custo justificar. |

### Melhor desenho de evolução

O melhor desenho é começar com **PyCobrança como biblioteca de domínio** e **cobrança_api como orquestradora de comunicação**. Se no futuro o volume de PDFs, CNAB ou PIX crescer muito, a arquitetura pode evoluir para um **serviço de geração** separado, mas esse serviço ainda deve usar PyCobrança como engine interna.

```text
Fase inicial:
  cobrança_api -> importa PyCobrança como biblioteca

Fase de escala:
  cobrança_api -> fila -> workers que importam PyCobrança

Fase de alto volume, se necessário:
  cobrança_api -> fila/eventos -> generation-service -> PyCobrança
```

### Contrato entre as camadas

Para manter a separação saudável, o contrato entre cobrança_api e PyCobrança deve ser explícito e versionado.

- Entrada: DTOs/schemas de boleto, PIX, CNAB e opções de renderização.
- Saída: objetos de resultado com dados normalizados, artefatos binários, hashes, mensagens e códigos de erro.
- Erros: exceções de domínio mapeáveis para códigos estáveis, sem depender de texto livre.
- Versão: todo resultado deve informar versão da engine PyCobrança, versão da regra bancária e versão do template.
- Compatibilidade: alterações incompatíveis devem ser publicadas em nova versão de contrato.

### Regra prática de decisão

- Se a tarefa depende de regra bancária, cálculo, layout, CNAB, PIX ou PDF: fica no **PyCobrança**.
- Se a tarefa depende de HTTP, autenticação, autorização, tenant, fila, storage, webhook, retry externo ou comunicação com banco/provedor: fica na **cobrança_api**.
- Se a tarefa é orquestração de várias etapas: fica na **cobrança_api**, chamando funções puras ou serviços internos do PyCobrança.

### Conclusão

Sim, **PyCobrança para geração e cobrança_api para comunicação é o melhor cenário arquitetural** para este momento. O ajuste importante é desenhar PyCobrança como engine de domínio pura e versionada, e não apenas como um pacote utilitário de PDF. A cobrança_api deve orquestrar jobs, segurança, integração e entrega dos artefatos. Essa divisão permite começar simples, testar melhor em HML e evoluir para workers ou serviço dedicado de geração sem reescrever as regras bancárias.
