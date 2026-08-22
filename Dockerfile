# Imagem do servidor de legislação de Mesquita (Render, Cloud Run, Fly e afins).
FROM python:3.12-slim

WORKDIR /app

# As dependências mudam menos que o código: instaladas antes, para aproveitar o
# cache entre construções.
COPY requirements-servidor.txt ./
RUN pip install --no-cache-dir -r requirements-servidor.txt

COPY legis/ ./legis/

# O acervo viaja no repositório, comprimido, e é descomprimido aqui.
#
# A decisão anterior era outra — asset de release, baixado na construção — e
# está registrada no METODO.md junto com o motivo da troca. Em resumo: são
# 21,6 MB numa base que se recoleta uma ou duas vezes por ano, e vindo pelo Git
# desaparecem três modos de falha que a release trazia (repositório privado
# devolvendo 404 no download, asset errado anexado, URL divergente do nome do
# repositório) além da dependência de rede no build.
#
# O que NÃO mudou é a cadeia de integridade: o sha256 continua declarado aqui e
# conferido antes de descomprimir. Divergindo o arquivo, a construção falha em
# vez de subir um acervo diferente daquele que foi testado. Publicar acervo
# novo é trocar estas duas linhas e commitar o novo .gz.
#
# Gerado por `python preparar_release.py 1.5.0`: 4.143 atos, 67,8 → 21,1 MB.
ARG ACERVO=acervo/legislacao-mesquita-v1.5.0.db.gz
ARG ACERVO_SHA256=09ab7e550672ea43a1b58869bcd5626d9c8944398f259277a5eedc4087f22abc
COPY instalar_acervo.py ./
COPY acervo/ ./acervo/
RUN python instalar_acervo.py "$ACERVO" dados/mesquita.sqlite "$ACERVO_SHA256" \
    && rm -rf acervo/

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
