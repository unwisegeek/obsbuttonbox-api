pipeline {
    agent { docker { image 'python:3.8.10' } }
    stages {
        stage('build') {
            steps {
                export FLASK_APP=api
                sh 'flask run'
            }
        }
    }
}

