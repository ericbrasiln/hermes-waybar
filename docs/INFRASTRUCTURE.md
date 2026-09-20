# Infraestrutura do Hermes API Server

## Estado validado

O API Server do Hermes está exposto no endereço Tailscale do VPS:

```text
http://100.84.75.108:8642
```

Ele não escuta em `127.0.0.1` nem em uma interface pública comum. O processo está vinculado ao endereço Tailscale `100.84.75.108`.

## Configuração no gateway

A configuração persistente usa um drop-in do systemd do usuário:

```text
~/.config/systemd/user/hermes-gateway.service.d/api-server.conf
```

Conteúdo não secreto:

```ini
[Service]
Environment="API_SERVER_ENABLED=true"
Environment="API_SERVER_HOST=100.84.75.108"
Environment="API_SERVER_PORT=8642"
```

A chave continua em `~/.hermes/.env`, com permissão `0600`, e não deve ser copiada para este repositório.

## Verificação

No VPS:

```bash
systemctl --user is-active hermes-gateway
ss -ltnp | grep 100.84.75.108:8642
```

O cliente do projeto foi validado contra esse endereço e obteve:

```text
reachable: yes
authenticated: yes
version: 0.21.3
errors: 0
```

## Segurança

O API Server dá acesso a operações do agente e usa o backend de terminal local. O bind em Tailscale reduz a exposição, mas não substitui:

- uma chave forte e exclusiva;
- ACLs do Tailscale limitando os dispositivos autorizados;
- firewall restritivo quando disponível;
- sandbox para o backend de terminal em instalações com mais de um usuário confiável.

Não exponha a porta `8642` em `0.0.0.0` sem uma regra de firewall que limite o acesso.
