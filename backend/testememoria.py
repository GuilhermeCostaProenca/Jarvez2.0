from dotenv import load_dotenv
from mem0 import MemoryClient
import json
import logging
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_USER_ID = os.getenv("JARVEZ_USER_ID", "GuilhermeCostaProenca")


class JarvisMemory:
    def __init__(self, user_name: str = DEFAULT_USER_ID):
        self.user_name = user_name
        self.client = MemoryClient()

    def salvar_conversa(self):
        print(f"\nEnviando novas memorias para: {self.user_name}...")

        messages = [
            {"role": "user", "content": "Tenho focado no projeto Jarvez essa semana."},
            {"role": "assistant", "content": "Boa. Quer que eu te lembre das prioridades hoje?"},
            {"role": "user", "content": "Sim, prioriza backend de voz e memoria."},
        ]

        self.client.add(messages, user_id=self.user_name)
        print("Informacoes processadas e salvas com sucesso!")

    def buscar_memorias(self):
        print(f"\nJarvis, o que voce lembra sobre {self.user_name}?")

        query = f"Quais sao as preferencias e contexto de {self.user_name}?"
        response = self.client.search(query, filters={"user_id": self.user_name})

        results = response["results"] if isinstance(response, dict) and "results" in response else response

        memories_list = []
        for item in results:
            if isinstance(item, dict):
                memories_list.append(
                    {
                        "fato": item.get("memory"),
                        "data": item.get("updated_at"),
                    }
                )

        return memories_list


if __name__ == "__main__":
    brain = JarvisMemory(DEFAULT_USER_ID)
    brain.salvar_conversa()

    historico = brain.buscar_memorias()

    if historico:
        print(json.dumps(historico, indent=2, ensure_ascii=False))
    else:
        print("Nenhuma memoria encontrada para este usuario.")
