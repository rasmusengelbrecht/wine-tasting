import streamlit as st
from rembg import remove
from PIL import Image
from io import BytesIO
import base64
from imgurpython import ImgurClient
import os
import requests
import duckdb

# Initialize Imgur client
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
client = ImgurClient(client_id, client_secret)

# Connect to DuckDB database
con = duckdb.connect("md:?motherduck_token=" + st.secrets["motherduck_token"])

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

def upload_to_imgur(image_path):
    response = client.upload_from_path(image_path, anon=False)
    if response:
        return response['link']
    else:
        st.error("Error uploading image to Imgur.")
        return None

def fix_image(upload):
    image = Image.open(upload)
    col1.write("Original Image :camera:")
    col1.image(image)

    fixed = remove(image)
    col2.write("Fixed Image :wrench:")
    col2.image(fixed)
    
    st.sidebar.markdown("\n")
    
    # Temporarily save the fixed image to the local filesystem
    fixed_image_path = "./fixed_image.png"
    fixed.save(fixed_image_path)
    
    download_url = upload_to_imgur(fixed_image_path)  # Upload the fixed image to Imgur
    os.remove(fixed_image_path)  # Remove the temporary fixed image
    return download_url

col1, col2 = st.columns(2)

# Form for collecting user inputs
with st.expander("Submit Wine 🍷"):
    with st.form("image_data_form"):
        name = st.text_input("Name")
        price = st.number_input("Price (DKK)", value=75)
        my_capture = st.camera_input(label="Capture an image")

        if st.form_submit_button("Submit"):
            if my_capture is not None:
                # Save captured image temporarily to upload
                captured_image_path = "./captured_image.png"
                my_capture.save(captured_image_path)
                download_url = fix_image(upload=captured_image_path)
                if download_url:
                    # Load data into MotherDuck
                    motherduck_url = "YOUR_MOTHERDUCK_URL"
                    data_file_path = f"./{name.replace(' ', '_')}.png"
                    data_file_path_parquet = f"./{name.replace(' ', '_')}.parquet"
                    # Save the captured image to a file
                    Image.open(BytesIO(my_capture)).save(data_file_path)
                    # Convert the image file to Parquet format
                    con.sql(f"CREATE TABLE {name.replace(' ', '_')} AS SELECT * FROM '{data_file_path}'")
                    # Upload the Parquet file to MotherDuck
                    response = requests.post(motherduck_url, files={"data": open(data_file_path_parquet, "rb")})
                    if response.status_code == 200:
                        st.success("Data submitted successfully!")
                    else:
                        st.error("Error submitting data to MotherDuck.")
                    # Remove temporary files
                    os.remove(data_file_path)
                    os.remove(data_file_path_parquet)
            else:
                st.warning("Please capture an image.")
