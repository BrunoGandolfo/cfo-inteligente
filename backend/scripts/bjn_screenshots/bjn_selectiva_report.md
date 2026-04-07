# BJN Selectiva con rango de fechas

Fecha de ejecución: `2026-04-06`

Script usado: [bjn_prueba_selectiva.py](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_prueba_selectiva.py)

Reporte JSON completo: [bjn_selectiva_report.json](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/bjn_selectiva_report.json)

## Selectores confirmados

- Link a Búsqueda Selectiva: `[id="j_id10:j_id11"]`
- Fecha desde: `[id="formBusqueda:j_id20:j_id23:fechaDesdeCalInputDate"]`
- Hidden fecha desde: `[id="formBusqueda:j_id20:j_id23:fechaDesdeCalInputCurrentDate"]`
- Fecha hasta: `[id="formBusqueda:j_id20:j_id147:fechaHastaCalInputDate"]`
- Hidden fecha hasta: `[id="formBusqueda:j_id20:j_id147:fechaHastaCalInputCurrentDate"]`
- Resultados por página visible: `[id="formBusqueda:j_id20:j_id223:cantPagcomboboxField"]`
- Resultados por página hidden: `[id="formBusqueda:j_id20:j_id223:cantPagcomboboxValue"]`
- Ordenar por: `[name="formBusqueda:j_id20:j_id240:j_id248"]`
- Botón buscar: `[id="formBusqueda:j_id20:Search"]`
- Tabla real de resultados: `[id="formResultados:dataTable"]`
- Filas de resultados: `table[id="formResultados:dataTable"] tr.rich-table-row`
- Paginador: `[id="formResultados:zonaPaginador"]`
- Siguiente página: `[id="formResultados:sigLink"]`
- Click de sentencia individual: `td[id="formResultados:dataTable:0:colFec"]`

## Método que funcionó

- Fechas: `fill()` directo sobre los inputs RichFaces.
- Valor escrito:
  - Desde `01/01/YYYY`
  - Hasta `31/12/YYYY`
- Ajuste adicional necesario:
  - Hidden `fechaDesdeCalInputCurrentDate` = `MM/YYYY`
  - Hidden `fechaHastaCalInputCurrentDate` = `MM/YYYY`
- Resultados por página: setear visible + hidden en `200`.
- Orden: `select_option("FECHA_DESCENDENTE")`.

## Resultados confirmados

- 2024: `4850` resultados, `25` páginas, `200` resultados en página 1.
- 2023: `4820` resultados, `25` páginas, `200` resultados en página 1.
- 2020: `3888` resultados, `20` páginas, `200` resultados en página 1.

## Paginación

- El botón siguiente sí funciona.
- En 2024, pasó de `Página 1 de 25` a `Página 2 de 25`.
- Sigue mostrando `200` resultados por página en página 2.
- Tiempo medido para avanzar a página 2: `7.472 s`.
- Primer resultado en página 1: `30/12/2024`, `1459/2024`, `Tribunal Apelaciones Familia 3 T`.
- Primer resultado en página 2: `11/12/2024`, `400/2024`, `Tribunal Apelaciones Civil 6ºTº`.

## Popup de sentencia

- Sí abre desde la búsqueda selectiva.
- Estructura confirmada como equivalente a la búsqueda simple.
- Señales verificadas:
  - `#textoSentenciaBox`
  - `#panelTextoSent_body`
  - tabla `j_id3`
  - tabla `j_id21`
- Popup probado: [selectiva_sentencia_popup.png](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/selectiva_sentencia_popup.png)

## Tiempos observados

- Cargar `busquedaSimple.seam`: `2.308 s`
- Abrir Búsqueda Selectiva desde el link: `6.393 s`
- Configurar formulario: `0.101 s`
- Ejecutar búsqueda 2024: `6.971 s` de búsqueda efectiva
- Ejecutar búsqueda 2023: `6.930 s` de búsqueda efectiva
- Ejecutar búsqueda 2020: `6.917 s` de búsqueda efectiva
- Sleep AJAX usado después de cada acción: `6.0 s`

## Protocolo reproducible para crawler

1. Ir a `http://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSimple.seam`.
2. Esperar `domcontentloaded`.
3. Esperar que exista `A4J`.
4. Click en `[id="j_id10:j_id11"]`.
5. Esperar URL `**/busquedaSelectiva.seam?cid=*`.
6. Dormir `6 s`.
7. Verificar que existan:
   - `[id="formBusqueda:j_id20:j_id23:fechaDesdeCalInputDate"]`
   - `[id="formBusqueda:j_id20:j_id147:fechaHastaCalInputDate"]`
   - `[id="formBusqueda:j_id20:Search"]`
8. Setear resultados por página a `200` en visible + hidden.
9. Seleccionar `FECHA_DESCENDENTE` en `[name="formBusqueda:j_id20:j_id240:j_id248"]`.
10. `fill("01/01/YYYY")` en fecha desde.
11. `fill("31/12/YYYY")` en fecha hasta.
12. Setear hidden de calendario a `01/YYYY` y `12/YYYY`.
13. Click en `[id="formBusqueda:j_id20:Search"]`.
14. Dormir `6 s`.
15. Esperar texto con `resultado/s` o filas en `table[id="formResultados:dataTable"] tr.rich-table-row`.
16. Leer:
   - total desde `(\d+) resultado/s`
   - página desde `Página X de Y`
   - filas desde `table[id="formResultados:dataTable"] tr.rich-table-row`
17. Para página 2, click en `[id="formResultados:sigLink"]`, esperar cambio real en `Página 2 de Y` o en la primera fila, luego dormir `6 s`.
18. Para abrir sentencia, click en `td[id="formResultados:dataTable:0:colFec"]` y esperar popup.

## Capturas principales

- [selectiva_step_01_busqueda_simple.png](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/selectiva_step_01_busqueda_simple.png)
- [selectiva_step_02_formulario.png](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/selectiva_step_02_formulario.png)
- [selectiva_step_03_form_configurado.png](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/selectiva_step_03_form_configurado.png)
- [selectiva_test_2024_fill.png](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/selectiva_test_2024_fill.png)
- [selectiva_2024_pagina_2.png](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/selectiva_2024_pagina_2.png)
- [selectiva_sentencia_popup.png](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/selectiva_sentencia_popup.png)
- [selectiva_test_2023_ok.png](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/selectiva_test_2023_ok.png)
- [selectiva_test_2020_ok.png](/home/brunogandolfo/cfo-inteligente/backend/scripts/bjn_screenshots/selectiva_test_2020_ok.png)
