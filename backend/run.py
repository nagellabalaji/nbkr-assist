import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Run the server on port 5000 (standard Flask port)
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true' or os.getenv('FLASK_ENV', 'production').lower() == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
