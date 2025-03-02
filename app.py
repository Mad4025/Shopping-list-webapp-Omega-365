from flask import Flask, render_template, redirect, url_for, jsonify, request, session as sessn, g, abort
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from models import ShoppingList, ShoppingCart, User, PurchaseHistory, engine, load_dotenv, os, datetime
import stripe
from authlib.integrations.flask_client import OAuth
from sqlalchemy import distinct
from functools import wraps


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
stripe.api_key = os.getenv('stripe_api_key')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_google'

# Create a session factory
session_factory = sessionmaker(bind=engine)
db_session = scoped_session(session_factory)

def datetimefilter(value, format="%d.%m.%Y %H:%M:%S"):
    if value == "now":
        return datetime.now().strftime(format)
    return value.strftime(format)

app.jinja_env.filters['datetimefilter'] = datetimefilter

@login_manager.user_loader
def load_user(user_id):
    with Session(engine) as session:
        return session.get(User, int(user_id)) if user_id else None

@app.before_request
def set_global_user():
    g.current_user = current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# Clean up the session when the app shuts down
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# Set up Google's OAuth2
oauth = OAuth(app)
google = oauth.register("myApp",
    # Client_id and client_secret is individual and only found on console.cloud.google.com in your project under credentials
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    client_kwargs={'scope': 'openid profile email'},  # Make sure you have enabled these scopes in OAuth consent screen. You can add or remove scopes at 'Data Access'.
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',  # Connect to server.
)


@app.route('/')
def index():
    user_data = {
        'profile_pic': sessn.get('profile_pic'),
        'name': sessn.get('name'),
        'user_admin': sessn.get('user_admin', False)
    }
    return render_template('index.html', **user_data)


@app.route('/shopping-list')
def shopping_list():
    user_data = {
        'profile_pic': sessn.get('profile_pic'),
        'name': sessn.get('name'),
        'user_admin': sessn.get('user_admin', False)
    }
    with Session(engine) as session:
        items = session.query(ShoppingList).all()
        categories = set(item.category for item in items if item.category) # Unique categories
    return render_template('pages/shopping_list.html', items=items, categories=categories, **user_data)


@app.route('/add-item', methods=['GET'])
@login_required
@admin_required
def add_item_form():
    user_data = {
        'profile_pic': sessn.get('profile_pic'),
        'name': sessn.get('name'),
        'user_admin': sessn.get('user_admin', False)
    }
    return render_template('pages/add_item.html', **user_data)


@app.route('/admin')
@login_required
@admin_required
def admin():
    user_data = {
        'profile_pic': sessn.get('profile_pic'),
        'name': sessn.get('name'),
        'user_admin': sessn.get('user_admin', False)
    }

    with Session(engine) as session:
        user_count = session.query(User).count()
    return render_template('pages/admin.html', user_count=user_count, **user_data)


@app.route('/purchase-history')
def purchase_history():
    if not current_user.is_authenticated:
        return render_template('pages/purchase_history.html', transactions=[]) # Empty transactions

    user_data = {
        'profile_pic': sessn.get('profile_pic'),
        'name': sessn.get('name'),
        'user_admin': sessn.get('user_admin', False)
    }

    with Session(engine) as session:
        transaction_ids = session.query(distinct(PurchaseHistory.transaction_id)).filter_by(user_id=current_user.id).all()
        transactions = []
        for (trans_id,) in transaction_ids:
            purchases = session.query(PurchaseHistory).filter_by(transaction_id=trans_id, user_id=current_user.id).all()
            if purchases:
                total = sum(purchase.price * purchase.quantity for purchase in purchases)
                transactions.append({
                    'transaction_id': trans_id,
                    'purchases': purchases,
                    'total': total,
                    'date': purchases[0].purchased_at # Use the first item's date
                })
    return render_template('pages/purchase_history.html', transactions=transactions, **user_data)


