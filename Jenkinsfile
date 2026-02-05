pipeline {
  agent any

  environment {
    BEDROCK_MOCK = "true"
    OPENSEARCH_MOCK = "true"
  }

  stages {
    stage("Checkout") {
      steps { checkout scm }
    }

    stage("Check Python") {
      steps {
        bat '''
          where python
          python --version
          where pip
          pip --version
        '''
      }
    }

    stage("Setup Python") {
      steps {
        dir("ai/ai-server") {
          script {
            if (isUnix()) {
              sh '''
                python3 -m venv .venv
                . .venv/bin/activate
                python -m pip install --upgrade pip
                pip install -r requirements.txt
                pip install pytest
              '''
            } else {
              bat '''
                py -m venv .venv
                call .venv\\Scripts\\activate
                python -m pip install --upgrade pip
                pip install -r requirements.txt
                pip install pytest
              '''
            }
          }
        }
      }
    }

    stage("Build") {
      steps {
        dir("ai/ai-server") {
          script {
            if (isUnix()) {
              sh '''
                . .venv/bin/activate
                python -m compileall app
              '''
            } else {
              bat '''
                call .venv\\Scripts\\activate
                python -m compileall app
              '''
            }
          }
        }
      }
    }

    stage("Test") {
      steps {
        dir("ai/ai-server") {
          script {
            if (isUnix()) {
              sh '''
                . .venv/bin/activate
                pytest -q
              '''
            } else {
              bat '''
                call .venv\\Scripts\\activate
                pytest -q
              '''
            }
          }
        }
      }
    }
  }
}
