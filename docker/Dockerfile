FROM continuumio/miniconda3

WORKDIR /opt/pbp

RUN apt-get update && apt-get install -y libsox-fmt-all libsox-dev

# TODO PBP should be installed from published package.
#  For now, grabbing the latest from their repos.
RUN git clone https://github.com/mbari-org/pbp.git \
 && cd pbp \
 && pip install -r requirements.txt \
 && /opt/conda/bin/conda install jupyter -y --quiet

ENV PYTHONPATH /opt/pbp:/opt/pbp/pbp
EXPOSE 8899

CMD ["/opt/conda/bin/jupyter", "notebook", "--notebook-dir=/opt/pbp", "--ip='*'","--port=8899","--no-browser", "--allow-root"]
