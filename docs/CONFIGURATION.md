# Configuração local

O helper lê, nesta ordem:

1. argumentos da linha de comando;
2. variáveis de ambiente;
3. arquivo `~/.config/hermes-waybar/config.toml`.

A chave da API não deve ser colocada na configuração do Waybar.

## Arquivo de configuração

```toml
[hermes]
endpoint = "http://100.84.75.108:8642"
api_key = "COLOQUE_A_CHAVE_LOCALMENTE"
timeout = 8
```

Proteja o arquivo:

```bash
chmod 600 ~/.config/hermes-waybar/config.toml
```

O repositório não fornece nem solicita a chave. O usuário deve obtê-la no ambiente do próprio Hermes Gateway.

## Variáveis de ambiente

```bash
export HERMES_WAYBAR_ENDPOINT="http://100.84.75.108:8642"
export HERMES_WAYBAR_API_KEY="..."
export HERMES_WAYBAR_TIMEOUT="8"
```

As variáveis são úteis para testes. Para uso permanente, prefira um arquivo de credencial com permissão `0600`.

## Diagnóstico

Durante o desenvolvimento:

```bash
PYTHONPATH=src python3 -m hermes_waybar.cli doctor
PYTHONPATH=src python3 -m hermes_waybar.cli doctor --json
```

Uma instalação futura fornecerá o comando direto:

```bash
hermes-waybar doctor
```

O diagnóstico verifica:

- alcance do API Server;
- autenticação pelo `API_SERVER_KEY`;
- versão do Hermes;
- capabilities;
- quantidade de modelos disponíveis.

A saída nunca imprime a chave da API.
