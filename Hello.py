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
    fixed = remove(image)   
    
    # Temporarily save the fixed image to the local filesystem
    fixed_image_path = "./fixed_image.png"
    fixed.save(fixed_image_path)
    
    download_url = upload_to_imgur(fixed_image_path)  # Upload the fixed image to Imgur
    os.remove(fixed_image_path)  # Remove the temporary fixed image
    return fixed, download_url

# Form for collecting user inputs
with st.expander("Submit Wine 🍷"):
    name = st.text_input("Name")
    price = st.number_input("Price (DKK)", value=75)
    my_capture = st.camera_input(label="Capture an image")

    col1, col2 = st.columns(2)

    if my_capture is not None:
        # Save captured image temporarily to upload
        captured_image_path = "./captured_image.png"
        fixed_image, _ = fix_image(upload=my_capture)
        col1.write("Original Image :camera:")
        col1.image(my_capture)
        col2.write("Fixed Image :wrench:")
        col2.image(fixed_image)

    if st.button("Submit"):
        if my_capture is not None:
            # Save captured image temporarily to upload
            captured_image_path = "./captured_image.png"
            with open(captured_image_path, "wb") as f:
                f.write(my_capture.read())  # Save the uploaded image file to disk
            _, download_url = fix_image(upload=captured_image_path)
            if download_url:
                # Check if the table exists, if not, create it
                con.execute("""
                    CREATE TABLE IF NOT EXISTS main.wine_data (
                        name STRING,
                        price FLOAT,
                        download_url STRING
                    )
                """)
                # Insert data into wine_data table
                con.execute(f"INSERT INTO main.wine_data VALUES ('{name}', {price}, '{download_url}')")
                st.success("Data submitted successfully!")
            os.remove(captured_image_path)  # Remove the temporary captured image file
        else:
            st.warning("Please capture an image.")


# Query for filtered data
query = """
SELECT 
  *
FROM my_db.main.wine_data
"""
wine_df = con.execute(query).df()


# Rename the '_name' column to 'Pokemon' and 'height' to 'Height' in the DataFrame
wine_df.rename(columns={'name': 'Name', 'price': 'Price'}, inplace=True)


# Sort the DataFrame by height in descending order and select the top 10 tallest Pokémon
top_10_tallest = wine_df.nlargest(10, 'Price')