pipeline {
    agent any

    environment {
        DOCKER_BUILDKIT = '1'
        SONAR_QUBE_SERVER = 'SonarQubeServer'
    }

    // 🛠️ Eliminamos el bloque 'tools' conflictivo de aquí arriba

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
                // 🚀 SOLUCIÓN: Mapeamos el directorio actual ($WORKSPACE) al directorio /app del contenedor de pruebas
                // Esto hace que cualquier archivo que escriba pytest aparezca mágicamente afuera al instante.
                sh 'docker-compose run --rm -v $WORKSPACE:/app web pytest --cov=. --cov-report=xml'
            }
        }

        stage('Static Analysis (SonarQube)') {
            steps {
                script {
                    def scannerHome = tool name: 'SonarQubeScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                    
                    withSonarQubeEnv("${SONAR_QUBE_SERVER}") {
                        withCredentials([string(credentialsId: 'sonar-server-token', variable: 'SONAR_TOKEN')]) {
                            // Invocamos el scanner apuntando al archivo mapeado nativamente
                            sh "${scannerHome}/bin/sonar-scanner " +
                               "-Dsonar.login=${SONAR_TOKEN} " +
                               "-Dsonar.projectBaseDir=$WORKSPACE " +
                               "-Dsonar.python.coverage.reportPaths=coverage.xml"
                        }
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