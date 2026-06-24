pipeline {
    agent any

    environment {
        IMAGE_NAME = 'sentiment-ai'
        REGISTRY = 'ghcr.io/jefsaber'
        IMAGE_TAG = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Branch: ${env.BRANCH_NAME}"
                echo "Commit: ${env.GIT_COMMIT}"
                sh 'git log --oneline -5'
            }
        }

        stage('Lint') {
            steps {
                sh '''
                docker run --rm \
                  --volumes-from jenkins \
                  -w $WORKSPACE \
                  python:3.12-slim \
                  sh -c "pip install flake8 -q && flake8 src/ --max-line-length=100"
                '''
            }
        }

        stage('IaC Validate') {
            steps {
                dir('infra') {
                    sh 'terraform init -backend=false -input=false'
                    sh 'terraform fmt -check'
                    sh 'terraform validate'
                }
            }
        }

        stage('Build & Test') {
            steps {
                sh '''
                docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

                docker run --rm \
                  -e CI=true \
                  --volumes-from jenkins \
                  -w "$WORKSPACE" \
                  ${IMAGE_NAME}:${IMAGE_TAG} \
                  pytest tests/ -v \
                  --cov=src \
                  --cov-report=xml:coverage.xml \
                  --cov-report=term-missing \
                  --cov-fail-under=70

                ls -l coverage.xml
                grep -n "filename=" coverage.xml | head -20
                '''
            }
            post {
                failure {
                    echo 'Tests failed or coverage lower than 70 percent'
                }
            }
        }

        stage('SonarQube Analysis') {
            environment {
                SONARQUBE_TOKEN = credentials('sonar-token')
            }
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh '''
                    docker run --rm \
                      --network cicd-network \
                      --volumes-from jenkins \
                      -w "$WORKSPACE" \
                      -e SONAR_HOST_URL="$SONAR_HOST_URL" \
                      -e SONAR_TOKEN="$SONARQUBE_TOKEN" \
                      sonarsource/sonar-scanner-cli:latest \
                      sonar-scanner \
                      -Dsonar.projectKey=sentiment-ai \
                      -Dsonar.projectName=SentimentAI \
                      -Dsonar.projectBaseDir="$WORKSPACE" \
                      -Dsonar.sources=src \
                      -Dsonar.python.version=3.11 \
                      -Dsonar.python.coverage.reportPaths=coverage.xml \
                      -Dsonar.sourceEncoding=UTF-8 \
                      -Dsonar.scanner.metadataFilePath=$WORKSPACE/report-task.txt
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                docker run --rm \
                  -v /var/run/docker.sock:/var/run/docker.sock \
                  -v trivy-cache:/root/.cache/trivy \
                  aquasec/trivy:latest image \
                  --severity HIGH,CRITICAL \
                  --ignore-unfixed \
                  --exit-code 0 \
                  --format table \
                  ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
            post {
                failure {
                    echo 'High or critical vulnerabilities detected'
                    echo 'Please fix dependencies before deployment'
                }
            }
        }

        stage('Push') {
            when {
                anyOf {
                    branch 'main'
                    expression {
                        return env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main'
                    }
                }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-token',
                    usernameVariable: 'REGISTRY_USER',
                    passwordVariable: 'REGISTRY_PASS'
                )]) {
                    sh """
                    echo $REGISTRY_PASS | docker login ghcr.io -u $REGISTRY_USER --password-stdin

                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:latest
                    docker push ${REGISTRY}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('IaC Apply') {
            when {
                anyOf {
                    branch 'main'
                    expression {
                        return env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main'
                    }
                }
            }
            steps {
                dir('infra') {
                    sh '''
                    terraform init -input=false

                    NETWORK_ID=$(docker network inspect cicd-network --format "{{.Id}}" 2>/dev/null || true)

                    if [ -n "$NETWORK_ID" ]; then
                      terraform import \
                        -var="docker_host=unix:///var/run/docker.sock" \
                        docker_network.cicd \
                        "$NETWORK_ID" \
                        2>/dev/null || true
                    fi

                    docker rm -f sentiment-staging prometheus grafana 2>/dev/null || true

                    terraform apply -auto-approve \
                      -var="image_tag=${IMAGE_TAG}" \
                      -var="docker_host=unix:///var/run/docker.sock"
                    '''
                }
            }
        }

        stage('Deploy Staging') {
            when {
                anyOf {
                    branch 'main'
                    expression {
                        return env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main'
                    }
                }
            }
            steps {
                sh '''
                docker run --rm \
                  --network cicd-network \
                  curlimages/curl:latest \
                  -f http://sentiment-staging:8000/health
                '''
            }
        }

        stage('Smoke Test') {
            when {
                anyOf {
                    branch 'main'
                    expression {
                        return env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main'
                    }
                }
            }
            steps {
                sh '''
                echo "Waiting for services startup..."
                sleep 10

                echo "1. Checking SentimentAI health"
                docker run --rm \
                  --network cicd-network \
                  curlimages/curl:latest \
                  -f http://sentiment-staging:8000/health

                echo "Health OK"

                echo "2. Sending one prediction"
                docker run --rm \
                  --network cicd-network \
                  curlimages/curl:latest \
                  -s -X POST http://sentiment-staging:8000/predict \
                  -H "Content-Type: application/json" \
                  -d '{"text":"Ce produit est vraiment bien"}' > /dev/null

                echo "3. Checking metrics endpoint"
                docker run --rm \
                  --network cicd-network \
                  curlimages/curl:latest \
                  -s http://sentiment-staging:8000/metrics | grep -q sentiment_predictions_total

                echo "Metrics OK"

                echo "4. Waiting for Prometheus scrape..."
                sleep 20

                echo "5. Checking Prometheus target"
                docker run --rm \
                  --network cicd-network \
                  curlimages/curl:latest \
                  -s "http://prometheus:9090/api/v1/query?query=up%7Bjob%3D%22sentiment-ai%22%7D" | grep -q '"1"'

                echo "Prometheus scrape OK"

                echo "6. Checking Grafana health"
                docker run --rm \
                  --network cicd-network \
                  curlimages/curl:latest \
                  -f http://grafana:3000/api/health

                echo "Grafana OK"
                '''
            }
            post {
                failure {
                    sh 'docker logs prometheus || true'
                    sh 'docker logs sentiment-staging || true'
                    sh 'docker logs grafana || true'
                    echo 'Smoke Test failed. Check logs above.'
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded. Image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        }

        failure {
            echo 'Pipeline failed. Check logs above.'
        }
    }
}
