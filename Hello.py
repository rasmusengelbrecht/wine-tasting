import streamlit as st
from rembg import remove
from PIL import Image
from io import BytesIO
import base64
from imgurpython import ImgurClient
import os
import requests
import duckdb
import altair as alt


#-------------------------- Page Config --------------------------------

st.set_page_config(page_title="Wine Tasting", page_icon="🍷")


#----------------- Hide Streamlit footer, header -----------------------

hide_streamlit_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important;}
            footer {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


#--------------------------------------------------------------------


st.markdown(
    """
        # Wine Tasting 🍷

        Start submitting tonights bottles, and let the fun begin 🍾
    """
)



#--------------------------------------------------------------------


# Initialize Imgur client
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
client = ImgurClient(client_id, client_secret)

# Connect to DuckDB database
con = duckdb.connect("md:?motherduck_token=" + st.secrets["motherduck_token"])



#----------------- Functions -----------------------


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
    return fixed, download_url



#--------------------------------------------------------------------

grape_varieties = [
    "Unknown",
    "Chardonnay",
    "Cabernet Sauvignon",
    "Merlot",
    "Pinot Noir",
    "Sauvignon Blanc",
    "Syrah",
    "Riesling",
    "Zinfandel",
    "Malbec",
    "Grenache",
    "Tempranillo",
    "Sangiovese",
    "Nebbiolo",
    "Chenin Blanc",
    "Viognier",
    "Pinot Gris",
    "Gewürztraminer",
    "Muscat",
    "Semillon",
    "Verdejo",
    "Carmenere",
    "Petit Verdot",
    "Grüner Veltliner",
    "Albariño",
    "Shiraz",
    "Pinot Blanc",
    "Gamay",
    "Cabernet Franc",
    "Moscato",
    "Sémillon",
    "Bordeaux Blend",
    "Rhone Blend",
    "Super Tuscan",
    "Meritage",
    "Appassimento",
    "Appassite",
    "Nobile",
]

#--------------------------------------------------------------------

# Form for collecting user inputs
with st.expander("Submit Wine 🍷"):
    your_name = st.text_input("Your Name")
    wine_name = st.text_input("Name of Wine")
    grape_type = st.selectbox("Grape Type", grape_varieties)
    price = st.number_input("Price (DKK)", value=75)
    my_capture = st.camera_input(label="Capture an image")

    if my_capture is not None:
        # Save captured image temporarily to upload
        captured_image_path = "./captured_image.png"
        with open(captured_image_path, "wb") as f:
            f.write(my_capture.read())  # Save the uploaded image file to disk
        fixed_image, _ = fix_image(upload=captured_image_path)
        st.write("Fixed Image :wrench:")
        st.image(fixed_image)

    if st.button("Submit"):
        if my_capture is not None:
            _, download_url = fix_image(upload=captured_image_path)
            if download_url:
                # Check if the table exists, if not, create it
                con.execute("""
                    CREATE TABLE IF NOT EXISTS main.wine_data (
                        your_name STRING,
                        wine_name STRING,
                        grape_type STRING,
                        price FLOAT,
                        download_url STRING
                    )
                """)
                # Insert data into wine_data table
                con.execute(f"INSERT INTO main.wine_data VALUES ('{your_name}','{wine_name}','{grape_type}', {price}, '{download_url}')")
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

# Sort the DataFrame by price in descending order and select the top 10 most expensive wines
top_10_expensive = wine_df.nlargest(10, 'Price')

# Create Altair chart for images
image_chart = alt.Chart(top_10_expensive, height=500).mark_image(
    width=50,
    height=50
).encode(
    x=alt.X('Wine Name', sort=None),  # Disable sorting to maintain original order
    y='Price',
    url='download_url'
)

# Create Altair chart for bars
bar_chart = alt.Chart(top_10_expensive, height=500).mark_bar(
    color='dimgrey'
).encode(
    x=alt.X('Wine Name', sort=None),  # Disable sorting to maintain original order
    y='Price'
)

# Layer the image chart and bar chart
combined_chart = alt.layer(bar_chart, image_chart).configure_axis(
    grid=False
)

# Display the combined chart using Streamlit
st.altair_chart(combined_chart, use_container_width=True)