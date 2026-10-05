# ---------------------------------------------------------
# TEST OPENAI API CONNECTION
# ---------------------------------------------------------
#
# This script has one purpose:
#
# Verify that:
#   1. Our API key loads correctly
#   2. The OpenAI client connects
#   3. We can receive a model response
#
# We test this separately so that any API problems are
# easier to diagnose before adding Streamlit.
# ---------------------------------------------------------

import os

from dotenv import load_dotenv
from openai import OpenAI


# Load variables stored in our local .env file.
load_dotenv()


# Retrieve the API key.
api_key = os.getenv("OPENAI_API_KEY")


# Stop immediately if the key wasn't found.
if not api_key:
    raise ValueError(
        "OPENAI_API_KEY was not found. Check your .env file."
    )


# Create the OpenAI client.
client = OpenAI(
    api_key=api_key
)


# Send a very small test request.
response = client.responses.create(
    model="gpt-6-luna",
    input=(
        "Reply with exactly: "
        "Property Market AI connected successfully."
    )
)


# output_text gives us the model's final text response.
print(response.output_text)