// CI/CD pipeline for the AI Simulator Service.
// Runs on the local Jenkins server from jenkins/docker-compose.yml (see docs/JENKINS_SETUP.md).
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 30, unit: 'MINUTES')
    }

    // GitHub cannot reach a Jenkins running on a laptop, so poll instead of a webhook
    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        IMAGE = 'ai-sim-service'
        // Prefix for the throwaway containers and network of this build
        CI_ID = "ai-sim-ci-${env.BUILD_NUMBER}"
        // Minikube (docker driver) runs as a container with this name on the host engine
        MINIKUBE_NODE = 'minikube'
    }

    parameters {
        booleanParam(name: 'DEPLOY', defaultValue: true, description: 'Deploy to Minikube after all checks pass')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_SHORT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
                    currentBuild.displayName = "#${env.TAG}"
                }
            }
        }

        stage('Build test image') {
            steps {
                sh 'docker build --target test -t $IMAGE:$TAG-test .'
            }
        }

        stage('Lint') {
            steps {
                sh 'docker run --rm $IMAGE:$TAG-test ruff check app tests'
            }
        }

        stage('Unit tests') {
            steps {
                // Real Redis on a private network, as in production
                sh '''
                    docker network create $CI_ID
                    docker run -d --name $CI_ID-redis --network $CI_ID --network-alias redis redis:7-alpine
                    docker create --name $CI_ID-tests --network $CI_ID -e REDIS_URL=redis://redis:6379 \
                        $IMAGE:$TAG-test pytest --junitxml=reports/junit.xml
                    set +e
                    docker start -a $CI_ID-tests
                    status=$?
                    set -e
                    mkdir -p reports
                    docker cp $CI_ID-tests:/app/reports/junit.xml reports/junit.xml || true
                    exit $status
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                }
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build --target runtime -t $IMAGE:$TAG -t $IMAGE:latest .'
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                    docker run -d --name $CI_ID-smoke $IMAGE:$TAG
                    docker exec -i $CI_ID-smoke python - < scripts/smoke_test.py
                '''
            }
            post {
                failure {
                    sh 'docker logs $CI_ID-smoke || true'
                }
            }
        }

        stage('Deploy to Minikube') {
            when {
                expression { params.DEPLOY }
            }
            steps {
                withCredentials([file(credentialsId: 'minikube-kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        # No registry: stream the image into the container runtime of the Minikube node
                        # (containerd by default since Minikube 1.39, Docker in older versions)
                        if docker exec $MINIKUBE_NODE docker info >/dev/null 2>&1; then
                            loader="docker load"
                        else
                            loader="ctr -n k8s.io images import -"
                        fi
                        docker save $IMAGE:$TAG $IMAGE:latest | docker exec -i $MINIKUBE_NODE $loader

                        kubectl apply -f k8s/00-namespace.yaml -f k8s/10-redis.yaml -f k8s/30-service.yaml
                        sed "s|image: ai-sim-service:latest|image: $IMAGE:$TAG|" k8s/20-ai-sim.yaml | kubectl apply -f -
                        kubectl -n ai-sim rollout status deployment/ai-sim --timeout=180s

                        # Same smoke test, now inside a pod of the new deployment
                        kubectl -n ai-sim exec -i deploy/ai-sim -- python - < scripts/smoke_test.py
                        kubectl -n ai-sim get pods,svc -o wide
                    '''
                }
            }
        }
    }

    post {
        always {
            sh '''
                docker rm -f $CI_ID-tests $CI_ID-redis $CI_ID-smoke >/dev/null 2>&1 || true
                docker network rm $CI_ID >/dev/null 2>&1 || true
                docker image rm $IMAGE:$TAG-test >/dev/null 2>&1 || true
            '''
        }
        success {
            echo "Image ${env.IMAGE}:${env.TAG} built, verified${params.DEPLOY ? ' and deployed to Minikube' : ''}"
        }
    }
}
