pipeline {
    agent any

    environment {
        E2E_BASE_URL = "http://127.0.0.1"
        E2E_EMAIL_DIR = "${WORKSPACE}/server/.dev-emails"

        STAGING_SSH_HOST = "54.221.255.24"
        STAGING_BASE_URL = "http://${STAGING_SSH_HOST}"

        PROD_SSH_HOST = "44.223.130.58"
        PROD_BASE_URL = "http://${PROD_SSH_HOST}"

        // AWS Config
        AWS_REGION = "ap-southeast-2"
        ECR_REGISTRY = "309858210311.dkr.ecr.ap-southeast-2.amazonaws.com"

        // RDS & S3 Config
        DB_HOST = "rmit-store-infra-rmitdatabase-r9zxdgvssnp0.c38ikukessnm.ap-southeast-2.rds.amazonaws.com"
        S3_BUCKET = "rmit-store-infra-mediabucket-rg166hqxyinn"
    }

    stages {
        stage('Backend: install & test') {
            steps {
                dir('server') {
                    echo 'Creating Python virtual environment...'
                    sh 'python3 -m venv .venv'
                    echo 'Installing backend dependencies...'
                    sh '.venv/bin/pip install -r requirements-dev.txt'
                    echo 'Running backend unit and integration tests...'
                    sh '''
                        mkdir -p results
                        .venv/bin/pytest --junitxml=results/junit.xml --cov=apps --cov-report=xml:results/coverage.xml --cov-report=term
                    '''
                }
            }
            post {
                always {
                    junit(allowEmptyResults: true, testResults: 'server/results/junit.xml')
                }
            }
        }

        stage('Frontend: install & build') {
            steps {
                dir('client') {
                    echo 'Installing frontend dependencies...'
                    sh 'npm ci'
                    echo 'Building Vue frontend...'
                    sh 'npm run build'
                }
            }
        }

        stage('Build & Push Docker Images to ECR') {
            steps {
                echo 'Authenticating and Pushing to AWS ECR...'
                withCredentials([usernamePassword(credentialsId: 'aws-ecr-credentials', passwordVariable: 'AWS_SECRET_ACCESS_KEY', usernameVariable: 'AWS_ACCESS_KEY_ID')]) {
                    sh '''
                        export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
                        export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
                        COMMIT_HASH=$(git rev-parse --short HEAD)

                        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

                        echo 'Building Images...'
                        docker build -t ${ECR_REGISTRY}/rmit-store-frontend:${BUILD_NUMBER} ./client
                        
                        docker build \
                            --build-arg APP_VERSION=${BUILD_NUMBER} \
                            --build-arg GIT_COMMIT=${COMMIT_HASH} \
                            -t ${ECR_REGISTRY}/rmit-store-backend:${BUILD_NUMBER} ./server

                        echo 'Pushing Images...'
                        docker push ${ECR_REGISTRY}/rmit-store-frontend:${BUILD_NUMBER}
                        docker push ${ECR_REGISTRY}/rmit-store-backend:${BUILD_NUMBER}
                    '''
                }
            }
        }

        stage('Start CI Environment for E2E') {
            steps {
                echo 'Cleaning previous CI containers...'
                sh 'docker-compose down --remove-orphans || true'
                echo 'Preparing E2E email directory...'
                sh 'mkdir -p server/.dev-emails'
                echo 'Starting CI Services...'

                sh 'BACKEND_IMAGE=${ECR_REGISTRY}/rmit-store-backend:${BUILD_NUMBER} FRONTEND_IMAGE=${ECR_REGISTRY}/rmit-store-frontend:${BUILD_NUMBER} docker-compose up -d'

                sh 'sleep 15'
                sh 'docker-compose exec -T backend python manage.py migrate'

                withCredentials([string(credentialsId: 'rmit-ci-test-password', variable: 'CI_TEST_PASSWORD')]) {
                    sh '''
                        docker-compose exec -T backend python manage.py seed_demo --admin-email admin@rmit.edu.au --admin-password "$CI_TEST_PASSWORD"
                    '''
                }
                sh 'docker-compose exec -T frontend sh -c "echo \\"window.CONFIG = { API_URL: \'http://127.0.0.1:8000\' };\\" > /usr/share/nginx/html/config.js"'
            }
        }

        stage('E2E: web UI journeys') {
            steps {
                sh 'sed -i \'s/await page.goto(signupLink)/const fixedLink = signupLink.replace("localhost:5173", "127.0.0.1"); await page.goto(fixedLink)/g\' e2e/tests/seller-lifecycle.spec.js'
                withCredentials([string(credentialsId: 'rmit-ci-test-password', variable: 'CI_TEST_PASSWORD')]) {
                    sh '''
                        docker run --rm --network host --ipc=host \
                            -e E2E_BASE_URL="${E2E_BASE_URL}" -e BASE_URL="${E2E_BASE_URL}" \
                            -e TEST_PASSWORD="$CI_TEST_PASSWORD" -e ADMIN_PASSWORD="$CI_TEST_PASSWORD" \
                            -e E2E_EMAIL_DIR=/server/.dev-emails \
                            -v "${WORKSPACE}/e2e:/e2e" -v "${WORKSPACE}/server:/server" \
                            -w /e2e mcr.microsoft.com/playwright:v1.62.1-jammy bash -c 'npm ci && npx playwright test'
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts(artifacts: 'e2e/test-results/**/*', allowEmptyArchive: true)
                }
            }
        }

        stage('Smoke test (CI Container)') {
            steps {
                sh 'python3 scripts/smoke_test.py --base-url http://127.0.0.1:8000 --retries 5 --retry-delay 5'
            }
        }

        stage('Deploy to Staging') {
            when { expression { env.GIT_BRANCH == 'origin/main' || env.BRANCH_NAME == 'main' } }
            steps {
                withCredentials([
                    sshUserPrivateKey(credentialsId: 'rmit-staging-ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
                    usernamePassword(credentialsId: 'aws-ecr-credentials', passwordVariable: 'AWS_SECRET_ACCESS_KEY', usernameVariable: 'AWS_ACCESS_KEY_ID')
                ]) {
                    sh '''#!/usr/bin/env bash
                    set -euo pipefail
                    COMMIT_HASH="$(git rev-parse --short HEAD)"
                    RELEASE_DIR="/home/ec2-user/rmit-store-releases/${BUILD_NUMBER}"
                    REMOTE="${SSH_USER}@${STAGING_SSH_HOST}"
                    SSH_OPTIONS=(-i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no)

                    ssh "${SSH_OPTIONS[@]}" "$REMOTE" "mkdir -p '$RELEASE_DIR'"
                    git archive --format=tar HEAD | ssh "${SSH_OPTIONS[@]}" "$REMOTE" "tar -xf - -C '$RELEASE_DIR'"

                    ssh "${SSH_OPTIONS[@]}" "$REMOTE" "
                        set -e
                        export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
                        export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
                        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

                        cd '$RELEASE_DIR'
                        export STACK_NAME='rmit-staging'
                        export APP_VERSION='staging-${BUILD_NUMBER}'
                        export GIT_COMMIT='$COMMIT_HASH'
                        export BACKEND_IMAGE='${ECR_REGISTRY}/rmit-store-backend:${BUILD_NUMBER}'
                        export FRONTEND_IMAGE='${ECR_REGISTRY}/rmit-store-frontend:${BUILD_NUMBER}'
                        export DB_HOST='${DB_HOST}'
                        export AWS_STORAGE_BUCKET_NAME='${S3_BUCKET}'

                        bash scripts/swarm/deploy.sh
                    "
                    '''
                }
            }
        }

        stage('Verify Staging Deployment') {
            when { expression { env.GIT_BRANCH == 'origin/main' || env.BRANCH_NAME == 'main' } }
            steps {
                sh 'sleep 15'
                sh 'python3 scripts/smoke_test.py --base-url "${STAGING_BASE_URL}" --retries 10 --retry-delay 5 --expect-commit "$(git rev-parse --short HEAD)"'
            }
        }

        stage('Deploy to Production') {
            when { expression { env.GIT_BRANCH == 'origin/main' || env.BRANCH_NAME == 'main' } }
            steps {
                withCredentials([
                    sshUserPrivateKey(credentialsId: 'rmit-prod-ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
                    usernamePassword(credentialsId: 'aws-ecr-credentials', passwordVariable: 'AWS_SECRET_ACCESS_KEY', usernameVariable: 'AWS_ACCESS_KEY_ID')
                ]) {
                    sh '''#!/usr/bin/env bash
                    set -euo pipefail
                    COMMIT_HASH="$(git rev-parse --short HEAD)"
                    RELEASE_DIR="/home/ec2-user/rmit-store-releases/${BUILD_NUMBER}"
                    REMOTE="${SSH_USER}@${PROD_SSH_HOST}"
                    SSH_OPTIONS=(-i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no)

                    ssh "${SSH_OPTIONS[@]}" "$REMOTE" "mkdir -p '$RELEASE_DIR'"
                    git archive --format=tar HEAD | ssh "${SSH_OPTIONS[@]}" "$REMOTE" "tar -xf - -C '$RELEASE_DIR'"

                    ssh "${SSH_OPTIONS[@]}" "$REMOTE" "
                        set -e
                        export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
                        export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
                        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

                        cd '$RELEASE_DIR'
                        export STACK_NAME='rmit-prod'
                        export APP_VERSION='prod-${BUILD_NUMBER}'
                        export GIT_COMMIT='$COMMIT_HASH'
                        export BACKEND_IMAGE='${ECR_REGISTRY}/rmit-store-backend:${BUILD_NUMBER}'
                        export FRONTEND_IMAGE='${ECR_REGISTRY}/rmit-store-frontend:${BUILD_NUMBER}'
                        export DB_HOST='${DB_HOST}'
                        export AWS_STORAGE_BUCKET_NAME='${S3_BUCKET}'

                        bash scripts/swarm/deploy.sh
                    "
                    '''
                }
            }
        }

        stage('Verify Production Deployment') {
            when { expression { env.GIT_BRANCH == 'origin/main' || env.BRANCH_NAME == 'main' } }
            steps {
                sh 'sleep 15'
                sh 'python3 scripts/smoke_test.py --base-url "${PROD_BASE_URL}" --retries 10 --retry-delay 5 --expect-commit "$(git rev-parse --short HEAD)"'
            }
        }
    }

    post {
        success { echo 'CI pipeline completed successfully.' }
        failure {
            echo 'Pipeline failed. Production deployment must not continue.'
            mail to: 'admin@rmit.edu.au', subject: "FAILED: Jenkins Job '${env.JOB_NAME} [Build #${env.BUILD_NUMBER}]'", body: "Pipeline failed. Check console output: ${env.BUILD_URL}"
        }
        always {
            sh 'docker-compose down --remove-orphans || true'
        }
    }
}
