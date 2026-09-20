# hermes-waybar — plano de implementação

## Objetivo

Criar um helper local para Waybar que monitore e controle, com autenticação explícita, um Hermes Gateway local ou remoto.

## Restrições

- O helper roda na máquina do usuário, não na VPS.
- O projeto não terá acesso automático ao `archebn`.
- Nenhum token será colocado no `config.jsonc` do Waybar.
- A primeira entrega será somente leitura.
- Estados não confirmados devem aparecer como `unknown` ou `unavailable`, nunca como atividade inventada.
- A integração deve funcionar sem depender do Omarchy. Omarchy/Quickshell será uma referência de design, não uma dependência.
- O projeto será distribuído sob MIT.

## Decisões iniciais

### 1. Separar o coletor do módulo visual

O Waybar executará um comando local que produz JSON. O comando não deverá conter lógica específica da aparência do tema.

```text
hermes-waybar status --waybar
```

A configuração do Waybar cuidará de `format`, classes CSS, posição e intervalos.

### 2. Criar uma camada de adaptadores

O núcleo não deve assumir que todos os Hermes usam o mesmo transporte. A interface deverá permitir:

- `HttpApiAdapter`: API HTTP/SSE do Hermes;
- `TuiGatewayAdapter`: WebSocket JSON-RPC do TUI Gateway;
- `LocalStateAdapter`: fallback somente leitura para estado local, inspirado no Hermarchy.

A implementação inicial validará primeiro o transporte HTTP/SSE disponível no gateway usado pelo projeto.

### 3. Manter estado local mínimo

O helper poderá armazenar somente:

- cache curto para não sobrecarregar o gateway;
- último estado conhecido, com timestamp;
- identificadores de notificação já emitidos;
- configuração não secreta.

Tokens e chaves ficam fora do cache, logs e saída do Waybar.

### 4. Usar JSON nativo do Waybar

Toda saída destinada ao módulo será um objeto JSON com, no mínimo:

```json
{
  "text": "☤",
  "tooltip": "Hermes: idle",
  "class": "idle",
  "alt": "idle"
}
```

## Fases

### Fase 0 — contrato e descoberta do gateway

1. Identificar endpoints, autenticação e eventos disponíveis no Hermes Gateway.
2. Validar separadamente o caminho HTTP, o caminho SSE e o WebSocket usado pelo Hermes Desktop.
3. Definir o modelo interno de estado.
4. Definir comportamento para gateway indisponível, timeout, resposta inválida e sessão inexistente.
5. Registrar exemplos reais anonimizados em `tests/fixtures/`.
6. Não fixar o transporte antes de validar autenticação e listagem de sessões.

**Resultado parcial:** `/api/status` responde, mas as rotas protegidas não aceitaram o token estático testado enquanto o gateway anuncia `auth_required: true`. O registro detalhado está em [`docs/PROTOCOL.md`](PROTOCOL.md).

**Saída:** contrato documentado e decisão de transporte.

### Fase 1 — módulo de status somente leitura

1. Implementar configuração carregada de arquivo XDG.
2. Implementar cliente HTTP sem dependência externa, salvo decisão contrária após a Fase 0.
3. Implementar normalização para `idle`, `executing`, `waiting`, `completed`, `failed`, `unavailable` e `unknown`.
4. Implementar `hermes-waybar status --waybar`.
5. Implementar timeout, cache curto e saída segura para o Waybar.
6. Adicionar testes unitários para cada estado e falha de transporte.

**Saída:** indicador confiável no Waybar.

### Fase 2 — instalação local e notificações

1. Criar instalador não destrutivo para arquivos do helper.
2. Criar exemplo de módulo Waybar.
3. Criar unidade opcional `systemd --user` para o listener de eventos, se necessário.
4. Integrar `notify-send` com cooldown e deduplicação.
5. Documentar rollback e remoção.

**Saída:** pacote instalável manualmente na máquina Arch.

### Fase 3 — sessões e abertura do Desktop

1. Listar sessões permitidas pelo protocolo.
2. Permitir selecionar uma sessão ativa.
3. Abrir o Hermes Desktop via comando configurável ou URL.
4. Mostrar sessão, perfil, modelo e diretório de trabalho no tooltip.

**Saída:** módulo de consulta e navegação.

### Fase 4 — envio de prompts

1. Implementar comando local explícito para enviar prompt.
2. Adicionar menu interativo, sem exigir `rofi` ou `wofi` no núcleo.
3. Adicionar confirmação para envio e ações potencialmente destrutivas.
4. Mostrar estado de envio, execução e erro.
5. Testar alternância de mensagens e associação correta à sessão.

**Saída:** envio controlado pelo Waybar.

### Fase 5 — aprovações, interrupção e tarefas

1. Exibir solicitações de aprovação e intervenção humana.
2. Permitir aprovar, rejeitar e interromper somente com ação explícita.
3. Mostrar tarefas em andamento e workers/subagentes quando o protocolo fornecer esses dados.
4. Adicionar notificações para conclusão, falha e solicitação de input.

**Saída:** controle operacional completo.

### Fase 6 — empacotamento e compatibilidade

1. Testar Waybar sem Omarchy.
2. Testar Waybar em Omarchy quando possível.
3. Preparar pacote AUR somente depois de uma instalação manual reproduzível.
4. Adicionar CI para testes Python, shell, JSONC e documentação.
5. Publicar primeira versão estável somente após validação manual na máquina do usuário.

## Estrutura proposta

```text
hermes-waybar/
├── LICENSE
├── README.md
├── pyproject.toml
├── docs/
│   ├── PLAN.md
│   ├── ARCHITECTURE.md
│   └── PROTOCOL.md
├── src/
│   └── hermes_waybar/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── models.py
│       ├── output.py
│       ├── notify.py
│       ├── state.py
│       └── adapters/
│           ├── __init__.py
│           ├── base.py
│           ├── http_api.py
│           ├── tui_gateway.py
│           └── local_state.py
├── scripts/
│   ├── install.sh
│   └── uninstall.sh
├── systemd/
│   └── hermes-waybar-events.service
├── waybar/
│   ├── module.jsonc
│   └── style.css
└── tests/
    ├── fixtures/
    ├── test_config.py
    ├── test_models.py
    ├── test_output.py
    └── adapters/
```

## Critérios de aceitação da primeira versão

- `hermes-waybar status --waybar` sempre produz JSON válido, inclusive sem rede.
- O módulo diferencia pelo menos `idle`, `executing`, `waiting`, `failed`, `unavailable` e `unknown`.
- Timeout e resposta malformada não travam o Waybar.
- Nenhum segredo aparece em stdout, stderr, tooltip, cache ou log.
- A configuração não sobrescreve automaticamente o Waybar existente.
- A instalação e a remoção são reversíveis.
- Os testes passam em Python 3.11 e 3.12.
