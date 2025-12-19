# TaggedByBelle - Professional Audio Tagging Service



##  Quick Start

### 1. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Application:
```bash
# Activate virtual environment
.\venv\Scripts\activate

# Start server
uvicorn app.main:app --reload
```

### 3. Open Browser:
```
http://localhost:8000
```


---

### Color Palette:
- **Brand**: Electric Lime (#e2fb52) 
- **Accent**: Purple (#7c3aed) 
- **Theme**: Professional Dark Mode 

### Typography:
- **Font**: Inter (Google Fonts)
- **Sizes**: Responsive scale (xs to 5xl)
- **Weights**: 400 to 900

---


### Backend:
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **Jinja2** - Template engine
- **Pydantic** - Data validation

### Frontend:
- **Custom Design System** - 500+ lines of modern CSS
- **Vanilla JavaScript** - 300+ lines for interactions
- **Chart.js** - Analytics visualization
- **Google Fonts** - Inter typography

---


```
app/
├── static/              # Static assets (CSS, JS, Images)
├── templates/           # Jinja2 templates (18 pages)
├── domain/              # Database models
├── core/                # Configuration
├── db/                  # Database setup
└── main.py             # Application entry point
```

---


### Production Environment Variables

Required environment variables for production:
- `SECRET_KEY` - Secret key for session management (generate a secure random string)
- `DATABASE_URL` - Database connection string (format depends on provider)
- `SQL_ECHO` - (Optional) Set to "true" for SQL query logging

---


