import streamlit as st
import pandas as pd
from db import init_db, get_session, User, Availability, Potluck, Wish
import hashlib
import json
import datetime
import random

# Page Config
st.set_page_config(page_title="Reunión Anual", page_icon="🎉", layout="wide")

def load_styles():
    st.markdown("""
    <style>

    /* --- Shared Background & Carousel --- */
    .landing-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -2;
        background-size: cover;
        background-position: center;
        background-color: #2d2a4a; /* Fallback */
        animation: bgCarousel 20s infinite ease-in-out;
    }
    
    @keyframes bgCarousel {
        0% { background-image: url('assets/IMG-20191220-WA0023.jpg'); }
        25% { background-image: url('assets/IMG-20220121-WA0006.jpg'); }
        50% { background-image: url('assets/IMG-20220306-WA0039.jpg'); }
        75% { background-image: url('assets/IMG-20220710-WA0020.jpg'); }
        100% { background-image: url('assets/IMG-20191220-WA0023.jpg'); }
    }

    .landing-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(45, 42, 74, 0.6); /* Slightly darker for text readability */
        z-index: -1;
        backdrop-filter: blur(4px);
    }
    
    /* --- Snow Effect --- */
    .snow {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 100;
        background-image: 
            radial-gradient(4px 4px at 10% 10%, rgba(255,255,255,0.8), transparent),
            radial-gradient(6px 6px at 20% 30%, rgba(255,255,255,0.6), transparent),
            radial-gradient(3px 3px at 40% 70%, rgba(255,255,255,0.9), transparent),
            radial-gradient(4px 4px at 60% 20%, rgba(255,255,255,0.7), transparent),
            radial-gradient(5px 5px at 90% 80%, rgba(255,255,255,0.8), transparent);
        background-size: 200px 200px;
        animation: snowAnim 10s linear infinite;
    }
    
    @keyframes snowAnim {
        from { transform: translateY(0); }
        to { transform: translateY(200px); }
    }
    
    /* --- Card & Mobile First Layout --- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(25, 25, 35, 0.85);
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        margin: 0 auto;
        max-width: 95vw; /* Mobile friendly max width */
    }
    
    @media (min-width: 768px) {
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 2.5rem;
            max-width: 500px; /* Limit width on desktop */
        }
    }

    /* Style inputs inside the dark card */
    .stTextInput label {
        color: #eee !important;
    }
    
    /* Make buttons pop */
    button[kind="primary"] {
        background-color: #c0392b !important; /* Christmas Red style optionally, or stick to purple */
        /* Let's keep purple but maybe a bit more festive? Or Red for Xmas? User said "Navidad" style. */
        /* Let's go with a nice warm red/gold accent or stick to the purple if user prefers. 
           User said "Temática navideña", let's try a festive red. */
        background-color: #D42426 !important;
        border: none;
        font-weight: bold;
        transition: transform 0.1s;
    }
    button[kind="primary"]:hover {
        transform: scale(1.02);
        background-color: #E74C3C !important;
    }
    
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
    }

    </style>
    """, unsafe_allow_html=True)


load_styles()

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.rerun()

# ----------------------------------------
# Page Functions
# ----------------------------------------

def show_profile():
    st.header("📅 Mi Disponibilidad")
    st.write("Indica las fechas en las que puedes asistir a la reunión.")
    
    session = get_session()
    user_id = st.session_state.user_id
    
    # Get existing availability
    avail = session.query(Availability).filter(Availability.user_id == user_id).first()
    
    current_dates = []
    if avail and avail.dates_json:
        try:
            current_dates_str = json.loads(avail.dates_json)
            current_dates = current_dates_str
        except:
            pass

    with st.expander("Géstionar mis fechas", expanded=True):
        new_date = st.date_input("Agregar fecha disponible", min_value=datetime.date.today())
        if st.button("Agregar Fecha", key="add_date"):
            date_str = new_date.strftime("%Y-%m-%d")
            if date_str not in current_dates:
                current_dates.append(date_str)
                current_dates.sort()
                
                if not avail:
                    avail = Availability(user_id=user_id, dates_json=json.dumps(current_dates))
                    session.add(avail)
                else:
                    avail.dates_json = json.dumps(current_dates)
                session.commit()
                st.success(f"Fecha {date_str} agregada.")
                st.rerun()
            else:
                st.warning("Esa fecha ya está en tu lista.")

        st.write("### Tus Fechas Seleccionadas:")
        if current_dates:
            for d in current_dates:
                col1, col2 = st.columns([4, 1])
                col1.write(f"🗓️ {d}")
                if col2.button("🗑️", key=f"del_{d}"):
                    current_dates.remove(d)
                    avail.dates_json = json.dumps(current_dates)
                    session.commit()
                    st.rerun()
        else:
            st.info("No has seleccionado fechas aún.")
    
    # Summary of everyone's availability
    st.divider()
    st.subheader("📊 Disponibilidad del Grupo")
    all_avails = session.query(Availability).all()
    date_counts = {}
    for a in all_avails:
        if a.dates_json:
            try:
                dates = json.loads(a.dates_json)
                for d in dates:
                    date_counts[d] = date_counts.get(d, 0) + 1
            except:
                pass
    
    if date_counts:
        df = pd.DataFrame(list(date_counts.items()), columns=["Fecha", "Coincidencias"])
        df = df.sort_values(by="Coincidencias", ascending=False)
        st.dataframe(df, hide_index=True)
    
    session.close()

