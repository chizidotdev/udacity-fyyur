#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from sqlalchemy.exc import SQLAlchemyError
from flask_wtf import Form
from forms import *
from models import db_setup, Venue, Artist, Show


app = Flask(__name__)
moment = Moment(app)
db = db_setup(app)
    
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  data=[]
  results = Venue.query.distinct(Venue.city, Venue.state).all()
  for result in results:
      city_state_unit = {
          "city": result.city,
          "state": result.state
      }
      venues = Venue.query.filter_by(city=result.city, state=result.state).all()

      # format each venue
      formatted_venues = []
      for venue in venues:
          formatted_venues.append({
              "id": venue.id,
              "name": venue.name,
              "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
          })
      
      city_state_unit["venues"] = formatted_venues
      data.append(city_state_unit)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"  
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }

  search_term = request.form.get('search_term', '')
  response = {}
  venues = list(Venue.query.filter(
      Venue.name.ilike(f"%{search_term}%") |
      Venue.state.ilike(f"%{search_term}%") |
      Venue.city.ilike(f"%{search_term}%") 
  ).all())
  response["count"] = len(venues)
  response["data"] = []

  for venue in venues:
      venue_unit = {
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
      }
      response["data"].append(venue_unit)
  
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  data = db.session.query(Venue).filter(Venue.id == venue_id).first()
  # print("data: ", data)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  form = VenueForm()

  # TODO: modify data to be the data object returned from db insertion
  if form.validate():
    try:
      seeking_talent = False
      if 'seeking_' in request.form:
        seeking_talent = request.form['seeking_venue'] == 'y'    
      new_venue = Venue(
          name=request.form['name'],
          city=request.form['city'],
          state=request.form['state'],
          address=request.form['address'],
          phone=request.form['phone'],
          genres=request.form.getlist('genres'),
          website=request.form['website_link'],
          facebook_link=request.form['facebook_link'],
          image_link=request.form['image_link'],
          seeking_talent=seeking_talent,
          seeking_description=request.form['seeking_description'],
      )
      # print("new_venue: ", request.form['seeking_talent'])
      db.session.add(new_venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

    except Exception:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue' + ' could not be listed.')

    finally:
        db.session.close()
  else:
    flash('An error occurred. Venue' + ' could not be listed.')
    print(form.errors)


  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback() 
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
   
  artist_data = Artist.query.all()
  return render_template('pages/artists.html', artists=artist_data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  artist_query = Artist.query.filter(Artist.name.ilike('%' + request.form['search_term'] + '%'))
  artist_list = list(map(Artist.short, artist_query)) 
  response = {
    "count":len(artist_list),
    "data": artist_list
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

    artist = Artist.query.get(artist_id)

    # get past shows
    past_shows = list(filter(lambda show: show.start_time < datetime.now(), artist.shows))
    temp_shows = []
    for show in past_shows:
        temp = {}
        temp["venue_name"] = show.venue_name
        temp["venue_id"] = show.venue_id
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

        temp_shows.append(temp)

    setattr(artist, "past_shows", temp_shows)
    setattr(artist, "past_shows_count", len(past_shows))


    # get upcoming shows
    upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), artist.shows))
    temp_shows = []
    for show in upcoming_shows:
        temp = {}
        temp["venue_name"] = show.venue_name
        temp["venue_id"] = show.venue_id
        temp["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")

        temp_shows.append(temp)

    setattr(artist, "upcoming_shows", temp_shows)
    setattr(artist, "upcoming_shows_count", len(upcoming_shows))

    return render_template('pages/show_artist.html', artist=artist)



  
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm(request.form)
  # TODO: populate form with fields from artist with ID <artist_id>

  artist_query = Artist.query.get(artist_id)

  return render_template('forms/edit_artist.html', form=form, artist=artist_query)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  if form.validate():
    try:
      artist_data = Artist.query.get(artist_id)

      artist_data.name = form.name.data
      artist_data.genres = form.genres.data
      artist_data.city = form.city.data
      artist_data.state = form.state.data
      artist_data.phone = form.phone.data
      artist_data.facebook_link = form.facebook_link.data
      artist_data.image_link = form.image_link.data
      artist_data.website_link = form.website_link.data
      artist_data.seeking_venue = form.seeking_venue.data
      artist_data.seeking_description = form.seeking_description.data

      artist_obj = db.session.merge(artist_data)
      
      db.session.add(artist_obj)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash("Artist was not edited successfully.")
    finally:
      db.session.close()

      # return redirect(url_for('show_artist', artist_id=artist_id))
  else:
      print(form.errors)
      flash('Artist was not updated!')

  return render_template('errors/404.html'), 404

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  # TODO: populate form with values from venue with ID <venue_id>
  venue_query = Venue.query.get(venue_id)

  return render_template('forms/edit_venue.html', form=form, venue=venue_query)
  
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  
  form = VenueForm(request.form)
  if form.validate():
    try:
        venue = Venue.query.get(venue_id)

        venue.name = form.name.data
        venue.city=form.city.data
        venue.state=form.state.data
        venue.address=form.address.data
        venue.phone=form.phone.data
        venue.genres=form.genres.data # convert array to string separated by commas
        venue.facebook_link=form.facebook_link.data
        venue.image_link=form.image_link.data
        venue.seeking_talent=form.seeking_talent.data
        venue.seeking_description=form.seeking_description.data
        venue.website_link=form.website_link.data

        venue_obj = db.session.merge(venue)

        db.session.add(venue_obj)
        db.session.commit()

        flash("Venue " + form.name.data + " edited successfully")
        
    except Exception:
        db.session.rollback()
        print(sys.exc_info())
        flash("Venue was not edited successfully.")
    finally:
        db.session.close()
  else: 
      print("\n\n", form.errors)
      flash("Venue was not edited successfully.")

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)

  if form.validate():
    try:
      seeking_venue = False
      if 'seeking_venue' in request.form:
        seeking_venue = request.form['seeking_venue'] == 'y'
      new_artist = Artist(
        name=request.form['name'],
        city=request.form['city'],
        state= request.form['state'],
        phone=request.form['phone'],
        genres=request.form.getlist('genres'),
        website=request.form['website_link'],
        facebook_link=request.form['facebook_link'],
        image_link=request.form['image_link'],
        seeking_venue=seeking_venue,
        seeking_description=request.form['seeking_description'],
      )
      db.session.add(new_artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
      
    except Exception:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist' + ' could not be listed.')
    finally:
        db.session.close()
  else:
    print(form.errors)
    flash('An error occurred. Artist' + ' could not be listed.')

      
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  # _data=[{
  #   "venue_id": 1,
  #   "venue_name": "The Musical Hop",
  #   "artist_id": 4,
  #   "artist_name": "Guns N Petals",
  #   "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "start_time": "2019-05-21T21:30:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 5,
  #   "artist_name": "Matt Quevedo",
  #   "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "start_time": "2019-06-15T23:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-01T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-08T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-15T20:00:00.000Z"
  # }]

  data = []

  shows = Show.query.all()
  for show in shows:
      show_data = {}
      show_data["venue_id"] = show.venues.id
      show_data["venue_name"] = show.venues.name
      show_data["artist_id"] = show.artists.id
      show_data["artist_name"] = show.artists.name
      show_data["artist_image_link"] = show.artists.image_link
      show_data["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
      
      data.append(show_data)
  
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

  if form.validate():
    try:
      new_show = Show(
        venue_id=request.form['venue_id'],
        artist_id=request.form['artist_id'],
        start_time=request.form['start_time'],
      )
      db.session.add(new_show)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
      
    except Exception:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Show could not be listed.')
    finally:
      db.session.close()
  else:
    print(form.errors)
    flash('An error occurred. Show was not listed.')
 
  return render_template('pages/home.html')

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
