#!/usr/bin/env python
"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21
__author__ = 'wesc+api@google.com (Wesley Chun)'
"""
from datetime import datetime
import json
import os
import time
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import taskqueue
from models import BooleanMessage
from models import StringMessage
from models import SpeakerMessage
from models import ConflictException
from models import Profile
from models import ProfileMiniForm
from models import ProfileForm
from models import TeeShirtSize
from models import Conference
from models import ConferenceForm
from models import ConferenceForms
from models import ConferenceQueryForm
from models import ConferenceQueryForms
from models import Session
from models import SessionForm
from models import SessionForms
from settings import WEB_CLIENT_ID
from utils import getUserId

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": ["Default", "Topic"],
}

SESSION_DEFAULTS = {
    "highlights": ["Default", "Highlight"],
    "duration": 60,
    "typeOfSession": "Lecture",
}

OPERATORS = {
            'EQ':   '=',
            'GT':   '>',
            'GTEQ': '>=',
            'LT':   '<',
            'LTEQ': '<=',
            'NE':   '!='
            }

FIELDS = {
         'CITY': 'city',
         'TOPIC': 'topics',
         'MONTH': 'month',
         'MAX_ATTENDEES': 'maxAttendees',
         }

CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

CONF_POST_REQUEST = endpoints.ResourceContainer(
    ConferenceForm,
    websafeConferenceKey=messages.StringField(1),
)

CONF_QRY_BY_TOPIC = endpoints.ResourceContainer(
    topics=messages.StringField(1, repeated=True),
)

SESS_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey=messages.StringField(1),
)

SESS_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey=messages.StringField(1),
)

SESS_QRY_BY_TYPE = endpoints.ResourceContainer(
    websafeConferenceKey=messages.StringField(1),
    typeOfSession=messages.StringField(2),
)

SESS_QRY_BY_DATE = endpoints.ResourceContainer(
    websafeConferenceKey=messages.StringField(1),
    dateOfSession=messages.StringField(2),
)

SESS_QRY_BY_SPEAKER = endpoints.ResourceContainer(
    speaker=messages.StringField(1),
)

SESS_QRY_BY_TYPE_AND_TIME = endpoints.ResourceContainer(
    typeOfSessionNot=messages.StringField(2),
    startTimeBefore=messages.StringField(3),
)

SESS_QRY_BY_HIGHLIGHT = endpoints.ResourceContainer(
    highlights=messages.StringField(1, repeated=True),
)

MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT ANNOUNCEMENTS"

MEMCACHE_FEATURED_SPEAKER_KEY = "FEATURED SPEAKER"
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


@endpoints.api(name='conference',
               version='v1',
               allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
               scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""

# - - - Profile objects - - - - - - - - - - - - - - - - - - -

    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(pf, field.name,
                            getattr(TeeShirtSize, getattr(prof, field.name)))
                else:
                    setattr(pf, field.name,
                            getattr(prof, field.name))
        pf.check_initialized()
        return pf

    def _getProfileFromUser(self):
        """Return user Profile from datastore,
           creating new one if non-existent.
        """
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get user id by calling getUserId(user)
        user_id = getUserId(user)
        # create a new key of kind Profile from the id
        p_key = ndb.Key(Profile, user_id)

        # get the entity from datastore by using get() on the key
        profile = p_key.get()
        if not profile:
            profile = Profile(
                key=p_key,
                displayName=user.nickname(),
                mainEmail=user.email(),
                teeShirtSize=str(TeeShirtSize.NOT_SPECIFIED),
            )
            # save the profile to datastore
            profile.put()
        return profile

    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
            # put the modified profile to datastore
            prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)

    @endpoints.method(message_types.VoidMessage, ProfileForm,
                      path='profile', http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()

    @endpoints.method(ProfileMiniForm, ProfileForm,
                      path='profile', http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)

# - - - Conference objects - - - - - - - - - - - - - - - - -
    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm."""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf

    def _createConferenceObject(self, request):
        """Create or update Conference object,
        returning ConferenceForm/request.
        """
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException("Conference 'name' required")

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']

        # add default values for those missing
        # (both data model & outbound Message)
        for df in DEFAULTS:
            if data[df] in (None, []):
                data[df] = DEFAULTS[df]
                setattr(request, df, DEFAULTS[df])

        # convert dates from strings to Date objects;
        # set month based on start_date
        if data['startDate']:
            data['startDate'] = datetime.strptime(data['startDate'][:10],
                                                  "%Y-%m-%d").date()
            data['month'] = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = datetime.strptime(data['endDate'][:10],
                                                "%Y-%m-%d").date()

        # set seatsAvailable to be same as maxAttendees on creation
        # both for data model & outbound Message
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
            setattr(request, "seatsAvailable", data["maxAttendees"])

        # make Profile Key from user ID
        p_key = ndb.Key(Profile, user_id)
        # allocate new Conference ID with Profile key as parent
        c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
        # make Conference key from ID
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        data['key'] = c_key
        data['organizerUserId'] = request.organizerUserId = user_id

        # create Conference
        Conference(**data).put()
        # send email to organizer confirming creation
        taskqueue.add(params={'email': user.email(),
                      'conferenceInfo': repr(request)},
                      url='/tasks/send_confirmation_email'
                      )

        # return (modified) ConferenceForm
        return request

    @ndb.transactional()
    def _updateConferenceObject(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}

        # update existing conference
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s'
                % request.websafeConferenceKey)

        # check that user is owner
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')

        # Not getting all the fields, so don't create a new object; just
        # copy relevant fields from ConferenceForm to Conference object
        for field in request.all_fields():
            data = getattr(request, field.name)
            # only copy fields where we get data
            if data not in (None, []):
                # special handling for dates (convert string to Date)
                if field.name in ('startDate', 'endDate'):
                    data = datetime.strptime(data, "%Y-%m-%d").date()
                    if field.name == 'startDate':
                        conf.month = data.month
                # write to Conference object
                setattr(conf, field.name, data)
        conf.put()
        prof = ndb.Key(Profile, user_id).get()
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))

    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
                      http_method='POST', name='createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)

    @endpoints.method(CONF_POST_REQUEST, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='PUT', name='updateConference')
    def updateConference(self, request):
        """Update conference w/provided fields & return w/updated info."""
        return self._updateConferenceObject(request)

    @endpoints.method(ConferenceQueryForms, ConferenceForms,
                      path='queryConferences',
                      http_method='POST',
                      name='queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""
        conferences = self._getQuery(request)

        # return individual ConferenceForm object per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "")
                   for conf in conferences]
                   )

    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='GET', name='getConference')
    def getConference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s'
                % request.websafeConferenceKey)
        prof = conf.key.parent().get()
        # return ConferenceForm
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='getConferencesCreated',
                      http_method='POST',
                      name='getConferencesCreated')
    def getConferencesCreated(self, request):
        """Query for conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # make profile key
        p_key = ndb.Key(Profile, getUserId(user))
        # create ancestor query for this user
        conferences = Conference.query(ancestor=p_key)
        # get the user profile and display name
        prof = p_key.get()
        displayName = getattr(prof, 'displayName')
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, displayName)
                   for conf in conferences]
        )

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='conferences/attending',
                      http_method='GET', name='getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        # Get user profile
        prof = self._getProfileFromUser()

        # Get conferenceKeysToAttend from profile.
        array_of_keys = []
        for i in (prof.conferenceKeysToAttend):
            # make a ndb key from websafe key
            array_of_keys.append(ndb.Key(urlsafe=i))

        # Fetch conferences from datastore.
        conferences = ndb.get_multi(array_of_keys)

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(items=[self._copyConferenceToForm(conf, "")
                               for conf in conferences]
                               )

    @endpoints.method(CONF_QRY_BY_TOPIC, ConferenceForms,
                      path='conferencesByTopic',
                      http_method='GET', name='getConferencesByTopic')
    def getConferencesByTopic(self, request):
        """Given topic(s), return all conferences
        with one or more matching topics.
        """
        # create query for all conferences with given topics
        confs = Conference.query(Conference.topics.IN(request.topics))
        # return set of ConferenceForm objects per Session
        return ConferenceForms(
            items=[self._copyConferenceToForm(
                   conf, getattr(conf.key.parent().get(), 'displayName'))
                   for conf in confs]
        )

    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)

        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(filtr["field"],
                                                   filtr["operator"],
                                                   filtr["value"])
            q = q.filter(formatted_query)
        return q

    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {field.name: getattr(f, field.name)
                     for field in f.all_fields()}

            try:
                filtr["field"] = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException(
                    "Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality has been used in previous filters
                # disallow if inequality was performed on different field
                # track field on which the inequality operation is performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException(
                        "Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)

    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        retval = None
        # get user Profile
        prof = self._getProfileFromUser()

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException(
                    "There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='POST', name='registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        return self._conferenceRegistration(request)

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='DELETE', name='unregisterFromConference')
    def unregisterFromConference(self, request):
        """Unregister user for selected conference."""
        return self._conferenceRegistration(request, False)

# - - - Sessions - - - - - - - - - - - - - - - - - - - - - -
    def _copySessionToForm(self, sess):
        """Copy relevant fields from Session to SessionForm."""
        sf = SessionForm()
        for field in sf.all_fields():
            if hasattr(sess, field.name):
                # convert Date and Time to string; just copy others
                if field.name.endswith('date'):
                    setattr(sf, field.name, str(getattr(sess, field.name)))
                elif field.name.endswith('Time'):
                    setattr(sf, field.name, str(getattr(sess, field.name)))
                else:
                    setattr(sf, field.name, getattr(sess, field.name))
            elif field.name == "websafeKey":
                setattr(sf, field.name, sess.key.urlsafe())
        sf.check_initialized()
        return sf

    def _createSessionObject(self, request):
        """Create or update Session object, returning SessionForm/request."""
        # Check for user login
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # Check that Session name was provided
        if not request.name:
            raise endpoints.BadRequestException(
                "Session 'name' field required")

        # Check that conference key is provided
        if not request.websafeConferenceKey:
            raise endpoints.BadRequestException(
                "Session 'websafeConferenceKey' field required")

        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s'
                % request.websafeConferenceKey)

        # check that user is owner of the conference
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the conference owner can create sessions.')

        # copy SessionForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}
        del data['websafeKey']
        del data['websafeConferenceKey']

        # add defaults for those missing (both data model & outbound Message)
        for df in SESSION_DEFAULTS:
            if data[df] in (None, []):
                data[df] = SESSION_DEFAULTS[df]
                setattr(request, df, SESSION_DEFAULTS[df])

        # convert dates and times from strings to Date and Time objects;
        if data['date']:
            data['date'] = datetime.strptime(data['date'][:10],
                                             "%Y-%m-%d").date()
        if data['startTime']:
            data['startTime'] = datetime.strptime(data['startTime'][:5],
                                                  "%H:%M").time()

        # get Conference key from url
        c_key = ndb.Key(urlsafe=request.websafeConferenceKey)
        # allocate new Session ID with Conference key as parent
        s_id = Session.allocate_ids(size=1, parent=c_key)[0]
        # make Session key from IDs
        s_key = ndb.Key(Session, s_id, parent=c_key)
        data['key'] = s_key

        # create Session and return (modified) SessionForm
        Session(**data).put()
        # add task to check if session speaker should be featured
        taskqueue.add(params={
                     'websafeConferenceKey': request.websafeConferenceKey,
                     'speaker': data['speaker']},
                     url='/tasks/check_featured_speaker',
                     method='GET'
                     )
        return self._copySessionToForm(s_key.get())

    @endpoints.method(SESS_POST_REQUEST, SessionForm,
                      path='conference/{websafeConferenceKey}/create_session',
                      http_method='POST', name='createSession')
    def createSession(self, request):
        """Create new session."""
        return self._createSessionObject(request)

    @endpoints.method(CONF_GET_REQUEST, SessionForms,
                      path='conference/{websafeConferenceKey}/sessions',
                      http_method='GET', name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """Given a conference, return all sesssions."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s'
                % request.websafeConferenceKey)
        # create ancestor query for all key matches for this conference
        sessions = Session.query(ancestor=ndb.Key(
            urlsafe=request.websafeConferenceKey))
        # return set of SessionForm objects per Session
        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in sessions])

    @endpoints.method(SESS_QRY_BY_TYPE, SessionForms,
                      path='conferenceSessionsByType',
                      http_method='GET', name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        """Given a conference, return all sesssions with a specific type."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s'
                % request.websafeConferenceKey)
        # create ancestor query for all key matches for this conference
        sessions = Session.query(ancestor=ndb.Key(
            urlsafe=request.websafeConferenceKey))
        # filter sessions by typeOfSession
        sessions = sessions.filter(
            Session.typeOfSession == request.typeOfSession)
        # return set of SessionForm objects per Session
        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in sessions])

    @endpoints.method(SESS_QRY_BY_DATE, SessionForms,
                      path='conferenceSessionsByDate',
                      http_method='GET', name='getConferenceSessionsByDate')
    def getConferenceSessionsByDate(self, request):
        """Given a conference and a date, return all sessions,
        ordered by session start time."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s'
                % request.websafeConferenceKey)

        # convert date from string to Date object;
        queryDate = datetime.strptime(request.dateOfSession[:10],
                                      "%Y-%m-%d").date()

        # create ancestor query for all key matches for this conference
        sessions = Session.query(ancestor=ndb.Key(
            urlsafe=request.websafeConferenceKey))
        # filter sessions by dateOfSession
        sessions = sessions.filter(Session.date == queryDate)
        # order sessions by startTime
        sessions = sessions.order(Session.startTime)
        # return set of SessionForm objects per Session
        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in sessions])

    @endpoints.method(SESS_QRY_BY_SPEAKER, SessionForms,
                      path='sessionsBySpeaker',
                      http_method='GET', name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Given a speaker, return all sessions given by this
        particular speaker, across all conferences.
        """
        # create query for all sessions with given speaker
        sessions = Session.query(Session.speaker == request.speaker)
        # return set of SessionForm objects per Session
        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in sessions])

    @endpoints.method(SESS_QRY_BY_HIGHLIGHT, SessionForms,
                      path='sessionsByHighlight',
                      http_method='GET', name='getSessionsByHighlight')
    def getSessionsByHighlights(self, request):
        """Given highlight(s), return all sessions
        with one or more matching highlights, across all conferences.
        """
        # create query for all sessions with given highlights
        sessions = Session.query(Session.highlights.IN(request.highlights))
        # return set of SessionForm objects per Session
        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in sessions])

    @endpoints.method(SESS_QRY_BY_TYPE_AND_TIME, SessionForms,
                      path='sessionsByTypeAndTime',
                      http_method='GET', name='getSessionsByTypeAndTime')
    def getSessionsByTypeAndTime(self, request):
        """Return all sessions that match a type and time preference.
        """
        # convert time string to time data type
        queryTime = datetime.strptime(request.startTimeBefore[:5],
                                      "%H:%M").time()

        # create query for all sessions before given startTime
        sessions_type = Session.query(
            Session.typeOfSession != request.typeOfSessionNot)
        sessions_time = Session.query(
            Session.startTime < queryTime)

        # add sessions that match type criteria to a list
        list_by_type = []
        for session in sessions_type:
            list_by_type.append(session)

        list_of_sessions = []
        # for each session that matches time criteria
        for session in sessions_time:
            # check if this also meets the type criteria
            if session in list_by_type:
                # add to list which will be returned
                list_of_sessions.append(session)

        # return set of SessionForm objects per Session
        return SessionForms(
            items=[self._copySessionToForm(sess) for sess in list_of_sessions])

# - - - Wishlist - - - - - - - - - - - - - - - - - - - - - - -
    @ndb.transactional(xg=True)
    def _sessionWishlist(self, request, add=True):
        """Register or unregister user for selected conference."""
        retval = None
        # get user Profile
        prof = self._getProfileFromUser()

        # check if sess exists given websafeSessionKey
        # get session; check that it exists
        wsck = request.websafeSessionKey
        sess = ndb.Key(urlsafe=wsck).get()
        if not sess:
            raise endpoints.NotFoundException(
                'No session found with key: %s' % wsck)

        # add
        if add:
            # check if user already added, otherwise add
            if wsck in prof.sessionKeysToAttend:
                raise ConflictException(
                    "You have already added this session to your wishlist.")

            # add session to user's wishlist
            prof.sessionKeysToAttend.append(wsck)
            retval = True

        # delete
        else:
            # check if user already registered
            if wsck in prof.sessionKeysToAttend:

                # delete session from user's wishlist
                prof.sessionKeysToAttend.remove(wsck)
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        return BooleanMessage(data=retval)

    @endpoints.method(message_types.VoidMessage, SessionForms,
                      path='sessions/wishlist',
                      http_method='GET', name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        """Query for all the sessions in a conference
        that the user is interested in.
        """
        # get user Profile
        prof = self._getProfileFromUser()
        sess_keys = [ndb.Key(urlsafe=wsck)
                     for wsck in prof.sessionKeysToAttend]
        sessions = ndb.get_multi(sess_keys)

        # return set of ConferenceForm objects per Conference
        return SessionForms(items=[self._copySessionToForm(sess)
                                   for sess in sessions])

    @endpoints.method(SESS_GET_REQUEST, BooleanMessage,
                      path='session/{websafeSessionKey}',
                      http_method='POST', name='addSessionToWishlist')
    def addSessionToWishlist(self, request):
        """Adds the session to the user's list
        of sessions they are interested in attending.
        """
        return self._sessionWishlist(request)

    @endpoints.method(SESS_GET_REQUEST, BooleanMessage,
                      path='session/{websafeSessionKey}',
                      http_method='DELETE', name='deleteSessionInWishlist')
    def deleteSessionInWishlist(self, request):
        """Deletes the session from the user's list
        of sessions they are interested in attending.
        """
        return self._sessionWishlist(request, add=False)

# - - - Announcements - - - - - - - - - - - - - - - - - - - -
    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache; used by
        memcache cron job & putAnnouncement().
        """
        confs = Conference.query(ndb.AND(
            Conference.seatsAvailable <= 5,
            Conference.seatsAvailable > 0)
        ).fetch(projection=[Conference.name])

        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = '%s %s' % (
                'Last chance to attend! The following conferences '
                'are nearly sold out:',
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

        return announcement

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='conference/announcement/get',
                      http_method='GET', name='getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        # return an existing announcement from Memcache or an empty string.
        announcement = memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY)
        if not announcement:
            announcement = ""
        return StringMessage(data=announcement)

# - - - Featured Speaker - - - - - - - - - - - - - - - - - - - -
    @staticmethod
    def _cacheFeaturedSpeaker(websafeConferenceKey, session_speaker):
        """Check if speaker should be a Featured speaker for the conference,
        and set in memcache if so; used by memcache & getFeaturedSpeaker().
        """

        # query for all sessions with given speaker
        sessions = Session.query(ancestor=ndb.Key(
            urlsafe=websafeConferenceKey))
        sessions = sessions.filter(Session.speaker == session_speaker)

        speaker = ""
        session_names = ""

        if sessions and sessions.count() > 1:
            # If there is more than one session by this speaker
            # at this conference, add a memcache entry that
            # features the speaker and session names.
            speaker = session_speaker
            for session in sessions:
                session_names += ', '+session.name

            memcache.set(
                         MEMCACHE_FEATURED_SPEAKER_KEY, (
                                                         speaker,
                                                         session_names
                                                         )
                         )

        return (speaker, session_names)

    @endpoints.method(message_types.VoidMessage, SpeakerMessage,
                      path='conference/featured',
                      http_method='GET', name='getFeaturedSpeaker')
    def getFeaturedSpeaker(self, request):
        """Return Featured Speaker from memcache."""
        # return Featured Speaker from Memcache or an empty string.
        mem = memcache.get(MEMCACHE_FEATURED_SPEAKER_KEY)
        if not mem:
            mem = ""
        return SpeakerMessage(speaker_msg=mem[0], sessions_msg=mem[1])

# registers API
api = endpoints.api_server([ConferenceApi])
