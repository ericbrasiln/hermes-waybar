# Arquitetura técnica

## Componentes

### `hermes-waybar`

CLI local que produz saída para o Waybar e expõe ações explícitas. O binário não executa o Hermes Agent localmente por padrão.

Comandos previstos:

```text
hermes-waybar status --waybar
hermes-waybar sessions --waybar
hermes-waybar prompt --session SESSION_ID
hermes-waybar approve --request REQUEST_ID
hermes-waybar stop --run RUN_ID
hermes-waybar doctor
```

### Adaptadores

Os adaptadores convertem protocolos externos em modelos internos. O restante do programa não deve conhecer detalhes de HTTP, SSE, WebSocket, cabeçalhos ou métodos JSON-RPC.

```python
class HermesAdapter(Protocol):
    def status(self) -> AgentStatus: ...
    def sessions(self) -> list[Session]: ...
    def submit_prompt(self, session_id: str, prompt: str) -> Run: ...
```

A interface acima é conceitual. O contrato final será ajustado depois da inspeção do protocolo real e coberto por testes de contrato.

## Fluxo de leitura

```text
Waybar executa o helper
  ↓
config.py carrega endpoint e credencial
  ↓
adapter consulta status
  ↓
models.py normaliza a resposta
  ↓
output.py produz JSON do Waybar
  ↓
stdout
```

O processo deve terminar rapidamente. Streaming e notificações devem ficar em um processo separado ou em um listener controlado por `systemd --user`.

## Fluxo de eventos

```text
Hermes Gateway → SSE/WebSocket → listener local
                                  ├─ cache de estado
                                  ├─ deduplicação
                                  └─ notify-send
```

O listener não deve executar prompts automaticamente. Eventos recebidos são dados não confiáveis e não podem virar comandos shell sem validação.

## Segurança

- Nunca colocar token em JSONC do Waybar.
- Nunca registrar URLs completas contendo credenciais.
- Definir permissões `0600` para arquivos de credenciais.
- Limitar tamanho de respostas, tooltips, prompts e detalhes de erro.
- Usar timeout de conexão e de leitura.
- Validar origem e esquema do endpoint.
- Não permitir que conteúdo vindo do agente seja interpretado como shell.
- Pedir confirmação para envio de prompt, aprovação, rejeição e interrupção.
- Não expor o listener HTTP local em `0.0.0.0`.

## Compatibilidade com Omarchy

O projeto deve tratar Omarchy como ambiente opcional. A integração principal usa o contrato do Waybar e deve funcionar em qualquer sessão Wayland com Waybar.

O modelo de estados do Hermarchy será usado como referência sem copiar sua suposição de estado local. Em um Hermes remoto, o estado precisa vir da API ou dos eventos do gateway.

## Decisões ainda abertas

1. API HTTP/SSE ou TUI Gateway WebSocket como transporte principal.
2. Ferramenta de menu: `wofi`, `rofi-wayland`, `walker` ou abertura sem menu.
3. Forma de armazenamento da credencial no Arch.
4. Como associar uma notificação ao perfil e à sessão corretos em um gateway multiplexado.
5. Necessidade real de um plugin interno do Hermes Desktop.
