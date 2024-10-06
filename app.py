from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import re
import joblib
from huggingface_hub import InferenceClient

# Initialize FastAPI app
app = FastAPI()

# Load the pre-trained model pipeline
model_pipeline = joblib.load('model_pipeline.pkl')

# Hugging Face API token (make sure to keep this secure in a production environment)
token = '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'

# Initialize the Hugging Face client
client = InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct", token=token)

# Define Pydantic model for input validation
class CustomerInput(BaseModel):
    customer_information: str

# Route to make churn predictions
@app.post("/predict")
async def predict_churn(customer: CustomerInput):
    # Define the prompt for the Hugging Face model
    prompt = f"""
    **Task:** Extract and return customer information in a specific order as a list.
    only return the list of values without adding any information, notes, or explanations.

    **Instructions:**
    1. **Extract the following features from the provided query in the exact order listed below.**
    2. **For each feature, select the value from the given options only.**
    3. **Return the values as a Python list in the specified order. Ensure the values are case-sensitive and match exactly as described in the options.**

    **Order of Features and Values (with defaults if missing):**
    1. **Gender**: 'Female' or 'Male' (default: 'Male')
    2. **Senior_citizen**: 1 if the customer is a senior citizen, otherwise 0 (default: 0)
    3. **Is_married**: 'Yes' if married, 'No' otherwise (default: 'No')
    4. **Dependents**: 'Yes' if the customer has dependents, 'No' otherwise (default: 'No')
    5. **Tenure**: Number of months the customer has been with the company (default: 0)
    6. **Phone_service**: 'Yes' if the customer has phone service, 'No' otherwise (default: 'No')
    7. **Dual**: 'No phone service', 'No', or 'Yes' (default: 'No')
    8. **Internet_service**: 'DSL', 'Fiber optic', or 'No' (default: 'No')
    9. **Online_security**: 'Yes', 'No', or 'No internet service' (default: 'No')
    10. **Online_backup**: 'Yes', 'No', or 'No internet service' (default: 'No')
    11. **Device_protection**: 'Yes', 'No', or 'No internet service' (default: 'No')
    12. **Tech_support**: 'Yes', 'No', or 'No internet service' (default: 'No')
    13. **Streaming_tv**: 'Yes', 'No', or 'No internet service' (default: 'No')
    14. **Streaming_movies**: 'Yes', 'No', or 'No internet service' (default: 'No')
    15. **Contract**: 'Month-to-month', 'One year', or 'Two year' (default: 'Month-to-month')
    16. **Paperless_billing**: 'Yes' or 'No' (default: 'Yes')
    17. **Payment_method**: 'Electronic check', 'Mailed check', 'Bank transfer (automatic)', or 'Credit card (automatic)' (default: 'Electronic check')
    18. **Monthly_charges**: A number representing monthly charges (default: 0.0)
    19. **Total_charges**: A number representing total charges (default: 0.0)

    Important:
    - The list must strictly follow the order mentioned.
    - All categorical values must match the provided options exactly.
    - **Do not omit or skip any feature, especially the last one.**
    - Only return the list, do not add any additional text or explanations.

    customer information:
    {customer.customer_information}
    """

    # Send prompt to Hugging Face Inference API
    response = client.text_generation(prompt)

    # Use regex to extract the list from the response
    list_pattern = r"\[(.*?)\]"
    match = re.search(list_pattern, response)

    if match:
        list_str = match.group(0)
        generated_features = eval(list_str)

        # Proceed with feature list and predict churn
        columns = ['Gender', 'Senior_citizen', 'Is_married', 'Dependents', 'Tenure', 'Phone_service', 'Dual',
                   'Internet_service', 'Online_security', 'Online_backup', 'Device_protection', 'Tech_support',
                   'Streaming_tv', 'Streaming_movies', 'Contract', 'Paperless_billing', 'Payment_method',
                   'Monthly_charges', 'Total_charges']

        # Create a DataFrame with the extracted features
        input_df = pd.DataFrame([generated_features], columns=columns)

        # Predict churn using the pre-trained model
        prediction = model_pipeline.predict(input_df)

        # Return the prediction
        return {"Churn Prediction": "Yes" if prediction[0] == 1 else "No"}
    
    else:
        raise HTTPException(status_code=400, detail="No valid list found in the response.")