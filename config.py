class Config:
    SECRET_KEY = 'your_secret_key'

    MONGO_URI = "mongodb://localhost:27017"

    FLASK_JWT_SECRET_KEY = '7e4d21e87dd2238e8cf031df'
    UPLOAD_FOLDER = 'D:\\project\\esprit project\\Back_End\\Uploads'

    # Flask-Mail configuration
    # MAIL_SERVER = 'smtp.gmail.com'
    # MAIL_PORT = 465
    # MAIL_USE_TLS = False
    # MAIL_USE_SSL = True
    # MAIL_USERNAME = 'airecruittn@gmail.com'  # Your Gmail email address
    # MAIL_PASSWORD = 'pjxn bnsz ilyv eaqm'  # Your Gmail password
    # MAIL_DEFAULT_SENDER = 'airecruittn@gmail.com'  # Default sender
    #
   
    REDIRECT_URI = 'https://localhost:5000/home'
