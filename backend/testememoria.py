from dotenv import load_dotenv
from mem0 import MemoryClient
import logging
import json
import os

# Configuração básica
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JarvisMemory:
    def __init__(self, user_name="PedroLucas"):
        self.user_name = user_name
        # O MemoryClient busca a MEM0_API_KEY automaticamente do seu .env
        self.client = MemoryClient()

    def salvar_conversa(self):
        """Simula o envio de mensagens para a memória do Mem0"""
        print(f"\n🚀 Enviando novas memórias para: {self.user_name}...")
        
        messages = [
            {"role": "user", "content": "Ultimamente estou escutando muito Alee."},
            {"role": "assistant", "content": "Ótima escolha! Qual sua música favorita dele?"},
            {"role": "user", "content": "Minha favorita é Tempo do ouro e minha cor preferida é Preto."},
        ]

        # O método add extrai os fatos e salva no banco de dados
        self.client.add(messages, user_id=self.user_name)
        print("✅ Informações processadas e salvas com sucesso!")

    def buscar_memorias(self):
        """Recupera as informações que o Jarvis aprendeu"""
        print(f"\n🧠 Jarvis, o que você lembra sobre {self.user_name}?")
        
        query = f"Quais são as preferências e gostos de {self.user_name}?"
        
        # Na v2, usamos o dicionário filters
        response = self.client.search(query, filters={"user_id": self.user_name})

        # Tratamento da estrutura de resposta (lista ou dicionário)
        results = response["results"] if isinstance(response, dict) and "results" in response else response

        memories_list = []
        for item in results:
            if isinstance(item, dict):
                memories_list.append({
                    "fato": item.get("memory"),
                    "data": item.get("updated_at")
                })
        
        return memories_list

# --- EXECUÇÃO ---
if __name__ == "__main__":
    brain = JarvisMemory("PedroLucas")

    # 1. Primeiro enviamos a informação (Comente essa linha se já enviou uma vez e quer só testar a busca)
    brain.salvar_conversa()

    # 2. Depois buscamos o que foi aprendido
    historico = brain.buscar_memorias()

    # Exibição organizada
    if historico:
        print(json.dumps(historico, indent=2, ensure_ascii=False))
    else:
        print("❌ Nenhuma memória encontrada para este usuário.")
