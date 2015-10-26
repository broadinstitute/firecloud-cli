FROM phusion/baseimage

RUN \
  apt-get update \
  && apt-get install -y -qq --no-install-recommends \
    python python-pip \
  && apt-get -yq autoremove && apt-get -yq clean && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* && rm -rf /var/tmp/*

RUN curl https://sdk.cloud.google.com | bash
ENV PATH="/root/google-cloud-sdk/bin:$PATH"
# Tell gcloud to save state in /.config so it's easy to override as a mounted volume.
ENV HOME=/

RUN pip install virtualenv
COPY . /firecloud-cli
WORKDIR /firecloud-cli
RUN ./install.sh
ENV PATH="/.firecloud-cli/ubin:$PATH"

RUN mkdir /working
WORKDIR /working

CMD ["firecloud", "--help"]
