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
    ckey = "CKEY"
    csecret = "CSECRET"
    atoken = "ATOKEN"
    asecret = "ASECRET"

    # create instance of elasticsearch
    # es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

    host = 'AWS HOST_NAME'
    awsauth = AWS4Auth("AWS ACCESS KEY", "AWS SECRET KEY", 'us-west-2', 'es')


    es = elasticsearch.Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=elasticsearch.connection.RequestsHttpConnection
    )

    query = str(request.POST.get('myword'))

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
                    location = []
                    location.append(geocoder.google(dict_data['user']['location']).latlng[0])
                    location.append(geocoder.google(dict_data['user']['location']).latlng[1])
                    try:
                        es.index(index="sentiment",
                                 doc_type="test-type",
                                 id=self.i,
                                 body={"author": dict_data["user"]["screen_name"],
                                       "date": dict_data["created_at"],
                                       "location": dict_data["user"]["location"],
                                       "lat": geocoder.google(dict_data['user']['location']).latlng[0],
                                       "lng": geocoder.google(dict_data['user']['location']).latlng[1],
                                       "message": dict_data["text"]
                                       })

                        # print(es.get(index='sentiment', doc_type='test-type', id=self.i))

                        self.i += 1

                    except:
                        pass
                    return True
            else:
                return False

        # on failure
        def on_error(self, status):
            print("error")

        def on_timeout(self):
            print("Timeout")


    # create instance of the tweepy tweet stream listener
    listener = TweetStreamListener()

    # set twitter keys/tokens
    auth = OAuthHandler(ckey, csecret)
    auth.set_access_token(atoken, asecret)

    # create instance of the tweepy stream
    stream = Stream(auth, listener,timeout=10)

    try:
        stream.filter(track=[query])
    except:
        print(listener.i)


    pass_list = {}

    pass_list.setdefault('tweet', [])


    for j in range(listener.i):
        a = es.get(index='sentiment', doc_type='test-type', id=j)
        pass_list['tweet'].append(a)

    #Another way to retreive static pre-stored tweets, but we will not use non-realtime tweets hence, will just print them.

    res = es.search(index="sentiment", doc_type="test-type", body={"query": {"match": {"message": "trump"}}})
    print("%d documents found" % res['hits']['total'])
    for doc in res['hits']['hits']:
        print("%s) %s" % (doc['_id'], doc['_source']['message']))












    pass_list_final = json.dumps(pass_list)



    return render(request,"index.html",{"my_data":pass_list_final})
