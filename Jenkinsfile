pipeline {
    agent any

    environment {
        DOCKER_BUILDKIT = '1'
        SONAR_QUBE_SERVER = 'SonarQubeServer'
    }

    // Usamos el identificador con guion exacto para mapear SonarRunnerInstallation
    tools {
        'sonar-runner' 'SonarQubeScanner'
    }

    stages {
        stage('Limpieza y Entorno') {
            steps {
                script {
                    sh 'echo DB_NAME=postgres > .env'
                    sh 'echo DB_USER=postgres >> .env'
                    sh 'echo DB_PASSWORD=postgres >> .env'
                    sh 'echo DB_HOST=db >> .env'
                    sh 'echo DB_PORT=5432 >> .env'
                    sh 'echo SECRET_KEY=django-insecure-test-key-123 >> .env'
                    sh 'echo DEBUG=True >> .env'
                    
                    sh 'docker-compose down --remove-orphans || true'
                }
            }
        }

        stage('Build Infrastructure') {
            steps {
                sh 'docker-compose build --no-cache web'
                sh 'docker-compose build db redis'
            }
        }

        stage('Test & Coverage') {
            steps {
                sh 'docker-compose run --rm web pytest --cov=. --cov-report=xml'
            }
        }

        stage('Static Analysis (SonarQube)') {
            steps {
                withSonarQubeEnv("${SONAR_QUBE_SERVER}") {
                    withCredentials([string(credentialsId: 'sonar-server-token', variable: 'SONAR_TOKEN')]) {
                        sh "sonar-scanner -Dsonar.login=${SONAR_TOKEN} -Dsonar.projectBaseDir=$WORKSPACE"
                    }
                }
            }
        }
    }

    post {
        always {
            sh 'docker-compose down --remove-orphans || true'
        }
    }
}