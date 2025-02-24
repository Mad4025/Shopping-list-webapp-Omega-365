from flask import Flask, render_template, redirect, url_for, jsonify, request, session as sessn, g
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from models import ShoppingList, ShoppingCart, User, PurchaseHistory, engine, load_dotenv, os, datetime
import stripe
from authlib.integrations.flask_client import OAuth
from sqlalchemy import distinct


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
    with Session(engine) as db_session:
        return db_session.get(User, int(user_id)) if user_id else None

@app.before_request
def set_global_user():
    g.current_user = current_user

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
    # Make sure you have enabled these scopes in OAuth consent screen.
    client_kwargs={'scope': 'openid profile email'},  # Use all of the scopes you added in console.cloud.google.com
    # Connect to server.
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',  # Important for OIDC
)


@app.route('/')
def index():
    profile_pic = sessn.get('profile_pic')
    name = sessn.get('name')
    return render_template('index.html', profile_pic=profile_pic, name=name)


@app.route('/shopping-list')
def shopping_list():
    profile_pic = sessn.get('profile_pic')
    name = sessn.get('name')
    with Session(engine) as session:
        items = session.query(ShoppingList).all()
    return render_template('pages/shopping_list.html', items=items, profile_pic=profile_pic, name=name)


@app.route('/add-item', methods=['GET'])
def add_item_form():
    profile_pic = sessn.get('profile_pic')
    name = sessn.get('name')
    return render_template('pages/add_item.html', profile_pic=profile_pic, name=name)


@app.route('/purchase-history')
def purchase_hitory():
    profile_pic = sessn.get('profile_pic')
    name = sessn.get('name')
    with Session(engine) as session:
        transaction_ids = session.query(distinct(PurchaseHistory.transaction_id)).all()
        transactions = []
        for (trans_id,) in transaction_ids:
            purchases = session.query(PurchaseHistory).filter_by(transaction_id=trans_id).all()
            if purchases:
                total = sum(purchase.price * purchase.quantity for purchase in purchases)
                transactions.append({
                    'transaction_id': trans_id,
                    'purchases': purchases,
                    'total': total,
                    'date': purchases[0].purchased_at # Use the first item's date
                })
    return render_template('pages/purchase_history.html', transactions=transactions, name=name, profile_pic=profile_pic)


@app.route('/add-item', methods=['POST'])
def add_item():
    item_name = request.form['item_name']
    quantity = request.form['quantity']
    price = request.form['price']
    with Session(engine) as session:
        new_item = ShoppingList(item_name=item_name, quantity=quantity, price=price)
        session.add(new_item)
        session.commit()
    return redirect(url_for('shopping_list'))


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    item_name = request.form['item_name']
    with Session(engine) as session:
        # Check available stock in ShoppingList
        shopping_item = session.query(ShoppingList).filter_by(item_name=item_name).first()
        if not shopping_item or shopping_item.quantity <= 0:
            return jsonify({'status': 'error', 'message': 'Item out of stock'}), 400
        
        # Check if item exists in cart
        cart_item = session.query(ShoppingCart).filter_by(item_name=item_name).first()
        if cart_item:
            if shopping_item.quantity <= cart_item.quantity:
                return jsonify({'status': 'error', 'message': 'Not enough stock'}), 400
            cart_item.quantity += 1
        else:
            cart_item = ShoppingCart(item_name=item_name, quantity=1)
            session.add(cart_item)

        # Reduce stock in ShoppingList
        shopping_item.quantity -= 1
        session.commit()

        # Fetch all cart items
        cart_items = session.query(ShoppingCart).all()
        cart_list = [{'id':item.id, 'item_name': item.item_name, 'quantity':item.quantity} for item in cart_items]
    return jsonify({'status':'success', 'cart':cart_list})


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    with Session(engine) as session:
        cart_items = session.query(ShoppingCart).all()
        if not cart_items:
            return 'Your cart is empty', 400
        
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
                        'unit_amount': int(shopping_item.price * 100) # Convert
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
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            return str(e), 500

  
@app.route('/success')
def success():
    session_id = request.args.get('session_id')
    if session_id:
        with Session(engine) as session:
            # Fetch cart items
            cart_items = session.query(ShoppingCart).all()
            for cart_item in cart_items:
                shopping_item = session.query(ShoppingList).filter_by(item_name=cart_item.item_name).first()
                if shopping_item:
                    # Purchase history log.
                    purchase = PurchaseHistory(
                        transaction_id=session_id,
                        item_name=cart_item.item_name,
                        quantity=cart_item.quantity,
                        price=float(shopping_item.price)
                    )
                    session.add(purchase)
                    session.delete(cart_item)
            session.commit()
    # Future changes here: remove items in cart when you buy and maybe even add a receipt 0_0.
    return redirect(url_for('shopping_list'))


@app.route('/cancel')
def cancel():
    return redirect(url_for('shopping_list'))


@app.route('/get-cart', methods=['GET'])
def get_cart():
    with Session(engine) as session:
        cart_items = session.query(ShoppingCart).all()
        cart_list = [{'id': item.id, 'item_name': item.item_name, 'quantity': item.quantity} for item in cart_items]
    return jsonify({'cart': cart_list})


@app.route('/delete-from-cart', methods=['POST'])
def delete_from_cart():
    item_id = request.form['item_id']
    with Session(engine) as session:
        item = session.query(ShoppingCart).filter_by(id=item_id).first()
        if item:
            session.delete(item)
            session.commit()
        cart_items = session.query(ShoppingCart).all()
        cart_list = [{'id': item.id, 'item_name': item.item_name, 'quantity': item.quantity} for item in cart_items]
    return jsonify({'cart': cart_list})


# Takes you to google's login thing.
@app.route('/login/google')
def login_google():
    return oauth.myApp.authorize_redirect(redirect_uri="http://localhost:5000" + url_for('google_callback'), _external=True)


# Where Google takes you after using their login thing.
@app.route('/auth/google/callback')
def google_callback():
    token = oauth.myApp.authorize_access_token()
    sessn['user'] = token
    # Login logic
    user_info = google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
    sessn['profile_pic'] = user_info['picture']  # Save profile picture URL
    sessn['name'] = user_info['name']
    user = db_session.query(User).filter_by(username=user_info['name']).first()
    # To update user roles
    if not user:
        user = User(username=user_info['name'], role='user') # user = filler data
    db_session.commit() # Commit changes to the database

    login_user(user)
    return redirect(url_for('shopping_list'))


# To log out the user.
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))