#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db = SQLAlchemy(app)

migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    shows = db.relationship('Show', lazy=True, backref='venue')
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(120))    

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', lazy=True, backref='artist')
    
# TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'Show'

  show_id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

# create all tables
db.create_all()

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # show venues based on (city, state) group categories
  
  city_state = db.session.query(Venue.city, Venue.state).distinct().all()
  venues = [Venue.query.filter(Venue.city==c_s.city, Venue.state==c_s.state).all() for c_s in city_state]
  
  cities = [c_s[0] for c_s in city_state]
  states = [c_s[1] for c_s in city_state]

  c_s_v = list(zip(cities, states, venues))
  areas = [dict(zip(['city', 'state', 'venues'], item)) for item in c_s_v]

  return render_template('pages/venues.html', areas=areas);

@app.route('/venues/search', methods=['POST'])
def search_venues():

  search_term = request.form.get('search_term', '')
  # use ilike instead of like to guarantee case-insensitive
  response = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  
  now = datetime.datetime.now()
  venue = Venue.query.get_or_404(venue_id)
  upcoming = []
  past = []

  upcoming_shows = Show.query.filter(Show.venue_id == venue_id, Show.start_time > now).all()
  for show in upcoming_shows:
    upcoming.append(dict(zip(
      ['artist_image_link', 'artist_id', 'artist_name', 'start_time'],
      [show.artist.image_link, show.artist_id, show.artist.name, show.start_time]
    )))
  past_shows = Show.query.filter(Show.venue_id == venue_id, Show.start_time <= now).all()
  for show in past_shows:
    past.append(dict(zip(
      ['artist_image_link', 'artist_id', 'artist_name', 'start_time'],
      [show.artist.image_link, show.artist_id, show.artist.name, show.start_time]
    )))

  return render_template('pages/show_venue.html', venue=venue, upcoming=upcoming, past=past)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  data = request.form
  form = VenueForm(data)

  if form.validate_on_submit():
    
    # form validation pass, db insert
    venue = Venue(
      name = data.get('name'),
      city = data.get('city'),
      state = data.get('state'),
      address = data.get('address'),
      phone = data.get('phone'),
      image_link = data.get('image_link'),
      facebook_link = data.get('facebook_link'),
      genres = ','.join(data.getlist('genres'))
    )

    if data.get('seeking_talent') == 'yes':
      venue.seeking_talent = True
      venue.seeking_description = data.get('seeking_description')
    else:
      venue.seeking_talent = False
      venue.seeking_description = ''

    try:
      db.session.add(venue)
      db.session.commit()
    except():
      db.session.rollback()
      error = True
    finally:
      db.session.close()
    if error:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + data.name + ' could not be listed.', 'error')
    else:
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
      return render_template('pages/home.html')  

  else:
    # form.validate_on_submit fails, return to form and display errors
    return render_template('forms/new_venue.html', form=form)

#  Delete Venue
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  v_name = venue.name
  try:
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    flash(f'An error occurred. Venue {v_name} could not be deleted. Possiblly some show to be played or been played there', 'error')
    abort(500)
  finally:
    db.session.close()

  flash(f'Venue {v_name} was successfully deleted!', 'success')
  return render_template('/pages/home.html')


