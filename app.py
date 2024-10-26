from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime
from pathlib import Path
import os

app = Flask(__name__)

# Create data directory
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

class HistoryManager:
    def __init__(self):
        self.history_file = data_dir / "history.json"
        self.history = self.load_history()

    def load_history(self):
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def add_entry(self, original_text, reformulated_text, parameters):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'original': original_text,
            'reformulated': reformulated_text,
            'parameters': parameters
        }
        self.history.append(entry)
        self.save_history()

    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history[-100:], f, ensure_ascii=False, indent=2)

history_manager = HistoryManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reformulate', methods=['POST'])
def reformulate():
    data = request.json
    text = data.get('text', '')
    tone = data.get('tone', 'Professionnel')
    format_type = data.get('format', 'Paragraphe')
    length = data.get('length', 'Moyen')

    if not text:
        return jsonify({'error': 'Please enter text to reformulate'}), 400

    system_prompt = """Tu es un expert en reformulation. Tu dois reformuler le texte selon les paramètres spécifiés par l'utilisateur: ton, format et longueur. IMPORTANT : retourne UNIQUEMENT le texte reformulé, sans aucune mention des paramètres. 
Respecte scrupuleusement le format demandé, la longueur et le ton. Ne rajoute aucun autre commentaire."""

    prompt = f"""<|im_start|>system
{system_prompt}
<|im_end|>
<|im_start|>user
Texte à reformuler: {text}
Ton: {tone}
Format: {format_type}
Longueur: {length}
<|im_end|>
<|im_start|>assistant"""

    try:
        response = requests.post('http://localhost:11434/api/generate',
                               json={
                                   "model": "qwen2.5:3b",
                                   "prompt": prompt,
                                   "stream": False
                               })
        
        if response.status_code == 200:
            result = response.json()
            reformulated_text = result['response']
            
            lines = reformulated_text.split('\n')
            cleaned_lines = [line for line in lines if not any(x in line.lower() for x in 
                           ['paramètre', 'ton:', 'format:', 'longueur:', 'voici', 'reformulation'])]
            cleaned_text = '\n'.join(cleaned_lines).strip()
            
            parameters = {
                "tone": tone,
                "format": format_type,
                "length": length
            }
            history_manager.add_entry(text, cleaned_text, parameters)
            
            return jsonify({'result': cleaned_text})
        else:
            return jsonify({'error': 'Reformulation failed. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
