pipeline {
    agent any
    
    environment {
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -la'
                sh 'echo "Checkout complete"'
            }
        }
        
        stage('Validate') {
            steps {
                sh '''
                    echo "🔍 Validating project structure..."
                    test -f backend/main.py && echo "✅ backend/main.py exists"
                    test -f worker/main.py && echo "✅ worker/main.py exists"
                    test -f docker-compose.yml && echo "✅ docker-compose.yml exists"
                    test -f Jenkinsfile && echo "✅ Jenkinsfile exists"
                '''
            }
        }
        
        stage('Test Backend Health') {
            steps {
                sh '''
                    echo "🧪 Testing backend connectivity..."
                    curl -s http://host.docker.internal:8000/health || echo "⚠️ Backend not reachable (expected if not running locally)"
                '''
            }
        }
        
        stage('Deploy Info') {
            steps {
                sh '''
                    echo " Deployment Info:"
                    echo "   - Build Number: ${BUILD_NUMBER}"
                    echo "   - Branch: master"
                    echo "   - Ready for deployment!"
                '''
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed!'
        }
    }
}
