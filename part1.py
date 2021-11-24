from elasticsearch import Elasticsearch
from elasticsearch import helpers
import pandas as pd
import csv



#################################Erotima 1a #################################
movies=pd.read_csv('movies.csv') #read csv file
es = Elasticsearch([{'host': 'localhost', 'port': 9200}]) #set server 

def csv_reader(file_name):
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    with open(file_name, 'r',encoding="utf8") as outfile:   #Διαβάζεται το αρχείο 
        reader = csv.DictReader(outfile)
        helpers.bulk(es, reader, index="movies", doc_type="type") #Αποθηκεύεται το αρχείο σε ένα index με όνομα movies 
    
# csv_reader('movies.csv') #ανεβάζω τα data 


#################################Erotima 1b #################################

user_title=input("Enter Title: ")
# user_title="Toy Story"
res= es.search(index='movies',body={"query":{ "match": {"title": user_title  } },"sort": [ {"_score" : { "order":"desc" }} ]  }    , size=1000)
hits=res['hits']['total']['value']

for i in range(hits):
    print(res['hits']['hits'][i]['_source']['title']) #τυπώνονται: Τίτλος και movie id 
    # print(res['hits']['hits'][i]['_source']['movieId']) #Τυπώνει το id 

