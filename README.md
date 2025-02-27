1. **Clone the Repository**
   ```bash
   git clone <repo-url>
   cd <repo-folder>
Create & Activate a Virtual Environment (optional but recommended)


python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
**Install Dependencies
Install the required packages with:**

pip install flask flask-sqlalchemy flask-migrate pymysql
**Configure Your Database**

Update the MySQL connection in app.py with your credentials:
**Connecting with your XAmp Mysql database**
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost:3307/library'
Create the library database using your MySQL client or phpMyAdmin.

**Run Migrations Initialize migrations and upgrade your database schema:**
**Models Migration to database**
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

Run the Application

**Running the App**
python app.py
The app will be available at http://127.0.0.1:5000.



This short README guides users on what to install and how to get your application running after they clone

**important to note Uses of flask comands**
Create Tables Using Migrations:
Your app.py contains your models. To create the tables based on those models, you'll use Flask-Migrate. Here are the steps:
1
**Initialize Migrations:**
In your project directory, run:
**flask db init**
This creates a migrations folder.
2
**Create a Migration Script:**
Generate a migration script that detects your models:
**flask db migrate -m "Initial migration"**
3
**Apply the Migration:**
Apply the migration to create the tables in your library database:
**flask db upgrade**
