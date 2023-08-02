local wezterm = require 'wezterm';
wezterm.on('window-resized', function(window, pane)
  wezterm.reload_configuration()
end)
conf = {
  audible_bell = "Disabled",
  hide_tab_bar_if_only_one_tab = true,
--  window_decorations = "RESIZE",
  window_padding = {
    left = 0,
    right = 0,
    top = 0,
    bottom = 0,
  },
--  color_scheme = "Solarized (light) (terminal.sexy)",
}
local ok, local_conf = pcall(require, 'wezterm_local')
if ok then
  for k, v in pairs(local_conf) do
    conf[k] = v
  end
end
return conf
