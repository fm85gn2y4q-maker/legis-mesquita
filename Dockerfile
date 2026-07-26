# Imagem do servidor de legislação de Mesquita (Render, Cloud Run, Fly e afins).
FROM python:3.12-slim

WORKDIR /app

# As dependências mudam menos que o código: instaladas antes, para aproveitar o
# cache entre construções.
COPY requirements-servidor.txt ./
RUN pip install --no-cache-dir -r requirements-servidor.txt

COPY legis/ ./legis/

# O acervo é artefato de dados, não código-fonte: vem de um asset de release,
# com a versão fixada. Assim o deploy é reproduzível, o rollback é trocar a
# versão, e o histórico do Git não carrega uma cópia binária a cada coleta.
#
# A versão é declarada AQUI, como padrão do ARG, e não como argumento de
# construção do serviço de hospedagem: nem todo serviço repassa argumentos de
# build, e depender disso deixa a imagem sem acervo por um motivo invisível.
#
# A conferência do sha256 fecha a cadeia: divergindo o arquivo publicado, a
# construção falha em vez de subir um acervo diferente do declarado.
# Publicar acervo novo é trocar estas duas linhas.
# Gerados por `python preparar_release.py 1.0.0` sobre o acervo de v1.0.0:
# 4.129 atos, 69,2 MB → 21,6 MB comprimidos.
#
# O usuário do GitHub veio do projeto anterior; se o repositório desta base
# tiver outro nome, é esta linha — e só ela — que muda.
ARG ACERVO_URL=https://github.com/fm85gn2y4q-maker/legis-mesquita/releases/download/acervo-v1.0.0/legislacao-mesquita-v1.0.0.db.gz
ARG ACERVO_SHA256=96403c42352342e6c3e9adba7adba0b40e1f54b3536a4d39299280e5a63cded4
COPY baixar_acervo.py ./
RUN python baixar_acervo.py "$ACERVO_URL" dados/mesquita.sqlite "$ACERVO_SHA256"

# O serviço define a porta; 8080 é o padrão do Cloud Run quando ele não define.
ENV PORT=8080 \
    LEGIS_HOST=0.0.0.0 \
    LEGIS_BANCO=/app/dados/mesquita.sqlite \
    PYTHONUTF8=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

# LEGIS_DOMINIOS é definido depois do primeiro deploy, quando o endereço
# público passa a existir. Sem ele, só requisições locais são aceitas — o que
# na prática significa que o serviço responde 421 a tudo.
CMD ["python", "-m", "legis", "--http"]
