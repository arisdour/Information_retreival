from elasticsearch import Elasticsearch
import pandas as pd
from pandas import DataFrame


movies=pd.read_csv('movies.csv') #read csv file
es = Elasticsearch([{'host': 'localhost', 'port': 9200}]) #set server 

################################# Erotima 1b #################################

user_title = input("Enter Title: ")
# user_title="Toy Story"
userId=int(input("Enter Id: "))
# userId =1




res= es.search(index='movies',body={"query":{ "match": {"title": user_title  } },"sort": [ {"_score" : { "order":"desc" }} ]  }    , size=1000)
movie_id=[];
movie_score=[]
titles=[]
hits=res['hits']['total']['value']


for i in range(hits):
    movie_id.append(res['hits']['hits'][i]['_source']['movieId'])
    movie_score.append(res['hits']['hits'][i]['_score'])
    titles.append(res['hits']['hits'][i]['_source']['title'])
        


###############################################################################


ratings=pd.read_csv('ratings.csv') #read csv file    
average_score=ratings.drop(['userId','timestamp'],axis=1)
average_score= average_score.groupby(['movieId'] , observed=True).mean(['rating'])  #μ.ο. για κάθε ταινία 


for i in range(0, len(movie_id)):     ## Κάνω τις λίστες float 
    movie_id[i] = float(movie_id[i])
    
for i in range(0, len(movie_score)): 
    movie_score[i] = float(movie_score[i])
    


def metric(userid, movid, score ):
    try:
        avg=average_score.loc[movid][0]
        usr_rat=ratings.loc[(ratings.userId == userid) & (ratings.movieId== movid)]
        usr_rat=usr_rat[['rating'] ].astype(float)
        usr_rat=usr_rat.to_numpy()
        usr_rat=usr_rat[0][0]
        metric= 0.5*score +0.1*avg + 0.9* usr_rat  #Υπολογίζω μία δικία μου μετρική 
    except IndexError:
        usr_rat=0
        avg=average_score.loc[movid][0]
        metric=0.5*score +0.1*avg + 0.9* usr_rat ## Αν δεν την έχει βαθμλογήσει ο user --> κρατάω μόνο μ.ο. και score 
    except KeyError:
        avg=0              #ΑΝ δεν την έχει βαθολογήσει κανείς ---> μ.ο.=0 κρατάω μόνο score 
        metric= score
        
    return metric

My_score=[] #Τα αποθηκεύω σε μια λίστα 
for i in range(len(movie_score)):
    a=movie_id[i]
    b=movie_score[i]
    My_score.append(metric(userId,a,b))



My_score=DataFrame(My_score,columns=['Custom Score']) # Κάνω την λίστα df 
titles=DataFrame(titles,columns=['Title']) # Προσθέτω τίτλους
My_score=pd.concat([My_score, titles], axis=1)
My_score = My_score.sort_values('Custom Score', ascending=False) # Ταξινομό με descending custom score
print(My_score)
