@app.route('/profile')
@login_required
def profile():
    user_data = {
        'profile_pic': sessn.get('profile_pic'),
        'name': sessn.get('name'),
        'email': sessn.get('email'),
        'user_admin': sessn.get('user_admin', False)
    }

    total_spent = 0
    with Session(engine) as session:
        total_purchases = session.query(distinct(PurchaseHistory.transaction_id)).filter_by(user_id=current_user.id).count()
        user_data['total_purchases'] = total_purchases

        purchases = session.query(PurchaseHistory).filter_by(user_id=current_user.id).all()
        total_spent += sum(purchase.price * purchase.quantity for purchase in purchases)
        user_data['total_spent'] = total_spent
    return render_template('pages/profile.html', **user_data)


@app.route('/add-item', methods=['POST'])
def add_item():
    item_name = request.form['item_name']
    category = request.form['category'] # Default to 'Uncategorized' if not provided, instead of NULL.
    quantity = request.form['quantity']
    price = request.form['price']
    with Session(engine) as session:
        new_item = ShoppingList(item_name=item_name, quantity=quantity, price=price, category=category)
        session.add(new_item)
        session.commit()
    return redirect(url_for('shopping_list'))


@app.route('/edit-item/<int:item_id>', methods=['PUT'])
def edit_item(item_id):
    if not sessn.get('user_admin'):
        return jsonify({ 'status': 'error', 'message': 'Unauthorized' }), 403
    
    data = request.get_json()
    item_name = data.get('itemName')
    price = data.get('price')
    quantity = data.get('quantity')
    category = data.get('category')


    with Session(engine) as session:
        item = session.query(ShoppingList).filter_by(id=item_id).first()
        if item:
            item.item_name = item_name
            item.price = price
            item.quantity = quantity
            item.category = category
            session.commit()
            return jsonify({ 'status': 'success' })
        else:
            return jsonify({ 'status': 'error', 'message': 'Item not found.' }), 404


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if not current_user.is_authenticated:
        return jsonify({ 'status': 'error', 'message': 'Please log in to add items to cart' }), 403

    item_name = request.form['item_name']
    # Check available stock in ShoppingList
    shopping_item = db_session.query(ShoppingList).filter_by(item_name=item_name).first()
    if not shopping_item or shopping_item.quantity <= 0:
        return jsonify({'status': 'error', 'message': 'Item out of stock'}), 400
    
    # Check if item exists in cart
    cart_item = db_session.query(ShoppingCart).filter_by(item_name=item_name, user_id=current_user.id).first()
    if cart_item:
        if shopping_item.quantity >= cart_item.quantity + shopping_item.quantity:
            return jsonify({'status': 'error', 'message': 'Not enough stock'}), 400
        cart_item.quantity += 1
    else:
        cart_item = ShoppingCart(
            item_name=item_name, 
            quantity=1,
            user_id=current_user.id
            )
        db_session.add(cart_item)

    # Reduce stock in ShoppingList
    shopping_item.quantity -= 1
    db_session.commit()

    # Fetch all cart items
    cart_items = db_session.query(ShoppingCart).filter_by(user_id=current_user.id).all()
    cart_list = [{'id':item.id, 'item_name': item.item_name, 'quantity': item.quantity} for item in cart_items]
    return jsonify({ 
        'status':'success', 
        'cart': cart_list,
        'stock': shopping_item.quantity,
        'item_id': shopping_item.id
        })


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    if not current_user.is_authenticated:
        return redirect(url_for('login_google'))

    with Session(engine) as session:
        cart_items = session.query(ShoppingCart).filter_by(user_id=current_user.id).all()
        if not cart_items:
            return jsonify({ 'status': 'error', 'message': 'Your cart is empty' })
        
        line_items = []
        for cart_item in cart_items:
            shopping_item = session.query(ShoppingList).filter_by(item_name=cart_item.item_name).first()
            if shopping_item and shopping_item.price:
                line_items.append({
                    'price_data': {
                        'currency':'usd',
                        'product_data': {
                            'name': cart_item.item_name,
                        },
                        'unit_amount': int(shopping_item.price * 100) # Convert (stripe sets the amount to pennies instead of dollars).
                    },
                    'quantity': cart_item.quantity,
                })
            else:
                # Skip items without a price or handle error
                continue
        
        if not line_items:
            return 'no valid items in cart', 400
        
        try:
            checkout_session = stripe.checkout.Session.create (
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=f'{request.host_url}success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{request.host_url}cancel'
            )
            return jsonify({ 'status': 'success', 'checkout_url': checkout_session.url })
        except Exception as e:
            return str(e), 500

  
