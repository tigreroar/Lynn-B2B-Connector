import streamlit as st
import google.generativeai as genai
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Daisy B2B Connector",
    page_icon="🤝",
    layout="centered"
)

# --- CONFIGURACIÓN DE API KEY Y MODELO ---
# Se busca la API Key en st.secrets (recomendado para Streamlit Cloud) o en variables de entorno.
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    # Si no estás en Streamlit Cloud, busca en variables de entorno o descomenta la línea de abajo para pruebas locales
    # api_key = "TU_API_KEY_AQUI" 
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ Error: Gemini API Key no encontrada. Configura .streamlit/secrets.toml o tus variables de entorno.")
    st.stop()

genai.configure(api_key=api_key)

# --- INSTRUCCIONES DEL SISTEMA (SYSTEM PROMPT) ---
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

# Configuración del modelo (Gemini 2.0 Flash)
# Nota: Usamos 'gemini-2.0-flash-exp' que es el nombre técnico actual para el preview.
try:
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=SYSTEM_INSTRUCTION
    )
except Exception as e:
    st.error(f"Error cargando el modelo Gemini 2.0 Flash: {e}. Asegúrate de tener acceso a la versión experimental o cambia a gemini-1.5-flash.")
    st.stop()

# --- GESTIÓN DEL CHAT ---

if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensaje inicial proactivo para iniciar la Fase 1 inmediatamente
    welcome_msg = (
        "Hello! I am the **Daisy B2B Connector**. Let's build some relationships.\n\n"
        "To start, please tell me:\n"
        "1. Your **Name** & **Brokerage**\n"
        "2. The **Target Zip Code**\n"
        "3. Pick a Tribe: **(A) Welcome Wagon**, **(B) Wealth Squad**, or **(C) House Preppers**."
    )
    st.session_state.messages.append({"role": "model", "content": welcome_msg})

# Mostrar historial
st.title("🤝 Daisy B2B Connector")
st.caption("Powered by Agent Coach AI")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capturar input del usuario
if prompt := st.chat_input("Enter your details here..."):
    # 1. Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta
    try:
        # Reconstruir historial para la API
        history = [
            {"role": m["role"], "parts": [m["content"]]} 
            for m in st.session_state.messages 
            if m["role"] != "system" # System instruction va en la init del modelo
        ]
        
        chat = model.start_chat(history=history[:-1]) # Todo menos el último mensaje que acabamos de enviar
        response = chat.send_message(prompt)
        
        ai_response = response.text

        # 3. Guardar y mostrar respuesta del modelo
        st.session_state.messages.append({"role": "model", "content": ai_response})
        with st.chat_message("model"):
            st.markdown(ai_response)

    except Exception as e:

        st.error(f"An error occurred: {e}")

