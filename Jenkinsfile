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

    stage("Setup Python") {
      steps {
        dir("ai/ai-server") {
          sh """
            python3 -m venv .venv
            . .venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
            pip install pytest
          """
        }
      }
    }

    stage("Build") {
      steps {
        dir("ai/ai-server") {
          sh """
            . .venv/bin/activate
            python -m compileall app
          """
        }
      }
    }

    stage("Test") {
      steps {
        dir("ai/ai-server") {
          sh """
            . .venv/bin/activate
            pytest -q
          """
        }
      }
    }
  }
}
