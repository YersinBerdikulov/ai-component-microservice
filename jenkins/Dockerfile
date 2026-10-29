# Jenkins LTS with the tools the pipeline needs:
#   docker CLI (+ buildx) - talks to the host Docker engine through the mounted socket
#   kubectl               - deploys to Minikube
FROM jenkins/jenkins:lts-jdk21

USER root

COPY --from=docker:29-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:29-cli /usr/local/libexec/docker/cli-plugins/docker-buildx /usr/local/libexec/docker/cli-plugins/docker-buildx

ARG KUBECTL_VERSION=v1.37.2
ARG TARGETARCH=amd64
RUN curl -fsSLo /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" \
    && chmod +x /usr/local/bin/kubectl

USER jenkins

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
