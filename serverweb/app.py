from flask import Flask, render_template, jsonify
import json
from dotenv import load_dotenv
import os
from routes.web import web_bp
from routes.api import api_bp

app = Flask(__name__)

load_dotenv()  # Charge les variables d'environnement depuis .env
app.secret_key = os.getenv("FLASK_SECRET_KEY")


# Charger la configuration
with open('config.json') as f:
    config = json.load(f)


# Enregistrer les routes
app.register_blueprint(web_bp)
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/config')
def get_config():
    return jsonify(config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

