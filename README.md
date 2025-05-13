StockSim
StockSim is a Django-based web application that simulates stock market trading, allowing users to experience buying and selling stocks in a virtual environment. The platform provides real-time stock data, portfolio management, and transaction history to help users understand market dynamics without financial risk.

Features
🔐 User Authentication – Secure sign-up, login, and logout

📈 Real-Time Stock Simulation – Mock trading using live or mock data

💼 Portfolio Management – Track virtual assets and investments

🧾 Transaction History – View logs of all buy/sell activities

🖥️ Responsive UI – Clean, mobile-friendly interface

Tech Stack
Framework: Django

Frontend: HTML, CSS, Bootstrap

Database: SQLite

Language: Python

External APIs: For live stock data (if enabled)

Installation
bash
Copy
Edit

# Checkout the project at
https://stocksim-nv5p.onrender.com/

# Clone the repository
git clone https://github.com/sona-poddar/stocksim.git
cd stocksim

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run the server
python manage.py runserver
Visit http://127.0.0.1:8000/ in your browser to use the app.

# Project Structure

accounts/: Handles user authentication and profile management.

market/: Core application logic for stock simulation.

stocksim/: Project configuration and settings.

templates/: HTML templates for rendering pages.

static/: Static files like CSS and JavaScript.

db.sqlite3: SQLite database file.

manage.py: Django's command-line utility.


Contributing
Pull requests and suggestions are welcome! If you find a bug or want to contribute a feature, feel free to fork the repo and open a PR.

License
This project is licensed under the MIT License.

Let me know if you’d like to add badges (build, license, etc.) or example screenshots to the README!
