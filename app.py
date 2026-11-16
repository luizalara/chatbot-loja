import streamlit as st
import ollama
import json
from datetime import datetime

# CONFIG DA PÁGINA

st.set_page_config(
    page_title="IA de Atendimento",
    page_icon="🤖",
    layout="wide"
)
# CARREGAR EMPRESA

try:
    with open("empresa.json", "r", encoding="utf-8") as arquivo:
        empresa = json.load(arquivo)
except:
    empresa = {
        "nome_empresa": "Loja da Luiza",
        "horario": "Segunda a Sexta das 08h às 18h",
        "produtos": "Roupas femininas\nRoupas masculinas\nAcessórios",
        "pagamento": "Pix\nCartão\nDinheiro",
        "endereco": "Rua Exemplo, 123",
        "faq": """
    Prazo de entrega: Até 2 dias úteis

    Trocas: Até 30 dias

    Frete grátis: Acima de R$ 199

    Atendimento: Segunda a Sexta das 08h às 18h
    """
    }

# CARREGAR PRODUTOS


try:
    with open("produtos.json", "r", encoding="utf-8") as arquivo:
        produtos_catalogo = json.load(arquivo)
except:
    produtos_catalogo = []



# MEU SIDEBAR (usei emojis rsrs)


with st.sidebar:

    st.title("⚙️ Configurações")

    st.subheader("🖼️ Logo da Empresa")

    logo = st.file_uploader(
        "Enviar Logo",
        type=["png", "jpg", "jpeg"]
    )


    nome_empresa = st.text_input(
        "Nome da Empresa",
        empresa["nome_empresa"]
    )

    horario = st.text_area(
        "Horário de Funcionamento",
        empresa["horario"]
    )

    produtos = st.text_area(
        "Produtos e Serviços",
        empresa["produtos"]
    )

    pagamento = st.text_area(
        "Formas de Pagamento",
        empresa["pagamento"]
    )

    endereco = st.text_area(
        "Endereço",
        empresa["endereco"]
    )

    faq = st.text_area(
    "Perguntas Frequentes (FAQ)",
    empresa.get(
        "faq",
        """Prazo de entrega: Até 2 dias úteis

Trocas: Até 30 dias

Frete grátis: Acima de R$ 199

Atendimento: Segunda a Sexta das 08h às 18h"""
    )
)

    if st.button("💾 Salvar Empresa"):

        empresa = {
        "nome_empresa": nome_empresa,
        "horario": horario,
        "produtos": produtos,
        "pagamento": pagamento,
        "endereco": endereco,
        "faq": faq
}

        with open(
            "empresa.json",
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                empresa,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

        st.success("Empresa salva com sucesso!")

        

    st.divider()

    st.subheader("📦 Cadastrar Produto")

    novo_produto = st.text_input(
        "Nome do Produto"
    )

    novo_preco = st.text_input(
        "Preço"
    )

    nova_descricao = st.text_area(
        "Descrição"
    )

    novo_estoque = st.number_input(
        "Estoque",
        min_value=0,
        step=1
    )

    if st.button("Adicionar Produto"):

        produto = {
            "produto": novo_produto,
            "preco": novo_preco,
            "descricao": nova_descricao,
            "estoque": int(novo_estoque)
        }

        produtos_catalogo.append(produto)

        with open(
            "produtos.json",
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                produtos_catalogo,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

        st.success("Produto adicionado com sucesso!")
        st.rerun()

    st.divider()

    if st.button("🗑 Limpar Conversa"):
        st.session_state.mensagens = []
        st.rerun()


# TÍTULO


if logo:
    st.image(
        logo,
        width=200
    )

st.title("IA de Atendimento")

st.write(
    "Assistente virtual para pequenos negócios."
)

# DASHBOARD


total_produtos = len(produtos_catalogo)

total_estoque = sum(
    produto["estoque"]
    for produto in produtos_catalogo
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Empresa",
    nome_empresa
)

c2.metric(
    "Produtos",
    total_produtos
)

c3.metric(
    "Itens em Estoque",
    total_estoque
)

# PRODUTOS

st.subheader("📋 Produtos Cadastrados")

for indice, produto in enumerate(produtos_catalogo):

    with st.expander(f"📦 {produto['produto']}"):

        novo_nome = st.text_input(
            "Produto",
            value=produto["produto"],
            key=f"nome_{indice}"
        )

        novo_preco = st.text_input(
            "Preço",
            value=produto["preco"],
            key=f"preco_{indice}"
        )

        nova_descricao = st.text_area(
            "Descrição",
            value=produto["descricao"],
            key=f"descricao_{indice}"
        )

        novo_estoque = st.number_input(
            "Estoque",
            min_value=0,
            value=int(produto["estoque"]),
            key=f"estoque_{indice}"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                f"💾 Salvar {produto['produto']}",
                key=f"salvar_{indice}"
            ):

                produtos_catalogo[indice] = {
                    "produto": novo_nome,
                    "preco": novo_preco,
                    "descricao": nova_descricao,
                    "estoque": int(novo_estoque)
                }

                with open(
                    "produtos.json",
                    "w",
                    encoding="utf-8"
                ) as arquivo:

                    json.dump(
                        produtos_catalogo,
                        arquivo,
                        ensure_ascii=False,
                        indent=4
                    )

                st.success("Produto atualizado!")
                st.rerun()

        with col2:

            if st.button(
                f"🗑 Excluir {produto['produto']}",
                key=f"excluir_{indice}"
            ):

                produtos_catalogo.pop(indice)

                with open(
                    "produtos.json",
                    "w",
                    encoding="utf-8"
                ) as arquivo:

                    json.dump(
                        produtos_catalogo,
                        arquivo,
                        ensure_ascii=False,
                        indent=4
                    )

                st.rerun()

# CHAT

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for mensagem in st.session_state.mensagens:

    with st.chat_message(mensagem["role"]):
        st.write(mensagem["content"])

pergunta = st.chat_input(
    "Digite sua mensagem..."
)

if pergunta:

    st.session_state.mensagens.append(
        {
            "role": "user",
            "content": pergunta
        }
    )

    with st.chat_message("user"):
        st.write(pergunta)

    try:

        contexto_empresa = f"""
Empresa: {nome_empresa}

Horário:
{horario}

Serviços:
{produtos}

Formas de pagamento:
{pagamento}

Endereço:
{endereco}

FAQ:
{faq}
"""
        catalogo = ""

        for produto in produtos_catalogo:

            catalogo += f"""
Produto: {produto['produto']}
Preço: R$ {produto['preco']}
Descrição: {produto['descricao']}
Estoque: {produto['estoque']}
"""

        with st.spinner("Pensando..."):

            resposta = ollama.chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": f"""
Você é uma atendente virtual.

Informações da empresa:

{contexto_empresa}

Catálogo:

{catalogo}

Regras:
- Responda sempre em português.
- Use os produtos cadastrados.
- Informe preços quando solicitado.
- Informe estoque quando solicitado.
- Não invente produtos.
- Seja simpática e objetiva.
"""
                    },
                    {
                        "role": "user",
                        "content": pergunta
                    }
                ]
            )

            resposta = resposta["message"]["content"]
            


    except Exception as erro:

        resposta = f"Erro ao conectar com a IA:\n\n{erro}"

    # SALVAR LOG DA CONVERSA
    
    try:
        with open(
            "conversas.json",
            "r",
            encoding="utf-8"
        ) as arquivo:
            conversas = json.load(arquivo)
    except:
        conversas = []

    conversas.append(
        {
            "data": datetime.now().strftime(
                "%d/%m/%Y %H:%M"
            ),
            "pergunta": pergunta,
            "resposta": resposta
        }
    )

    with open(
        "conversas.json",
        "w",
        encoding="utf-8"
    ) as arquivo:
        json.dump(
            conversas,
            arquivo,
            ensure_ascii=False,
            indent=4
        )

    st.session_state.mensagens.append(
        {
            "role": "assistant",
            "content": resposta
        }
    )

    with st.chat_message("assistant"):
        st.write(resposta)