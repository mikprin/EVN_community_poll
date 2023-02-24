import random
import os, sys

import numpy as np
from scipy.spatial.distance import hamming
from sklearn.cluster import KMeans

def calculate_distances(p1,p2):
    '''Calculate distance between two lists
    using hamming distance and penalties
    '''

    # For now penalize each element
    # Example of penalties:
    # [1, 0.5, 0.333, 0.25, 0.2]
    # Each element is 1/(index+1)
    penalties = [1/(x+1) for x in range(len(p1))]

    # If we don't want to penalize:
    # penalties = [1 for x in range(len(p1))]

    # Calculate hamming distance for each element
    distances = []
    for i in range(len(p1)):
        if not i == 0:
            # print(f"Hamming: {p1[0:i]} {p2[0:i]}")
            distances.append(hamming(p1[0:i], p2[0:i]))

    # Find resulting distance as sum of all distances
    distance = 0
    for i in range(len(distances)):
        distance += distances[i] * penalties[i]
    return distance




def calculate_distance_vector_list(p1, p_list):
    '''Calculate distance between a list and a vector'''
    distances = []
    for p2 in p_list:
        distances.append(calculate_distances(p1, p2))
    # Average distance
    distance = sum(distances) / len(distances)
    return distance

def get_vectors_from_users(users_subset):
    vectors = []
    for user in users_subset:
        vectors.append(users[user])
    return vectors

def cluster_vectors(vectors, clusters):
    
    # Define number of clusters
    M = clusters

    # Define k-means model
    kmeans = KMeans(n_clusters=M)

    # Define function for calculating distance between vectors
    def distance(x, y):
        return np.linalg.norm(x - y)

    # Define function to compute distance matrix
    def distance_matrix(vectors):
        n = len(vectors)
        D = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                d = calculate_distances(vectors[i], vectors[j])
                D[i][j] = d
                D[j][i] = d
        return D

    # Compute distance matrix
    D = distance_matrix(vectors)

    # Fit k-means model to distance matrix
    kmeans.fit(D)

    # Get cluster assignments
    cluster_assignments = kmeans.labels_
    return cluster_assignments


def cluster_users(users, clusters):
    '''Cluster with k-means. Output is a dictionary:
    user: cluster'''
    vectors = list(users.values())
    cluster_assignments = cluster_vectors(vectors, clusters)
    i = 0
    clustered_users = {}
    for user in users:
        clustered_users[user] = cluster_assignments[i]
        # print(f"{user} {cluster_assignments[i]}")
        i += 1
    return clustered_users

def create_user_clusters(users, clusters):
    '''Cluster with k-means. Output is a dictionary:
    cluster: [users]'''
    clustered_users = cluster_users(users, clusters)
    user_clusters = {}
    for user in clustered_users:
        if not clustered_users[user] in user_clusters:
            user_clusters[clustered_users[user]] = []
        user_clusters[clustered_users[user]].append(user)
    return user_clusters

def print_clusters(vectors, cluster_assignments, print_flag=True):
    # Print clusters and return string
    s = ""
    for i in range(max(cluster_assignments)+1):
        s += f"Cluster {i}:"
        if print_flag:
            print(f"Cluster {i}:")
    for j in range(len(vectors)):
        if cluster_assignments[j] == i:
            s += f"  {vectors[j]}"
            if print_flag:
                print(f"  {vectors[j]}")
            