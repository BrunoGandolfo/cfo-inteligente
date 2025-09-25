--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-1.pgdg24.04+1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-1.pgdg24.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: localidad; Type: TYPE; Schema: public; Owner: cfo_user
--

CREATE TYPE public.localidad AS ENUM (
    'MONTEVIDEO',
    'MERCEDES'
);


ALTER TYPE public.localidad OWNER TO cfo_user;

--
-- Name: moneda; Type: TYPE; Schema: public; Owner: cfo_user
--

CREATE TYPE public.moneda AS ENUM (
    'UYU',
    'USD'
);


ALTER TYPE public.moneda OWNER TO cfo_user;

--
-- Name: tipooperacion; Type: TYPE; Schema: public; Owner: cfo_user
--

CREATE TYPE public.tipooperacion AS ENUM (
    'INGRESO',
    'GASTO',
    'RETIRO',
    'DISTRIBUCION'
);


ALTER TYPE public.tipooperacion OWNER TO cfo_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: cfo_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO cfo_user;

--
-- Name: areas; Type: TABLE; Schema: public; Owner: cfo_user
--

CREATE TABLE public.areas (
    id uuid NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion character varying(255),
    activo boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.areas OWNER TO cfo_user;

--
-- Name: clientes; Type: TABLE; Schema: public; Owner: cfo_user
--

CREATE TABLE public.clientes (
    id uuid NOT NULL,
    nombre character varying(200) NOT NULL,
    telefono character varying(50),
    activo boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.clientes OWNER TO cfo_user;

--
-- Name: distribuciones_detalle; Type: TABLE; Schema: public; Owner: cfo_user
--

CREATE TABLE public.distribuciones_detalle (
    id uuid NOT NULL,
    operacion_id uuid NOT NULL,
    socio_id uuid NOT NULL,
    monto_uyu numeric(15,2) NOT NULL,
    monto_usd numeric(15,2) NOT NULL,
    porcentaje numeric(5,2) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.distribuciones_detalle OWNER TO cfo_user;

--
-- Name: operaciones; Type: TABLE; Schema: public; Owner: cfo_user
--

CREATE TABLE public.operaciones (
    id uuid NOT NULL,
    tipo_operacion public.tipooperacion NOT NULL,
    fecha date NOT NULL,
    monto_original numeric(15,2) NOT NULL,
    moneda_original public.moneda NOT NULL,
    tipo_cambio numeric(10,4) NOT NULL,
    monto_uyu numeric(15,2) NOT NULL,
    monto_usd numeric(15,2) NOT NULL,
    area_id uuid NOT NULL,
    localidad public.localidad NOT NULL,
    descripcion character varying(500),
    cliente character varying(200),
    proveedor character varying(200),
    deleted_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.operaciones OWNER TO cfo_user;

--
-- Name: proveedores; Type: TABLE; Schema: public; Owner: cfo_user
--

CREATE TABLE public.proveedores (
    id uuid NOT NULL,
    nombre character varying(200) NOT NULL,
    telefono character varying(50),
    activo boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.proveedores OWNER TO cfo_user;

--
-- Name: socios; Type: TABLE; Schema: public; Owner: cfo_user
--

CREATE TABLE public.socios (
    id uuid NOT NULL,
    nombre character varying(100) NOT NULL,
    porcentaje_participacion numeric(5,2) NOT NULL,
    activo boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.socios OWNER TO cfo_user;

--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: cfo_user
--

CREATE TABLE public.usuarios (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    nombre character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    es_socio boolean,
    activo boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.usuarios OWNER TO cfo_user;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: cfo_user
--

COPY public.alembic_version (version_num) FROM stdin;
d41b8703364f
\.


--
-- Data for Name: areas; Type: TABLE DATA; Schema: public; Owner: cfo_user
--

COPY public.areas (id, nombre, descripcion, activo, created_at, updated_at) FROM stdin;
d3aff49c-748c-4d1d-bc47-cdda1cfb913d	Jurídica	Servicios jurídicos	t	2025-09-21 21:26:46.812574	2025-09-21 21:26:46.812578
53ba7821-8836-4e74-ad56-a288d290881d	Notarial	Servicios notariales	t	2025-09-21 21:26:46.812585	2025-09-21 21:26:46.812585
14700c01-3b3d-49c6-8e2e-f3ebded1b1bb	Contable	Servicios contables	t	2025-09-21 21:26:46.812589	2025-09-21 21:26:46.81259
11c64c64-c7f6-4e85-9c26-b577c3d7a5b7	Recuperación	Recuperación de deudas	t	2025-09-21 21:26:46.812592	2025-09-21 21:26:46.812593
b11006d3-6cfc-4766-9201-ab56274401a6	Gastos Generales	Gastos operativos generales	t	2025-09-21 21:26:46.812595	2025-09-21 21:26:46.812596
651dfb5c-15d8-41e2-8339-785b137f44f2	Otros	Ingresos no imputables a áreas específicas	t	2025-09-21 18:56:33.444379	2025-09-21 18:56:33.444379
\.


--
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: cfo_user
--

COPY public.clientes (id, nombre, telefono, activo, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: distribuciones_detalle; Type: TABLE DATA; Schema: public; Owner: cfo_user
--

COPY public.distribuciones_detalle (id, operacion_id, socio_id, monto_uyu, monto_usd, porcentaje, created_at) FROM stdin;
87def26c-1713-4659-88bf-b1b4b8a5605e	46f00483-f5cc-4411-ba1c-07383c8a0b03	a3c42595-a2bd-41f3-b477-9978c78222b7	30000.00	5000.00	20.00	2025-09-22 14:44:53.207791
e2e4a274-ab14-419c-93e2-a5664e69c28d	46f00483-f5cc-4411-ba1c-07383c8a0b03	6dd15186-3ec2-4dbf-8d04-d92b2c4e7f18	30000.00	5000.00	20.00	2025-09-22 14:44:53.207796
5d23587c-bc2b-4523-8c99-2ef601e6ecf9	46f00483-f5cc-4411-ba1c-07383c8a0b03	63d1cf00-b5e4-4a98-bd8b-a91d7666506e	30000.00	5000.00	20.00	2025-09-22 14:44:53.207798
04bd4734-328d-4bed-b6e3-c667741cb4fb	46f00483-f5cc-4411-ba1c-07383c8a0b03	aab1c0be-f0a7-40ee-aa9b-63e7422e2f26	30000.00	5000.00	20.00	2025-09-22 14:44:53.2078
9c092702-beec-437d-b461-00d4fe49dce3	46f00483-f5cc-4411-ba1c-07383c8a0b03	57784d73-1162-440b-bc1f-52f193bfdb88	30000.00	5000.00	20.00	2025-09-22 14:44:53.207803
8ce57ece-97d9-4231-826e-f17eb4acaf2e	c06ee93d-72f8-4346-988f-3ba8f4fe62eb	a3c42595-a2bd-41f3-b477-9978c78222b7	5000.00	10000.00	20.00	2025-09-23 14:55:52.110736
8dbc31c9-d2aa-44b7-805b-5e45d0ac6c2d	c06ee93d-72f8-4346-988f-3ba8f4fe62eb	6dd15186-3ec2-4dbf-8d04-d92b2c4e7f18	5000.00	10000.00	20.00	2025-09-23 14:55:52.110741
78583db2-da24-4e6c-9b65-055110d94aed	c06ee93d-72f8-4346-988f-3ba8f4fe62eb	63d1cf00-b5e4-4a98-bd8b-a91d7666506e	5000.00	10000.00	20.00	2025-09-23 14:55:52.110743
5b996e81-f52e-4251-8fd4-2fbedee3fa15	c06ee93d-72f8-4346-988f-3ba8f4fe62eb	aab1c0be-f0a7-40ee-aa9b-63e7422e2f26	5000.00	10000.00	20.00	2025-09-23 14:55:52.110746
3d6c9114-3f01-448c-bf3a-ca25ab3153ed	c06ee93d-72f8-4346-988f-3ba8f4fe62eb	57784d73-1162-440b-bc1f-52f193bfdb88	5000.00	10000.00	20.00	2025-09-23 14:55:52.110748
a2233ba1-7797-4922-a5fc-e563f4722467	db236053-174c-44a4-b558-23486b4cb775	a3c42595-a2bd-41f3-b477-9978c78222b7	12000.00	1000.00	20.00	2025-09-23 14:56:32.918382
a635a36a-e0d4-40a9-be3e-0b632e4a937c	db236053-174c-44a4-b558-23486b4cb775	6dd15186-3ec2-4dbf-8d04-d92b2c4e7f18	12000.00	1000.00	20.00	2025-09-23 14:56:32.918387
05aabfcd-7f2c-4c4b-9f84-6713d2bfd501	db236053-174c-44a4-b558-23486b4cb775	63d1cf00-b5e4-4a98-bd8b-a91d7666506e	12000.00	1000.00	20.00	2025-09-23 14:56:32.918389
ee462fe3-7e40-4ab1-8690-6b41f44c4b93	0eaeabf4-730f-4808-b786-c83bf0b0b68a	a3c42595-a2bd-41f3-b477-9978c78222b7	30000.00	20000.00	20.00	2025-09-23 14:59:15.045888
2c3bf303-fd90-4e3d-b46a-6f17bb18524d	0eaeabf4-730f-4808-b786-c83bf0b0b68a	6dd15186-3ec2-4dbf-8d04-d92b2c4e7f18	30000.00	20000.00	20.00	2025-09-23 14:59:15.045893
7dc3935b-04d0-450f-8546-73876aaddca4	0eaeabf4-730f-4808-b786-c83bf0b0b68a	63d1cf00-b5e4-4a98-bd8b-a91d7666506e	30000.00	20000.00	20.00	2025-09-23 14:59:15.045895
fea3823b-9056-49a4-b422-78a10ba1fbfc	0eaeabf4-730f-4808-b786-c83bf0b0b68a	aab1c0be-f0a7-40ee-aa9b-63e7422e2f26	30000.00	20000.00	20.00	2025-09-23 14:59:15.045897
d2c437d0-2c73-4556-9cfd-588a980e2b27	0eaeabf4-730f-4808-b786-c83bf0b0b68a	57784d73-1162-440b-bc1f-52f193bfdb88	30000.00	20000.00	20.00	2025-09-23 14:59:15.0459
\.


--
-- Data for Name: operaciones; Type: TABLE DATA; Schema: public; Owner: cfo_user
--

COPY public.operaciones (id, tipo_operacion, fecha, monto_original, moneda_original, tipo_cambio, monto_uyu, monto_usd, area_id, localidad, descripcion, cliente, proveedor, deleted_at, created_at, updated_at) FROM stdin;
c6669612-53f5-4e26-bf1a-a40ede71db23	INGRESO	2025-09-22	10000.00	USD	41.0500	410500.00	10000.00	11c64c64-c7f6-4e85-9c26-b577c3d7a5b7	MERCEDES	asesoramiento	gandolfo	\N	\N	2025-09-22 14:24:40.845883	2025-09-22 14:24:40.845886
17395a7f-5ce9-4745-a1af-668b87b01c56	RETIRO	2025-09-22	3000.00	UYU	41.0500	3000.00	5000.00	b11006d3-6cfc-4766-9201-ab56274401a6	MERCEDES	fue por la venta. 	\N	\N	\N	2025-09-22 14:37:36.350368	2025-09-22 14:37:36.350371
a50a8961-c3b1-41f0-9fda-0fa8f54dfc33	INGRESO	2025-09-22	35000.00	UYU	41.0500	35000.00	852.62	53ba7821-8836-4e74-ad56-a288d290881d	MONTEVIDEO	escritura	estevez	\N	\N	2025-09-22 15:09:39.467849	2025-09-22 15:09:39.467851
3e473a99-e134-48d3-81a6-c1f61a18ab5a	INGRESO	2025-09-22	100000.00	UYU	41.0500	100000.00	2436.05	651dfb5c-15d8-41e2-8339-785b137f44f2	MONTEVIDEO	HONORARIOS	GANDOLFO	\N	\N	2025-09-22 13:11:09.494025	2025-09-22 12:58:47.675109
b43afc37-5913-4a4e-ac02-dc34962a619b	GASTO	2025-09-22	23000.00	UYU	41.0500	23000.00	560.29	53ba7821-8836-4e74-ad56-a288d290881d	MERCEDES	papeleria	\N	salerno	\N	2025-09-22 14:30:47.74365	2025-09-22 12:58:47.675109
46f00483-f5cc-4411-ba1c-07383c8a0b03	DISTRIBUCION	2025-09-22	150000.00	UYU	41.0500	150000.00	25000.00	b11006d3-6cfc-4766-9201-ab56274401a6	MONTEVIDEO	Distribución de utilidades	\N	\N	2025-09-22 16:48:45.469268	2025-09-22 14:44:53.200225	2025-09-22 16:48:45.470269
d84c6f5d-fa02-4519-bf73-5ff47400669f	GASTO	2025-09-22	35000.00	UYU	41.0500	35000.00	852.62	d3aff49c-748c-4d1d-bc47-cdda1cfb913d	MONTEVIDEO	papeles	\N	gandulia	2025-09-22 17:11:17.387094	2025-09-22 15:10:05.619427	2025-09-22 17:11:17.387433
25be0fa0-9af3-441b-8fa6-d24109177097	INGRESO	2025-09-23	25000.00	USD	40.9500	1023750.00	25000.00	53ba7821-8836-4e74-ad56-a288d290881d	MONTEVIDEO	ASESORAMIENTO	GALPERIN	\N	\N	2025-09-23 14:50:35.845827	2025-09-23 14:50:35.845831
fcad3585-9756-4d2b-a4b9-1eb8dfd105e3	INGRESO	2025-09-23	15000.00	UYU	40.9500	15000.00	366.30	14700c01-3b3d-49c6-8e2e-f3ebded1b1bb	MERCEDES	CONTRATO	LAMELA	\N	\N	2025-09-23 14:51:27.733392	2025-09-23 14:51:27.733396
94cbd8c8-7526-415a-bedc-026ec4a92a27	GASTO	2025-09-23	1200.00	USD	40.9500	49140.00	1200.00	b11006d3-6cfc-4766-9201-ab56274401a6	MERCEDES	SOFTWARE INTERNACIONAL	\N	GENEXUS	\N	2025-09-23 14:52:14.779076	2025-09-23 14:52:14.779078
072bf9a3-fa7e-4d8b-afba-047906c0070d	GASTO	2025-09-23	45000.00	UYU	40.9500	45000.00	1098.90	b11006d3-6cfc-4766-9201-ab56274401a6	MERCEDES	SERVICIOS LOCALES	\N	LIMPIEZA	\N	2025-09-23 14:53:00.066988	2025-09-23 14:53:00.066991
1cdbb1e8-a837-43ab-b932-a5537242ad34	RETIRO	2025-09-23	2000.00	USD	40.9500	81900.00	2000.00	b11006d3-6cfc-4766-9201-ab56274401a6	MONTEVIDEO	POCOS INGRESOS	\N	\N	\N	2025-09-23 14:54:10.753696	2025-09-23 14:54:10.753699
ab7f1e18-8cbd-4b53-9204-9da88141d49b	RETIRO	2025-09-23	10000.00	UYU	40.9500	10000.00	8000.00	b11006d3-6cfc-4766-9201-ab56274401a6	MERCEDES	CESION DE CARTERA	\N	\N	\N	2025-09-23 14:54:48.356591	2025-09-23 14:54:48.356594
c06ee93d-72f8-4346-988f-3ba8f4fe62eb	DISTRIBUCION	2025-09-23	25000.00	UYU	40.9500	25000.00	50000.00	b11006d3-6cfc-4766-9201-ab56274401a6	MONTEVIDEO	Distribución de utilidades	\N	\N	\N	2025-09-23 14:55:52.105841	2025-09-23 14:55:52.105843
db236053-174c-44a4-b558-23486b4cb775	DISTRIBUCION	2025-09-23	36000.00	UYU	40.9500	36000.00	3000.00	b11006d3-6cfc-4766-9201-ab56274401a6	MERCEDES	Distribución de utilidades	\N	\N	\N	2025-09-23 14:56:32.915611	2025-09-23 14:56:32.915614
7747aed0-fad6-44c6-b5a8-ebb022926acb	GASTO	2025-09-23	25000.00	UYU	40.9500	25000.00	610.50	53ba7821-8836-4e74-ad56-a288d290881d	MERCEDES	PAPELERIA	\N	GANDULIA	\N	2025-09-23 14:57:11.467674	2025-09-23 14:57:11.467677
f845b430-c5e1-495f-8a48-32d20b5bf872	INGRESO	2025-09-23	10000.00	USD	40.9500	409500.00	10000.00	11c64c64-c7f6-4e85-9c26-b577c3d7a5b7	MONTEVIDEO	RECUPERACION CON MUCHOS CONTADOS	MERCURIUS	\N	\N	2025-09-23 14:57:46.293479	2025-09-23 14:57:46.293482
37b4ce95-7246-4033-8bb2-06d2bff096ca	RETIRO	2025-09-23	300000.00	UYU	40.9500	300000.00	20000.00	b11006d3-6cfc-4766-9201-ab56274401a6	MERCEDES	\N	\N	\N	\N	2025-09-23 14:58:07.304198	2025-09-23 14:58:07.304202
d960be38-5a40-472c-ad30-72ce91970477	RETIRO	2025-09-23	100000.00	UYU	40.9500	100000.00	25000.00	b11006d3-6cfc-4766-9201-ab56274401a6	MERCEDES	VARIAS ESCRITURAS	\N	\N	\N	2025-09-23 14:58:38.438529	2025-09-23 14:58:38.438531
0eaeabf4-730f-4808-b786-c83bf0b0b68a	DISTRIBUCION	2025-09-23	150000.00	UYU	40.9500	150000.00	100000.00	b11006d3-6cfc-4766-9201-ab56274401a6	MERCEDES	Distribución de utilidades	\N	\N	\N	2025-09-23 14:59:15.042606	2025-09-23 14:59:15.042609
c34fe0a6-573c-4e8b-94c9-04b710c06551	GASTO	2025-09-23	20000.00	USD	41.0500	821000.00	20000.00	11c64c64-c7f6-4e85-9c26-b577c3d7a5b7	MONTEVIDEO	PAPELERIA	\N	GANDULIA	\N	2025-09-23 16:03:35.667041	2025-09-23 16:03:35.667044
382bec38-a479-4c5b-b2a1-8b59a221c8b8	INGRESO	2025-09-23	23000.00	UYU	41.0500	23000.00	560.29	53ba7821-8836-4e74-ad56-a288d290881d	MONTEVIDEO	CONTRATO	ELSO	\N	\N	2025-09-23 18:01:06.238661	2025-09-23 18:01:06.238663
d5c0a394-8cb5-42c2-a7df-d52185709edc	INGRESO	2025-09-23	10000.00	USD	41.0500	410500.00	10000.00	14700c01-3b3d-49c6-8e2e-f3ebded1b1bb	MERCEDES	CONTRATO	GANDOLFO	\N	2025-09-23 18:01:27.955029	2025-09-23 17:50:35.047808	2025-09-23 18:01:27.955971
\.


--
-- Data for Name: proveedores; Type: TABLE DATA; Schema: public; Owner: cfo_user
--

COPY public.proveedores (id, nombre, telefono, activo, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: socios; Type: TABLE DATA; Schema: public; Owner: cfo_user
--

COPY public.socios (id, nombre, porcentaje_participacion, activo, created_at, updated_at) FROM stdin;
a3c42595-a2bd-41f3-b477-9978c78222b7	Agustina	20.00	t	2025-09-21 21:26:46.82288	2025-09-21 21:26:46.822882
6dd15186-3ec2-4dbf-8d04-d92b2c4e7f18	Viviana	20.00	t	2025-09-21 21:26:46.822886	2025-09-21 21:26:46.822886
63d1cf00-b5e4-4a98-bd8b-a91d7666506e	Gonzalo	20.00	t	2025-09-21 21:26:46.822889	2025-09-21 21:26:46.82289
aab1c0be-f0a7-40ee-aa9b-63e7422e2f26	Pancho	20.00	t	2025-09-21 21:26:46.822892	2025-09-21 21:26:46.822893
57784d73-1162-440b-bc1f-52f193bfdb88	Bruno	20.00	t	2025-09-21 21:26:46.822894	2025-09-21 21:26:46.822895
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: cfo_user
--

COPY public.usuarios (id, email, nombre, password_hash, es_socio, activo, created_at, updated_at) FROM stdin;
e85916c0-898a-46e0-84a5-c9c2ff92eaea	agustina@conexion.uy	Agustina	$2b$12$E/5JyqEZlWlBRQ7iRchaY.bImSceuWVRm/GUtcesDB3bsdXX/ef/W	t	t	2025-09-21 21:34:23.904471	2025-09-21 21:34:23.904474
dc3e2ff1-497a-4118-bf41-ba5df8c8cfcc	viviana@conexion.uy	Viviana	$2b$12$.OlyYjka7EPWyKQw2ITAD.QEquKAmqqW2RvV6ZZycdwLaw317cqdO	t	t	2025-09-21 21:34:23.90448	2025-09-21 21:34:23.904481
020b4e8c-8702-4677-b2e8-c162cd06f680	gonzalo@conexion.uy	Gonzalo	$2b$12$YNMMswsAhktzH2/2668Y9eS1MzpXGbji4HOt3Sx7rTEFh37j3j5BW	t	t	2025-09-21 21:34:23.904484	2025-09-21 21:34:23.904484
1ebac58d-c63e-400f-bb74-a2cd3e4386fb	pancho@conexion.uy	Pancho	$2b$12$AWUdEwmH0kw8iFOWbYm03.vvjMHqe9jpP0.KFmBxGf3sgUfkj5jxW	t	t	2025-09-21 21:34:23.904487	2025-09-21 21:34:23.904487
af117d98-782c-457c-a194-1cfddbb60ea0	bruno@conexion.uy	Bruno	$2b$12$Jvxmy.3pDwZfMdDTWHiSMOmQrYndVS4RErzmVOhdQKwERZWABwj8e	t	t	2025-09-21 21:34:23.904489	2025-09-21 21:34:23.90449
d0cdb101-bb6f-4001-8ba3-39707e6b2da9	operador1@conexion.uy	Operador 1	$2b$12$nHiTKBCxwhOhxReXSkVR6./eGiADXX0clijb4C.guePIgLeib1R7i	f	t	2025-09-21 21:34:23.904492	2025-09-21 21:34:23.904492
b2b2fbcf-40b0-42fa-b5bd-a9632431295b	operador2@conexion.uy	Operador 2	$2b$12$/R5y5iNzr5m9yWeJmn.IUuRZx02jwqGzOxhG1xNCtuXu1e68jUm.m	f	t	2025-09-21 21:34:23.904494	2025-09-21 21:34:23.904495
81a4c390-7fa0-48dc-8396-dbc691f55266	operador3@conexion.uy	Operador 3	$2b$12$QTO6ZBJVDO7c2GoB/h3Q/uGS8rGzq1k5mRHrZNEKW3eXZk.QxEGyG	f	t	2025-09-21 21:34:23.904497	2025-09-21 21:34:23.904497
ce49b59a-4d91-4847-b792-920549bd8545	operador4@conexion.uy	Operador 4	$2b$12$e8Dli3PNpLWzErk.XJBXye.8F4Tgca8nLNIlGU4kEUL9YADAy8qpW	f	t	2025-09-21 21:34:23.904499	2025-09-21 21:34:23.9045
b1a5cd26-ee65-423f-96ee-3e12e4044b22	bgandolfo@cgmasociados.com	Bruno Gandolfo	$2b$12$EncpkkO.Xzn3ltVKh7.4Eu5g3uYvwvbuuQTx0pF8fflUDcSFTk6cW	t	t	\N	\N
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: areas areas_nombre_key; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT areas_nombre_key UNIQUE (nombre);


--
-- Name: areas areas_pkey; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT areas_pkey PRIMARY KEY (id);


--
-- Name: clientes clientes_nombre_key; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_nombre_key UNIQUE (nombre);


--
-- Name: clientes clientes_pkey; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_pkey PRIMARY KEY (id);


--
-- Name: distribuciones_detalle distribuciones_detalle_pkey; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.distribuciones_detalle
    ADD CONSTRAINT distribuciones_detalle_pkey PRIMARY KEY (id);


--
-- Name: operaciones operaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.operaciones
    ADD CONSTRAINT operaciones_pkey PRIMARY KEY (id);


--
-- Name: proveedores proveedores_nombre_key; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT proveedores_nombre_key UNIQUE (nombre);


--
-- Name: proveedores proveedores_pkey; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.proveedores
    ADD CONSTRAINT proveedores_pkey PRIMARY KEY (id);


--
-- Name: socios socios_nombre_key; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.socios
    ADD CONSTRAINT socios_nombre_key UNIQUE (nombre);


--
-- Name: socios socios_pkey; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.socios
    ADD CONSTRAINT socios_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: distribuciones_detalle distribuciones_detalle_operacion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.distribuciones_detalle
    ADD CONSTRAINT distribuciones_detalle_operacion_id_fkey FOREIGN KEY (operacion_id) REFERENCES public.operaciones(id);


--
-- Name: distribuciones_detalle distribuciones_detalle_socio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.distribuciones_detalle
    ADD CONSTRAINT distribuciones_detalle_socio_id_fkey FOREIGN KEY (socio_id) REFERENCES public.socios(id);


--
-- Name: operaciones operaciones_area_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cfo_user
--

ALTER TABLE ONLY public.operaciones
    ADD CONSTRAINT operaciones_area_id_fkey FOREIGN KEY (area_id) REFERENCES public.areas(id);


--
-- PostgreSQL database dump complete
--