def show_potluck():
    st.header("🍲 Potluck: ¿Qué llevamos?")
    st.write("Propón 3 opciones de platillos. El sistema o el admin ayudarán a asignar para no repetir.")
    
    session = get_session()
    user_id = st.session_state.user_id
    
    potluck = session.query(Potluck).filter(Potluck.user_id == user_id).first()
    
    with st.form("potluck_form"):
        d1 = st.text_input("Opción 1 (Tu favorita)", value=potluck.dish_1 if potluck else "")
        d2 = st.text_input("Opción 2", value=potluck.dish_2 if potluck else "")
        d3 = st.text_input("Opción 3", value=potluck.dish_3 if potluck else "")
        
        submitted = st.form_submit_button("Guardar Opciones")
        if submitted:
            if not potluck:
                potluck = Potluck(user_id=user_id)
                session.add(potluck)
            potluck.dish_1 = d1
            potluck.dish_2 = d2
            potluck.dish_3 = d3
            session.commit()
            st.success("Opciones guardadas.")
            st.rerun()
    
    if potluck and potluck.assigned_dish:
        st.success(f"✅ ¡Se te ha asignado: **{potluck.assigned_dish}**!")
    else:
        st.info("Aún no se te asigna un platillo definitivo.")

    st.divider()
    st.subheader("👀 Qué propusieron los demás")
    all_potlucks = session.query(Potluck).join(User).all()
    
    potluck_data = []
    for p in all_potlucks:
        potluck_data.append({
            "Amigo": p.user.name or p.user.username,
            "Opción 1": p.dish_1,
            "Opción 2": p.dish_2,
            "Opción 3": p.dish_3,
            "Asignado": p.assigned_dish or "Pendiente"
        })
    
    if potluck_data:
        st.dataframe(pd.DataFrame(potluck_data))
        
        if st.button("🧙 Auto-Asignar (Beta)"):
            assigned_so_far = set()
            all_ps = session.query(Potluck).all()
            for p in all_ps:
                if p.dish_1 and p.dish_1 not in assigned_so_far:
                    p.assigned_dish = p.dish_1
                    assigned_so_far.add(p.dish_1)
                elif p.dish_2 and p.dish_2 not in assigned_so_far:
                    p.assigned_dish = p.dish_2
                    assigned_so_far.add(p.dish_2)
                elif p.dish_3 and p.dish_3 not in assigned_so_far:
                    p.assigned_dish = p.dish_3
                    assigned_so_far.add(p.dish_3)
                else:
                    p.assigned_dish = "CONFLICTO: Hablar con Admin"
            session.commit()
            st.success("Asignación automática completada.")
            st.rerun()

    session.close()

def show_secretsanta():
    st.header("🎁 Mercado de Regalos (Secret Santa)")
    st.markdown("""
    **Cómo funciona:**
    1. Escribe 5 deseos o ideas de regalos.
    2. Ve al "Mercado" y escoge un regalo que quieras comprar para alguien (¡es anónimo!).
    3. Una vez que escojas, te comprometes a comprarlo.
    """)
    
    session = get_session()
    user_id = st.session_state.user_id
    
    # 1. My Wishes
    st.subheader("1. Mis Deseos")
    my_wishes = session.query(Wish).filter(Wish.user_id == user_id).all()
    
    c1, c2 = st.columns([3, 1])
    new_wish_desc = c1.text_input("Agregar un deseo/idea", key="new_wish")
    if c2.button("Agregar Deseo"):
        if len(my_wishes) >= 5:
            st.error("Máximo 5 deseos.")
        elif new_wish_desc:
            w = Wish(user_id=user_id, description=new_wish_desc)
            session.add(w)
            session.commit()
            st.rerun()
    
    if my_wishes:
        for w in my_wishes:
            st.text(f"- {w.description}")
            
    st.divider()
    
    # 2. Market
    st.subheader("2. Mercado de Regalos (Claim)")
    
    available_wishes = session.query(Wish).filter(Wish.user_id != user_id, Wish.claimed_by_id == None).all()
    my_claims = session.query(Wish).filter(Wish.claimed_by_id == user_id).all()
    
    if my_claims:
        st.success(f"🎁 Ya has escogido {len(my_claims)} regalo(s) para comprar:")
        for c in my_claims:
            st.info(f"🎁 **{c.description}**\n\n🏷️ **Etiqueta el regalo con el ID: #{c.id}** (¡No pongas el nombre del destinatario, solo este número!)")
            if st.button(f"Soltar #{c.id}", key=f"release_{c.id}"):
                c.claimed_by_id = None
                session.commit()
                st.rerun()
    
    st.write("### Regalos disponibles para escoger:")
    if available_wishes:
        display_wishes = list(available_wishes)
        random.shuffle(display_wishes)
        
        for w in display_wishes:
            col1, col2 = st.columns([4, 1])
            col1.write(f"❓ {w.description}")
            if col2.button("✋ Yo lo compro", key=f"claim_{w.id}"):
                w.claimed_by_id = user_id
                session.commit()
                st.balloons()
                st.rerun()
    else:
        st.warning("No hay más regalos disponibles para escoger (o son tuyos).")
    
    session.close()

