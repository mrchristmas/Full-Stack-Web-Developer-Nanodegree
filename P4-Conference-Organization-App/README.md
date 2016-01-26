# Project 4 - Conference Organization App
This web application was built for the purpose of managing the creation and organization of user conferences.

The application is deployed on [Google's App Engine][1]. While it includes a front-end for some navigation, emphasis was placed on the API endpoints for manipulating the information contained in the Google [Datastore][2].

### How can I get the code?
Feel free to Fork your own version of this code and play around within the files.

### What are the technical requirements?
* Google App Engine Launcher
* Python 2.7 (libraries: protorpc)

### What's Included
Within the repository you'll find the following files:
```
conference.py
main.py
models.py
settings.py
utils.py
app.yaml
cron.yaml
index.yaml
static (directory)
templates (directory)
```

### How do I run the application?
1. Open web browser, navigate to https://conference-app-1181.appspot.com/
2. Play around in the app!

### Application Features
* 

### Using the API
- [Google Cloud Endpoints][3]

### Model Design
Kinds:
- Profile
- Conference (parent: Profile)
- Session (parent: Conference)

I chose to implement Sessions in a similar vain as Conferences, creating Session as a Kind in the ndb model.  I also created two messages classes: SessionForm and SessionForms.  Session entities are children of a Conference entity to make for simpler querying and to ensure data integrity of each Session.  Session name is required, and Session highlights are repeatable (I was thinking like a Ted talk, how people tag talks as 'Inspiring' or 'Funny').  Duration is implemented as an integer and represents minutes.  Speaker is left as a string field for now.  User validation is in place such that only the organizer of the conference is allowed to create sessions for that conference.

The design for creating a session is very similar to the design for creating a Conference.  In conference.py I created two regular methods: _createSessionObject and _copySessionToForm, as well as an endpoint: createSession.  Getting sessions via the various queries requires the user to provide a websafeConferenceKey and/or other parameters as part of the api request.  It should be relatively easy for a developer to supply these inputs as part of a front-end interface in order to interact with the Session API endpoints.




[1]: https://developers.google.com/appengine
[2]: https://cloud.google.com/appengine/docs/python/ndb/
[3]: https://developers.google.com/appengine/docs/python/endpoints/
