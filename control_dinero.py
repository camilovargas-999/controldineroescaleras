import streamlit as st
import pandas as pd
from datetime import datetime, date
import json

st.set_page_config(
    page_title="Escaleras La Esperanza",
    page_icon="🏗️",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

    .stApp { background-color: #0f1117; }

    .card {
        background: #1a1d27;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2a2d3a;
        margin-bottom: 12px;
    }
    .card-green  { border-left: 4px solid #00c9a7; }
    .card-blue   { border-left: 4px solid #4f8ef7; }
    .card-orange { border-left: 4px solid #f7954f; }
    .card-red    { border-left: 4px solid #f74f4f; }
    .card-purple { border-left: 4px solid #a07cf7; }

    .big-number {
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #fff;
    }
    .label { color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
    .green  { color: #00c9a7 !important; }
    .red    { color: #f74f4f !important; }
    .orange { color: #f7954f !important; }
    .blue   { color: #4f8ef7 !important; }

    div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif; font-size: 1.6rem; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    section[data-testid="stSidebar"] {
        background: #13151f;
        border-right: 1px solid #2a2d3a;
    }
    .sidebar-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.2rem;
        font-weight: 800;
        color: #00c9a7;
        padding: 8px 0 16px 0;
    }
    .semana-badge {
        background: #00c9a720;
        border: 1px solid #00c9a740;
        border-radius: 20px;
        padding: 4px 12px;
        color: #00c9a7;
        font-size: 0.75rem;
        display: inline-block;
        margin-bottom: 12px;
    }
    hr.divider { border-color: #2a2d3a; margin: 16px 0; }
</style>
""", unsafe_allow_html=True)

# ─── ESTADO INICIAL ──────────────────────────────────────────────────────────
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
BILLETES = [100000, 50000, 20000, 10000, 5000, 2000, 1000, 500]

TRABAJADORES_DEFAULT = [
    {"nombre": "Jaime",         "tarifa": 90000},
    {"nombre": "Sebastián",     "tarifa": 85000},
    {"nombre": "Nicolás",       "tarifa": 85000},
    {"nombre": "Jefer",         "tarifa": 85000},
    {"nombre": "Ander",         "tarifa": 85000},
    {"nombre": "Yulian",        "tarifa": 85000},
    {"nombre": "Leandro",       "tarifa": 70000},
    {"nombre": "Abraham",       "tarifa": 60000},
    {"nombre": "Camioneta Gris","tarifa": 0},
    {"nombre": "Camioneta Furgón","tarifa": 0},
]

def init_state():
    semana = datetime.now().strftime("Semana %W - %Y")

    if 'semana_label' not in st.session_state:
        st.session_state['semana_label'] = semana

    # Producción: {dia: [{nombre, valor}, {nombre, valor}, {nombre, valor}]}
    if 'produccion' not in st.session_state:
        st.session_state['produccion'] = {d: [{"nombre": "", "valor": 0.0} for _ in range(3)] for d in DIAS}
    if 'produccion_proxima' not in st.session_state:
        st.session_state['produccion_proxima'] = {d: [{"nombre": "", "valor": 0.0} for _ in range(3)] for d in DIAS}
    if 'pendientes' not in st.session_state:
        st.session_state['pendientes'] = []

    # Caja: {dia: [{concepto, entrada, salida}]}
    if 'caja' not in st.session_state:
        st.session_state['caja'] = {d: [] for d in DIAS}
    if 'saldo_inicio' not in st.session_state:
        st.session_state['saldo_inicio'] = {d: 0.0 for d in DIAS}

    # Calculadora billetes
    if 'billetes' not in st.session_state:
        st.session_state['billetes'] = {b: 0 for b in BILLETES}
    if 'bancos' not in st.session_state:
        st.session_state['bancos'] = 0.0
    if 'apps' not in st.session_state:
        st.session_state['apps'] = 0.0
    if 'otros_efectivo' not in st.session_state:
        st.session_state['otros_efectivo'] = 0.0

    # Salarios
    if 'trabajadores' not in st.session_state:
        st.session_state['trabajadores'] = [
            {**t, "dias": {d: False for d in DIAS}, "incentivos": 0.0, "adelantos": 0.0, "almuerzos": 0}
            for t in TRABAJADORES_DEFAULT
        ]
    if 'deudas' not in st.session_state:
        st.session_state['deudas'] = []

    # Ahorro
    if 'ahorro_meta' not in st.session_state:
        st.session_state['ahorro_meta'] = 0.0
    if 'ahorro_movimientos' not in st.session_state:
        st.session_state['ahorro_movimientos'] = []

    # Meta semana
    if 'meta_semana' not in st.session_state:
        st.session_state['meta_semana'] = 0.0

    if 'costo_almuerzo' not in st.session_state:
        st.session_state['costo_almuerzo'] = 15000.0

def fmt(v):
    return "COP {:,.0f}".format(v).replace(",", ".")

def total_produccion(prod_dict):
    return sum(1 for d in prod_dict.values() for e in d if e.get('nombre', '').strip())

def total_valor_produccion(prod_dict):
    return sum(e.get('valor', 0) for d in prod_dict.values() for e in d)

def total_caja_entradas():
    total = 0
    for d in DIAS:
        for mov in st.session_state.caja[d]:
            total += mov.get('entrada', 0)
    return total

def total_caja_salidas():
    total = 0
    for d in DIAS:
        for mov in st.session_state.caja[d]:
            total += mov.get('salida', 0)
    return total

def saldo_final_dia(dia):
    idx = DIAS.index(dia)
    if idx == 0:
        saldo = st.session_state.saldo_inicio.get(dia, 0)
    else:
        saldo = saldo_final_dia(DIAS[idx - 1])
    for mov in st.session_state.caja[dia]:
        saldo += mov.get('entrada', 0) - mov.get('salida', 0)
    return saldo

def total_salarios():
    total = 0
    for t in st.session_state.trabajadores:
        dias_trabajados = sum(1 for v in t['dias'].values() if v)
        total += dias_trabajados * t['tarifa'] + t.get('incentivos', 0) - t.get('adelantos', 0)
    return total

def total_ahorro():
    return sum(m['valor'] for m in st.session_state.ahorro_movimientos if m['tipo'] == 'Depósito') \
         - sum(m['valor'] for m in st.session_state.ahorro_movimientos if m['tipo'] == 'Retiro')

# ─── INICIALIZAR ─────────────────────────────────────────────────────────────
init_state()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="sidebar-title">🏗️ La Esperanza</div>', unsafe_allow_html=True)
semana_label = st.sidebar.text_input("Semana", value=st.session_state['semana_label'])
st.session_state['semana_label'] = semana_label

pestana = st.sidebar.radio("", [
    "📊 Resumen General",
    "🏭 Producción",
    "💵 Caja Diaria",
    "💴 Calculadora Efectivo",
    "👷 Salarios",
    "💰 Ahorro",
])

st.sidebar.markdown("<hr class='divider'>", unsafe_allow_html=True)
st.sidebar.markdown(f"<div class='label'>Semana activa</div>", unsafe_allow_html=True)
st.sidebar.markdown(f"<div class='semana-badge'>📅 {semana_label}</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
#  1. RESUMEN GENERAL
# ════════════════════════════════════════════════════════════════
if pestana == "📊 Resumen General":
    st.markdown(f"# 📊 Resumen General")
    st.markdown(f"<div class='semana-badge'>📅 {semana_label}</div>", unsafe_allow_html=True)

    meta = st.number_input("🎯 Meta de ingresos de la semana (COP)", value=float(st.session_state['meta_semana']),
                           step=100000.0, format="%.0f")
    st.session_state['meta_semana'] = meta

    st.markdown("---")

    ingresos   = total_caja_entradas()
    gastos     = total_caja_salidas()
    salarios   = total_salarios()
    escaleras  = total_produccion(st.session_state['produccion'])
    ahorro_act = total_ahorro()
    balance    = ingresos - gastos - salarios

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💵 Ingresos semana",   fmt(ingresos))
    c2.metric("📤 Gastos semana",     fmt(gastos + salarios))
    c3.metric("📦 Escaleras producidas", escaleras)
    c4.metric("💰 Ahorro acumulado",  fmt(ahorro_act))

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="card card-green">', unsafe_allow_html=True)
        st.markdown(f"<div class='label'>Balance neto de la semana</div>", unsafe_allow_html=True)
        color = "green" if balance >= 0 else "red"
        st.markdown(f"<div class='big-number {color}'>{fmt(balance)}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if meta > 0:
            pct = min(ingresos / meta * 100, 100)
            st.markdown(f"**🎯 Cumplimiento:** {pct:.1f}% de {fmt(meta)}")
            st.progress(int(pct))

    with col_b:
        st.markdown('<div class="card card-blue">', unsafe_allow_html=True)
        st.markdown("<div class='label'>Desglose de egresos</div>", unsafe_allow_html=True)
        st.markdown(f"• Gastos operativos: **{fmt(gastos)}**")
        st.markdown(f"• Salarios: **{fmt(salarios)}**")
        st.markdown(f"• **Total egresos: {fmt(gastos + salarios)}**")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Producción por día
    st.subheader("📦 Producción diaria")
    prod_data = []
    for d in DIAS:
        escaleras = st.session_state['produccion'][d]
        nombres = [e['nombre'] for e in escaleras if e.get('nombre','').strip()]
        valor_dia = sum(e.get('valor', 0) for e in escaleras)
        prod_data.append({
            "Día": d,
            "Escaleras": ", ".join(nombres) if nombres else "—",
            "Cantidad": len(nombres),
            "Valor total": fmt(valor_dia)
        })
    st.dataframe(pd.DataFrame(prod_data), use_container_width=True, hide_index=True)

    # Caja resumen por día
    st.subheader("💵 Caja por día")
    caja_data = []
    for d in DIAS:
        ent = sum(m.get('entrada', 0) for m in st.session_state.caja[d])
        sal = sum(m.get('salida', 0) for m in st.session_state.caja[d])
        saldo = saldo_final_dia(d)
        caja_data.append({"Día": d, "Entradas": fmt(ent), "Salidas": fmt(sal), "Saldo final": fmt(saldo)})
    st.dataframe(pd.DataFrame(caja_data), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════
#  2. PRODUCCIÓN
# ════════════════════════════════════════════════════════════════
elif pestana == "🏭 Producción":
    st.markdown("# 🏭 Producción de Escaleras")
    st.markdown(f"<div class='semana-badge'>📅 {semana_label}</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📅 Semana Actual", "📅 Próxima Semana", "📋 Pendientes"])

    for tab, key, label in [
        (tab1, 'produccion', 'Semana actual'),
        (tab2, 'produccion_proxima', 'Próxima semana')
    ]:
        with tab:
            st.markdown(f"#### {label}")
            total_sem = 0
            total_valor_sem = 0.0

            for dia in DIAS:
                st.markdown(f"**{dia}**")
                # 3 escaleras × 2 campos (nombre + valor) = 6 recuadros por día
                cols = st.columns(7)  # 3 pares + 1 columna de resumen
                dia_cantidad = 0
                dia_valor = 0.0

                for i in range(3):
                    escalera = st.session_state[key][dia][i]
                    with cols[i * 2]:
                        nombre = st.text_input(
                            f"Escalera {i+1} — Nombre",
                            value=escalera.get('nombre', ''),
                            placeholder=f"Ej: Recta 3m",
                            key=f"{key}_{dia}_nombre_{i}"
                        )
                        st.session_state[key][dia][i]['nombre'] = nombre
                    with cols[i * 2 + 1]:
                        valor = st.number_input(
                            f"Valor (COP)",
                            value=float(escalera.get('valor', 0.0)),
                            min_value=0.0, step=10000.0, format="%.0f",
                            key=f"{key}_{dia}_valor_{i}"
                        )
                        st.session_state[key][dia][i]['valor'] = valor
                    if nombre.strip():
                        dia_cantidad += 1
                        dia_valor += valor

                with cols[6]:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.metric("Subtotal", fmt(dia_valor))
                    st.caption(f"{dia_cantidad} escalera{'s' if dia_cantidad != 1 else ''}")

                total_sem      += dia_cantidad
                total_valor_sem += dia_valor
                st.markdown("<hr class='divider'>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            c1.markdown(
                f"<div class='card card-green'><div class='label'>Escaleras {label}</div>"
                f"<div class='big-number green'>{total_sem} escaleras</div></div>",
                unsafe_allow_html=True
            )
            c2.markdown(
                f"<div class='card card-blue'><div class='label'>Valor total {label}</div>"
                f"<div class='big-number blue'>{fmt(total_valor_sem)}</div></div>",
                unsafe_allow_html=True
            )

    with tab3:
        st.markdown("#### 📋 Escaleras Pendientes")
        nueva = st.text_input("Agregar pendiente (descripción)")
        if st.button("➕ Agregar") and nueva.strip():
            st.session_state['pendientes'].append({"desc": nueva, "done": False})
            st.rerun()

        for i, p in enumerate(st.session_state['pendientes']):
            col1, col2 = st.columns([5, 1])
            with col1:
                done = st.checkbox(p['desc'], value=p['done'], key=f"pend_{i}")
                st.session_state['pendientes'][i]['done'] = done
            with col2:
                if st.button("🗑️", key=f"del_pend_{i}"):
                    st.session_state['pendientes'].pop(i)
                    st.rerun()

        pendientes_activos = sum(1 for p in st.session_state['pendientes'] if not p['done'])
        st.info(f"📌 {pendientes_activos} pendientes sin completar")

# ════════════════════════════════════════════════════════════════
#  3. CAJA DIARIA
# ════════════════════════════════════════════════════════════════
elif pestana == "💵 Caja Diaria":
    st.markdown("# 💵 Caja Diaria")
    st.markdown(f"<div class='semana-badge'>📅 {semana_label}</div>", unsafe_allow_html=True)

    dia_sel = st.selectbox("Seleccionar día", DIAS)

    col_si, _ = st.columns([1, 3])
    with col_si:
        if DIAS.index(dia_sel) == 0:
            saldo_ini = st.number_input(
                "Saldo inicio del lunes (COP)",
                value=float(st.session_state['saldo_inicio'].get(dia_sel, 0)),
                step=1000.0, format="%.0f"
            )
            st.session_state['saldo_inicio'][dia_sel] = saldo_ini
        else:
            dia_ant = DIAS[DIAS.index(dia_sel) - 1]
            saldo_ini = saldo_final_dia(dia_ant)
            st.metric("Saldo inicio (del día anterior)", fmt(saldo_ini))

    st.markdown("---")

    # Agregar movimiento
    st.markdown("#### ➕ Agregar movimiento")
    with st.form(f"form_caja_{dia_sel}"):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            concepto = st.text_input("Concepto")
        with fc2:
            entrada = st.number_input("Entrada (COP)", min_value=0.0, step=1000.0, format="%.0f")
        with fc3:
            salida = st.number_input("Salida (COP)", min_value=0.0, step=1000.0, format="%.0f")
        if st.form_submit_button("✅ Registrar"):
            if concepto.strip():
                st.session_state['caja'][dia_sel].append({
                    "concepto": concepto,
                    "entrada": entrada,
                    "salida": salida
                })
                st.rerun()

    # Tabla de movimientos
    movs = st.session_state['caja'][dia_sel]
    if movs:
        st.markdown(f"#### 📋 Movimientos del {dia_sel}")
        df_movs = pd.DataFrame(movs)
        df_display = df_movs.copy()
        df_display['entrada'] = df_display['entrada'].apply(fmt)
        df_display['salida']  = df_display['salida'].apply(fmt)
        df_display.columns    = ['Concepto', 'Entrada', 'Salida']
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        ent_total = sum(m.get('entrada', 0) for m in movs)
        sal_total = sum(m.get('salida', 0) for m in movs)
        saldo_f   = saldo_final_dia(dia_sel)

        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Total Entradas", fmt(ent_total))
        c2.metric("📤 Total Salidas",  fmt(sal_total))
        c3.metric("💼 Saldo Final",    fmt(saldo_f))

        # Botón eliminar último
        if st.button("🗑️ Eliminar último movimiento"):
            st.session_state['caja'][dia_sel].pop()
            st.rerun()
    else:
        st.info(f"No hay movimientos registrados para el {dia_sel}.")

# ════════════════════════════════════════════════════════════════
#  4. CALCULADORA EFECTIVO
# ════════════════════════════════════════════════════════════════
elif pestana == "💴 Calculadora Efectivo":
    st.markdown("# 💴 Calculadora de Efectivo")
    st.markdown("Cuenta tus billetes y calcula el total disponible.")
    st.markdown("---")

    st.markdown("#### 💵 Billetes en caja")
    total_efectivo = 0
    cols = st.columns(4)
    for i, billete in enumerate(BILLETES):
        with cols[i % 4]:
            cant = st.number_input(
                f"$ {fmt(billete)}",
                value=int(st.session_state['billetes'].get(billete, 0)),
                min_value=0, step=1,
                key=f"billete_{billete}"
            )
            st.session_state['billetes'][billete] = cant
            subtotal = cant * billete
            total_efectivo += subtotal
            if cant > 0:
                st.caption(f"= {fmt(subtotal)}")

    st.markdown("---")
    st.markdown("#### 🏦 Otros fondos")
    c1, c2, c3 = st.columns(3)
    with c1:
        bancos = st.number_input("Bancos (COP)", value=float(st.session_state['bancos']),
                                  step=1000.0, format="%.0f")
        st.session_state['bancos'] = bancos
    with c2:
        apps = st.number_input("Apps / Nequi / Daviplata (COP)", value=float(st.session_state['apps']),
                                step=1000.0, format="%.0f")
        st.session_state['apps'] = apps
    with c3:
        otros = st.number_input("Otros (COP)", value=float(st.session_state['otros_efectivo']),
                                 step=1000.0, format="%.0f")
        st.session_state['otros_efectivo'] = otros

    st.markdown("---")
    gran_total = total_efectivo + bancos + apps + otros

    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.metric("💵 Efectivo",  fmt(total_efectivo))
    cc2.metric("🏦 Bancos",    fmt(bancos))
    cc3.metric("📱 Apps",      fmt(apps))
    cc4.metric("💰 TOTAL",     fmt(gran_total))

    st.markdown(
        f"<div class='card card-green'><div class='label'>Total disponible</div>"
        f"<div class='big-number green'>{fmt(gran_total)}</div></div>",
        unsafe_allow_html=True
    )

    # Tabla resumen billetes
    if any(v > 0 for v in st.session_state['billetes'].values()):
        st.markdown("#### 📊 Resumen de billetes")
        bill_data = [
            {"Billete": fmt(b), "Cantidad": st.session_state['billetes'][b],
             "Subtotal": fmt(st.session_state['billetes'][b] * b)}
            for b in BILLETES if st.session_state['billetes'][b] > 0
        ]
        st.dataframe(pd.DataFrame(bill_data), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════
#  5. SALARIOS
# ════════════════════════════════════════════════════════════════
elif pestana == "👷 Salarios":
    st.markdown("# 👷 Control de Salarios")
    st.markdown(f"<div class='semana-badge'>📅 {semana_label}</div>", unsafe_allow_html=True)

    tab_sal, tab_deudas = st.tabs(["💳 Salarios", "📋 Deudas / Adelantos"])

    with tab_sal:
        costo_alm = st.number_input("Costo almuerzo por día (COP)",
                                     value=float(st.session_state['costo_almuerzo']),
                                     step=500.0, format="%.0f")
        st.session_state['costo_almuerzo'] = costo_alm

        st.markdown("---")
        total_pagar = 0
        total_pagar_alm = 0

        for i, t in enumerate(st.session_state['trabajadores']):
            with st.expander(f"👷 {t['nombre']} — Tarifa: {fmt(t['tarifa'])}/día"):
                st.markdown("**Días trabajados:**")
                dias_cols = st.columns(6)
                dias_trabajados = 0
                for j, dia in enumerate(DIAS):
                    with dias_cols[j]:
                        trabajó = st.checkbox(dia[:3], value=t['dias'].get(dia, False),
                                              key=f"sal_{i}_{dia}")
                        st.session_state['trabajadores'][i]['dias'][dia] = trabajó
                        if trabajó:
                            dias_trabajados += 1

                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    inc = st.number_input("Incentivos", value=float(t.get('incentivos', 0)),
                                          step=1000.0, format="%.0f", key=f"inc_{i}")
                    st.session_state['trabajadores'][i]['incentivos'] = inc
                with ec2:
                    ade = st.number_input("Adelantos", value=float(t.get('adelantos', 0)),
                                          step=1000.0, format="%.0f", key=f"ade_{i}")
                    st.session_state['trabajadores'][i]['adelantos'] = ade
                with ec3:
                    alm = st.number_input("Almuerzos (días)", value=int(t.get('almuerzos', 0)),
                                          step=1, min_value=0, key=f"alm_{i}")
                    st.session_state['trabajadores'][i]['almuerzos'] = alm

                base        = dias_trabajados * t['tarifa']
                a_pagar     = base + inc - ade
                a_pagar_alm = a_pagar - (alm * costo_alm)
                total_pagar     += a_pagar
                total_pagar_alm += a_pagar_alm

                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Días trabajados", dias_trabajados)
                sc2.metric("A pagar",         fmt(a_pagar))
                sc3.metric("Con almuerzos",   fmt(a_pagar_alm))

        st.markdown("---")
        t1, t2 = st.columns(2)
        t1.metric("💳 Total a pagar", fmt(total_pagar))
        t2.metric("🍽️ Total con almuerzos", fmt(total_pagar_alm))

    with tab_deudas:
        st.markdown("#### 📋 Registro de deudas y adelantos")
        with st.form("form_deuda"):
            d1, d2, d3, d4 = st.columns(4)
            with d1:
                trab_sel = st.selectbox("Trabajador", [t['nombre'] for t in st.session_state['trabajadores']])
            with d2:
                tipo_deuda = st.selectbox("Tipo", ["Adelanto", "Deuda"])
            with d3:
                val_deuda = st.number_input("Valor (COP)", min_value=0.0, step=1000.0, format="%.0f")
            with d4:
                fecha_deuda = st.date_input("Fecha", value=date.today())
            if st.form_submit_button("➕ Registrar"):
                st.session_state['deudas'].append({
                    "trabajador": trab_sel,
                    "tipo": tipo_deuda,
                    "valor": val_deuda,
                    "fecha": str(fecha_deuda),
                    "pagado": False
                })
                st.rerun()

        if st.session_state['deudas']:
            for i, d in enumerate(st.session_state['deudas']):
                col1, col2 = st.columns([5, 1])
                with col1:
                    pagado = st.checkbox(
                        f"{'✅' if d['pagado'] else '⏳'} {d['trabajador']} — {d['tipo']}: {fmt(d['valor'])} ({d['fecha']})",
                        value=d['pagado'], key=f"deuda_{i}"
                    )
                    st.session_state['deudas'][i]['pagado'] = pagado
                with col2:
                    if st.button("🗑️", key=f"del_deuda_{i}"):
                        st.session_state['deudas'].pop(i)
                        st.rerun()
        else:
            st.info("No hay deudas registradas.")

# ════════════════════════════════════════════════════════════════
#  6. AHORRO
# ════════════════════════════════════════════════════════════════
elif pestana == "💰 Ahorro":
    st.markdown("# 💰 Control de Ahorro")
    st.markdown("Registra depósitos y retiros de tu fondo de ahorro.")
    st.markdown("---")

    meta_ahorro = st.number_input(
        "🎯 Meta de ahorro (COP)",
        value=float(st.session_state['ahorro_meta']),
        step=100000.0, format="%.0f"
    )
    st.session_state['ahorro_meta'] = meta_ahorro

    saldo_ahorro = total_ahorro()

    a1, a2, a3 = st.columns(3)
    a1.metric("💰 Saldo actual",  fmt(saldo_ahorro))
    a2.metric("🎯 Meta",          fmt(meta_ahorro))
    if meta_ahorro > 0:
        pct_ahorro = min(saldo_ahorro / meta_ahorro * 100, 100)
        a3.metric("📊 Avance", f"{pct_ahorro:.1f}%")
        st.progress(int(pct_ahorro))
    else:
        a3.metric("📊 Avance", "—")

    st.markdown("---")

    # Agregar movimiento
    st.markdown("#### ➕ Nuevo movimiento")
    with st.form("form_ahorro"):
        fa1, fa2, fa3, fa4 = st.columns(4)
        with fa1:
            tipo_mov = st.selectbox("Tipo", ["Depósito", "Retiro"])
        with fa2:
            val_mov = st.number_input("Valor (COP)", min_value=0.0, step=10000.0, format="%.0f")
        with fa3:
            fecha_mov = st.date_input("Fecha", value=date.today())
        with fa4:
            desc_mov = st.text_input("Descripción")
        if st.form_submit_button("✅ Registrar"):
            if val_mov > 0:
                st.session_state['ahorro_movimientos'].append({
                    "tipo": tipo_mov,
                    "valor": val_mov,
                    "fecha": str(fecha_mov),
                    "desc": desc_mov
                })
                st.rerun()

    # Historial
    if st.session_state['ahorro_movimientos']:
        st.markdown("#### 📋 Historial de movimientos")
        df_ah = pd.DataFrame(st.session_state['ahorro_movimientos'])
        df_ah['valor'] = df_ah['valor'].apply(fmt)
        df_ah.columns = ['Tipo', 'Valor', 'Fecha', 'Descripción']
        st.dataframe(df_ah, use_container_width=True, hide_index=True)

        if st.button("🗑️ Eliminar último"):
            st.session_state['ahorro_movimientos'].pop()
            st.rerun()

        # Totales
        dep = sum(m['valor'] for m in st.session_state['ahorro_movimientos'] if m['tipo'] == 'Depósito')
        ret = sum(m['valor'] for m in st.session_state['ahorro_movimientos'] if m['tipo'] == 'Retiro')
        st.markdown(f"• Total depositado: **{fmt(dep)}** &nbsp;|&nbsp; Total retirado: **{fmt(ret)}**")
    else:
        st.info("No hay movimientos de ahorro registrados.")

    st.markdown("---")
    st.markdown(
        f"<div class='card card-purple'><div class='label'>Saldo de ahorro</div>"
        f"<div class='big-number'>{fmt(saldo_ahorro)}</div></div>",
        unsafe_allow_html=True
    )
