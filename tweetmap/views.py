from django.shortcuts import render
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import time
import json
from elasticsearch import Elasticsearch
from requests_aws4auth import AWS4Auth
import elasticsearch
import time
import geocoder
from django.views.decorators.csrf import csrf_protect

# Create your views here.



def index(request):

    return render(request,"home.html",{})


@csrf_protect
def home(request):
    # import twitter keys and tokens
    ckey = "lRpnCx9V3uT1k5haiOjgsMymg"
    csecret = "GAVMJfzMf7lKcR3sUg70qDIdeccjyGJ5giFEUGdLBq3YtvKHt4"
    atoken = "99720772-TiTD2K9Rv19Bid8Xm8My34GACinStkURjbMifzEEA"
    asecret = "FBk6JORnaJ9vNnudanqg6fMAjktEK4UNbwKKQO6BVTSbl"

    # create instance of elasticsearch
    # es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

    host = 'search-crtweetmap-ao63kddlivnkgfyddm3ggrosg4.us-west-2.es.amazonaws.com'
    awsauth = AWS4Auth("AKIAIUE3INCBISG7S3NA", "ePipkepslQuHbUKaIPw0gLFo+yLId70OFpMxq4DR", 'us-west-2', 'es')

    es = elasticsearch.Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=elasticsearch.connection.RequestsHttpConnection
    )

    class TweetStreamListener(StreamListener):
        i = 0

        def __init__(self, time_limit=10):
            self.start_time = time.time()
            self.limit = time_limit

        # on success
        def on_data(self, data):

            # decode json
            dict_data = json.loads(data)



            if (time.time() - self.start_time) < self.limit:
                if 'user' in dict_data and dict_data['user']['location']:
                    try:
                        es.index(index="sentiment",
                                 doc_type="test-type",
                                 id=self.i,
                                 body={"author": dict_data["user"]["screen_name"],
                                       "date": dict_data["created_at"],
                                       "location": dict_data['user']['location'],
                                       "lat": geocoder.google(dict_data['user']['location']).latlng[0],
                                       "lng": geocoder.google(dict_data['user']['location']).latlng[1],
                                       "message": dict_data["text"]
                                       })

                        print(es.get(index='sentiment', doc_type='test-type', id=self.i))

                        self.i += 1

                    except:
                        pass
                    return True
            else:
                return False

        # on failure
        def on_error(self, status):
            print(status)


    # create instance of the tweepy tweet stream listener
    listener = TweetStreamListener()

    # set twitter keys/tokens
    auth = OAuthHandler(ckey, csecret)
    auth.set_access_token(atoken, asecret)

    # create instance of the tweepy stream
    stream = Stream(auth, listener)



    query = str(request.POST.get('myword'))

    stream.filter(track=[query])

    pass_list = {}

    pass_list.setdefault('tweet', [])


    for j in range(listener.i):
        a = es.get(index='sentiment', doc_type='test-type', id=j)

        pass_list['tweet'].append(a)







    pass_list_final = json.dumps(pass_list)



    return render(request,"index.html",{"my_data":pass_list_final})
