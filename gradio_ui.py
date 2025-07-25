import gradio as gr
import requests
from config import Config

API_URL = Config.FASTAPI_API_URL

def call_pipeline_api(text_input, file):
    # If file uploaded, read its content; else use text_input
    if file is not None:
        with open(file, 'r', encoding="utf-8") as f:
            transcript = f.read()
    else:
        transcript = text_input
    
    payload = {"transcript": transcript}

    try:
        response = requests.post(API_URL, json=payload)
        print("Response status:", response.status_code)

        if response.status_code == 200:
            try:
                return response.json()  # Expecting JSON (dict or list)
            except Exception as e:
                return {"error": f"Invalid JSON returned: {str(e)}", "raw_response": response.text}
        else:
            return {"error": f"HTTP {response.status_code}", "raw_response": response.text}
    
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

with gr.Blocks() as demo:
    gr.Markdown("## Transcript Action Item Extractor")
    
    with gr.Tab("Enter Text"):
        text_input = gr.Textbox(
            lines=15, 
            placeholder="Paste transcript text here...",
            label="Transcript Text"
        )
    
    with gr.Tab("Upload File"):
        file_input = gr.File(file_types=[".txt"], label="Upload transcript .txt file")
    
    output = gr.JSON(label="Extracted Action Items")
    
    btn = gr.Button("Run Pipeline")
    btn.click(
        call_pipeline_api,
        inputs=[text_input, file_input],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch()