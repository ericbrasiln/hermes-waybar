# hermes-waybar

Integração entre o [Hermes Agent](https://github.com/NousResearch/hermes-agent) e o [Waybar](https://github.com/Alexays/Waybar) para Linux/Wayland.

O projeto pretende oferecer, a partir do Waybar:

- indicador do estado do Hermes;
- tooltip com sessão, modelo e tarefa ativa;
- abertura do Hermes Desktop;
- envio de prompts;
- visualização de tarefas e sessões;
- notificações de conclusão, erro, aprovação e solicitação de intervenção;
- conexão com um Hermes Gateway remoto por Tailscale ou HTTPS.

O projeto será instalado pelo usuário na máquina local. O repositório não pressupõe acesso remoto à máquina que executa o Waybar.

## Estado do projeto

**Fase:** planejamento e validação do protocolo.

A primeira implementação será somente leitura. O envio de prompts e as ações que alteram sessões entrarão depois de validarmos autenticação, roteamento e eventos do gateway.

## Arquitetura inicial

```text
Waybar
  └── custom/hermes
        └── hermes-waybar CLI/helper local
              └── adaptador HTTP/SSE ou WebSocket JSON-RPC
                    └── Hermes Gateway remoto
                          └── Hermes Desktop
```

O helper local não deve armazenar tokens na configuração do Waybar. Credenciais serão lidas de um arquivo local com permissões restritas ou de um mecanismo de credenciais documentado na instalação.

## Requisitos previstos

- Linux/Wayland;
- Waybar;
- Python 3.11+;
- `curl` ou cliente HTTP equivalente;
- `notify-send` para notificações opcionais;
- acesso de rede ao Hermes Gateway;
- `jq` somente se for usado por scripts auxiliares, não como requisito do núcleo.

## Desenvolvimento

O plano de implementação está em [`docs/PLAN.md`](docs/PLAN.md). A arquitetura está em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

Ainda não instale este projeto em uma máquina de produção. O protocolo do gateway será validado antes da primeira versão instalável.

## Licença

MIT. Consulte [`LICENSE`](LICENSE).
