import pytest

from app.services.impo_relation_parser import (
    extraer_decretos_pendientes,
    parse_nota_relaciones,
    parse_norma_ref,
)


@pytest.fixture(scope="session", autouse=True)
def crear_tablas():
    """La suite es pura y no debe depender del setup de base de datos del repo."""
    yield


def test_parse_nota_simple_reglamentado():
    nota = "Reglamentado por: Decreto Nº 335/990 de 26/07/1990"

    relaciones = parse_nota_relaciones(nota, articulo_origen="Artículo 1")

    assert len(relaciones) == 1
    rel = relaciones[0]
    assert rel["tipo_relacion"] == "REGLAMENTA"
    assert rel["tipo_norma_destino"] == "DECRETO"
    assert rel["numero_destino"] == 335
    assert rel["anio_destino"] == 1990
    assert rel["fecha_destino"] == "26/07/1990"
    assert rel["articulo_origen"] == "Artículo 1"
    assert "Reglamentado por:" in rel["texto_original"]


def test_parse_nota_reglamentado_multiple_decretos():
    nota = (
        "Reglamentado por: Decreto Nº 268/020 de 30/09/2020, "
        "Decreto Nº 143/018 de 22/05/2018, Decreto Nº 2/012 de 09/01/2012"
    )

    relaciones = parse_nota_relaciones(nota, articulo_origen="Artículo 2")

    assert len(relaciones) == 3
    assert [r["numero_destino"] for r in relaciones] == [268, 143, 2]
    assert [r["anio_destino"] for r in relaciones] == [2020, 2018, 2012]
    assert all(r["tipo_relacion"] == "REGLAMENTA" for r in relaciones)


def test_parse_nota_redaccion_dada_por():
    nota = "Redacción dada por: Ley Nº 18.996 de 07/11/2012 artículo 43"

    relaciones = parse_nota_relaciones(nota, articulo_origen="Artículo 3")

    assert len(relaciones) == 1
    rel = relaciones[0]
    assert rel["tipo_relacion"] == "MODIFICA"
    assert rel["tipo_norma_destino"] == "LEY"
    assert rel["numero_destino"] == 18996
    assert rel["anio_destino"] == 2012
    assert rel["articulo_destino"] == "43"


def test_parse_nota_agregado_por():
    nota = "Agregado/s por: Ley Nº 19.355 de 19/12/2015 artículo 727"

    relaciones = parse_nota_relaciones(nota, articulo_origen="Artículo 4")

    assert len(relaciones) == 1
    rel = relaciones[0]
    assert rel["tipo_relacion"] == "AGREGA"
    assert rel["numero_destino"] == 19355
    assert rel["anio_destino"] == 2015
    assert rel["articulo_destino"] == "727"


def test_parse_nota_derogado_por():
    nota = "Derogado/a por: Ley Nº 20.446 de 16/12/2025"

    relaciones = parse_nota_relaciones(nota, articulo_origen="Artículo 5")

    assert len(relaciones) == 1
    rel = relaciones[0]
    assert rel["tipo_relacion"] == "DEROGA"
    assert rel["numero_destino"] == 20446
    assert rel["anio_destino"] == 2025
    assert rel["articulo_destino"] is None


def test_parse_nota_nueva_redaccion():
    nota = "Este artículo dio nueva redacción a: Ley Nº 19.315 de 18/02/2015 artículo 12"

    relaciones = parse_nota_relaciones(nota, articulo_origen="Artículo 6")

    assert len(relaciones) == 1
    rel = relaciones[0]
    assert rel["tipo_relacion"] == "NUEVA_REDACCION"
    assert rel["numero_destino"] == 19315
    assert rel["anio_destino"] == 2015
    assert rel["articulo_destino"] == "12"


def test_parse_nota_vacia():
    assert parse_nota_relaciones("", articulo_origen="Artículo 7") == []


def test_parse_nota_sin_relaciones_retorna_lista_vacia_o_referencia_interna():
    relaciones = parse_nota_relaciones(
        "<b>Ver en esta norma, artículo:</b> <a>80</a>",
        articulo_origen="Artículo 8",
    )

    assert relaciones == []


