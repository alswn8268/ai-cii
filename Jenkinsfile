pipeline {
  agent any

  environment {
    BEDROCK_MOCK = "true"
    OPENSEARCH_MOCK = "true"
  }

  stages {
    stage("Check Python") {
      steps {
        dir("ai/ai-server") {
          bat '''
            where python
            python --version
            python -m pip --version
          '''
        }
      }
    }

    stage("Setup Python") {
      steps {
        dir("ai/ai-server") {
          bat '''
            python -m venv .venv
            call .venv\\Scripts\\activate
            python -m pip install --upgrade pip
            pip install -r requirements.txt
            pip install pytest
          '''
        }
      }
    }

    stage("Build") {
      steps {
        dir("ai/ai-server") {
          bat '''
            call .venv\\Scripts\\activate
            python -m compileall app
          '''
        }
      }
    }

    stage("Test") {
      steps {
        dir("ai/ai-server") {
          bat '''
            call .venv\\Scripts\\activate
            pytest -q
          '''
        }
      }
    }
  }
}
