from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://nancymary2005:Test123@cluster0.4u5my.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client.stockdb
stock_collection = db.stock_items
users_collection = db.users

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('stock'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        users_collection.insert_one({'username': username, 'password': hashed_password})
        flash('Registration successful! Please log in.')
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/index', methods=['POST'])
def index():
    username = request.form['username']
    password = request.form['password']
    user = users_collection.find_one({'username': username})
    
    if user and check_password_hash(user['password'], password):
        session['username'] = username
        return redirect(url_for('stock'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/stock')
def stock():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    stocks = list(stock_collection.find({'username': session['username']}))  # Fetch only user's items

    # Compute dashboard values
    total_items = len(stocks)
    total_stock_value = sum(stock.get('total_amount', 0) for stock in stocks)
    low_stock_count = sum(1 for stock in stocks if stock.get('quantity', 0) < 5)  # Example: Low stock if quantity < 5

    return render_template(
        'stock.html',
        stocks=stocks,
        total_items=total_items,
        total_stock_value=total_stock_value,
        low_stock_count=low_stock_count
    )

@app.route('/add_stock', methods=['GET', 'POST'])
def add_stock():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        stock_item = {
            'username': session['username'],  # Associate stock with logged-in user
            'item_code': request.form['item_code'],
            'item_name': request.form['item_name'],
            'item_type': request.form['item_type'],
            'date': request.form['date'],
            'net_weight': float(request.form['net_weight']),
            'price': float(request.form['price']),
            'quantity': int(request.form['quantity']),
            'total_amount': float(request.form['price']) * int(request.form['quantity'])
        }
        stock_collection.insert_one(stock_item)
        flash('Stock item added successfully')
        return redirect(url_for('stock'))
    
    return render_template('add_stock.html')

@app.route('/edit_stock/<item_code>')
def edit_stock(item_code):
    if 'username' not in session:
        return redirect(url_for('home'))
    
    stock = stock_collection.find_one({'item_code': item_code, 'username': session['username']})
    if not stock:
        flash('Stock item not found')
        return redirect(url_for('stock'))

    return render_template('update_stock.html', stock=stock)

@app.route('/update_stock/<item_code>', methods=['POST'])
def update_stock(item_code):
    if 'username' not in session:
        return redirect(url_for('home'))
    
    update_fields = {
        'item_type': request.form['item_type'],
        'item_name': request.form['item_name'],
        'net_weight': float(request.form['net_weight']),
        'date': request.form['date'],
        'price': float(request.form['price']),
        'quantity': int(request.form['quantity']),
        'total_amount': float(request.form['price']) * int(request.form['quantity'])
    }
    
    stock_collection.update_one({'item_code': item_code, 'username': session['username']}, {'$set': update_fields})
    flash('Stock item updated successfully')
    return redirect(url_for('stock'))

@app.route('/delete_stock/<item_code>')
def delete_stock(item_code):
    if 'username' not in session:
        return redirect(url_for('home'))
    
    stock_collection.delete_one({'item_code': item_code, 'username': session['username']})
    flash('Stock item deleted successfully')
    return redirect(url_for('stock'))

if __name__ == '__main__':
    app.run(debug=True)