@pytest.mark.parametrize(
    "texto,anio_esperado",
    [
        ("Decreto Nº 335/990 de 26/07/1990", 1990),
        ("Decreto Nº 1/007 de 01/01/2007", 2007),
        ("Decreto Nº 2/015 de 01/01/2015", 2015),
        ("Decreto Nº 2/020 de 01/01/2020", 2020),
        ("Decreto Nº 2/024 de 01/01/2024", 2024),
    ],
)
def test_parse_norma_ref_convierte_anios_decretos(texto, anio_esperado):
    ref = parse_norma_ref(texto)

    assert ref is not None
    assert ref["tipo_norma"] == "DECRETO"
    assert ref["anio"] == anio_esperado


@pytest.mark.parametrize(
    "texto,numero_esperado",
    [
        ("Ley Nº 16.060 de 01/01/1989 artículo 1", 16060),
        ("Ley Nº 19.889 de 01/01/2020 artículo 2", 19889),
    ],
)
def test_parse_norma_ref_elimina_puntos(texto, numero_esperado):
    ref = parse_norma_ref(texto)

    assert ref is not None
    assert ref["tipo_norma"] == "LEY"
    assert ref["numero"] == numero_esperado


def test_parse_nota_literal_o_numeral():
    nota = "Literal C) reglamentado por: Decreto Nº 437/009 de 28/09/2009"

    relaciones = parse_nota_relaciones(nota)

    assert len(relaciones) == 1
    rel = relaciones[0]
    assert rel["tipo_relacion"] == "REGLAMENTA"
    assert rel["numero_destino"] == 437
    assert rel["anio_destino"] == 2009
    assert rel["articulo_origen"] == "Literal C)"


def test_parse_nota_compleja_real_con_html_y_varias_relaciones():
    nota = """
        <div>
            <b>Reglamentado por:</b> Decreto Nº 268/020 de 30/09/2020,
            Decreto Nº 143/018 de 22/05/2018;
            <span>Redacción dada por:</span> Ley Nº 18.996 de 07/11/2012 artículo 43.
            Agregado/s por: Ley Nº 19.355 de 19/12/2015 artículo 727.
            Derogado/a por: Ley Nº 20.446 de 16/12/2025.
            Este artículo dio nueva redacción a: Ley Nº 19.315 de 18/02/2015 artículo 12.
            Ver vigencia: Ley Nº 19.996 de 03/11/2021 artículo 2.
        </div>
    """

    relaciones = parse_nota_relaciones(nota, articulo_origen="Artículo 9")

    assert len(relaciones) == 7
    assert [r["tipo_relacion"] for r in relaciones] == [
        "REGLAMENTA",
        "REGLAMENTA",
        "MODIFICA",
        "AGREGA",
        "DEROGA",
        "NUEVA_REDACCION",
        "VIGENCIA",
    ]
    assert relaciones[-1]["tipo_norma_destino"] == "LEY"
    assert relaciones[-1]["numero_destino"] == 19996


def test_extraer_decretos_pendientes_filtra_solo_decretos():
    relaciones = [
        {
            "tipo_relacion": "REGLAMENTA",
            "tipo_norma_destino": "DECRETO",
            "numero_destino": 335,
            "anio_destino": 1990,
        },
        {
            "tipo_relacion": "MODIFICA",
            "tipo_norma_destino": "LEY",
            "numero_destino": 18996,
            "anio_destino": 2012,
        },
        {
            "tipo_relacion": "REGLAMENTA",
            "tipo_norma_destino": "DECRETO",
            "numero_destino": 143,
            "anio_destino": 2018,
        },
    ]

    pendientes = extraer_decretos_pendientes(relaciones)

    assert pendientes == [
        {"tipo_norma": "DECRETO", "numero": 335, "anio": 1990},
        {"tipo_norma": "DECRETO", "numero": 143, "anio": 2018},
    ]
