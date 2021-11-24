# info_retreival
This repo contains a simple information retrieval project that uses Python and the Elastic Search API 

*** Description ****

The goal of this project is to develop a search engine for movies that is based ElasticSearch. The search engine is going to present the results of the search using Machine Learning  Techniques. 

*** Required Libraries ***

- Elasticsearch : conda install -c conda-forge elasticsearch
- Pandas : conda install pandas
- Sci-kit Learn : conda install -c intel scikit-learn
- Gensim : conda install -c anaconda gensim
- Keras : conda install -c anaconda keras-gpu
- Matplotlib : conda install matplotlib

** Part 1 ** 

The code in Part1.py (Erotima 1a) file is used to connect to the Elasticsearch API and upload the movies.csv to  the database. Then a small script is added (Erotima 1b) where the user is asked to enter a movie title. The results are then presented using Elasticsearch's BM25 metric.

** Part 2 ** 

In Part2.py the code of Part1.py is modified in order to present the results using a custom metric. The metric takes into consideration the rating that the user has given to the movie (all user ratings are included in the ratings.csv file) , the average rating of the movie and Elasticsearch's BM25 metric.

** Part 3 ** 

Taking into consideration the fact that the users only rate a small amount of movies , in Part3.py the code that is developed , uses K-Means clustering  to group  users  into clusters according to  the way they rate movies.

**Part 4 ** 

In Part4.py  a Neural Network is trained in order to predict the missing ratings of each user. The model is trained on the  ratings.csv file . The ratings are converted using word embeddings and one-hot encoding in order to be fed in the Neural Network for training.
