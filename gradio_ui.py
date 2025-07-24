import gradio as gr
import requests

API_URL = "http://127.0.0.1:8000/pipeline"

def call_pipeline_api(text_input, file):
    # If file uploaded, read its content; else use text_input
    if file is not None:
        with open(file, 'r', encoding="utf-8") as f:
            transcript = f.read()
    else:
        transcript = text_input
    
    payload = {"transcript": transcript}
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code} - {response.text}"

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