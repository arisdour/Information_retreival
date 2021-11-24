import pandas as pd
from pandas import DataFrame
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Dense 
from keras.utils import to_categorical
from elasticsearch import Elasticsearch


from gensim.models.doc2vec import Doc2Vec, TaggedDocument



movies=pd.read_csv('movies.csv') #read csv file
es = Elasticsearch([{'host': 'localhost', 'port': 9200}]) #set server 


user_title = input("Enter Title: ")
# user_title="Pulp Fiction"
userId=int(input("Enter Id: "))
#userId =232

movies=pd.read_csv('movies.csv') #read csv file
ratings=pd.read_csv('ratings.csv') #read csv file
ratings=ratings.drop("timestamp" , axis=1)
title=movies["title"]

############################################################################### one hot encoding ########################

genres=movies["genres"]   #Κατηγορίες που ανήκει κάθε ταινία 


df=movies.drop(['movieId'] ,axis=1)  #κρατάω τις κατηγορίες για κάθε ταινία 

genre = df['genres'].str.split('|').tolist()  #χωρίζω τις κατηγορίες που ανήκει μία ταινία και μετά τις κάνω λίστα 

flat_genre = [item for sublist in genre for item in sublist]

set_genre = set(flat_genre)


unique_genre = list(set_genre)  #Βρίσκω τις διαφορετικές κατηγορίες σε λίστα



df = df.reindex(df.columns.tolist() + unique_genre, axis=1, fill_value=0) #Φτιάχνω ένα dF που σε κάθε ταινία  έχει 0 για όλες τις κατηγορίες

for index, row in df.iterrows():
    for val in row.genres.split('|'):
        if val != 'NA':
            df.loc[index, val] = 1   # Βάζω 1 όπου βρίσκω ότι ανήκει η ταινία 

df1=df.drop(['genres' ,'title'], axis = 1)  

################################################################################ doc2Vec ################################

title=title.str.split()
split_titles=title.values.tolist() # Μετατρέπω ολόκληρο τον τίτλο της ταινίας σε string

tagged_data = [TaggedDocument(d,[str(i)]) for i, d in enumerate(title)]  #λεξιλόγιο για το doc2vec model

model = Doc2Vec(tagged_data, vector_size=200, window=2, min_count=1, workers=4, epochs = 50) #φτιάχνω το μοντέλο 


titlesVectors = [model.docvecs[str(i)] for i in range(len(title))]# κάνω την κατηγοριοποίηση για τον κάθε τίτλο 
df=pd.DataFrame(titlesVectors) # Βάζω τις ταινίες σε df 
df=pd.concat([df, df1], axis=1)
df_movid=pd.concat([df, movies['movieId']], axis=1)  ##Τελικό διάνυσμα για κάθε ταινία 

# ########################################################################################################################

NNuser=ratings[ratings['userId'] == userId]  #Βρίσκω τις ταινίες που έχει βαθμολογίσει ο χρήστης 
NNuser=NNuser.join(df_movid.set_index('movieId'), on='movieId') #Κάνω join για να βρω τα vectors των ταινιών που έχει βαθμολογίσει
NNuser=NNuser.drop(["userId", "movieId" ] , axis=1)


y=NNuser.rating  #έξοδος νευρωνικού 
y=y.to_numpy()
y =pd.DataFrame(to_categorical(y , num_classes=6)) #Κανω 1 hot encoding σε κάθε κατηγορία ώστε να μπορώ να κάνω classification με το Νευρωνικό 


# ###################################### Create Sets #####################################################################
X=NNuser.drop('rating', axis=1)                                                 
X_train, X_test, y_train, y_test = train_test_split(X, y,test_size=0.25) #Δημιουργία training set και test set

# ################################### Neural Network #####################################################################

model=Sequential([
    Dense(units=700,input_shape=(220,),activation='relu'),
    Dense(units=500,activation='relu'),
    Dense(units=6,activation='softmax')
    ])
model.compile(optimizer="Adam",loss="categorical_crossentropy",metrics=['accuracy'] ,)  
history=model.fit(X_train, y_train, verbose=1, epochs=50) #training
######################################################### Evaluation ####################################################
# evaluate=model.evaluate(X_test, y_test)
# print("test loss, test acc:", evaluate)


#########################################################################################################################


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
average_score= average_score.groupby(['movieId'] , observed=True).mean(['rating'])  


for i in range(0, len(movie_id)):     
    movie_id[i] = float(movie_id[i])
    
for i in range(0, len(movie_score)): 
    movie_score[i] = float(movie_score[i])
    


def metric(userid, movid, score ,nnpred):
    try:
        avg=average_score.loc[movid][0]
        usr_rat=ratings.loc[(ratings.userId == userid) & (ratings.movieId== movid)]
        usr_rat=usr_rat[['rating'] ].astype(float)
        usr_rat=usr_rat.to_numpy()
        usr_rat=usr_rat[0][0]
        metric= 0.5*score +0.1*avg + 0.9* usr_rat
    except IndexError:
        usr_rat=nnpred
        avg=average_score.loc[movid][0]
        metric=0.5*score +0.1*avg + 0.9* usr_rat
        
    except KeyError:
        avg=0
        metric= 0.8*score
        
    return metric

My_score=[]
for i in range(len(movie_score)):
    a=movie_id[i]
    b=movie_score[i]
    predictionmovie=df_movid.loc[df_movid.movieId == a]# Κάνω predict μονο για τις ταινίες που έχει επιστρέψει η ElasticSearch
    predictionmovie=predictionmovie.reset_index(drop=True).drop(['movieId'], axis=1)
    yhat =pd.DataFrame(model.predict(predictionmovie))
    yhat1=yhat.idxmax(axis=1)  #### movie rating  που προέβλεψε το ΝΝ
    yhat1=yhat1[0]
    My_score.append(metric(userId,a,b,yhat1 ))




My_score=DataFrame(My_score,columns=['Custom Score'])
titles=DataFrame(titles,columns=['Title'])
My_score=pd.concat([My_score, titles], axis=1)
My_score = My_score.sort_values('Custom Score', ascending=False)
print(My_score)






