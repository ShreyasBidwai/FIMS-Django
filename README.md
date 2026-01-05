# FIMS - Family Information Management System

A comprehensive web-based application for managing family records, member information, and geographic data built with Django.

![Django](https://img.shields.io/badge/Django-4.2.23-green.svg)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Overview

FIMS (Family Information Management System) is a full-stack web application that provides a centralized platform for managing family information, including family heads, members, hobbies, and geographic data (states and cities). The system features comprehensive CRUD operations, advanced search capabilities, data export functionality, and robust admin features.

## ✨ Key Features

### Family Management
- **Complete CRUD Operations** - Create, read, update, and delete family records
- **Multi-Member Support** - Add multiple family members under each family head
- **Photo Management** - Upload and manage photos for family heads and members
- **Hobby Tracking** - Record and manage hobbies for family heads
- **Validation** - Comprehensive server-side and client-side validation

### Search & Filter
- **Global Search** - Search across family heads, members, states, and cities
- **Advanced Filtering** - Filter by state, status, and multiple criteria
- **Real-time Results** - AJAX-powered search with instant feedback

### Data Export
- **PDF Reports** - Generate professional PDF reports with photos and styling
- **Excel Export** - Export individual or bulk family data to Excel
- **Custom Formatting** - Styled exports with headers, borders, and colors

### Admin Features
- **Dashboard** - Comprehensive dashboard with real-time statistics
- **Audit Logging** - Complete audit trail of all user actions
- **Status Management** - Active/Inactive/Soft Delete status system
- **Pagination** - Efficient data browsing with 10 records per page

### Security
- **URL Obfuscation** - Hashid-based URL encoding for security
- **Authentication** - Secure login system with session management
- **Password Reset** - Email-based password reset with time-limited tokens
- **Soft Delete** - Data preservation with soft delete pattern

## 🛠️ Technology Stack

### Backend
- **Django 4.2.23** - Python web framework
- **MySQL** - Relational database
- **ReportLab** - PDF generation
- **openpyxl** - Excel file generation
- **Pillow** - Image processing
- **hashids** - URL obfuscation

### Frontend
- **HTML5** - Semantic markup
- **JavaScript/jQuery** - Client-side interactivity
- **CSS3** - Custom styling
- **AJAX** - Asynchronous requests

### Infrastructure
- **WhiteNoise** - Static file serving
- **SMTP (Gmail)** - Email delivery

## 📦 Installation

### Prerequisites
- Python 3.x
- MySQL 8.0+
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/FIMS-Django.git
   cd FIMS-Django
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MySQL database**
   ```sql
   CREATE DATABASE fimsdb;
   CREATE USER 'fims'@'localhost' IDENTIFIED BY 'fims';
   GRANT ALL PRIVILEGES ON fimsdb.* TO 'fims'@'localhost';
   FLUSH PRIVILEGES;
   ```

5. **Update settings** (if needed)
   
   Edit `fimsDjango/fimsDjango/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'fimsdb',
           'USER': 'fims',
           'PASSWORD': 'fims',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   
   # Email configuration (for password reset)
   EMAIL_HOST_USER = 'your-email@gmail.com'
   EMAIL_HOST_PASSWORD = 'your-app-password'
   ```

6. **Run migrations**
   ```bash
   cd fimsDjango
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

9. **Run development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    
    Open your browser and navigate to: `http://127.0.0.1:8000`

## 📖 Usage

### Initial Setup
1. Login with your superuser credentials
2. Add states and cities from the dashboard
3. Start registering families

### Family Registration
1. Navigate to the registration page
2. Fill in family head information
3. Add family members (optional)
4. Add hobbies for the family head
5. Upload photos
6. Submit the form

### Managing Records
- **View**: Click on any family record to see detailed information
- **Edit**: Use the edit button to update family information
- **Delete**: Soft delete records using the status dropdown
- **Search**: Use the global search to find specific records
- **Export**: Generate PDF or Excel reports for any family

### Dashboard Features
- View real-time statistics (total families, members, active/inactive counts)
- Browse all records with pagination
- Search across all tables simultaneously
- Filter cities by state
- Manage states and cities

## 🗄️ Database Schema

### Core Models
- **FamilyHead** - Family head information with personal details
- **FamilyMember** - Family member records linked to family head
- **Hobby** - Hobbies associated with family heads
- **State** - State/province information
- **City** - City information linked to states
- **Country** - Country information
- **PasswordReset** - Password reset token management
- **AdminLog** - Audit trail for all admin actions

### Key Relationships
- FamilyMember → FamilyHead (Many-to-One)
- Hobby → FamilyHead (Many-to-One)
- City → State (Many-to-One)
- State → Country (Many-to-One)

## 🔐 Security Features

- **CSRF Protection** - Django's built-in CSRF protection
- **SQL Injection Prevention** - ORM-based queries
- **URL Obfuscation** - Hashid encoding for primary keys
- **File Upload Validation** - Size and format restrictions
- **Session Management** - Secure session-based authentication
- **Soft Delete** - Data preservation instead of hard deletion
- **Password Hashing** - Django's built-in password hashing

## 📊 Project Structure

```
FIMS-Django-main/
├── fimsDjango/
│   ├── fims/                      # Main Django app
│   │   ├── models.py              # Database models
│   │   ├── views.py               # Business logic
│   │   ├── excel_export.py        # Excel generation
│   │   ├── utils.py               # Utility functions
│   │   ├── templates/             # HTML templates
│   │   └── static/fims/           # Static assets
│   │       ├── css/               # Stylesheets
│   │       ├── js/                # JavaScript files
│   │       └── images/            # Images
│   ├── fimsDjango/                # Project settings
│   │   ├── settings.py            # Configuration
│   │   ├── urls.py                # URL routing
│   │   └── wsgi.py                # WSGI config
│   ├── media/                     # Uploaded files
│   ├── staticfiles/               # Collected static files
│   └── manage.py                  # Django CLI
└── requirements.txt               # Python dependencies
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

## 🙏 Acknowledgments

- Django documentation and community
- ReportLab for PDF generation
- openpyxl for Excel handling
- All contributors and users of this project

## 📞 Support

For support, email your.email@example.com or open an issue in the GitHub repository.

## 🔄 Version History

- **v1.0.0** (Current)
  - Initial release
  - Complete CRUD operations
  - PDF/Excel export
  - Admin dashboard
  - Audit logging
  - Search and filter functionality

## 🚀 Future Enhancements

- [ ] REST API for mobile applications
- [ ] Advanced analytics and reporting
- [ ] Bulk import from CSV/Excel
- [ ] Email notifications
- [ ] Multi-language support
- [ ] Role-based access control
- [ ] Data visualization charts
- [ ] Export to additional formats (Word, CSV)

---

**Note**: Remember to update the database credentials, email settings, and SECRET_KEY in `settings.py` before deploying to production.