def login_page():
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'landing'

    # Background and Snow
    st.markdown("""
        <div class="landing-bg"></div>
        <div class="landing-overlay"></div>
        <div class="snow"></div>
    """, unsafe_allow_html=True)
    
    # ------------------
    # LANDING VIEW
    # ------------------
    if st.session_state.auth_mode == 'landing':
        st.markdown("""
            <div class="landing-container">
            </div>
            <style>
            [data-testid="stHeader"] {display: none;}
            .block-container {padding-top: 0; padding-bottom: 0;}
            </style>
        """, unsafe_allow_html=True)
        
        # Center Content
        # Mobile-First: We use columns, but on mobile columns stack. 
        # To ensure centering on desktop, we use [1,2,1] and put content in middle.
        # On mobile, the middle column will just take width (if we handle it right).
        
        col1, col2, col3 = st.columns([1, 6, 1]) # Wider center for mobile by default? No, layout="wide" might stretch it.
        # Better: Use [1, 1, 1] but with max-width CSS on the container (already added).
        
        c1, c2, c3 = st.columns([1, 10, 1]) # Use almost full width, let CSS constrain max-width
        
        with c2:
             # Spacer
            st.markdown("<div style='height: 25vh;'></div>", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown("<h1 style='text-align: center; color: white;'>🎄 Reunión Anual 2025 🎅</h1>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #eee; margin-bottom: 25px; font-size: 1.1rem;'>🎁 Intercambio · 🍲 Cena · 🎉 Fiesta</p>", unsafe_allow_html=True)
                
                b1, b2 = st.columns(2)
                if b1.button("Iniciar Sesión", use_container_width=True, type="primary"):
                    st.session_state.auth_mode = 'login'
                    st.rerun()
                if b2.button("Registrarse", use_container_width=True):
                    st.session_state.auth_mode = 'register'
                    st.rerun()

    # ------------------
    # LOGIN VIEW
    # ------------------
    elif st.session_state.auth_mode == 'login':
        c1, c2, c3 = st.columns([1, 10, 1])
        with c2:
            st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.subheader("Iniciar Sesión")
                username = st.text_input("Usuario", key="login_user")
                password = st.text_input("Contraseña", type="password", key="login_pass")
                
                if st.button("Entrar", type="primary", use_container_width=True):
                    session = get_session()
                    user = session.query(User).filter(User.username == username).first()
                    if user and user.password_hash == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.user_id = user.id
                        st.session_state.username = user.username
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
                    session.close()
                
                if st.button("⬅️ Volver", use_container_width=True):
                    st.session_state.auth_mode = 'landing'
                    st.rerun()

    # ------------------
    # REGISTER VIEW
    # ------------------
    elif st.session_state.auth_mode == 'register':
        c1, c2, c3 = st.columns([1, 10, 1])
        with c2:
            st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.subheader("Registrarse")
                new_user = st.text_input("Nuevo Usuario", key="reg_user")
                new_name = st.text_input("Nombre Completo", key="reg_name")
                new_pass = st.text_input("Contraseña", type="password", key="reg_pass")
                
                if st.button("Registrarme", type="primary", use_container_width=True):
                    session = get_session()
                    if session.query(User).filter(User.username == new_user).first():
                        st.error("Ese usuario ya existe")
                    else:
                        u = User(username=new_user, password_hash=hash_password(new_pass), name=new_name)
                        session.add(u)
                        session.commit()
                        st.success("Registro exitoso.")
                        st.session_state.auth_mode = 'login'
                        st.rerun()
                    session.close()

                if st.button("⬅️ Volver", use_container_width=True):
                    st.session_state.auth_mode = 'landing'
                    st.rerun()


# ----------------------------------------
# Main Execution Flow
# ----------------------------------------

try:
    init_db()
except Exception as e:
    print(f"DB Init failed: {e}")
    pass

if not st.session_state.logged_in:
    login_page()
else:
    # Sidebar Greeting
    with st.sidebar:
        st.title(f"Hola, {st.session_state.username} 👋")

    # Multipage Navigation
    pg = st.navigation([
        st.Page(show_profile, title="Mi Perfil", icon="👤"),
        st.Page(show_potluck, title="Comida (Potluck)", icon="🍲"),
        st.Page(show_secretsanta, title="Intercambio (Secret Santa)", icon="🎁"),
        st.Page(logout, title="Cerrar Sesión", icon="🚪"),
    ])
    pg.run()
