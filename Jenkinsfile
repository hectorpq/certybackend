pipeline {
    agent any

    environment {
        SCANNER_HOME = tool 'SonarScanner'
        GITHUB_TOKEN_ID = 'github-token' 
    }

    stages {
        stage('Limpieza y Entorno') {
            steps {
                script {
                    // Generamos el .env necesario para Django y Docker Compose
                    sh '''
                        echo "DB_NAME=postgres" > .env
                        echo "DB_USER=postgres" >> .env
                        echo "DB_PASSWORD=postgres" >> .env
                        echo "DB_HOST=db" >> .env
                        echo "DB_PORT=5432" >> .env
                        echo "SECRET_KEY=django-insecure-test-key-123" >> .env
                        echo "DEBUG=True" >> .env
                    '''
                    // Aseguramos permisos del socket para que Testcontainers funcione en 'web'
                    sh 'chmod 666 /var/run/docker.sock || true'
                }
                // Limpieza profunda de intentos fallidos anteriores
                sh 'docker compose down --remove-orphans || true'
            }
        }

        stage('Build') {
            steps {
                sh 'docker compose build web'
            }
        }

        stage('Test & Coverage') {
            steps {
                // Ahora 'web' tiene el socket mapeado, Testcontainers podrá levantar el Postgres de prueba
                sh 'docker compose run --rm web pytest --cov=. --cov-report=xml'
            }
        }

        stage('Linting (Estilo)') {
            steps {
                sh 'docker compose run --rm web flake8 . || true'
            }
        }

        stage('Static Analysis (SonarQube)') {
            steps {
                withSonarQubeEnv('SonarQubeServer') {
                    withCredentials([string(credentialsId: "${GITHUB_TOKEN_ID}", variable: 'GITHUB_TOKEN')]) {
                        sh """
                        ${SCANNER_HOME}/bin/sonar-scanner \
                        -Dsonar.analysis.github.token=${GITHUB_TOKEN}
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            // Siempre limpiar para no dejar procesos consumiendo RAM
            sh 'docker compose down --remove-orphans'
        }
    }
}