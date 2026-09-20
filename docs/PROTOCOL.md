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

O `/api/status` reportou o gateway em execução, modo `multiple`, com os perfis `default`, `baskerville`, `magah`, `marvin` e `stoner`. Esse endpoint é público e não prova que uma operação autenticada funcionará.

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

A terceira opção parece a mais promissora para preservar a compatibilidade com o Desktop remoto. Ela ainda precisa de uma prova de conexão e de uma decisão sobre a dependência WebSocket no helper local.

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
