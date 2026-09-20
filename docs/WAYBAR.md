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
  "format": "{}"
},
```

O script existente `usb-status.sh` não precisa ser alterado.

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
