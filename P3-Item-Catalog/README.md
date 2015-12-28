# Project 3 - Item Catalog
This web application displays a listing of restaurants, and a corresponding menu for each restaurant.  Registered users have the ability to create, update, and delete restaurants and menu items.

The application is based in Python, makes use of the Flask web-development framework, and is backed by a SQLite database.  Google's OAuth2 specifications are used for authorization.

### How can I get the code?
Feel free to Fork your own version of this code and play around within the files.

### What are the technical requirements?
* Python 2.7 (libraries: flask, sqlalchemy, werkzeug, oauth2client)

### What's Included
Within the repository you'll find the following files:
```
app.py
database_setup.py
restaurantmenu.db
client_secrets.json
static (directory)
templates (directory)
```

### How do I run the application?
1. Run app.py.  This will host the application on a local server.
2. Open web browser, and navigate to localhost:5000/
3. Play around in the app!

### Application Features
* JSON API endpoints provide read access to the restaurants and menu items in the database.
* Responsive web layout compatible with mobile and desktop browsers.
* Bootstrap styling for familiarity.
* Login using your Google credentials for access to 'Admin' features.
* Create new restaurants, and assign images or logos to each restaurant.
* Update menu item course, name, price, or description using dedicated forms.
