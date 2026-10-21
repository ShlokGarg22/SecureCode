# SecureCode - AI-Powered Security Code Reviewer

## 🛡️ Overview

SecureCode (DiffGuard) is an AI-powered security code review platform that finds vulnerabilities and provides AI-generated remediation with side-by-side code diffs. It automatically scans codebases, identifies security issues, and suggests fixes.

## ✨ Features

### **Core Features**
- **Multi-language Security Scanning**: Python, JavaScript/TypeScript, Node.js, Java, Go, PHP
- **AI-Powered Explanations**: Detailed vulnerability analysis with attack scenarios
- **Side-by-Side Code Diffs**: Visual comparison of vulnerable vs fixed code
- **Multiple Security Tools**: Semgrep for SAST, Gitleaks for secrets detection
- **Framework-Specific Detection**: Django, React, Flask, Express.js vulnerabilities

### **Security Features**
- 🔐 JWT Authentication with Role-Based Access Control
- ⏱️ Rate Limiting & API Security
- 📁 Secure File Upload Validation
- 🔒 Encrypted Secrets Management
- 👥 Multi-tenancy Support

### **Advanced Capabilities**
- 🤖 Multiple AI Provider Support (Groq, Gemini, OpenAI, Amazon Bedrock)
- 📊 Compliance Reporting (PCI DSS, HIPAA, GDPR, ISO27001)
- 🔄 CI/CD Integration (GitHub Actions, GitLab CI, Jenkins)
- 📈 Performance Monitoring & Analytics
- 📋 Export Reports (JSON, PDF, SARIF, CSV)

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### **Option 1: Docker (Recommended)**
```bash
# Clone the repository
git clone <repository-url>
cd SecureCode

# Start services
docker-compose up -d

# Access the application
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/docs
```

### **Option 2: Local Development**
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
SecureCode/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── ai/             # AI explainer services
│   │   ├── core/           # Configuration & security
│   │   ├── engine/         # Security scanners
│   │   ├── models/         # Pydantic models
│   │   └── db/            # Database layer
│   ├── tests/              # Backend tests
│   ├── data/               # Uploads & scan data
│   └── rules/              # Security rules
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app router
│   │   ├── components/    # React components
│   │   └── lib/           # API clients & utilities
│   └── public/            # Static assets
├── demo_vulnerable_project/  # Sample vulnerable code
├── demo_fixed_project/      # Sample fixed code
└── docker-compose.yml      # Docker orchestration
```

## 🔧 Configuration

### **Environment Variables**

Create `.env` files in both backend and frontend directories:

**Backend (.env)**
```env
# Security
DIFFGUARD_DEBUG=false
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# AI Providers (choose one or more)
AI_PROVIDER=auto
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret

# File Upload Limits
MAX_UPLOAD_SIZE_MB=100
MAX_FILE_COUNT=10000
MAX_EXTRACTED_SIZE_MB=500
```

**Frontend (.env.local)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=SecureCode
```

## 🔐 Authentication

SecureCode uses JWT authentication with three default roles:

### **Demo Tokens**
```
GET /api/auth/demo-tokens

Returns:
- viewer: Read-only access (view reports)
- analyst: Can scan projects and view reports
- admin: Full access with user management
```

### **Authentication Flow**
1. Get a demo token from `/api/auth/demo-tokens`
2. Store token in localStorage or session
3. Include in requests: `Authorization: Bearer <token>`
4. Token automatically refreshed on 401 errors

## 📡 API Reference

### **Main Endpoints**

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/health` | GET | Health check | No |
| `/api/auth/demo-tokens` | GET | Get demo tokens | No |
| `/api/auth/verify` | GET | Verify authentication | Yes |
| `/api/scans` | GET | List all scans | Analyst+ |
| `/api/scans/upload` | POST | Upload & scan project | Analyst+ |
| `/api/scans/{id}` | GET | Get scan details | Analyst+ |
| `/api/scans/{id}/export/json` | GET | Export JSON report | Analyst+ |

### **Rate Limiting**
- **Default**: 100 requests/minute per IP
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Window`
- **Response**: 429 with Retry-After header

