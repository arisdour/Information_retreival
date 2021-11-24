import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame
from sklearn.cluster import KMeans
from elasticsearch import Elasticsearch
import math
import random

random.seed(1047398)

movies=pd.read_csv('movies.csv') #read csv file
ratings=pd.read_csv('ratings.csv') #read csv file   



total = pd.merge(movies, ratings, on=['movieId'])
total = total.drop(['timestamp', 'movieId'], axis=1)
users_total=total
movies_total = total.drop(['userId'], axis=1)

b = DataFrame(total.genres.str.split('|')) #Περιλαμβάνει τις κατηγορίες κάθε ταινίας 
movies_total['genres']=b['genres']
movies_total=movies_total.explode('genres') #Καθε ταινία 


users_total['genres']=b['genres']
users_total=users_total.explode('genres') #Έχει τον τίτλο το userId και το Rating για κάθε ταινία

userscore_category =users_total.groupby(['userId' ,'genres']).mean(['rating']) # Περιέχει το average rating για κάθε κατηγορία που έχει βαθμολογίσει ο κάθε χρήστης 


c=pd.DataFrame(userscore_category.index)
c=c.rename(columns={0: "genres"}) #οι κατηγορίες που έχουν βαθμολογηθεί από τον κάθε χρήστη
userscore_category['genres']=c['genres'].values # γίνεται προσθηκή του c 
userscore_category[['userId','genres']] = pd.DataFrame(userscore_category.genres.tolist(), index= userscore_category.index)
userscore_category=userscore_category.reset_index(drop=True) # Εδω είναι το df που περιέχει τους χρήστες και τον μ.ο των βαθμολογιών ανά είδος 

userscore_category=userscore_category.pivot(index='userId', columns='genres', values='rating') #εδω φτιάχνεται το μητρώo στο οποίο θα εφαρμοστεί ο Kmeans μέσω pivot
kmeans_userscore=userscore_category.apply(lambda x: x.fillna(x.mean())) #αντικατάσταση κενών τιμών  με τον μ.ο. της genre 


# ########################## Elbow Method #######################################

distortions = []                                                             #Find Number of Clusters 
for i in range(1, 21):
    km = KMeans(n_clusters=i, init='random',n_init=10, max_iter=300,tol=1e-04, random_state=0)
    km.fit(kmeans_userscore)
    distortions.append(km.inertia_)


# plt.plot(range(1, 21), distortions, marker='o')
# plt.xlabel('Number of clusters')
# plt.ylabel('Distortion')
# plt.show()

# # ########################## Kmeans  ############################################

dataset_array = kmeans_userscore.values #Περιέχει τα data για τον Kmeans

kmeans = KMeans(n_clusters=8).fit(dataset_array)

labels=pd.DataFrame(kmeans.labels_)

userscore_category["Labels"]=labels # Προστείθενται τα Labels στον στο αρχικό DF 

es = Elasticsearch([{'host': 'localhost', 'port': 9200}]) 

# ################################## Erotima 1b #################################

user_title = input("Enter Title: ")
# user_title="Pulp Fiction"
userId=int(input("Enter Id: "))
# userId =456


res= es.search(index='movies',body={"query":{ "match": {"title": user_title  } },"sort": [ {"_score" : { "order":"desc" }} ]  }    , size=1000)
movie_id=[];
movie_score=[]
titles=[]
genres=[]
hits=res['hits']['total']['value']

for i in range(hits):
    movie_id.append(res['hits']['hits'][i]['_source']['movieId'])
    movie_score.append(res['hits']['hits'][i]['_score'])
    titles.append(res['hits']['hits'][i]['_source']['title'])
    genres.append(res['hits']['hits'][i]['_source']['genres'])
        

# ###############################################################################


ratings=pd.read_csv('ratings.csv') #read csv file    
average_score=ratings.drop(['userId','timestamp'],axis=1)
average_score= average_score.groupby(['movieId'] , observed=True).mean(['rating'])  #Εύρεση μέσου όρου για κάθε ταινία 



for i in range(0, len(movie_id)):     # Μετατροπή των δύο λιστών σε Float 
    movie_id[i] = float(movie_id[i])
    
for i in range(0, len(movie_score)): 
    movie_score[i] = float(movie_score[i])
  
#### Μ.Ο. για χρήστες που ανήκουν στο ίδο Cluster #############################

CLuster=userscore_category.iloc[userId-1]  #Βρίσκω το διάνυσμα του χρήστη με τον μέσο όρο για κάθε κατηγορία και το label

CLuster=CLuster.loc[['Labels']][0]   # Κρατάω την τιμή του label στο οποίο ανήκει ο χρήστης

df0 = userscore_category[userscore_category['Labels']== CLuster] #Βρίσκω όλους τους χρήστες του ίδιου Label / Cluster 

df0=df0.reset_index()

Cluster_users_average=df0['userId'].to_frame() # Κρατάω τα userId 

Cluster_users_average=Cluster_users_average.merge(ratings, how='left', on='userId') # Φτιάχνω ένα df με όλες τις ταινίες που έχει βαθμολογήσει ο χρήστης 




def metric(userid, movid, score ,clav):
    try:
        avg=average_score.loc[movid][0]
        usr_rat=ratings.loc[(ratings.userId == userid) & (ratings.movieId== movid)]
        usr_rat=usr_rat[['rating'] ].astype(float)
        usr_rat=usr_rat.to_numpy()
        usr_rat=usr_rat[0][0]
        metric= 0.5*score +0.1*avg + 0.9* usr_rat
    except IndexError:
        usr_rat=clav##genres.iloc[i]
        avg=average_score.loc[movid][0]
        metric=0.5*score +0.1*avg + 0.9* usr_rat #Εδω αν δεν την έχει βαθμολογήσει ο χρήστης βάζω τον μέσο όρο των υπόλοιπων χρηστών 
    except KeyError:
        avg=0        # Αν δεν την έχει βαθμολογήσει κανείς κρατάω το score
        metric= score  
        
    return metric

My_score=[]
for i in range(len(movie_score)):
    a=movie_id[i]    #μου δίνει το id ταινίας 
    b=movie_score[i]  #score ταινίας 
    cluster_average=Cluster_users_average[Cluster_users_average["movieId"] == a]
    cluster_average=cluster_average['rating'].mean(axis=0)  #εδώ βρίσκω τον μ.ο. της ταινίας για όλο το cluster 
    if(math.isnan(cluster_average) == True):
        cluster_average=0  #ελέγχω αν είναι nan και αν είναι το μηδενίζω 
    My_score.append(metric(userId,a,b,cluster_average))



My_score=DataFrame(My_score,columns=['Custom Score'])
titles=DataFrame(titles,columns=['Title'])
My_score=pd.concat([My_score, titles], axis=1)
My_score = My_score.sort_values('Custom Score', ascending=False)
print(My_score)
