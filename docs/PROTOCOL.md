# Validação do protocolo Hermes

## Resultado

O endpoint remoto configurado no Hermes Desktop responde em HTTP e expõe uma API de dashboard. A validação foi feita sem imprimir ou persistir o token de sessão.

### Observações verificadas

| Endpoint | Resultado | Interpretação |
|---|---:|---|
| `/api/status` | `200 application/json` | Endpoint público de estado disponível |
| `/api/dashboard/plugins` | `200 application/json` | Rotas do dashboard disponíveis |
| `/health` | `302 /login` | Rota protegida pelo fluxo de login |
| `/health/detailed` | `302 /login` | Rota protegida pelo fluxo de login |
| `/v1/capabilities` | `302 /login` | API Server não acessível sem autenticação de sessão válida |
| `/v1/models` | `302 /login` | API Server não acessível sem autenticação de sessão válida |
| `/api/sessions` | `401 unauthenticated` | Token estático testado não autentica esta rota no modo atual |
| `/api/model/options` | `401 unauthenticated` | Token estático testado não autentica esta rota no modo atual |
| `/api/messaging/platforms` | `401 unauthenticated` | Token estático testado não autentica esta rota no modo atual |
| `WS /api/ws?token=...` | `403 Forbidden` | Token estático testado também não autentica o WebSocket do Desktop |

O `/api/status` reportou o gateway em execução, modo `multiple`, com os perfis `default`, `baskerville`, `magah`, `marvin` e `stoner`. Esse endpoint é público e não prova que uma operação autenticada funcionará.

A tentativa de WebSocket usou o formato documentado no código do Hermes Desktop para conexões em modo token: `ws(s)://host/api/ws?token=...`. O servidor rejeitou o upgrade com `403` antes de qualquer frame JSON-RPC.

## Validação adicional do API Server

O gateway também possui um API Server separado do dashboard. No VPS, ele está habilitado e protegido por `API_SERVER_KEY`, mas escuta somente em `127.0.0.1:8642`.

Testes locais no VPS:

| Endpoint | Resultado |
|---|---:|
| `http://127.0.0.1:8642/health` | `200` |
| `http://127.0.0.1:8642/health/detailed` | `200` |
| `http://127.0.0.1:8642/v1/capabilities` | `200` |
| `http://127.0.0.1:8642/v1/models` | `200` |

O mesmo serviço não está acessível pelo endereço Tailscale `100.84.75.108:8642`, porque o bind atual é loopback.

Essa validação muda a decisão técnica: **o API Server HTTP é o transporte recomendado para o projeto**, desde que seja exposto de forma restrita à rede Tailscale ou por um proxy HTTPS. O dashboard na porta 9119 não deve ser usado como API pública do Waybar.

## Diagnóstico

O servidor anuncia `auth_required: true`. O código do Hermes Desktop documenta dois modelos diferentes:

- token estático legado: REST usa `X-Hermes-Session-Token`;
- autenticação OAuth: REST usa cookie de sessão e WebSocket usa ticket de uso único.

O arquivo de conexão do Desktop está no formato de token estático, mas as rotas protegidas responderam como modo autenticado/OAuth. Portanto, o token disponível para esta validação não é suficiente para consumir a API protegida.

Isso não demonstra que o token foi exposto ou inválido em definitivo. Demonstra apenas que a combinação endpoint + método de autenticação testada não autoriza as rotas necessárias.

## Decisão provisória

Não devemos implementar ainda o cliente HTTP/SSE como se estivesse validado.

A próxima etapa deve ser uma destas:

1. validar a autenticação nativa do Hermes Desktop e identificar como obter um ticket/cookie sem copiar credenciais de navegador; ou
2. habilitar explicitamente uma interface de API destinada a clientes externos, com credencial própria e escopo adequado; ou
3. validar o WebSocket `/api/ws` usado pelo Desktop, mantendo a autenticação no mesmo modelo do aplicativo.

A terceira opção foi testada. O WebSocket `WS /api/ws?token=...`, que é o formato usado pelo Desktop em conexões de token estático, respondeu `403 Forbidden`. Assim, o transporte está acessível, mas a credencial disponível não é aceita por nenhuma das duas interfaces testadas.

## Próxima decisão necessária

Antes de escrever o adaptador, precisamos resolver a autenticação do cliente externo. As alternativas são:

1. criar uma credencial própria para clientes externos, se o Hermes Gateway oferecer esse modo;
2. usar um fluxo OAuth com sessão/ticket próprio, sem extrair cookies do Hermes Desktop;
3. executar um pequeno relay autorizado no ambiente do gateway, com uma credencial independente e escopo mínimo.

Não devemos copiar cookies do Electron, reutilizar tokens internos do Desktop ou colocar credenciais em arquivos do Waybar.

## Consequência para o projeto

A arquitetura continua:

```text
Waybar → helper local → adaptador Hermes → gateway remoto
```

Mas o adaptador não deve ser fixado em HTTP/SSE antes da validação de autenticação. O código deve começar por uma interface abstrata e uma ferramenta `hermes-waybar doctor` que teste:

- alcance de rede;
- autenticação;
- perfil selecionado;
- capacidade de listar sessões;
- capacidade de receber eventos;
- versão do gateway.
