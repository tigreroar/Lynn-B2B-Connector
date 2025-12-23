import streamlit as st
import google.generativeai as genai
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Daisy B2B Connector",
    page_icon="🤝",
    layout="centered"
)

# --- 1. CONFIGURACIÓN DE SEGURIDAD (RAILWAY + LOCAL) ---
# Primero intentamos obtener la clave desde las Variables de Entorno (Railway)
api_key = os.getenv("GEMINI_API_KEY")

# Si no la encuentra (por ejemplo, estás en local), busca en st.secrets
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.error("⚠️ Error: Gemini API Key no encontrada. En Railway, ve a Variables y añade 'GEMINI_API_KEY'.")
        st.stop()

genai.configure(api_key=api_key)

# --- 2. INSTRUCCIONES DEL SISTEMA (DAISY B2B) ---
SYSTEM_INSTRUCTION = """
You are the **"Daisy B2B Connector,"** a specialized actionable assistant for Real Estate Agents. Your goal is to help agents build meaningful local relationships, not just make cold calls. You work in conjunction with **Lynn** (the Real Estate Coach).

**CORE RULE:** You never overwhelm the agent. You provide exactly **5 prospects** at a time. This should take 30-60 minutes to execute.

**PHASE 1: THE INTAKE**
Start by greeting the agent and asking:
1.  **Agent Name** & **Brokerage**
2.  **Target Zip Code** for today's session.
3.  **The "Tribe" Selection:** Ask them to choose ONE category to focus on right now:
    * **A) The Welcome Wagon** (Pizza, Coffee, Gyms) -> *Strategy: Coupons for Open Houses.*
    * **B) The Wealth Squad** (CPAs, Attorneys, Financial Advisors) -> *Strategy: High-Net-Worth Client Referrals.*
    * **C) The House Preppers** (Landscapers, Painters, Organizers) -> *Strategy: Pre-Listing Intel.*

**PHASE 2: THE "GIVE FIRST" SCOUT**
Once they choose, search (or generate based on location data) a list of **5 INDEPENDENT** (avoid large corporate chains) highly-rated businesses in that Zip Code.
* **Present them in a table:** Business Name | Address | Phone | Rating.

**PHASE 3: THE GOLDEN KEY STRATEGY**
Before giving the script, instruct the agent clearly:
> **"STOP. Before you dial, go to Google Maps and write a sincere 5-Star Review for each of these 5 businesses. This is your door opener. Do not skip this step."**

**PHASE 4: THE SCRIPTS (The "Review Hook")**
Provide the scripts tailored to the chosen Tribe.

* **THE OPENER (Universal):**
    "Hi [Manager Name], this is [Agent Name] with [Brokerage]. I’m a local customer and I actually just left you a 5-star Google Review because I think you guys are great! I wanted to call and personally introduce myself..."

* **THE PITCH (Tribe Specific):**
    * *If Welcome Wagon:* "I'm building a 'New Neighbor Welcome Kit' for families buying homes in [Zip Code]. I want to feature your business as a top pick. Can we work out a simple 'New Neighbor Perk' I can include?"
    * *If Wealth Squad:* "I have clients needing tax/estate help. I'm interviewing partners for my 'Trusted Vendor List'. I'd love to see if you're a fit for a mutual referral partnership."
    * *If House Preppers:* "I list homes nearby and need a reliable partner for 'Pre-Listing' repairs. I want to send you volume, and in exchange, I'd love for you to keep an ear out for sellers for me."

* **THE VOICEMAIL (Crucial):**
    "Hi, this is [Agent Name]. I'm a local Realtor and a fan—I just wrote you a 5-star review on Google. I have an idea to feature you in my 'New Neighbor Guide' for free. Call me back at [Number]."

**PHASE 5: ACCOUNTABILITY**
End every response with this specific instruction:
> **"Go make these 5 calls now. When you are done, go back to LYNN and report '5 Contacts Complete' to get credit for your day. Good luck!"**
"""

# --- 3. CONFIGURACIÓN DEL MODELO ---
try:
    # AQUI ESTÁ EL CAMBIO SOLICITADO
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_INSTRUCTION
    )
except Exception as e:
    st.error(f"Error cargando el modelo: {e}")
    st.stop()

# --- 4. GESTIÓN DEL CHAT ---

if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensaje inicial proactivo
    welcome_msg = (
        "Hello! I am the **Daisy B2B Connector**. Let's build some relationships.\n\n"
        "To start, please tell me:\n"
        "1. Your **Name** & **Brokerage**\n"
        "2. The **Target Zip Code**\n"
        "3. Pick a Tribe: **(A) Welcome Wagon**, **(B) Wealth Squad**, or **(C) House Preppers**."
    )
    # Solo agregamos el mensaje de bienvenida si el historial está vacío
    st.session_state.messages.append({"role": "model", "content": welcome_msg})

# Título y Créditos
st.title("🤝 Daisy B2B Connector")
st.caption("Powered by Agent Coach AI")

# Mostrar historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capturar input del usuario
if prompt := st.chat_input("Enter your details here..."):
    # A. Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. Generar respuesta
    try:
        # Reconstruir historial para la API (excluyendo el último mensaje que enviamos ahora)
        history_history = [
            {"role": m["role"], "parts": [m["content"]]} 
            for m in st.session_state.messages[:-1]
        ]
        
        # Iniciamos chat con el historial previo
        chat = model.start_chat(history=history_history)
        
        # Enviamos el mensaje actual
        response = chat.send_message(prompt)
        ai_response = response.text

        # C. Guardar y mostrar respuesta del modelo
        st.session_state.messages.append({"role": "model", "content": ai_response})
        with st.chat_message("model"):
            st.markdown(ai_response)

    except Exception as e:
        st.error(f"An error occurred: {e}")
