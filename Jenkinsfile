pipeline {
    agent any

    environment {
        // Nombre de la herramienta configurada en "Global Tool Configuration"
        SCANNER_HOME = tool 'SonarScanner'
        // ID de la credencial de GitHub guardada en Jenkins
        GITHUB_TOKEN_ID = 'github-token' 
    }

    stages {
        stage('Checkout') {
            steps {
                // Usamos las credenciales para clonar o actualizar el código
                checkout scm
            }
        }

        stage('Limpieza') {
            steps {
                script{
                    sh '''
                        echo "DB_NAME=postgres" > .env
                        echo "DB_USER=postgres" >> .env
                        echo "DB_PASSWORD=postgres" >> .env
                        echo "DB_HOST=db" >> .env
                        echo "DB_PORT=5432" >> .env
                        echo "SECRET_KEY=secret_key_de_test_123" >> .env
                        echo "DEBUG=True" >> .env
                    '''
                }
                sh 'docker compose down --remove-orphans || true'
                
            }
        }

        stage('Build') {
            steps {
                // Construye la imagen con las dependencias del sistema (GDAL, libpq, etc.)
                sh 'docker-compose build web'
            }
        }

        stage('Test & Coverage') {
            steps {
                // Ejecuta pytest y genera el reporte XML para SonarQube
                sh 'docker compose run --rm web pytest --cov=. --cov-report=xml'
            }
        }

        stage('Linting (Estilo)') {
            steps {
                // Asegura la calidad de estilo con flake8
                sh 'docker compose run --rm web flake8 .'
            }
        }

        stage('Static Analysis (SonarQube)') {
            steps {
                // El bloque withSonarQubeEnv inyecta la URL y el Token de SonarQube
                withSonarQubeEnv('SonarQubeServer') {
                    // Usamos el token de GitHub para la decoración de Pull Requests
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
            // Limpia los contenedores de db (PostgreSQL) y redis al finalizar
            sh 'docker compose down'
        }
    }
}