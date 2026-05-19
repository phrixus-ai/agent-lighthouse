"""AgentLighthouse - AI & Agent Readiness Scanner
Entry point: python -m webaudit"""

from webaudit.app import create_app

app = create_app()

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    port = int(os.environ.get("WEBAUDIT_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
