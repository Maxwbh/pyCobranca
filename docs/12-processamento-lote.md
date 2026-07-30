# 12 — Processamento em Lote e Assíncrono

Requisições com muitos boletos (referência: **100 a 200 por requisição**) devem ser tratadas como
**trabalhos assíncronos**. Gerar todos os PDFs ou arquivos CNAB dentro do ciclo HTTP síncrono
aumenta timeout, consumo de memória e risco de perda parcial do processamento.

> **Onde isto roda.** A orquestração assíncrona (jobs, filas, storage, webhooks, autenticação) é
> responsabilidade da **aplicação/serviço de cobrança** — não da biblioteca. A PyCobrança é a **engine
> de domínio** chamada pelos workers (ver [04 — API REST](04-api-rest.md) e a
> divisão de responsabilidades ao final deste documento). Este capítulo descreve o **contrato
> assíncrono** que a biblioteca precisa suportar (erros determinísticos, idempotência por item,
> artefatos serializáveis) para operar bem sob esse modelo.

## Estratégia para boletos em lote

1. **Recepção síncrona curta** — a API valida o envelope da requisição, cria um `job_id` e responde
   **`202 Accepted`** com `job_id`, quantidade recebida e endpoint de consulta. A validação profunda,
   a geração e a persistência ocorrem em background.
2. **Processamento assíncrono por item** — cada boleto vira um item rastreável (`item_id`, status,
   mensagens, artefatos). A falha de um item **não** cancela o lote (exceto erro estrutural no
   envelope). Concorrência limitada por banco/carteira/tenant.
3. **Retorno individual e consolidado** — o cliente consulta o job inteiro ou um item específico.
   PDFs individuais são armazenados separadamente; sob demanda, gera-se um consolidado (`.zip`) com
   PDFs + manifesto JSON + relatório de erros.
4. **Download por manifesto** — o resultado inclui manifesto com status por item, URLs temporárias,
   hashes, tamanhos e mensagens. Evita respostas HTTP pesadas e permite reprocessar só os itens com erro.

## Forma mais performática de retorno

A mais performática é **retornar imediatamente um `job_id` e processar em background**,
disponibilizando resultados por consulta, webhook ou download de artefatos.

| Forma de retorno | Quando usar | Observação de performance |
|------------------|-------------|---------------------------|
| `202 Accepted` + `job_id` | Padrão para 100–200 boletos. | Evita timeout HTTP; escala por workers. |
| Consulta paginada de itens | Acompanhar progresso/erros item a item. | Evita payloads grandes. |
| Webhook de conclusão | Integração entre sistemas. | Reduz polling. |
| Download individual | Segunda via / reprocessamento pontual. | Consumo sob demanda. |
| Download consolidado `.zip` | Exportação de lote concluído. | Mais eficiente que base64 no JSON. |
| PDF único com todos os boletos | Só por exigência operacional. | Alto uso de memória; gerar como artefato em background. |

> **Não retornar PDFs em base64 dentro do JSON** para lotes: aumenta o tráfego e dificulta
> streaming, cache e armazenamento. Persistir em storage e retornar referências com expiração/permissão.

## Estados do job e do item

```text
received → validating → processing → partially_completed
                             │              │
                             │              ▼
                             │          completed
                             ▼
                          failed
```

Estados por item: `pending` · `validating` · `rendering` · `completed` · `failed` · `skipped`.

## Idempotência e rastreabilidade

- Cada requisição em lote aceita uma `idempotency_key` por cliente/tenant.
- Cada item aceita uma chave externa (`external_id`) para evitar duplicidade.
- O job registra: versão do template, versão das regras bancárias, banco, carteira, convênio,
  tenant, usuário solicitante e ambiente.
- Reprocessar cria nova tentativa do item, preservando histórico de erro/artefato anterior.

## Concorrência e limites (sugestão)

- Tamanho máximo do lote por endpoint (inicial: **200 itens**).
- Limite de jobs simultâneos por tenant.
- Limite de workers por tipo de tarefa (validação, PDF, PIX, CNAB).
- **Fila separada para renderização de PDF** (costuma ser intensiva em CPU/memória).
- Timeout por item e timeout total do job.
- Retentativa com *backoff* apenas para falhas transitórias.

## Estratégia equivalente para CNAB — agrupamento determinístico

O CNAB segue o mesmo padrão assíncrono, com uma diferença crítica: **o agrupamento bancário é
determinístico**. Regras (ver também [06 — CNAB](06-cnab.md)):

1. A API recebe os títulos que devem compor uma remessa.
2. O job valida se todos pertencem ao **mesmo banco, layout, convênio, carteira e conta** — ou
   separa automaticamente em **sublotes compatíveis**.
3. Cada sublote gera um **arquivo CNAB próprio**.
4. O resultado entrega um manifesto com arquivos, totais, quantidade de registros, hash e erros por item.

Critérios específicos:

- **Nunca misturar** banco/layout/convênio/conta incompatíveis no mesmo arquivo.
- Validar totais de header/trailer antes de disponibilizar o arquivo.
- Guardar o conteúdo CNAB de forma **imutável** para auditoria.
- Permitir reprocessar **apenas o sublote com erro**.

## Modelo de endpoints sugerido (serviço REST)

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

## Divisão de responsabilidades (engine × comunicação)

| Camada | Responsabilidades |
|--------|-------------------|
| **PyCobrança** (engine de domínio, sem HTTP/fila/storage) | Validação de domínio; linha digitável, código de barras, nosso número; PIX/Bolepix (EMV/QR); geração/leitura de CNAB; renderização de PDF/HTML; serialização de artefatos e manifestos técnicos; erros determinísticos; executável em testes sem infraestrutura. |
| **Serviço REST** (aplicação e comunicação) | Endpoints REST/OpenAPI; autenticação/autorização/tenant; jobs assíncronos, itens, tentativas e estados; idempotência; persistência de status/auditoria/artefatos; orquestração de workers; entrega por polling/webhook/download assinado; comunicação com bancos/gateways; tradução de erros técnicos em respostas HTTP. |

**Regra de decisão:** se a tarefa depende de regra bancária, cálculo, layout, CNAB, PIX ou PDF →
**PyCobrança**. Se depende de HTTP, autenticação, tenant, fila, storage, webhook, retry externo ou
comunicação com banco/provedor → **o serviço de cobrança**.

## Evolução da arquitetura

```text
Fase inicial:   Serviço REST  → importa PyCobrança como biblioteca
Fase de escala: Serviço REST  → fila → workers que importam PyCobrança
Alto volume:    Serviço REST  → fila/eventos → generation-service → PyCobrança (engine interna)
```

## Critérios de aceite para lotes

- Lote de 100 boletos com sucesso e **falhas parciais controladas**.
- Lote de 200 boletos **sem timeout HTTP**.
- PDFs individuais e `.zip` consolidado.
- Manifesto com status, hashes e URLs de artefatos.
- Webhook de conclusão e consulta por polling.
- **Idempotência** repetindo a mesma requisição.
- CNAB com **sublotes** por banco/layout/convênio/conta.
- Medir tempo médio por item, tempo total, CPU, memória e storage.
