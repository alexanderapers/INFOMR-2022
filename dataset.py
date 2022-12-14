import csv
import os
from mesh import Mesh
import numpy as np
from os.path import join
import trimesh
from features_mesh import Features_Mesh
from shape_features_mesh import Shape_Features_Mesh
from tqdm import tqdm
import pandas as pd
from scipy import stats


class Dataset:
    def __init__(self, folder_name_dataset, write_basic_csv=False, write_other_csv=False):
        self.folder_name_dataset = folder_name_dataset
        self.exclude_list = ["m1693.ply"]
        #self.meshes_file_paths = self.get_all_meshes_file_paths()
        #self.meshes = self.make_all_meshes()
        if write_basic_csv:
            self.write_basic_info_csv()
        if write_other_csv:
            self.write_bounding_box_csv()
            self.write_alignment_csv()
            self.write_flipping_csv()


    def write_basic_info_csv(self):
        print("Writing basic csv info of {}".format(self.folder_name_dataset))
        with open(os.getcwd() + "/csv/" + self.folder_name_dataset + "_basic_mesh_info.csv", "w") as conn:
            writer = csv.writer(conn)
            writer.writerow(["mesh_name", "category", "n_vertices", "n_faces", "d_centroid_origin", "scale"])
            for mesh in self.make_all_meshes():
                writer.writerow(mesh.basic_mesh_info())


    def write_bounding_box_csv(self):
        print("Writing bounding box csv info of {}".format(self.folder_name_dataset))
        with open(os.getcwd() + "/csv/" + self.folder_name_dataset + "_bounding_box.csv", "w") as conn:
            writer = csv.writer(conn)
            writer.writerow(["mesh name"] + ["corner{0}{1}".format(i, j) for i in range(1,9) for j in ["x", "y", "z"]])
            for mesh in self.make_all_meshes():
                writer.writerow([mesh.name] + list(mesh.get_AABB().flatten()))


    def write_alignment_csv(self):
        print("Writing alignment csv info of {}".format(self.folder_name_dataset))
        with open(os.getcwd() + "/csv/" + self.folder_name_dataset + "_alignment.csv", "w") as conn:
            writer = csv.writer(conn)
            writer.writerow(["mesh name", "alignment_x", "alignment_y", "alignment_z"])
            for mesh in self.make_all_meshes():
                writer.writerow([mesh.name] + list(mesh.get_alignment()))


    def write_flipping_csv(self):
        print("Writing flipping csv info of {}".format(self.folder_name_dataset))
        with open(os.getcwd() + "/csv/" + self.folder_name_dataset + "_flipping.csv", "w") as conn:
            writer = csv.writer(conn)
            writer.writerow(["mesh name", "flip_x", "flip_y", "flip_z"])
            for mesh in self.make_all_meshes():
                writer.writerow([mesh.name] + list(mesh.get_flip()))


    def write_face_area_csv(self):
        print("Writing face area csv info of {}".format(self.folder_name_dataset))
        with open(os.getcwd() + "/csv/" + self.folder_name_dataset + "_face_area.csv", "w") as conn:
            writer = csv.writer(conn)
            writer.writerow(["face area"])
            for mesh in self.make_all_meshes():
                for face_area in mesh.get_face_areas():
                    writer.writerow([face_area])


    def write_elementary_features(self):
        print("Writing elementary features csv info of {}".format(self.folder_name_dataset))
        if not os.path.exists(join(os.getcwd(), "features")):
            os.mkdir("features")
        with open(os.getcwd() + "/features/" + self.folder_name_dataset + "_elementary_features.csv", "w") as conn:
            writer = csv.writer(conn)
            writer.writerow(["mesh name", "category", "area", "compactness", "AABB_volume", "diameter", "eccentricity"])
            for mesh in tqdm(self.make_all_meshes()):
                if mesh.name not in self.exclude_list:
                    writer.writerow(Features_Mesh(mesh).get_all_elementary_features())


    def write_shape_features(self):
        print("Writing shape features csv info of {}".format(self.folder_name_dataset))
        if not os.path.exists(join(os.getcwd(), "features")):
            os.mkdir("features")
        with open(os.getcwd() + "/features/" + self.folder_name_dataset + "_shape_features.csv", "w") as conn:
            for mesh in self:
                shape_features = Shape_Features_Mesh(mesh)
                break
            writer = csv.writer(conn)
            ft_names = [ft + "_" + str(i) for ft in ["A3", "D1", "D2", "D3", "D4"] for i in range(1, shape_features.n_bins + 1)]
            writer.writerow(["mesh name"] + ft_names)
            for mesh in tqdm(self):
                if mesh.name not in self.exclude_list:
                    writer.writerow(Shape_Features_Mesh(mesh).get_all_shape_features())


    def write_all_features_normalized(self):
        print("Writing all normalized features csv of {}".format(self.folder_name_dataset))
        if not os.path.exists(join(os.getcwd(), "features")):
            os.mkdir("features")
        all_features_file_path = os.getcwd() + "/features/" + self.folder_name_dataset + "_all_features_normalized.csv"
        elem_features_file_path = os.getcwd() + "/features/" + self.folder_name_dataset + "_elementary_features.csv"
        shape_features_file_path = os.getcwd() + "/features/" + self.folder_name_dataset + "_shape_features.csv"

        a = pd.read_csv(elem_features_file_path)
        b = pd.read_csv(shape_features_file_path)
        merged = a.merge(b, on='mesh name')
        merged.to_csv(all_features_file_path, index=False)

        # df = pd.read_csv(all_features_file_path)
        # old_order = list(df.columns)
        # ft_names = [ft + "_" + str(i) for ft in ["A3", "D1", "D2", "D3", "D4"] for i in range(1, 11)]
        # new_order = ["mesh name", "category", "area", "compactness", "AABB_volume", "diameter", "eccentricity"] + ft_names
        # df_reorder = df[new_order]
        # df_reorder.to_csv(all_features_file_path, index=False)
        self.normalize_features_csv()


    def normalize_features_csv(self):
        print("Normalizing...")
        all_features_file_path = os.getcwd() + "/features/" + self.folder_name_dataset + "_all_features_normalized.csv"
        features = pd.read_csv(all_features_file_path)
        info = np.zeros(shape=(5,2))
        info[0,0] = features['area'].mean()
        info[0,1] = features['area'].std()
        info[1,0] = features['compactness'].mean()
        info[1,1] = features['compactness'].std()
        info[2,0] = features['AABB_volume'].mean()
        info[2,1] = features['AABB_volume'].std()
        info[3,0] = features['diameter'].mean()
        info[3,1] = features['diameter'].std()
        info[4,0] = features['eccentricity'].mean()
        info[4,1] = features['eccentricity'].std()
        features['area'] = stats.zscore(features['area'])
        features['compactness'] = stats.zscore(features['compactness'])
        features['AABB_volume'] = stats.zscore(features['AABB_volume'])
        features['diameter'] = stats.zscore(features['diameter'])
        features['eccentricity'] = stats.zscore(features['eccentricity'])
        features.to_csv(all_features_file_path, index=False)
        np.save("norm_info", info)


    def get_face_areas_in_bins(self, bins):
        A = np.zeros(shape = len(bins)-1)
        for mesh in self.make_all_meshes():
            A += mesh.get_face_areas_in_bins(bins)
        return A / np.sum(A)


    def __iter__(self):
        return self.make_all_meshes()


    def __len__(self):
        return len(list(self.get_all_meshes_file_paths()))


    def to_list(self):
        return list(self.make_all_meshes())


    def make_all_meshes(self):
        """ Returns an iterator with all meshes """
        for mesh_file_path in self.get_all_meshes_file_paths():
            mesh = Mesh(mesh_file_path)
            yield mesh


    def get_all_meshes_file_paths(self):
        """ Returns an iterator with all the file paths to meshes in the Princeton folder """
        shape_dir = os.getcwd() + "/{}/".format(self.folder_name_dataset)
        for folder in os.listdir(shape_dir):
            if not folder.startswith(".") and not folder.endswith(".txt"):
                for filename in os.listdir(shape_dir + folder):
                    if filename.endswith(".ply") or filename.endswith(".obj") or filename.endswith(".off"):
                        file_path = shape_dir + folder + "/" + filename
                        yield file_path


    def get_mesh(self, mesh_name):
        for mesh in self.make_all_meshes():
            if mesh.name == mesh_name:
                return mesh
        raise Exception("This mesh was not found.")

    def get_mesh_file_path(self, mesh_name):
        for meshpath in self.get_all_meshes_file_paths():
            if meshpath.endswith(mesh_name) or meshpath.endswith(mesh_name + ".ply") or meshpath.endswith(mesh_name + ".obj") or meshpath.endswith(mesh_name + ".off"):
                return meshpath


    def show_mesh(self, mesh_name):
        found = False
        for mesh_file_path in self.get_all_meshes_file_paths():
            if mesh_file_path.split("/")[-1] == mesh_name:
                found = True
                Mesh(mesh_file_path).show()
        if not found:
            raise Exception("This mesh was not found.")


    def is_normalised(self):
        if not os.path.isfile("{}/yes_normalized.txt".format(self.folder_name_dataset)):
            for mesh in self.make_all_meshes():
                if not mesh.is_normalised():
                    return False
            with open("{}/yes_normalized.txt".format(self.folder_name_dataset), "w") as conn:
                conn.write("this has been normalized")
            return True
        return True


    def resample(self):
        if not os.path.isfile("{}/yes_remesh.txt".format(self.folder_name_dataset)):
            for mesh in self.make_all_meshes():
                mesh.subdivide_to_size()
                while mesh.n_vertices < 1000:
                    mesh.subdivide()
                mesh.decimation()

                print("Mesh remeshed! New # of vertices: " + str(mesh.n_vertices) + ", faces: " + str(mesh.n_faces))

                mesh.export(join(join(self.folder_name_dataset, mesh.category), mesh.name))

            self.write_basic_info_csv()
            self.write_bounding_box_csv()
            self.write_alignment_csv()
            with open("{}/yes_remesh.txt".format(self.folder_name_dataset), "w") as conn:
                conn.write("this has been remeshed")


    def normalize(self, debug=False):
        if not self.is_normalised():
            progress = 0
            for mesh in self.make_all_meshes():
                os.system('clear')
                os.system('cls')
                print("Progress: " + str(progress).rjust(5) + "/{} (".format(self.__len__()) + str(int(progress/self.__len__() * 100)).rjust(3) + "%)")
                progress += 1

                print(mesh.name)

                mesh.fix_mesh()

                print("Original centroid: " + str(mesh.centroid))
                mesh.normalize_translation()
                print("New centroid:      " + str(mesh.centroid))

                mesh.normalize_alignment()
                mesh.normalize_scale()
                mesh.normalize_flipping()

                print("Bounding box after alignment, scaling and flipping:\n" + str(mesh.get_AABB()))

                # if show_interims: #and USE_EIGENS:
                #     print("==> eigenvalues for (x, y, z)")
                #     print(eigenvalues)
                #     print("\n==> eigenvectors")
                #     print(eigenvectors)
                #     print("Order: " + str([newXindex, newYindex, newZindex]))
                #     print(ordered_eigenvectors)
                #     mesh.show()

                print("Exporting to " + join(join(self.folder_name_dataset, mesh.category), mesh.name))
                mesh.export(join(join(self.folder_name_dataset, mesh.category), mesh.name))

            self.write_basic_info_csv()
            self.write_bounding_box_csv()
            self.write_alignment_csv()
            self.write_flipping_csv()

    def save_thumbnails(self):
        progress = 0
        for mesh in self.make_all_meshes():
            if mesh.save_thumbnail():
                progress += 1
                print(progress, mesh.name)