## 🧪 Testing

### **Backend Tests**
```bash
cd backend
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_api.py -v           # API tests
pytest tests/test_ai_explainer.py -v # AI integration tests
pytest tests/test_security.py -v     # Security tests
```

### **Frontend Tests**
```bash
cd frontend
npm test              # Run Jest tests
npm run lint         # ESLint check
npm run build        # Production build
```

## 🛠️ Development

### **Adding New Vulnerability Detectors**
1. Create detector in `backend/app/engine/`
2. Add to orchestrator in `backend/app/engine/orchestrator.py`
3. Write tests in `backend/tests/test_new_detector.py`
4. Update frontend UI for results display

### **Custom Security Rules**
```yaml
# Create custom Semgrep rules in backend/rules/
- id: custom-sql-injection
  pattern: "cursor.execute(f'SELECT ...')"
  message: "SQL Injection detected"
  languages: [python]
  severity: ERROR
```

### **Extending AI Explanations**
- Add new vulnerability types to `backend/app/ai/explainer_enhanced.py`
- Include framework-specific patterns
- Update UI components to display new formats

## 📊 Deployment

### **Production Checklist**
- [ ] Rotate all API keys and secrets
- [ ] Configure HTTPS (TLS/SSL)
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure logging aggregation
- [ ] Enable database backups
- [ ] Set up CI/CD pipeline
- [ ] Configure firewall rules
- [ ] Implement DDoS protection

### **Docker Production**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - DIFFGUARD_DEBUG=false
      - SECRET_KEY=${SECRET_KEY}
    ports:
      - "8000:8000"
    volumes:
      - backend_data:/app/data
    restart: unless-stopped
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  backend_data:
```

### **Kubernetes**
See `kubernetes/` directory for:
- Deployment manifests
- Service configurations
- Ingress rules
- ConfigMaps & Secrets

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Write tests** for new functionality
4. **Submit a pull request**

### **Code Standards**
- **Python**: Black formatting, Flake8 linting
- **JavaScript**: ESLint, Prettier formatting
- **Commits**: Conventional commits format
- **Documentation**: Update README and code comments

## 📚 Additional Documentation

- [API Documentation](http://localhost:8000/api/docs)
- [Security Guidelines](./SECURITY.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Contributing Guide](./CONTRIBUTING.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

## 🆘 Support

### **Common Issues**
- **Backend not connecting**: Check CORS settings and ports
- **AI explanations failing**: Verify API keys and provider status
- **File upload errors**: Check file size limits and file types
- **Authentication issues**: Clear localStorage tokens and retry

### **Getting Help**
- Open an issue on GitHub
- Check existing issues for solutions
- Review API documentation

## 📄 License

MIT License - see [LICENSE](./LICENSE) file for details.

---

## 🔍 Quick Troubleshooting

### **Backend Won't Start**
```bash
# Check dependencies
pip list | grep -E "fastapi|uvicorn|pydantic"

# Check ports
netstat -tulpn | grep :8000

# Check logs
docker logs diffguard-backend
```

### **Frontend Won't Connect**
```bash
# Check API URL
echo $NEXT_PUBLIC_API_URL

# Check CORS
curl -I http://localhost:8000/api/health

# Check network
chrome://net-internals/#events
```

### **Scan Not Working**
```bash
# Check scanners
curl http://localhost:8000/api/health

# Check file permissions
ls -la backend/data/uploads/

# Check logs
tail -f backend/logs/app.log
```

## 🚨 Security Notice

This tool is designed to help identify security vulnerabilities. However:

1. **Use responsibly** - Only scan code you own or have permission to test
2. **Secure your deployment** - Enable authentication and rate limiting
3. **Rotate secrets regularly** - Especially API keys and tokens
4. **Keep dependencies updated** - Regular security patches
5. **Monitor usage** - Set up alerts for suspicious activity

For any security concerns, please contact the maintainers securely.