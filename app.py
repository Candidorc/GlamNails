import streamlit as st
from google import genai
from google.genai import types
import os
import random
from PIL import Image
import io

# ── API KEY ────────────────────────────────────────────────────────────────────
# Funciona tanto en local (.env / variable de entorno) como en Streamlit Cloud (secrets)
api_key = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

if not api_key:
    st.error("🔑 No se encontró la API KEY. Configúrala en Streamlit Cloud > Settings > Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# ── Configuración ──────────────────────────────────────────────────────────────
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
        return []
    extensions = (".jpg", ".jpeg", ".png", ".webp")
    return [
        os.path.join(BASE_IMAGES_DIR, f)
        for f in os.listdir(BASE_IMAGES_DIR)
        if f.lower().endswith(extensions)
    ]

def pil_to_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()

def generate_nail_image(base_img: Image.Image, ref_img: Image.Image):
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=[
            types.Part.from_text("BASE IMAGE (hand to keep):"),
            types.Part.from_bytes(data=pil_to_bytes(base_img), mime_type="image/jpeg"),
            types.Part.from_text("REFERENCE IMAGE (nail design to apply):"),
            types.Part.from_bytes(data=pil_to_bytes(ref_img), mime_type="image/jpeg"),
            types.Part.from_text(PROMPT),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["image", "text"]
        )
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return Image.open(io.BytesIO(part.inline_data.data))

    return None

# ── UI ─────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="GlamNails AI", page_icon="💅", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Jost:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Jost', sans-serif; }
.stApp { background: #0e0b0f; }
h1, h2, h3 { font-family: 'Cormorant Garamond', serif !important; }
.title-block { text-align: center; padding: 2.5rem 0 1rem 0; }
.title-block h1 { font-size: 3rem; font-weight: 300; color: #f0e6d3; margin-bottom: 0.2rem; }
.title-block p { color: #9e8f85; font-size: 0.85rem; letter-spacing: 0.2em; text-transform: uppercase; }
.divider { border: none; border-top: 1px solid #2a2028; margin: 1.5rem 0; }
.upload-label { color: #c4a882; font-size: 0.75rem; letter-spacing: 0.18em; text-transform: uppercase; font-weight: 500; margin-bottom: 0.5rem; }
.info-box { background: #1a1520; border: 1px solid #2a2028; border-left: 2px solid #c4a882; border-radius: 4px; padding: 0.8rem 1rem; color: #9e8f85; font-size: 0.8rem; margin: 1rem 0; }
.stButton > button {
    background: linear-gradient(135deg, #c4a882, #a08060) !important;
    color: #0e0b0f !important; border: none !important; border-radius: 2px !important;
    font-family: 'Jost', sans-serif !important; font-size: 0.8rem !important;
    font-weight: 500 !important; letter-spacing: 0.2em !important;
    text-transform: uppercase !important; padding: 0.7rem 2rem !important; width: 100% !important;
}
.success-badge { background: #1a1520; border: 1px solid #4a7c59; color: #7ec89a; border-radius: 4px; padding: 0.5rem 1rem; font-size: 0.75rem; letter-spacing: 0.15em; text-transform: uppercase; text-align: center; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
    <h1>💅 GlamNails AI</h1>
    <p>Generador automático de contenido para manicuristas</p>
</div>
<hr class="divider">
""", unsafe_allow_html=True)

base_images = get_base_images()

if not base_images:
    st.error("⚠️ No se encontraron imágenes en `base_images/`. Asegúrate de que la carpeta esté subida a GitHub con fotos dentro.")
    st.stop()

st.markdown('<div class="upload-label">Imagen de referencia (Pinterest, etc.)</div>', unsafe_allow_html=True)
uploaded_ref = st.file_uploader(
    label="referencia",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed"
)

if uploaded_ref:
    ref_img = Image.open(uploaded_ref).convert("RGB")
    st.image(ref_img, caption="✦ Tu referencia")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="info-box">
        ✦ Se seleccionará automáticamente una de tus <strong>{len(base_images)}</strong> imágenes base al azar.
    </div>
    """, unsafe_allow_html=True)

    if st.button("✦  Generar contenido"):
        chosen_path = random.choice(base_images)
        base_img = Image.open(chosen_path).convert("RGB")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="upload-label">Imagen base</div>', unsafe_allow_html=True)
            st.image(base_img)

        with st.spinner("Aplicando diseño de uñas... 20-40 segundos ✦"):
            try:
                result_img = generate_nail_image(base_img, ref_img)

                if result_img:
                    with col2:
                        st.markdown('<div class="upload-label">Resultado</div>', unsafe_allow_html=True)
                        st.image(result_img)

                    st.markdown('<hr class="divider">', unsafe_allow_html=True)
                    buf = io.BytesIO()
                    result_img.save(buf, format="JPEG", quality=95)
                    st.download_button(
                        label="⬇  Descargar imagen",
                        data=buf.getvalue(),
                        file_name="glamnails_result.jpg",
                        mime="image/jpeg"
                    )
                    st.markdown('<div class="success-badge">✦ Imagen generada con éxito</div>', unsafe_allow_html=True)
                else:
                    st.error("Gemini no devolvió imagen. Prueba con otra foto de referencia.")

            except Exception as e:
                st.error(f"Error: {str(e)}")

else:
    st.markdown("""
    <div class="info-box">
        ↑ Sube una imagen de inspiración (Pinterest, Instagram) y el sistema hará el resto.
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<hr class="divider">
<div style="text-align:center; color:#3a3038; font-size:0.7rem; letter-spacing:0.15em; padding-bottom:1rem;">
    GLAMNAILS AI · POWERED BY GEMINI
</div>
""", unsafe_allow_html=True)
