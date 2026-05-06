# App

Streamlit app files go here.

Typical files:

- `main.py` - main Streamlit demo
- `components.py` - reusable UI components
- `config.py` - demo configuration

Every generated project should include visible demo language such as:

> Portfolio demo using synthetic or public data.

## Configuration

The app loads settings from environment variables, local `.env`, or Streamlit secrets. For Windows development, copy `.env.example` with PowerShell:

```powershell
Copy-Item ..\.env.example ..\.env
notepad ..\.env
python -m streamlit run .\streamlit_app.py
```

Never commit `.env` or `.streamlit/secrets.toml`; both are ignored by git.
