pipeline {
    agent any

    environment {
        // Nombre de la herramienta configurada en "Global Tool Configuration"
        SCANNER_HOME = tool 'SonarScanner'
    }

    stages {
        stage('Limpieza') {
            steps {
                // Elimina contenedores previos para evitar conflictos de puertos o datos
                sh 'docker compose down'
            }
        }

        stage('Build') {
            steps {
                // Construye la imagen usando el Dockerfile que instalara GDAL y dependencias
                sh 'docker compose build web'
            }
        }

        stage('Test & Coverage') {
            steps {
                // Ejecuta pytest y genera el reporte de cobertura para SonarQube
                // Se usa --cov para que Sonar pueda mostrar qué porcentaje del código está probado
                sh 'docker compose run --rm web pytest --cov=. --cov-report=xml'
            }
        }

        stage('Linting (Estilo)') {
            steps {
                // Ejecuta flake8 para asegurar que el código sigue las reglas de estilo
                sh 'docker compose run --rm web flake8 .'
            }
        }

        stage('Static Analysis (SonarQube)') {
            steps {
                // El bloque withSonarQubeEnv se encarga de inyectar el Token y la URL del servidor
                withSonarQubeEnv('SonarQubeServer') {
                    sh "${SCANNER_HOME}/bin/sonar-scanner"
                }
            }
        }
    }

    post {
        always {
            // Limpia el entorno al finalizar, gane o pierda el pipeline
            sh 'docker compose down'
        }
    }
}