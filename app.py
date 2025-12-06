import streamlit as st
import pandas as pd
from db import init_db, get_session, User, Availability, Potluck, Wish
import hashlib

# Page Config
st.set_page_config(page_title="Reunión Anual", page_icon="🎉", layout="wide")

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    st.title("Bienvenido a la Reunión Anual 🎉")
    
    base_tab, login_tab, register_tab = st.tabs(["Información", "Iniciar Sesión", "Registrarse"])
    
    with base_tab:
        st.markdown("""
        ### ¡Hola amigos!
        Esta es nuestra app oficial para organizar la reunión del año.
        Aquí podrán:
        - Confirmar disponibilidad.
        - Proponer qué comida llevar (¡sin repetir!).
        - Participar en el intercambio (Secret Santa 2.0).
        """)
    
    with login_tab:
        username = st.text_input("Usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", key="login_pass")
        if st.button("Entrar"):
            try:
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
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    with register_tab:
        new_user = st.text_input("Nuevo Usuario", key="reg_user")
        new_name = st.text_input("Nombre Completo (para que sepamos quién eres)", key="reg_name")
        new_pass = st.text_input("Contraseña", type="password", key="reg_pass")
        if st.button("Registrarme"):
            if new_user and new_pass:
                try:
                    session = get_session()
                    # Check if exists
                    if session.query(User).filter(User.username == new_user).first():
                        st.error("Ese usuario ya existe")
                    else:
                        u = User(username=new_user, password_hash=hash_password(new_pass), name=new_name)
                        session.add(u)
                        session.commit()
                        st.success("¡Registro exitoso! Ahora inicia sesión.")
                    session.close()
                except Exception as e:
                    st.error(f"Error al registrar: {e}")
            else:
                st.warning("Llena todos los campos")

def main_app():
    st.sidebar.title(f"Hola, {st.session_state.username} 👋")
    
    menu = ["Mi Perfil", "Comida (Potluck)", "Intercambio (Secret Santa)", "Cerrar Sesión"]
    choice = st.sidebar.radio("Navegación", menu)
    
    if choice == "Mi Perfil":
        show_profile()
    elif choice == "Comida (Potluck)":
        show_potluck()
    elif choice == "Intercambio (Secret Santa)":
        show_secretsanta()
    elif choice == "Cerrar Sesión":
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()

import json
import datetime
import random

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
            # Convert strings back to date objects for display if needed, 
            # but simpler to keep as list of strings for now or UI logic.
            # Let's use strings for storage "YYYY-MM-DD"
            current_dates = current_dates_str
        except:
            pass

    # UI for selecting dates
    # Let's propose a multi-date picker or just adding one by one.
    # Streamlit's date_input with defaults is tricky if dynamic. 
    # Use a form to add a date.
    
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
    
    # Summary of everyone's availability (Optional but helpful)
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
        
        # Admin assignment tool (simple version: First Come, Unique Serve logic button)
        # Or just manual assignment by override?
        # Let's add a button to "Auto-Assign" based on unique strings if user is daring.
        if st.button("🧙 Auto-Asignar (Beta)"):
            # Simple greedy algorithm
            assigned_so_far = set()
            
            # Reset assignments
            # Re-query to be safe
            all_ps = session.query(Potluck).all()
            for p in all_ps:
                # Try option 1
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
    
    # Add new wish
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
    
    # Check if I already claimed something? 
    # Logic: "La persona no sepa quien le va a dar regalo ni a quien" -> 
    # If I pick a gift, I know WHAT I bought, but do I know WHO it is for?
    # The prompt says "don't know who they are giving to". 
    # So I display the list of wishes anonymously. 
    # If I click "Buy This", I am assigned. I buy it. I bring it labeled with the "ID"?
    # We need a way to link gift to receiver at the party.
    # Maybe generate a "Gift Code" like #104. 
    # Receiver: "I am #104? No..." 
    # Receiver needs to know "Who is giving to me?" No, "Assignación aleatoria donde la persona no sepa quien le va a dar regalo".
    # Standard Secret Santa: You get a name.
    # User Request: "sólo escoja entre los regalos".
    # "don't know who they are giving to".
    # Okay, so I pick "Lego Set". Implicitly I am giving to the person who asked for it. But I don't see their name.
    # At the party, how does the gift get to the right person?
    # The app must tell me: "Buy Lego Set. Label it with Ticket #XYZ".
    # The receiver has Ticket #XYZ.
    # Perfect.
    
    # Get all unclaimed wishes NOT from me
    available_wishes = session.query(Wish).filter(Wish.user_id != user_id, Wish.claimed_by_id == None).all()
    
    # My claims
    my_claims = session.query(Wish).filter(Wish.claimed_by_id == user_id).all()
    
    if my_claims:
        st.success(f"🎁 Ya has escogido {len(my_claims)} regalo(s) para comprar:")
        for c in my_claims:
            st.info(f"🎁 **{c.description}**\n\n🏷️ **Etiqueta el regalo con el ID: #{c.id}** (¡No pongas el nombre del destinatario, solo este número!)")
            # Option to release?
            if st.button(f"Soltar #{c.id}", key=f"release_{c.id}"):
                c.claimed_by_id = None
                session.commit()
                st.rerun()
    
    st.write("### Regalos disponibles para escoger:")
    if available_wishes:
        # Shuffle specifically for display so order doesn't reveal user groups
        # converting to list to shuffle
        display_wishes = list(available_wishes)
        random.shuffle(display_wishes)
        
        for w in display_wishes:
            col1, col2 = st.columns([4, 1])
            col1.write(f"❓ {w.description}")
            if col2.button("✋ Yo lo compro", key=f"claim_{w.id}"):
                # Claim it
                # Check race condition technically, but low volume
                w.claimed_by_id = user_id
                session.commit()
                st.balloons()
                st.rerun()
    else:
        st.warning("No hay más regalos disponibles para escoger (o son tuyos).")
    
    session.close()



# Main Execution Flow
try:
    # Attempt to init DB on start (create tables if not exist)
    # This might fail if secrets are not set, handled gracefully in login
    init_db()
except Exception as e:
    # Optional: print error to console for debugging, or ignore if it's just connection issues before config
    print(f"DB Init failed: {e}")
    pass

if not st.session_state.logged_in:
    login_page()
else:
    main_app()
