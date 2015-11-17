import webbrowser


class Movie(object):
    """ This class provides a way to store movie information. """

    def __init__(self, movie_title, year, movie_storyline, poster_image, trailer_youtube):
        self.title = movie_title
        self.year = year
        self.storyline = movie_storyline
        self.poster_image_url = poster_image
        self.trailer_youtube_url = trailer_youtube

    def show_trailer(self):
        webbrowser.open(self.trailer_youtube_url)
