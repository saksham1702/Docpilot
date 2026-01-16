pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'docker.io'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Lint') {
            steps {
                sh '''
                    echo "🔍 Running linters..."
                    # Python linting (if flake8 available)
                    pip install flake8 || true
                    flake8 backend/ worker/ --ignore=E501,W503 --exit-zero
                '''
            }
        }
        
        stage('Build Images') {
            steps {
                sh '''
                    echo "🔨 Building Docker images..."
                    docker compose build --no-cache backend worker
                '''
            }
        }
        
        stage('Test') {
            steps {
                sh '''
                    echo "🧪 Running tests..."
                    # Start services
                    docker compose up -d db
                    sleep 10
                    
                    # Run backend tests
                    docker compose run --rm backend python -c "
from main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get('/health')
assert response.status_code == 200
print('✅ Health check passed')
"
                    
                    docker compose down
                '''
            }
        }
        
        stage('Deploy (Local)') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    echo "🚀 Deploying to local environment..."
                    docker compose up -d
                    sleep 5
                    curl -f http://localhost:8000/health || exit 1
                    echo "✅ Deployment verified!"
                '''
            }
        }
    }
    
    post {
        always {
            sh 'docker compose logs --tail=50 || true'
        }
        success {
            echo '✅ Pipeline completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed!'
        }
    }
}
