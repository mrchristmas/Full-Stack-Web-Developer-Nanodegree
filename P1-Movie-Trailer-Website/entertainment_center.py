import media
import fresh_tomatoes

# Create instances of Movie class and store as a list

movies = [
    media.Movie("Goodfellas",
                "1990",
                "Henry Hill and his friends work their way up through the mob "
                "hierarchy.",
                "https://upload.wikimedia.org/wikipedia/en/7/7b/"
                "Goodfellas.jpg",
                "https://www.youtube.com/watch?v=qo5jJpHtI1Y"),

    media.Movie("The Usual Suspects",
                "1995",
                "A sole survivor tells of the twisty events "
                "leading up to a horrific gun battle on a "
                "boat, which begin when five criminals meet "
                "at a seemingly random police lineup.",
                "https://upload.wikimedia.org/wikipedia/en/9/"
                "9c/Usual_suspects_ver1.jpg",
                "https://www.youtube.com/watch?v=oiXdPolca5w"),

    media.Movie("Django Unchained",
                "2012",
                "With the help of a German bounty hunter, a"
                " freed slave sets out to rescue his wife "
                "from a brutal Mississippi plantation owner.",
                "https://upload.wikimedia.org/wikipedia/en/"
                "8/8b/Django_Unchained_Poster.jpg",
                "https://www.youtube.com/watch?v=eUdM9vrCbow"),

    media.Movie("Reservoir Dogs",
                "1992",
                "After a simple jewelery heist goes terribly "
                "wrong, the surviving criminals begin to "
                "suspect that one of them is a police informant.",
                "https://upload.wikimedia.org/wikipedia/en/f/"
                "f6/Reservoir_dogs_ver1.jpg",
                "https://www.youtube.com/watch?v=GLPJSmUHZvU"),

    media.Movie("Home Alone",
                "1990",
                "An 8-year old troublemaker must protect his home"
                " from a pair of burglars when he is accidentally"
                " left home alone by his family during Christmas vacation.",
                "https://upload.wikimedia.org/wikipedia/en/4/47/"
                "Home_alone.jpg",
                "https://www.youtube.com/watch?v=CK2Btk6Ybm0"),

    media.Movie("Dazed and Confused",
                "1993",
                "The adventures of incoming high school and junior high "
                "students on the last day of school, in May of 1976.",
                "https://upload.wikimedia.org/wikipedia/en/9/"
                "9a/DazedConfused.jpg",
                "https://www.youtube.com/watch?v=3aQuvPlcB-8"),

    media.Movie("Toy Story",
                "1995",
                "A story of a boy and his toys that come to life.",
                "https://upload.wikimedia.org/wikipedia/en/1/13/"
                "Toy_Story.jpg",
                "https://www.youtube.com/watch?v=KYz2wyBy3kc"),

    media.Movie("Heavyweights",
                "1995",
                "Plump kids are lured into joining a posh fat "
                "camp with the promise of quick weight loss and"
                " good times, only to find that the facility is"
                " a woodland hellhole run by a psycho "
                "ex-fitness instructor.",
                "https://upload.wikimedia.org/wikipedia/en/b/"
                "b0/Heavyweights-theatrical.jpg",
                "https://www.youtube.com/watch?v=uD4GclR6ZEo"),

    media.Movie("Superbad",
                "2007",
                "Two co-dependent high school seniors are forced to"
                " deal with separation anxiety after their plan to"
                " stage a booze-soaked party goes awry.",
                "https://upload.wikimedia.org/wikipedia/en/8/8b/"
                "Superbad_Poster.png",
                "https://www.youtube.com/watch?v=MNpoTxeydiY")
]

# Generate movies web page and open in browser
fresh_tomatoes.open_movies_page(movies)
