import streamlit as st
from rembg import remove
from PIL import Image
from io import BytesIO
import base64
import requests

def upload_to_imgur(image):
    client_id = st.secrets["client_id"]
    headers = {'Authorization': 'Client-ID ' + client_id}
    payload = {'image': image}
    response = requests.post("https://api.imgur.com/3/image", headers=headers, data=payload)
    data = response.json()
    if response.status_code == 200:
        return data['data']['link']
    else:
        st.error("Error uploading image to Imgur.")
        return None

st.set_page_config(layout="wide", page_title="Image Background Remover")

st.write("## Remove background from your image")
st.write(
    ":dog: Try capturing an image to watch the background magically removed. Full quality images can be downloaded from the sidebar. This code is open source and available [here](https://github.com/tyler-simons/BackgroundRemoval) on GitHub. Special thanks to the [rembg library](https://github.com/danielgatis/rembg) :grin:"
)
st.sidebar.write("## Capture and download :gear:")

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Download the fixed image
def convert_image(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    return byte_im

def fix_image(upload):
    image = Image.open(upload)
    col1.write("Original Image :camera:")
    col1.image(image)

    fixed = remove(image)
    col2.write("Fixed Image :wrench:")
    col2.image(fixed)
    
    st.sidebar.markdown("\n")
    download_url = upload_to_imgur(convert_image(fixed))
    st.write(download_url)
    if download_url:
        st.sidebar.write("Download the fixed image [here](" + download_url + ")")

col1, col2 = st.columns(2)
my_capture = st.sidebar.camera_input(label="Capture an image")

if my_capture is not None:
    fix_image(upload=my_capture)
else:
    fix_image("./zebra.png")  # Placeholder image if no capture is made
