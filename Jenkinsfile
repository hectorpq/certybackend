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
                    // 🛠️ Sincronizado al 100% con tu .env real para que coincida con la BD local
                    sh 'echo DB_NAME=certificados_db > .env'
                    sh 'echo DB_USER=postgres >> .env'
                    sh 'echo DB_PASSWORD=123456 >> .env'
                    sh 'echo DB_HOST=db >> .env' // Se mantiene 'db' porque están dentro de la red de Docker
                    sh 'echo DB_PORT=5432 >> .env' // Puerto interno del contenedor db
                    sh 'echo SECRET_KEY=django-insecure-y+x$7x@@=@(svr3rkp&n3lhlw7&32vg661y3q(xqsi9v&is%w} >> .env'
                    sh 'echo DEBUG=True >> .env'
                    
                    // Configuración de Email para evitar errores si los tests los llaman
                    sh 'echo EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend >> .env'
                    sh 'echo EMAIL_HOST=smtp.gmail.com >> .env'
                    sh 'echo EMAIL_PORT=587 >> .env'
                    sh 'echo EMAIL_USE_TLS=True >> .env'
                    sh 'echo EMAIL_HOST_USER=rrickquispe@gmail.com >> .env'
                    sh 'echo EMAIL_HOST_PASSWORD=fogscnwqqxlgihly >> .env'
                    sh 'echo DEFAULT_FROM_EMAIL=rrickquispe@gmail.com >> .env'

                    sh 'docker rm -f test_runner || true'
                }
            }
        }

        stage('Build Infrastructure') {
            steps {
                sh 'docker-compose -p certybackend build --no-cache web'
                sh 'docker-compose -p certybackend build db redis'
            }
        }

        stage('Test & Coverage') {
            steps {
                sh 'docker-compose -p certybackend run --name test_runner web pytest --reuse-db --cov=. --cov-report=xml'
                
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
            sh 'docker rm -f test_runner || true'
        }
    }
}