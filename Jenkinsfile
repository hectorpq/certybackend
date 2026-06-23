pipeline {
    agent any

    environment {
        DOCKER_BUILDKIT = '1'
        SONAR_QUBE_SERVER = 'SonarQubeServer'
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
                    
                    // 🛠️ CORRECCIÓN: Eliminamos el 'down'. Solo borramos el contenedor de pruebas previo si existiera.
                    sh 'docker rm -f test_runner || true'
                }
            }
        }

        stage('Build Infrastructure') {
            steps {
                // Compilamos usando el proyecto unificado
                sh 'docker-compose -p certybackend build --no-cache web'
                sh 'docker-compose -p certybackend build db redis'
            }
        }

        stage('Test & Coverage') {
            steps {
                // Corremos las pruebas asegurándonos de limpiar el contenedor al finalizar la etapa
                sh 'docker-compose -p certybackend run --name test_runner web pytest --cov=. --cov-report=xml'
                
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
            // 🛠️ CORRECCIÓN: Al final del pipeline solo detenemos el contenedor de pruebas, NUNCA apagamos todo el entorno con down
            sh 'docker rm -f test_runner || true'
        }
    }
}