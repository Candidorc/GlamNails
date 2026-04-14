import streamlit as st
import google.generativeai as genai
import os
import random
from PIL import Image
import io

# ── Configuración Segura para la Nube ──────────────────────────────────────────

# Intentamos leer la clave desde st.secrets (Streamlit Cloud)
# Si no existe (en local), intentará buscarla en las variables de entorno
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    API_KEY = os.getenv("GOOGLE_API_KEY", "")

if not API_KEY:
    st.error("🔑 No se encontró la API KEY. Configúrala en 'Advanced Settings > Secrets'.")
    st.stop()

# Configuración del cliente Gemini
genai.configure(api_key=API_KEY)

BASE_IMAGES_DIR = "base_images"

PROMPT = """
You are a professional nail art editor.

Task: Take the nail design from the REFERENCE image and apply it exactly to the nails 
of the hand shown in the BASE image.

KEEP UNCHANGED (do not modify at all):
- Hand shape and fingers
- Skin tone and texture
- Lighting and shadows
- Background and fabric
- Rings, jewelry, or accessories
- Camera angle and composition

ONLY MODIFY:
- The nail design (color, pattern, art, finish, texture)

The result must look like a real, high-end beauty advertisement photo.
The nail design must be applied with perfect realism, matching the lighting of the base image.
No distortions. No artifacts. Photorealistic result.
"""

# ── Utilidades ─────────────────────────────────────────────────────────────────
def get_base_images():
    if not os.path.exists(BASE_IMAGES_DIR):
        # Crear la carpeta si no existe para evitar errores
        os.makedirs(BASE_IMAGES_DIR, exist_ok=True)
        return []
    extensions = (".jpg", ".jpeg", ".png", ".webp")
    return [
        os.path.join(BASE_IMAGES_DIR, f)
        for f in os.listdir(BASE_IMAGES_DIR)
        if f.lower().endswith(extensions)
    ]

def generate_nail_image(base_img: Image.Image, ref_img: Image.Image):
    # Usamos el modelo gemini-1.5-flash que es el más estable para visión
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    response = model.generate_content(
        [
            "BASE IMAGE (hand to keep):",
            base_img,
            "REFERENCE IMAGE (nail design to apply):",
            ref_img,
            PROMPT,
        ]
    )

    # Buscar la imagen en la respuesta
    try:
        # En la versión actual de la API, Gemini devuelve la imagen si se le pide
        # Pero si genera texto, este bloque captura el error
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return Image.open(io.BytesIO(part.inline_data.data))
        
        # Si no hay inline_data, devolvemos la respuesta como texto si fuera necesario
        return None
    except Exception:
        return None

# ── UI (NUEVO DISEÑO GLAMNAILS) ────────────────────────────────────────────────
st.set_page_config(
    page_title="GlamNails AI",
    page_icon="💅",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Jost', sans-serif; }
.stApp { background: #FCF5F3; } 

.top-bar {
    background: linear-gradient(135deg, #C48E85, #A06962);
    color: white;
    padding: 1.2rem;
    border-radius: 0 0 25px 25px;
    text-align: center;
    font-size: 1.2rem;
    font-weight: 500;
    margin-top: -3.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 10px rgba(160, 105, 98, 0.2);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

h1, h2, h3 { color: #3D2B29 !important; }
.title-block { text-align: center; padding: 0.5rem 0 1.5rem 0; }
.title-block h1 { font-size: 2rem; font-weight: 600; margin-bottom: 0.2rem; }

.upload-label { 
    color: #3D2B29; 
    font-size: 0.95rem; 
    font-weight: 600; 
    text-align: center;
    margin-bottom: 0.5rem; 
}

.info-box { 
    background: #FFFFFF; 
    border-radius: 20px; 
    padding: 1.2rem; 
    color: #5C433F; 
    font-size: 0.9rem; 
    text-align: center;
    margin: 1.5rem 0; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.04); 
}

.stButton > button {
    background: linear-gradient(135deg, #C48E85, #A06962) !important;
    color: #FFFFFF !important; 
    border: none !important; 
    border-radius: 30 : px !important;
    font-family: 'Jost', sans-serif !important; 
    font-size: 1rem !important;
    font-weight: 500 !important; 
    padding: 0.8rem 2rem !important; 
    width: 100% !important;
    box-shadow: 0 4px 12px rgba(160, 105, 98, 0.3) !important;
}

.success-badge { 
    background: #FFFFFF; 
    color: #A06962; 
    border-radius: 20px; 
    padding: 0.8rem; 
    font-size: 0.9rem; 
    font-weight: 500; 
    text-align: center; 
    margin: 1rem 0; 
}

[data-testid="stImage"] img { border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="top-bar">
    <span></span>
    <span>GlamNails AI</span>
    <span>👤</span>
</div>
<div class="title-block">
    <h1>Inspírate y Renueva tu Uña</h1>
</div>
""", unsafe_allow_html=True)

base_images = get_base_images()

if not base_images:
    st.error("⚠️ No se encontraron imágenes en `base_images/`. Asegúrate de subir la carpeta a GitHub.")
    st.stop()

st.markdown('<div class="upload-label">Inspiración de Pinterest (Sube tu diseño)</div>', unsafe_allow_html=True)
uploaded_ref = st.file_uploader(label="referencia", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")

if uploaded_ref:
    ref_img = Image.open(uploaded_ref).convert("RGB")
    st.image(ref_img, caption="Diseño Seleccionado", use_container_width=True)
    
    st.markdown(f'<div class="info-box">✨ Usaremos una de tus {len(base_images)} uñas base.</div>', unsafe_allow_html=True)

    if st.button("Procesando con IA ✨"):
        chosen_path = random.choice(base_images)
        base_img = Image.open(chosen_path).convert("RGB")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="upload-label">Antes</div>', unsafe_allow_html=True)
            st.image(base_img, use_container_width=True)

        with st.spinner("Creando magia en tus uñas... 💅"):
            try:
                result_img = generate_nail_image(base_img, ref_img)

                if result_img:
                    with col2:
                        st.markdown('<div class="upload-label">Después con IA</div>', unsafe_allow_html=True)
                        st.image(result_img, use_container_width=True)

                    buf = io.BytesIO()
                    result_img.save(buf, format="JPEG", quality=95)
                    st.download_button(
                        label="Aplicar y Descargar Diseño",
                        data=buf.getvalue(),
                        file_name="glamnails_result.jpg",
                        mime="image/jpeg"
                    )
                    st.markdown('<div class="success-badge">✨ ¡Diseño generado con éxito!</div>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Google Gemini no pudo generar la imagen. Esto puede pasar si el diseño es muy complejo. Intenta con otra foto.")

            except Exception as e:
                st.error(f"Error técnico: {str(e)}")

else:
    st.markdown('<div class="info-box">Selecciona una imagen arriba para empezar.</div>', unsafe_allow_html=True)
