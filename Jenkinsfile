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
                // 1. Ejecutamos las pruebas de forma normal usando el código interno de la imagen compilada
                sh 'docker-compose run --name test_runner web pytest --cov=. --cov-report=xml'
                
                // 2. Extraemos el archivo coverage.xml directamente leyendo el flujo del contenedor de test
                script {
                    sh 'docker cp test_runner:/app/coverage.xml ./coverage.xml'
                    sh 'docker rm -f test_runner'
                }
            }
        }

        stage('Static Analysis (SonarQube)') {
            steps {
                script {
                    def scannerHome = tool name: 'SonarQubeScanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                    
                    withSonarQubeEnv("${SONAR_QUBE_SERVER}") {
                        withCredentials([string(credentialsId: 'sonar-server-token', variable: 'SONAR_TOKEN')]) {
                            // Añadimos el relizamiento de rutas para que SonarQube asocie /app con la raíz del proyecto
                            sh "${scannerHome}/bin/sonar-scanner " +
                               "-Dsonar.login=${SONAR_TOKEN} " +
                               "-Dsonar.projectBaseDir=$WORKSPACE " +
                               "-Dsonar.python.coverage.reportPaths=coverage.xml " +
                               "-Dsonar.sources=."
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