#  Update Venue
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)

  form = VenueForm(
    id = venue.id,
    name = venue.name,
    genres = venue.genres.split(','),
    address = venue.address,
    city = venue.city,
    state = venue.state,
    phone = venue.phone,
    website = venue.website,
    facebook_link = venue.facebook_link,
    seeking_talent = venue.seeking_talent,
    image_link = venue.image_link,
    seeking_description = venue.seeking_description
  )
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # Take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  data = request.form
  form = VenueForm(data)

  venue = Venue.query.get_or_404(venue_id)

  if form.validate_on_submit():
    # form validation pass, db update
    venue.name = data.get('name')
    venue.city = data.get('city')
    venue.state = data.get('state')
    venue.address = data.get('address')
    venue.phone = data.get('phone')
    venue.image_link = data.get('image_link')
    venue.facebook_link = data.get('facebook_link')
    venue.genres = ','.join(data.getlist('genres'))
    venue.website = data.get('website')

    if data.get('seeking_talent') == 'yes':
      venue.seeking_talent = True
      venue.seeking_description = data.get('seeking_description')
    else:
      venue.seeking_talent = False
      venue.seeking_description = ''

    try:
      db.session.commit()
    except():
      db.session.rollback()
      error = True
    finally:
      db.session.close()
    if error:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + data.name + ' could not be updated.', 'error')
    else:
      # on successful db insert, flash success and redicet to venue page
      flash('Venue ' + request.form['name'] + ' was successfully updated!', 'success')   
      return redirect(url_for('show_venue', venue_id=venue_id)) 
  else:
    # form validation fail, return to update view
    return render_template('forms/edit_venue.html', form=form, venue=venue)  
 

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  # use ilike instead of like to guarantee case-insensitive
  response = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  now = datetime.datetime.now()
  upcoming = []
  past = []

  for show in Show.query.filter(Show.artist_id==artist.id, Show.start_time > now).all():
    upcoming.append(dict(zip(
      ['start_time', 'venue_id', 'venue_name', 'venue_image_link'],
      [show.start_time, show.venue_id, show.venue.name, show.venue.image_link]
    )))

  for show in Show.query.filter(Show.artist_id==artist.id, Show.start_time <= now).all():
    past.append(dict(zip(
      ['start_time', 'venue_id', 'venue_name', 'venue_image_link'],
      [show.start_time, show.venue_id, show.venue.name, show.venue.image_link]
    )))

  return render_template('pages/show_artist.html', artist=artist, upcoming_shows=upcoming, past_shows=past)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(
    id = artist.id,
    name = artist.name,
    genres = artist.genres.split(','),
    city = artist.city,
    state = artist.state,
    phone = artist.phone,
    website = artist.website,
    facebook_link = artist.facebook_link,
    seeking_venue = artist.seeking_venue,
    seeking_description = artist.seeking_description,
    image_link = artist.image_link
  )
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  data = request.form
  form = ArtistForm(data)

  artist = Artist.query.get_or_404(artist_id)

  if form.validate_on_submit():
    # form validation pass, db update
    artist.name = data.get('name')
    artist.city = data.get('city')
    artist.state = data.get('state')
    artist.website = data.get('website')
    artist.phone = data.get('phone')
    artist.image_link = data.get('image_link')
    artist.facebook_link = data.get('facebook_link')
    artist.genres = ','.join(data.getlist('genres'))
    if data.get('seeking_venue') == 'yes':
      artist.seeking_venue = True
      artist.seeking_description = data.get('seeking_description')
    else:
      artist.seeking_venue = False
      artist.seeking_description = ''

    try:
      db.session.commit()
    except():
      db.session.rollback()
      error = True
    finally:
      db.session.close()
    if error:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + data.name + ' could not be updated.', 'error')
    else:
      # on successful db insert, flash success and redicet to venue page
      flash('Artist ' + request.form['name'] + ' was successfully updated!', 'success')   
      return redirect(url_for('show_artist', artist_id=artist_id)) 
  else:
    # form validation fail, return to update view
    return render_template('forms/edit_artist.html', form=form, artist=artist)  


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  data = request.form
  form = ArtistForm(request.form)

  if form.validate_on_submit():
    artist = Artist(
      id = data.get('id'),
      name = data.get('name'),
      city = data.get('city'),
      state = data.get('state'),
      phone = data.get('phone'),
      genres = ','.join(data.getlist('genres')),
      image_link = data.get('image_link'),
      facebook_link = data.get('facebook_link'),
      website = data.get('website'),
    )

    if data.get('seeking_venue') == 'yes':
      artist.seeking_venue = True
      artist.seeking_description = data.get('seeking_description')
    else:
      artist.seeking_venue = False

    try:
      db.session.add(artist)
      db.session.commit()
    except():
      db.session.rollback()
      error = True
    if error:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
      return render_template('pages/home.html')
  else:
    # form.validate_on_submit fails, return to the form and display errors
    return render_template('forms/new_artist.html', form=form)

#  Delete Artist
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  a_name = artist.name
  try:
    db.session.delete(artist)
    db.session.commit()
  except:
    db.session.rollback()
    flash(f'An error occurred. Artist {a_name} could not be deleted. Possiblly the artist has some show to play or has played some show', 'error')
    abort(500)
  finally:
    db.session.close()

  flash(f'Artist {a_name} was successfully deleted!', 'success')
  return render_template('/pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  query = Show.query.all()
  data = [dict(zip(['venue_id', 'venue_name', 'artist_id', 'artist_name', 'artist_image_link', 'start_time']
   , [q.venue_id, q.venue.name, q.artist_id, q.artist.name, q.artist.image_link, q.start_time.strftime('%Y-%m-%d %H:%M')])) for q in query]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)
  error = False

  if form.validate_on_submit():
    # form validation passed, then check against db
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')
    # check artist id
    if Artist.query.get(artist_id) is None:
      flash(f'Artist with id {artist_id} has not been listed! Please check and input again.', 'error')
      return render_template('forms/new_show.html', form=form)
    # check venue id
    if Venue.query.get(venue_id) is None:
      flash(f'Venue with id {venue_id} has not been listed! Please check and input again.', 'error')
      return render_template('forms/new_show.html', form=form)
    # check if list time is earlier than now
    if False:
      return render_template('forms/new_show.html', form=form)

    # all check passed, db insert now
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)   

    try:
      db.session.add(show)
      db.session.commit()
    except():
      db.session.rollback()
      error = True
    finally:
      db.session.close()
    if error:
      flash('An error occurred. The show could not be listed.', 'error')
    else:
      # on successful db insert, flash success
      flash('Show was successfully listed!')
      return render_template('pages/home.html')

  # form.validate_on_submit() fails, re-direct back to the new_show page and display errors in the form
  else:
    return render_template('forms/new_show.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
