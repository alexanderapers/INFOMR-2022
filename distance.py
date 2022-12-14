import time
import csv
import numpy as np
#from numba import njit
from mesh import Mesh
from features_mesh import Features_Mesh
from shape_features_mesh import Shape_Features_Mesh
from scipy.stats import wasserstein_distance
from scipy.special import rel_entr


class Distance:
    def __init__(self, dataset_name, exclude_list):
        self.csv = "features/" + dataset_name + "_all_features_normalized.csv"
        self.features = self.csv_to_dict()
        self.exclude_list = exclude_list
        self.norm_info = np.load("norm_info.npy")
        self.n_bins = int((len(self.features["m1.ply"]) - 5) / 5)

        # edit this to tweak weights
        #self.area, self.compactness, self.AABB_volume, self.diameter, self.eccentricity
        elem_weights = np.array([10, 0, 0, 10, 10])
        a3_weights = np.repeat(5, self.n_bins)
        d1_weights = np.repeat(1, self.n_bins)
        d2_weights = np.repeat(3, self.n_bins)
        d3_weights = np.repeat(3, self.n_bins)
        d4_weights = np.repeat(3, self.n_bins)

        self.weights = self.normalize_weights(elem_weights, a3_weights, d1_weights, d2_weights, d3_weights, d4_weights)

        #print(self.features["m518.ply"])
        #print(self.features["m514.ply"])
        #print("euclidean:", self.distance("m518.ply", "m514.ply", self.euclidean))
        #print("EMD:", self.distance("m518.ply", "m514.ply", self.euclidean_EMD))
        #print("KL:", self.distance("m518.ply", "m514.ply", self.euclidean_KL))

        # print("weight: area", self.weights[0])
        # print("weight: compactness", self.weights[1])
        # print("weight: AABB_volume", self.weights[2])
        # print("weight: diameter", self.weights[3])
        # print("weight: eccentricity", self.weights[4])
        # print("weight: A3", sum(self.weights[5:35]))
        # print("weight: D1", sum(self.weights[35:65]))
        # print("weight: D2", sum(self.weights[65:95]))
        # print("weight: D3", sum(self.weights[95:125]))
        # print("weight: D4", sum(self.weights[125:155]))

        # compiling numba
        #self.manhatten(np.array([1.0]), np.array([1.0]))
        #self.euclidean(np.array([1.0]), np.array([1.0]))
        #self.cosine(np.array([1.0]), np.array([1.0]))

        # print this to see result of query
        #result = self.query("LabeledDB_new/Octopus/121.off", self.euclidean_EMD, k=10)
        #print(result)

        # for r, d in result:
        #     print(r, d)

    # Helper function so that weights don't need to add up to 1 at the input level
    def normalize_weights(*weight):
        all = np.concatenate(weight[1:])
        totalweight = np.sum(all)
        all = all / totalweight
        return all


    def query(self, mesh_file_path, metric, k=10):
        #start_time = time.perf_counter()
        query_mesh = self.meshify(mesh_file_path)
        query_features = self.extract_features_mesh(query_mesh)
        result = self.find_k_most_similar(query_features, metric, k)
        #print("--- % seconds ---" % (time.perf_counter() - start_time))
        return result


    def query_inside_db(self, mesh_file_path, metric, k=10):
        result = self.find_k_most_similar(self.features[mesh_file_path.split("/")[-1]], metric, k)
        return result
        

    def csv_to_dict(self):
        with open(self.csv, 'r') as read_obj:
            features_dict = dict()
            csv_reader = csv.reader(read_obj)
            next(csv_reader)
            for row in csv_reader:
                mesh_name = row[0]
                mesh_features = np.array(row[2:]).astype(float)
                features_dict[mesh_name] = mesh_features
            return features_dict


    def distance(self, mesh_name_1, mesh_name_2, metric):
        a = self.weights * self.features[mesh_name_1]
        b = self.weights * self.features[mesh_name_2]
        return metric(a, b)


    def meshify(self, query_mesh_file_path):
        mesh = Mesh(query_mesh_file_path)
        mesh.resample_mesh()
        mesh.normalize_mesh()
        mesh.save_thumbnail()
        return mesh


    def extract_features_mesh(self, query_mesh):
        elem_features = Features_Mesh(query_mesh).get_all_elementary_features()
        shape_features = Shape_Features_Mesh(query_mesh).get_all_shape_features()
        elem_features[2:] = (elem_features[2:] - self.norm_info[:, 0]) / self.norm_info[:, 1]
        return np.array(elem_features[2:] + shape_features[1:])


    def find_k_most_similar(self, query_features, metric, k=10):
        distances = {x: 0 for x in self.features}
        for mesh_name in self.features:
            distances[mesh_name] = metric(self.weights * query_features, self.weights * self.features[mesh_name])
        return sorted(distances.items(), key=lambda item: item[1])[:k]


    @staticmethod
    #@njit()
    def euclidean(mesh_features_1, mesh_features_2):
        return np.linalg.norm(mesh_features_1 - mesh_features_2)


    @staticmethod
    #@njit()
    def manhatten(mesh_features_1, mesh_features_2):
        return np.sum(np.abs(mesh_features_1 - mesh_features_2))


    @staticmethod
    #@njit()
    def cosine(mesh_features_1, mesh_features_2):
        norm_1 = np.linalg.norm(mesh_features_1)
        norm_2 = np.linalg.norm(mesh_features_2)
        return 1 - (np.dot(mesh_features_1, mesh_features_2) / (norm_1 * norm_2))


    #@staticmethod
    #@njit()
    def euclidean_EMD(self, mesh_features_1, mesh_features_2):
        distances = np.zeros(6)
        elem_distance = Distance.euclidean(mesh_features_1[:5], mesh_features_2[:5])
        distances[0] = elem_distance
        # print("elem distance", elem_distance)
        j = 1
        for i in range(5, 5*self.n_bins + 5, self.n_bins):
            hist_distance = wasserstein_distance(np.arange(self.n_bins), np.arange(self.n_bins),
                mesh_features_1[i:i+self.n_bins], mesh_features_2[i:i+self.n_bins])
            distances[j] = hist_distance / self.n_bins
            #print("hist distance:", distances[j], j)
            j += 1
        return np.mean(distances)


    #@staticmethod
    #njit()
    # KL divergence is kinda broken since it cannot deal with 0 values
    def euclidean_KL(self, mesh_features_1, mesh_features_2):
        distances = np.zeros(6)
        elem_distance = Distance.euclidean(mesh_features_1[:5], mesh_features_2[:5])
        distances[0] = elem_distance
        j = 1
        for i in range(5, 5*self.n_bins + 5, self.n_bins):
            hist_distance = Distance.symm_KL(mesh_features_1[i:i+self.n_bins], mesh_features_2[i:i+self.n_bins])
            distances[j] = hist_distance
            j += 1
        return np.mean(distances)


    @staticmethod
    #njit()
    def symm_KL(mesh_features_1, mesh_features_2):
        return np.sum(rel_entr(mesh_features_1, mesh_features_2) + rel_entr(mesh_features_2, mesh_features_1))


    def mahalanobis(self, mesh_features_1, mesh_features_2):
        if not hasattr(self, 'inv_covariance'):
            all_vectors = []
            for mesh_name in self.features:
                all_vectors.append(self.features[mesh_name])

            cov = np.cov(np.stack(all_vectors).T)
            self.inv_covariance = np.linalg.pinv(cov)

        diff = mesh_features_1 - mesh_features_2
        return (diff @ self.inv_covariance @ diff) ** 0.5
