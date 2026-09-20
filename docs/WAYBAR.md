# Integração com o Waybar

O módulo é compatível com a estrutura enviada pelo usuário.

## 1. Adicionar à lista

No `modules-right`, por exemplo depois de `custom/usb`:

```jsonc
"modules-right": [
  "memory",
  "cpu",
  "network",
  "custom/usb",
  "custom/hermes",
  "bluetooth",
  "pulseaudio",
  "backlight",
  "custom/battery",
  "custom/power"
],
```

## 2. Adicionar a definição do módulo

Dentro do objeto principal da configuração:

```jsonc
"custom/hermes": {
  "exec": "hermes-waybar status --waybar",
  "return-type": "json",
  "interval": 10,
  "tooltip": true,
  "format": "{}",
  "on-click": "hermes-waybar open",
  "on-click-right": "hermes-waybar hud"
},
```

- clique esquerdo: abre o Hermes Desktop; se já estiver aberto, foca a janela;
- clique direito: abre o Desktop e o deixa flutuante (HUD).

O foco usa `hyprctl dispatch focuswindow class:^Hermes$`. A classe de janela pode ser ajustada:

```bash
export HERMES_WAYBAR_WINDOW_CLASS='Hermes'
```

O clique usa `hermes desktop --skip-build` quando não há janela. Para outro comando:

```bash
export HERMES_WAYBAR_DESKTOP_COMMAND='seu-comando-do-desktop'
```

## Seletor de sessões e envio de prompt

Com o clique direito, o Rofi lista as sessões recentes usando o seu tema Nord.

Para enviar um prompt a uma sessão:

```bash
hermes-waybar prompt --theme ~/.config/rofi/themes/nord.rasi
```

Fluxo:

```text
selecionar sessão
  ↓
digitar o prompt no Rofi
  ↓
enviar para POST /api/sessions/{session_id}/chat
  ↓
resposta via notify-send
```

O prompt só é enviado após seleção e digitação explícitas. Nenhum prompt é enviado automaticamente.

Temas de referência no repositório:

```text
rofi/hermes-sessions.rasi
rofi/hermes-prompt.rasi
```

Ambos importam o seu tema base:

```rasi
@import "~/.config/rofi/themes/nord.rasi"
```

## Sessões e notificações

O tooltip lista as cinco sessões mais recentes. A notificação de conclusão usa um watcher separado:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/hermes-waybar-notifications.service \
  ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now hermes-waybar-notifications.service
```

O watcher usa `notify-send` quando disponível e notifica transições para estados finais registrados pelo API Server. Ele mantém apenas IDs e razões de encerramento em:

```text
~/.local/state/hermes-waybar/notifications.json
```

A primeira execução apenas cria o estado inicial. Ela não dispara notificações antigas.


## 3. Adicionar o estilo

A definição em [`../waybar/style.css`](../waybar/style.css) pode ser copiada para `themes/nord-custom/nord.css`:

```css
#custom-hermes {
  color: @frost-1;
  padding: 0 8px;
  margin: 0 2px;
}

#custom-hermes.busy {
  color: @frost-2;
}

#custom-hermes.offline,
#custom-hermes.error {
  color: @red;
}

#custom-hermes:hover {
  background-color: alpha(@frost-1, 0.12);
}
```

## 4. Testar antes de reiniciar

```bash
hermes-waybar doctor --json
hermes-waybar status --waybar
```

A segunda linha deve produzir um único objeto JSON, por exemplo:

```json
{"text":"☤","tooltip":"Hermes: disponível\nVersão: 0.21.3","class":"running","alt":"running"}
```

## 5. Recarregar o Waybar

```bash
pkill -SIGUSR2 waybar
```

Se o módulo não aparecer, execute o Waybar em foreground para ver o erro:

```bash
waybar -l debug
```
