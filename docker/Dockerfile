FROM continuumio/miniconda3

WORKDIR /opt/pbp

RUN apt-get update && apt-get install -y libsox-fmt-all libsox-dev

# Note: tentative adjustments
RUN /opt/conda/bin/conda install jupyter -y --quiet
RUN pip install mbari-pbp==1.1.0

ENV PYTHONPATH /opt/pbp:/opt/pbp/pbp
EXPOSE 8899

CMD ["/opt/conda/bin/jupyter", "notebook", "--notebook-dir=/opt/pbp", "--ip='*'","--port=8899","--no-browser", "--allow-root"]
