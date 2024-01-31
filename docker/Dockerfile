FROM continuumio/miniconda3

WORKDIR /opt/pbp

RUN apt-get update && apt-get install -y libsox-fmt-all libsox-dev

# TODO both PyPAM and PBP should be installed from published packages.
#  For now, grabbing the latest from their repos.
RUN git clone https://github.com/mbari-org/pypam-based-processing.git \
 && cd pypam-based-processing \
 && pip install -r requirements.txt

# Separated RUNs while testing
RUN pip install git+https://github.com/lifewatch/pypam.git
RUN /opt/conda/bin/conda install jupyter -y --quiet

ENV PYTHONPATH /opt/pbp:/opt/pbp/pypam-based-processing
EXPOSE 8899

CMD ["/opt/conda/bin/jupyter", "notebook", "--notebook-dir=/opt/pbp", "--ip='*'","--port=8899","--no-browser", "--allow-root"]
