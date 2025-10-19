# Polaris Career Navigator - Backend API

AI-powered backend for the Polaris Career Path Navigator. Provides personalized tech career recommendations using Google Gemini AI.

## 🚀 Live Demo

**API Base URL:** https://polaris-backend-hus2.onrender.com

**Frontend:** https://polaris-frontend-six.vercel.app

## 🛠️ Tech Stack

- **Python 3.13** - Core language
- **Flask 3.1** - Web framework
- **Google Gemini AI** - LLM for career analysis
- **Gunicorn** - Production WSGI server
- **Render** - Cloud hosting platform

## 📋 Features

- Tech role validation with AI
- Work style metrics estimation
- 27 personalized role recommendations
- AI-generated role insights
- Smart skills suggestions
- 100+ pre-loaded tech roles database

## 🔧 API Endpoints

- `GET /health` - Simple health check
- `POST /api/infer-industry` - Validate tech role and get metrics
- `POST /api/map/roles` - Get personalized recommendations
- `POST /api/role/<name>/pages` - Get detailed role information
- `POST /api/suggest-skills` - Get AI skill suggestions

## 💻 Local Development
```bash
git clone https://github.com/DamirStyles/polaris-backend.git
cd polaris-backend
pip install -r requirements.txt
echo "GOOGLE_API_KEY=your_key" > .env
python app.py
```

## 🌐 Environment Variables

- `GOOGLE_API_KEY` - Google Gemini API key (required)
- `FLASK_ENV` - Environment mode (optional)

## 📦 Project Structure

- `app.py` - Flask application entry
- `career_advisor.py` - AI integration
- `routes.py` - API handlers
- `services/` - Business logic
- `data/` - Tech roles database

## 👤 Author

**Damir Styles**
- GitHub: [@DamirStyles](https://github.com/DamirStyles)
- Live Demo: https://polaris-frontend-six.vercel.app
