import os
import sys

sys.path.insert(0, '/Users/cave/Projects/EnterpriseHub_new')

# Load .env.jorge manually
with open('/Users/cave/Projects/EnterpriseHub_new/.env.jorge') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

# Local overrides — disable HTTPS redirect and skip DB/Redis
os.environ['ENVIRONMENT'] = 'development'
os.environ.setdefault('DATABASE_URL', '')
os.environ.setdefault('REDIS_URL', '')

import uvicorn

from ghl_real_estate_ai.api.main import socketio_app

if __name__ == '__main__':
    uvicorn.run(socketio_app, host='0.0.0.0', port=8000, log_level='info')
