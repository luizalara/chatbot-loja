from fastapi import FastAPI, Header, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
import ollama
import requests
import json
import os
import time
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

# Chave da sua própria API (/chat)
API_KEY = os.getenv("API_KEY", "")

# Evolution API (Docker, exposto na porta 8080)
EVOLUTION_URL = os.getenv("EVOLUTION_URL", "http://localhost:8080")
EVOLUTION_KEY = os.getenv("EVOLUTION_KEY", "")
INSTANCIA = os.getenv("INSTANCIA", "luiza")

# Só estes números recebem resposta do bot (código do país + DDD + número, sem +)
# Defina no .env separados por vírgula. Quem não estiver na lista é ignorado.
NUMEROS_PERMITIDOS = [
    n.strip() for n in os.getenv("NUMEROS_PERMITIDOS", "").split(",") if n.strip()
]

# Memória curta por cliente (últimas mensagens)
historicos = {}
MAX_HISTORICO = 6


class Mensagem(BaseModel):
    pergunta: str


def montar_prompt():
    with open("empresa.json", "r", encoding="utf-8") as arquivo:
        empresa = json.load(arquivo)

    with open("produtos.json", "r", encoding="utf-8") as arquivo:
        produtos = json.load(arquivo)

    catalogo = ""
    for produto in produtos:
        catalogo += f"""
Produto: {produto['produto']}
Preço: R$ {produto['preco']}
Descrição: {produto['descricao']}
Estoque: {produto['estoque']}
"""

    return f"""
Você é uma atendente virtual.

Empresa:
{empresa['nome_empresa']}

Horário:
{empresa['horario']}

Formas de pagamento:
{empresa['pagamento']}

Endereço:
{empresa['endereco']}

FAQ:
{empresa.get('faq', '')}

Catálogo:
{catalogo}

Regras:
- Responda sempre em português.
- Use apenas essas informações.
- Não invente produtos.
- Seja simpática e objetiva.
"""


def gerar_resposta(pergunta, historico=None):
    mensagens = [{"role": "system", "content": montar_prompt()}]
    if historico:
        mensagens.extend(historico)
    mensagens.append({"role": "user", "content": pergunta})

    resposta = ollama.chat(
        model="llama3.2",
        messages=mensagens,
        keep_alive="60m",
        options={"num_predict": 200},
    )
    return resposta["message"]["content"]


def enviar_whatsapp(destino, texto):
    r = requests.post(
        f"{EVOLUTION_URL}/message/sendText/{INSTANCIA}",
        headers={"apikey": EVOLUTION_KEY, "Content-Type": "application/json"},
        json={"number": destino, "text": texto},
        timeout=30,
    )
    print("sendText:", r.status_code, r.text[:200])


def processar_mensagem(destino, texto):
    try:
        historico = historicos.get(destino, [])
        resposta = gerar_resposta(texto, historico)

        historico.append({"role": "user", "content": texto})
        historico.append({"role": "assistant", "content": resposta})
        historicos[destino] = historico[-MAX_HISTORICO:]

        enviar_whatsapp(destino, resposta)
    except Exception as erro:
        print("Erro ao processar mensagem:", erro)


@app.post("/chat")
def chat(dados: Mensagem, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")

    return {"resposta": gerar_resposta(dados.pergunta)}


@app.post("/webhook")
async def webhook(request: Request, tarefas: BackgroundTasks):
    corpo = await request.json()
    print("Webhook recebido:", json.dumps(corpo, ensure_ascii=False)[:500])

    if str(corpo.get("event", "")).lower().replace("_", ".") != "messages.upsert":
        return {"ok": True}

    dados = corpo.get("data", {})
    chave = dados.get("key", {})

    # ignora mensagens enviadas pelo próprio bot
    if chave.get("fromMe"):
        return {"ok": True}

    jid = chave.get("remoteJid", "")

    # ignora grupos e status
    if jid.endswith("@g.us") or jid == "status@broadcast":
        return {"ok": True}

    # em contas novas o jid pode vir como @lid; tenta achar o número real
    if jid.endswith("@lid"):
        jid = chave.get("remoteJidAlt") or chave.get("senderPn") or jid

    # ignora mensagens antigas (sincronização de histórico ao reconectar)
    ts = dados.get("messageTimestamp")
    if isinstance(ts, dict):
        ts = ts.get("low")
    try:
        if ts and time.time() - int(ts) > 120:
            print("Ignorado (mensagem antiga):", jid)
            return {"ok": True}
    except (TypeError, ValueError):
        pass

    numero = jid.split("@")[0]
    if numero not in NUMEROS_PERMITIDOS:
        print("Ignorado (fora da lista):", numero)
        return {"ok": True}

    mensagem = dados.get("message", {}) or {}
    texto = (
        mensagem.get("conversation")
        or mensagem.get("extendedTextMessage", {}).get("text")
        or ""
    )

    if not texto.strip():
        return {"ok": True}

    # responde em segundo plano para o Evolution não ficar esperando o Ollama
    tarefas.add_task(processar_mensagem, jid, texto)
    return {"ok": True}