import csv
import os
from mesh import Mesh
import numpy as np
from os.path import join
import trimesh

class Dataset:
    def __init__(self, folder_name_dataset, write_basic_csv=False, write_other_csv=False):
        self.folder_name_dataset = folder_name_dataset
        #self.meshes_file_paths = self.get_all_meshes_file_paths()
        #self.meshes = self.make_all_meshes()
        if write_basic_csv:
            self.write_basic_info_csv()
        if write_other_csv:
            self.write_bounding_box_csv()
            self.write_alignment_csv()


    def write_basic_info_csv(self):
        print("Writing basic csv info of {}".format(self.folder_name_dataset))
        with open(os.getcwd() + "/csv/" + self.folder_name_dataset + "_basic_mesh_info.csv", "w") as conn:
            writer = csv.writer(conn)
            writer.writerow(["mesh_name", "category", "n_vertices", "n_faces", "d_centroid_origin"])
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
            writer.writerow(["mesh name", "alignment_x", "alignment_y", "alignment_y"])
            for mesh in self.make_all_meshes():
                writer.writerow([mesh.name] + list(mesh.get_alignment()))


    def write_face_area_csv(self):
        print("Writing face area csv info of {}".format(self.folder_name_dataset))
        with open(os.getcwd() + "/csv/" + self.folder_name_dataset + "_face_area.csv", "w") as conn:
            writer = csv.writer(conn)
            writer.writerow(["face area"])
            for mesh in self.make_all_meshes():
                for face_area in mesh.get_face_areas():
                    writer.writerow([face_area])


    def get_face_areas_in_bins(self, bins):
        A = np.zeros(shape = len(bins)-1)
        for mesh in self.make_all_meshes():
            A += mesh.get_face_areas_in_bins(bins)
        return A / np.sum(A)


    def __iter__(self):
        #return self.meshes
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
                    if filename.endswith(".ply") or filename.endswith(".obj") or filename.endswith("off"):
                        file_path = shape_dir + folder + "/" + filename
                        yield file_path


    def get_mesh(self, mesh_name):
        for mesh in self.make_all_meshes:
            if mesh.name == mesh_name:
                return mesh
        raise Exception("This mesh was not found.")


    def show_mesh(self, mesh_name):
        found = False
        for mesh_file_path in self.get_all_meshes_file_paths():
            if mesh_file_path.split("/")[-1] == mesh_name:
                found = True
                Mesh(mesh_file_path).show()
        if not found:
            raise Exception("This mesh was not found.")


    def is_normalised(self):
        print("Checking if {} is normalized".format(self.folder_name_dataset))
        for mesh in self.make_all_meshes():
            if not mesh.is_normalised():
                return False
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

                # show_interims = False
                # if random.randint(0,100) == 0 and debug:
                #     show_interims = True
                #     mesh.show()

                print(mesh.name)

                print("Original centroid: " + str(mesh.centroid))
                # First, we set barycenter on origin.
                transformVector = -mesh.centroid
                transformMatrix = trimesh.transformations.translation_matrix(transformVector)
                mesh.apply_transform(transformMatrix)
                print("New centroid:      " + str(mesh.centroid))

                # Calculate covariance and eigenvectors...
                covariance = np.cov(np.transpose(mesh.get_vertices()))
                eigenvalues, eigenvectors = np.linalg.eig(covariance)

                idx = eigenvalues.argsort()[::-1]
                sorted_eigenvectors = eigenvectors[:,idx]
                sorted_eigenvectors[:, 2] = np.cross(sorted_eigenvectors[:, 0], sorted_eigenvectors[:, 1])
                sorted_eigenvectors = sorted_eigenvectors.T
                sorted_eigenvectors_homo = np.hstack([np.vstack([sorted_eigenvectors, np.array([0,0,0])]), np.array([[0],[0],[0],[1]])])
                mesh.apply_transform(sorted_eigenvectors_homo)

                mesh.normalize_scale()

                print("Bounding box after alignment and scaling:\n" + str(mesh.get_AABB()))

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
