FROM quay.io/jupyter/minimal-notebook:06fac8278099

## Some of the following as indicated in mybinder.org documentation.
## However, the base image above already has some of these in place,
## like user and uid, maybe others.
ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER=${NB_USER}
ENV NB_UID=${NB_UID}
ENV HOME=/home/${NB_USER}

WORKDIR ${HOME}

RUN pip install mbari-pbp==1.0.8

## TODO Copy some resources to faciliate use
#COPY .... ${HOME}

USER root
RUN apt-get update && apt-get install -y libsox-fmt-all libsox-dev
RUN chown -R ${NB_UID} ${HOME}
USER ${NB_USER}

## "Inherited Dockerfiles may unset the entrypoint with:"
ENTRYPOINT []
