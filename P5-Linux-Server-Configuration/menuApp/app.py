# app.py

import os

# Flask routing
from flask import Flask, render_template, request, redirect, url_for, flash

# Database setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

# CSRF
from flask.ext.seasurf import SeaSurf

# Login sessions
from flask import session as login_session
from functools import wraps
import random
import string

# Oauth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# Image uploads
from flask import send_from_directory
from werkzeug import secure_filename

# JSON API
from flask import jsonify

# XML API
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import tostring
import xml.etree.ElementTree as etree

# Initialize app
app = Flask(__name__)
csrf = SeaSurf(app)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

# Open Database Session
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create a state token to prevent request forgery.
# Store it in the session for later validation.
@app.route('/login')
def showLogin():
    """
    showLogin: show the user login screen
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


# Google Auth Connect
@csrf.exempt
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """gconnect: connect a user via google auth"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;\
        -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Google Auth Disconnect
@app.route('/gdisconnect')
def gdisconnect():
    """gdisconnect: disconnect a user from google auth"""
    access_token = login_session['credentials']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['credentials']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successfully logged out.")
        return redirect(url_for('showRestaurants'))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        flash("Failed to revoke token for given user.")
        return redirect(url_for('showRestaurants'))

# Image Uploads
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 # 1 MB limit on file size

# Define allowable file upload extensions
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/static/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Begin API Endpoints
# All restaurants
@app.route('/restaurants/JSON')
def restaurantsJSON():
    """
    restaurantsJSON: returns a list of all restaurants in JSON format
    """
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurants=[i.serialize for i in restaurants])


@app.route('/restaurants/xml')
def restaurantsXML():
    """
    restaurantsXML: returns a list of all restaurants in XML format
    """
    # Query database for all restaurants
    restaurants = session.query(Restaurant).all()

    # Declare root node of XML
    root = Element('Restaurants')

    # Loop through query responses and format as XML
    for r in restaurants:
        parent = SubElement(root, 'Restaurant')
        parent.set('id', str(r.id))
        child = SubElement(parent, 'name')
        child.text = r.name

    return app.response_class(tostring(root), mimetype='application/xml')


# Menu for a specific restaurant
@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    """
    restaurantMenuJSON: returns a menu in JSON format
    Args:
        restaurant_id (int): the id for the restaurant
    """
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurant/<int:restaurant_id>/menu/XML')
def restaurantMenuXML(restaurant_id):
    """
    restaurantMenuXML: returns a menu in XML format
    Args:
        restaurant_id (int): the id for the restaurant
    """
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    # Declare root node of XML
    root = Element('MenuItems')

    # Loop through query responses and format as XML
    for i in items:
        parent = SubElement(root, 'MenuItem')
        parent.set('id', str(i.id))
        child = SubElement(parent, 'course')
        child.text = i.course
        child = SubElement(parent, 'name')
        child.text = i.name
        child = SubElement(parent, 'description')
        child.text = i.description
        child = SubElement(parent, 'price')
        child.text = i.price

    return app.response_class(tostring(root), mimetype='application/xml')


# Specific menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def restaurantMenuItemJSON(restaurant_id, menu_id):
    """
    restaurantMenuItemJSON: returns a menu item in JSON format
    Args:
        restaurant_id (int): the id for the restaurant
        menu_id (int): the id for the menu item
    """
    menuItem = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=menuItem.serialize)


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/XML')
def restaurantMenuItemXML(restaurant_id, menu_id):
    """
    restaurantMenuItemXML: returns a menu item in XML format
    Args:
        restaurant_id (int): the id for the restaurant
        menu_id (int): the id for the menu item
    """
    menuItem = session.query(MenuItem).filter_by(id=menu_id).one()

    return app.response_class(tostring(menuItem.serialize),
                              mimetype='application/xml')
# End API Endpoints


# Show all restaurants
@app.route('/')
@app.route('/restaurants')
def showRestaurants():
    """
    showRestaurants: display all restaurants
    """
    restaurants = session.query(Restaurant).order_by(Restaurant.name).all()
    if 'username' not in login_session:
        return render_template('publicRestaurants.html',
                               restaurants=restaurants)
    return render_template('restaurants.html', restaurants=restaurants)


# New Restaurant
@app.route('/restaurant/new', methods=['GET', 'POST'])
@login_required
def newRestaurant():
    """
    newRestaurant: allows users to create a new restaurant
    """
    if request.method == 'POST':
        newRestaurant = Restaurant(name=request.form['name'])
        session.add(newRestaurant)
        session.commit()

        file = request.files['file']
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            filename = str(newRestaurant.id)+'.jpg'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        flash("New restaurant created!")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newRestaurant.html')


# Edit Restaurant
@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET', 'POST'])
@login_required
def editRestaurant(restaurant_id):
    """
    editRestaurant: allows users to update a restaurant
    Args:
        restaurant_id (int): the id for the restaurant to edit
    """
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        restaurant.name = request.form['name']

        file = request.files['file']
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            filename = str(restaurant_id)+'.jpg'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        session.commit()

        flash("Restaurant successfully edited")
        return redirect(url_for('showMenu', restaurant_id=restaurant.id))
    else:
        return render_template('editRestaurant.html', restaurant=restaurant)


# Delete Restaurant
@app.route('/restaurant/<int:restaurant_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteRestaurant(restaurant_id):
    """
    deleteRestaurant: allows users to delete a restaurant
    Args:
        restaurant_id (int): the id for the restaurant to delete
    """
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        session.delete(restaurant)
        session.commit()
        flash("Restaurant successfully deleted")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('deleteRestaurant.html', restaurant=restaurant)


# Show Restaurant Menu
@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    """
    showMenu: display all menu items for a restaurant
    Args:
        restaurant_id (int): the id for the restaurant to view
    """
    restaurant = \
        session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = \
        session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    if 'username' not in login_session:
        return render_template('publicMenu.html',
                               restaurant=restaurant, items=items)
    return render_template('menu.html', restaurant=restaurant, items=items)


# Create new menu item
@app.route('/restaurant/<int:restaurant_id>/menu/new', methods=['GET', 'POST'])
@login_required
def newMenuItem(restaurant_id):
    """
    newMenuItem: allows users to create a new menu item for a restaurant
    Args:
        restaurant_id (int): the id for the restaurant to create the new menu
        item.
    """
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        newItem = MenuItem(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            course=request.form['course'],
            restaurant_id=restaurant_id)
        session.add(newItem)
        session.commit()
        flash("New menu item created!")
        return redirect(url_for('showMenu', restaurant_id=restaurant.id))
    else:
        return render_template('newMenuItem.html', restaurant=restaurant)


# Edit menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editMenuItem(restaurant_id, menu_id):
    """
    editMenuItem: allows users to update a menu item for a restaurant
    Args:
        restaurant_id (int): the id for the restaurant to edit the menu item
    """
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.price = request.form['price']
        item.course = request.form['course']
        session.commit()
        flash("Menu item successfully edited")
        return redirect(url_for('showMenu', restaurant_id=restaurant.id))
    else:
        return render_template('editMenuItem.html',
                               restaurant=restaurant, item=item)


# Delete menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteMenuItem(restaurant_id, menu_id):
    """
    editRestaurant: allows users to delete a menu item for a restaurant
    Args:
        restaurant_id (int): the id for the restaurant to delete the menu item
    """
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Menu item successfully deleted")
        return redirect(url_for('showMenu', restaurant_id=restaurant.id))
    else:
        return render_template('deleteMenuItem.html',
                               restaurant=restaurant, item=item)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = False
    app.run(host='0.0.0.0', port=5000)
