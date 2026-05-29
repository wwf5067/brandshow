module.exports = {
  apps: [
    {
      name: 'brandshow-backend',
      cwd: '/Users/nikogao/Documents/Project/Personal/brandshow/backend',
      interpreter: '/Users/nikogao/Documents/Project/Personal/brandshow/backend/.venv/bin/python3',
      script: '/Users/nikogao/Documents/Project/Personal/brandshow/backend/.venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      env: {
        ENVIRONMENT: 'production',
      },
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      error_file: '/tmp/brandshow-backend-err.log',
      out_file: '/tmp/brandshow-backend-out.log',
    },
    {
      name: 'brandshow-frontend',
      cwd: '/Users/nikogao/Documents/Project/Personal/brandshow/frontend',
      script: 'npm',
      args: 'run dev',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      error_file: '/tmp/brandshow-frontend-err.log',
      out_file: '/tmp/brandshow-frontend-out.log',
    },
  ],
}