@app.route('/success')
def success():
    session_id = request.args.get('session_id')
    if session_id and current_user.is_authenticated:
        with Session(engine) as session:
            # Fetch cart items
            cart_items = session.query(ShoppingCart).filter_by(user_id=current_user.id).all()
            for cart_item in cart_items:
                shopping_item = session.query(ShoppingList).filter_by(item_name=cart_item.item_name).first()
                if shopping_item:
                    # Purchase history log.
                    purchase = PurchaseHistory(
                        transaction_id=session_id,
                        item_name=cart_item.item_name,
                        quantity=cart_item.quantity,
                        price=float(shopping_item.price),
                        user_id=current_user.id
                    )
                    session.add(purchase)
            session.query(ShoppingCart).filter_by(user_id=current_user.id).delete()
            session.commit()
    return redirect(url_for('purchase_history'))


@app.route('/cancel')
def cancel():
    return redirect(url_for('shopping_list'))


@app.route('/get-cart', methods=['GET'])
def get_cart():
    if current_user.is_authenticated:
        with Session(engine) as session:
            cart_items = session.query(ShoppingCart).filter_by(user_id=current_user.id).all()
            cart_list = [{'id': item.id, 'item_name': item.item_name, 'quantity': item.quantity} for item in cart_items]
        return jsonify({ 'cart': cart_list })
    else:
        return jsonify({ 'cart': [], 'message': 'Please log in to view your cart.' })


@app.route('/delete-from-cart', methods=['POST'])
def delete_from_cart():
    if not current_user.is_authenticated:
        return jsonify({ 'status': 'error', 'message': 'Please log in to manage your cart.' }), 403

    item_id = request.form['item_id']
    item = db_session.query(ShoppingCart).filter_by(id=item_id, user_id=current_user.id).first()
    shopping_item = db_session.query(ShoppingList).filter_by(item_name=item.item_name).first()
    if item:
        shopping_item.quantity += item.quantity
        db_session.delete(item)
        db_session.commit()
    cart_items = db_session.query(ShoppingCart).filter_by(user_id=current_user.id).all()
    cart_list = [{'id': item.id, 'item_name': item.item_name, 'quantity': item.quantity} for item in cart_items]
    return jsonify({ 
        'cart': cart_list,
        'stock': shopping_item.quantity,
        'item_id': shopping_item.id
        })


@app.route('/delete-account/<int:user_id>')
@login_required
def delete_account():
    pass # To be added.


@app.route('/delete-shopping-item')
@login_required
def delete_shopping_item():
    pass # To be added.


# Takes you to google's login thing.
@app.route('/login/google')
def login_google():
    return oauth.myApp.authorize_redirect(redirect_uri="http://localhost:5000" + url_for('google_callback'), _external=True)


# Where Google takes you after using their login thing.
@app.route('/auth/google/callback')
def google_callback():
    token = oauth.myApp.authorize_access_token()
    sessn['user'] = token
    user_info = google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
    sessn['profile_pic'] = user_info['picture']  # Save profile picture URL
    sessn['name'] = user_info['name']
    sessn['email'] = user_info['email']
    user = db_session.query(User).filter_by(email=sessn['email']).first()

    # Add the emails that will have admin privileges in the .env file.
    is_admin = sessn['email'] == os.getenv('ADMIN_EMAILS')

    # To update user roles
    if not user:
        user = User(
            email=sessn['email'], 
            role='admin' if is_admin else 'user')
        db_session.add(user)
    else:
        if is_admin and user.role != 'admin':
            user.role = 'admin'
        elif not is_admin and user.role == 'admin':
            user.role = 'user'
    db_session.commit() # Commit changes to the database

    login_user(user)
    # Save admin permissions (True or False) to sessn.
    sessn['user_admin'] = is_admin
    return redirect(url_for('shopping_list'))


# To log out the user.
@app.route('/logout')
@login_required
def logout():
    logout_user()
    sessn['user_admin'] = False
    return redirect(url_for('index'))