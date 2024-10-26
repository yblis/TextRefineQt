import sys
import json
from datetime import datetime
from pathlib import Path
import requests

# Create data directory
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

class TextReformulator:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.current_model = "qwen2.5:3b"
        self.system_prompt = """Tu es un expert en reformulation. Tu dois reformuler le texte selon les paramètres spécifiés par l'utilisateur: ton, format et longueur. IMPORTANT : retourne UNIQUEMENT le texte reformulé, sans aucune mention des paramètres. 
Respecte scrupuleusement le format demandé, la longueur et le ton. Ne rajoute aucun autre commentaire."""

    def reformulate(self, text, tone="Professionnel", format="Paragraphe", length="Moyen"):
        prompt = f"""<|im_start|>system
{self.system_prompt}
<|im_end|>
<|im_start|>user
Texte à reformuler: {text}
Ton: {tone}
Format: {format}
Longueur: {length}
<|im_end|>
<|im_start|>assistant"""

        try:
            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                reformulated_text = result['response']
                
                lines = reformulated_text.split('\n')
                cleaned_lines = [line for line in lines if not any(x in line.lower() for x in 
                               ['paramètre', 'ton:', 'format:', 'longueur:', 'voici', 'reformulation'])]
                return '\n'.join(cleaned_lines).strip()
            else:
                return f"Error: Failed to reformulate text (Status code: {response.status_code})"
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    reformulator = TextReformulator()
    
    print("=== Text Reformulator ===")
    print("\nEnter your text (press Ctrl+D or Ctrl+Z to finish):")
    
    # Read multiline input
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        text = '\n'.join(lines)
    
    # Predefined options
    tones = ["Professionnel", "Informatif", "Décontracté", "Enthousiaste", "Drôle", "Sarcastique"]
    formats = ["Mail", "Paragraphe", "Idées", "Article de blog"]
    lengths = ["Court", "Moyen", "Long"]
    
    print("\nSelect tone:")
    for i, tone in enumerate(tones, 1):
        print(f"{i}. {tone}")
    tone_idx = int(input("Enter number: ")) - 1
    selected_tone = tones[tone_idx]
    
    print("\nSelect format:")
    for i, fmt in enumerate(formats, 1):
        print(f"{i}. {fmt}")
    format_idx = int(input("Enter number: ")) - 1
    selected_format = formats[format_idx]
    
    print("\nSelect length:")
    for i, length in enumerate(lengths, 1):
        print(f"{i}. {length}")
    length_idx = int(input("Enter number: ")) - 1
    selected_length = lengths[length_idx]
    
    print("\nReformulating...")
    result = reformulator.reformulate(text, selected_tone, selected_format, selected_length)
    
    print("\n=== Result ===")
    print(result)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output_{timestamp}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nOutput saved to: {output_file}")

if __name__ == "__main__":
    main()
