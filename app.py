# Importa as bibliotecas necessárias para a aplicação Streamlit
import streamlit as st
import pdfplumber
import re
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from datetime import datetime
import locale

# Define a configuração da página para usar a largura total do navegador
st.set_page_config(layout="wide")

# --- Configurações de Layout e Estilo ---
# Novo esquema de cores: Azul profissional
blue_main_translucent = "rgba(0, 71, 171, 0.8)"  # Azul principal com transparência (80%)
blue_dark_translucent = "rgba(0, 51, 141, 0.8)"   # Azul mais escuro para o hover, também com transparência

# Estilo para o cabeçalho e para o widget de upload, injetado via markdown
st.markdown(
    f"""
    <style>
    .header-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 20px;
        background-color: {blue_main_translucent};
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    .header-container img {{
        max-height: 80px;
        margin-bottom: 15px;
        border-radius: 5px;
    }}
    .stDownloadButton > button {{
        background-color: {blue_main_translucent} !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 12px 25px !important;
        font-weight: bold !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }}
    .stDownloadButton > button:hover {{
        background-color: {blue_dark_translucent} !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    .stMarkdown h3 {{
        color: {blue_dark_translucent};
        border-bottom: 2px solid {blue_main_translucent};
        padding-bottom: 5px;
    }}
    /* Estilo para alterar o texto nativo do widget de upload */
    [data-testid="stFileUploadDropzone"] div div::after {{
        content: " ou clique para procurar no seu computador";
        display: inline;
        color: gray;
    }}
    [data-testid="stFileUploadDropzone"] div div::before {{
        content: "Arraste e solte o PDF da lista de presença aqui";
        display: block;
        color: {blue_dark_translucent};
        font-weight: bold;
        margin-bottom: 5px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Container principal para um visual mais organizado
with st.container():
    st.markdown(
        f"""
        <div class="header-container">
            <h1>Filtrar Alunos com Faltas</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 📄 Informações do Processo")

    # Cria um widget para o usuário fazer o upload de um arquivo PDF
    # O texto do widget foi alterado para português via CSS
    uploaded_file = st.file_uploader("", type="pdf")

    # O código abaixo será executado somente se um arquivo for enviado
    if uploaded_file:
        # Exibe uma mensagem de status enquanto o processamento ocorre
        st.info("Processando PDF... aguarde ⏳")
        
        # Lista para armazenar os índices das páginas que contêm alunos com falta
        paginas_com_falta_indices = []

        try:
            # Voltar ao início do arquivo para que pdfplumber possa lê-lo
            uploaded_file.seek(0)
            
            # Abrir o PDF com pdfplumber para extração de tabelas
            with pdfplumber.open(uploaded_file) as pdf:
                # Itera sobre cada página do documento, com seu índice
                for i, pagina in enumerate(pdf.pages):
                    # Tenta extrair tabelas da página
                    tabelas = pagina.extract_tables()
                    
                    # Assume que a página não tem faltas até que um 'F' seja encontrado
                    pagina_com_falta = False
                    
                    # Itera sobre as tabelas encontradas na página
                    for tabela in tabelas:
                        # Itera sobre as linhas da tabela
                        for linha in tabela:
                            # Itera sobre as células da linha
                            for celula in linha:
                                # Verifica se a célula contém a letra 'F' (indicando falta)
                                # A verificação é sensível ao caso, pois 'F' é o padrão para falta
                                if celula and 'F' in celula:
                                    pagina_com_falta = True
                                    # Interrompe as buscas se uma falta for encontrada na página
                                    break 
                            if pagina_com_falta:
                                break
                        if pagina_com_falta:
                            break
                    
                    # Se uma falta foi encontrada em qualquer tabela da página, adiciona o índice
                    if pagina_com_falta:
                        paginas_com_falta_indices.append(i)

        except Exception as e:
            # Exibe uma mensagem de erro se algo der errado durante o processamento
            st.error(f"Ocorreu um erro ao processar o PDF: {e}")
            # Interrompe a execução para evitar mais erros
            st.stop()

        # Verifica se alguma página com falta foi encontrada
        if not paginas_com_falta_indices:
            st.warning("Nenhum aluno com falta encontrado no PDF!")
        else:
            # Exibe uma mensagem de sucesso com o número de páginas encontradas
            st.success(f"✔️ {len(paginas_com_falta_indices)} páginas com faltas encontradas!")

            # Gerar o novo PDF usando pypdf, que mantém o layout original
            try:
                # Voltar ao início do arquivo para que pypdf possa lê-lo
                uploaded_file.seek(0)
                reader = PdfReader(uploaded_file)
                writer = PdfWriter()

                # Adiciona apenas as páginas que contêm faltas ao novo PDF
                for idx in paginas_com_falta_indices:
                    writer.add_page(reader.pages[idx])

                # Cria um buffer de memória para o novo arquivo PDF
                output = BytesIO()
                writer.write(output)
                output.seek(0)
                
                # Obtém o nome do mês atual para incluir no nome do arquivo
                nome_arquivo = "alunos_com_falta.pdf"

                # Cria o botão de download para o usuário
                st.download_button(
                    label="📥 Baixar PDF apenas com alunos faltantes",
                    data=output,
                    file_name=nome_arquivo,
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar o novo PDF: {e}")

