Este paquete .mcpb no incluye el servidor MCP: es solo un lanzador.

El servidor real (cfo_financiero_mcp.py) vive dentro de WSL, en:
  /home/bruno/proyectos/cfo-inteligente/backend/mcp_server/cfo_financiero_mcp.py

y corre con el intérprete del venv del proyecto:
  /home/bruno/proyectos/cfo-inteligente/backend/.venv/bin/python

manifest.json define server.mcp_config.command = "wsl.exe" para que Claude
Desktop (Windows) delegue la ejecución a esa distro WSL en vez de intentar
correr Python directamente en Windows. Este archivo solo existe para
satisfacer el campo obligatorio server.entry_point del schema de MCPB
(que exige un entry_point aunque el server real no esté empaquetado aquí).
