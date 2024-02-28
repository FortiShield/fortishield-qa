FROM ubuntu:focal

ENV DEBIAN_FRONTEND=noninteractive
ENV RUNNING_ON_DOCKER_CONTAINER=true

# install packages
RUN apt-get update && \
    apt-get install -y \
    git \
    python \
    python3-pip \
    curl \
    npm \
    apt-transport-https \
    lsb-release \
    gnupg

# install ES
RUN curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add - && \
    echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-7.x.list && \
    apt update && \
    apt install -y elasticsearch

# install fortishield manager
RUN curl -s https://packages.fortishield.github.io/key/GPG-KEY-FORTISHIELD | apt-key add - && \
    echo "deb https://packages.fortishield.github.io/4.x/apt/ stable main" | tee -a /etc/apt/sources.list.d/fortishield.list && \
    apt-get update && \
    apt-get install fortishield-manager

WORKDIR /
RUN git clone https://github.com/fortishield/fortishield-qa
WORKDIR /fortishield-qa/
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt --ignore-installed

# Install the QA framework
WORKDIR /fortishield-qa/deps/fortishield_testing
RUN python3 setup.py install

# Install search-ui deps
WORKDIR /usr/local/lib/python3.8/dist-packages/fortishield_testing-*/fortishield_testing/qa_docs/search_ui
RUN npm install

# Limit ES RAM
RUN echo "-Xms1g" >> /etc/elasticsearch/jvm.options && \
    echo "-Xmx1g" >> /etc/elasticsearch/jvm.options && \
    # Disable xpack to prevent ES showing security warning
    echo "xpack.security.enabled: false" >> /etc/elasticsearch/elasticsearch.yml

# copy entrypoint and grant permission
COPY ./entrypoint.sh /usr/bin/entrypoint.sh
RUN chmod 755 /usr/bin/entrypoint.sh

ENTRYPOINT [ "/usr/bin/entrypoint.sh" ]