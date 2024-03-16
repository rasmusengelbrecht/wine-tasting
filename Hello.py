import streamlit as st
from rembg import remove
from PIL import Image
from io import BytesIO
import base64
import os
import requests
import duckdb

# Initialize DuckDB connection
con = duckdb.connect("md:?motherduck_token=" + st.secrets["motherduck_token"])

st.set_page_config(layout="wide", page_title="Image Background Remover")

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Download the fixed image
def convert_image(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    return byte_im

def fix_image(upload):
    image = Image.open(upload)
    fixed = remove(image)
    
    # Temporarily save the fixed image to the local filesystem
    fixed_image_path = "./fixed_image.png"
    fixed.save(fixed_image_path)
    
    return fixed, fixed_image_path

# Form for collecting user inputs
with st.expander("Submit Wine 🍷"):
    with st.form("image_data_form"):
        name = st.text_input("Name")
        price = st.number_input("Price (DKK)", value=75)
        my_capture = st.file_uploader("Upload or capture an image", type=["png", "jpg", "jpeg"])

        if my_capture is not None:
            if my_capture.size > MAX_FILE_SIZE:
                st.error("The uploaded file is too large. Please upload an image smaller than 5MB.")
            else:
                fixed_image, fixed_image_path = fix_image(my_capture)
                st.write("Fixed Image :wrench:")
                st.image(fixed_image)
                
                # Proceed with form submission
                if st.form_submit_button("Submit"):
                    # Upload the fixed image to Imgur
                    # Code to upload image to Imgur and submit other form data to MotherDuck
                    pass
                # Remove the temporary fixed image
                os.remove(fixed_image_path)
        else:
            st.warning("Please upload or capture an image.")

# Query for filtered data
query = """
SELECT 
  *
FROM my_db.main.wine_data
"""
wine_df = con.execute(query).df()

# Rename the '_name' column to 'Name' and 'price' to 'Price' in the DataFrame
wine_df.rename(columns={'name': 'Name', 'price': 'Price'}, inplace=True)

# Sort the DataFrame by price in descending order and select the top 10 expensive wines
top_10_expensive = wine_df.nlargest(10, 'Price')