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
            echo "Image $IMAGE:$TAG built and verified"
        }
    }
}
