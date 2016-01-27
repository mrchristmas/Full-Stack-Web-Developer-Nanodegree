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
3. Use the [API Explorer][3]

### Application Features
* Create and manage user conferences
* Conferences include dates, cities, topics, maximum attendees, and number of seats still available.
* Users can register to attend conferences - the number of seats available adjusts based on registered attendees.
* As organizer of a conference, create Sessions specific to the conference.
* Sessions can have speakers, start time, duration, type of session (workshop, lecture etc…).
* Add conference sessions which you'd like to attend to your wishlist.
* Query for specific conferences and sessions based on various attributes of each.
 
### Using the API
- [API Explorer][3]
- Each endpoint includes a description documenting its purpose.
- [Google Cloud Endpoints][4]

### Model Design
Based on Google's ndb [Datastore][2] concept

Kinds:
- Profile
- Conference (parent: Profile)
- Session (parent: Conference)

####Design choices
I chose to implement Sessions in a similar vain as Conferences, creating Session as a Kind in the ndb model.  I also created two messages classes: SessionForm and SessionForms.  Session entities are children of a Conference entity to make for simpler querying and to ensure data integrity of each Session.  Session name is required, and Session highlights are repeatable (I was thinking like a Ted talk, how people tag talks as 'Inspiring' or 'Funny').  Duration is implemented as an integer and represents minutes.  Speaker is a string field.  User validation is in place such that only the organizer of the conference is allowed to create sessions for that conference.  The Profiles class include an attribute for storing Sessions to a user's wishlist.

The design for creating a Session is very similar to the design for creating a Conference.  In conference.py I created two regular methods: _createSessionObject and _copySessionToForm, as well as an endpoint: createSession.  Getting sessions via the various queries requires the user to provide a websafeConferenceKey and/or other parameters as part of the API request.  It should be relatively easy for a developer to supply these inputs as part of a front-end interface in order to interact with the Session API endpoints.

### Datastore Queries
#### Additional Queries
Get Conferences by Topic:
A user will want to know which conferences he/she would find of interest based on the conference topics.

Get Session by Highlights:
A user will want to know which sessions he/she would find of interest based on the session highlights.

Get Conference Sessions by Date (filtered for a conference, and sorted by session start time):
When viewing a list of sessions for a conference that spans many days, it can be useful to see a chronological list of sessions for a given day for that conference.  This can aid the user in creating an itinerary of sorts.

#### Problem with querying using inequality filters
Google's datastore has a well-known problem which makes it difficult to query the datastore using multiple inequality filters.  For example:  Let’s say that you don't like workshops and you don't like sessions after 7 pm. I would want to be able to query for all non-workshop sessions before 7 pm.  The problem is that Google does not allow me to run a single query where SessionType does not equal 'Workshops' and where StartTime is less than 7pm.  I can only run multiple inequality filters in one query for the same attribute (for example StartTime after 12pm and before 7pm).

My workaround for this was to create two queries.  One for the excluded SessionType, and one for the latest StartTime.  Then I would compare the fetched list objects against each other, and then return the values which resided in both lists.  This example can be found in conference.py in the getSessionsByTypeAndTime endpoint method.


[1]: https://developers.google.com/appengine
[2]: https://cloud.google.com/appengine/docs/python/ndb/
[3]: https://apis-explorer.appspot.com/apis-explorer/?base=https://conference-app-1181.appspot.com/_ah/api#p/
[4]: https://developers.google.com/appengine/docs/python/endpoints/
