pipeline {
  agent any

  environment {
    // ✅ Python 3.11 고정 (권장)
    PYTHON = "C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe"

    BEDROCK_MOCK = "true"
    OPENSEARCH_MOCK = "true"
  }

  stages {
    stage("Check Python") {
      steps {
        bat '''
          "%PYTHON%" --version
          "%PYTHON%" -m pip --version
        '''
      }
    }

    stage("Setup Python") {
      steps {
        dir("ai/ai-server") {
          bat '''
            "%PYTHON%" -m venv .venv
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
