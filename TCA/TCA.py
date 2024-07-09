import pandas as pd
import plotly.graph_objects as go
from scipy.cluster.hierarchy import  dendrogram,linkage,cut_tree
from scipy.cluster import hierarchy
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist
import numpy as np
import seaborn as sns


##########



class TCA:

    def __init__(self, data, state_mapping, colors='viridis'):
        self.data = data
        self.state_label = list(state_mapping.keys())
        self.state_numeric = list(state_mapping.values())
        self.colors = colors
        
        if len(self.colors) != len(self.state_label):
            raise ValueError("The number of colors must match the number of states")

    def plot_treatment_percentages(self, df):
        """
        Plot the percentage of patients under each state over time.

        Parameters:
        df (pd.DataFrame): DataFrame (format STS) containing the treatment data.

        Returns:
        None
        """
        fig = go.Figure()
        
        for treatment, treatment_label, color in zip(self.state_numeric, self.state_label, self.colors):
            treatment_data = df[df.eq(treatment).any(axis=1)]
            months = treatment_data.columns
            percentages = (treatment_data.apply(lambda x: x.value_counts().get(treatment, 0)) / len(treatment_data)) * 100
            fig.add_trace(go.Scatter(x=months, y=percentages, mode='lines', name=treatment_label, line=dict(color=color)))

        fig.update_layout(
            title='Percentage of Patients under Each State Over Time',
            xaxis_title='Time',
            yaxis_title='Percentage of Patients',
            legend_title='State',
            yaxis=dict(tickformat=".2f")
        )

        fig.show()

    def calculate_distance_matrix(self, metric='hamming'):
        """
        Calculate the distance matrix for the treatment sequences.

        Parameters:
        metric (str): The distance metric to use. Default is 'hamming'.

        Returns:
        distance_matrix (numpy.ndarray): A condensed distance matrix containing the pairwise distances between treatment sequences.
        """
        distance_matrix = pdist(self.data, metric)
        return distance_matrix
    
    def cluster(self, distance_matrix, method='ward', optimal_ordering=True):
        """
        Perform hierarchical clustering on the distance matrix.

        Parameters:
        distance_matrix (numpy.ndarray): A condensed distance matrix containing the pairwise distances between treatment sequences.
        method (str): The linkage algorithm to use. Default is 'ward'.
        optimal_ordering (bool): If True, the linkage matrix will be reordered so that the distance between successive leaves is minimal.

        Returns:
        linkage_matrix (numpy.ndarray): The linkage matrix containing the hierarchical clustering information.
        """
        linkage_matrix = linkage(distance_matrix, method=method, optimal_ordering=optimal_ordering)
        return linkage_matrix

    def plot_dendrogram(self, linkage_matrix):
        """
        Plot a dendrogram based on the hierarchical clustering of treatment sequences.

        Parameters:
        linkage_matrix (numpy.ndarray): The linkage matrix containing the hierarchical clustering information.

        Returns:
        None
        """
        plt.figure(figsize=(10, 6))
        dendrogram(linkage_matrix)
        plt.title('Dendrogram of Treatment Sequences')
        plt.xlabel('Patients')
        plt.ylabel('Distance')
        plt.show()

    def plot_clustermap(self, linkage_matrix):
        """
        Plot a clustermap of the treatment sequences with a custom legend.

        Parameters:
        linkage_matrix (numpy.ndarray): The linkage matrix containing the hierarchical clustering information.

        Returns:
        None
        """
        plt.figure(figsize=(8, 8))
        sns.clustermap(self.data,
                       cmap=self.colors,
                       metric='hamming',
                       method='ward',
                       row_linkage=linkage_matrix,
                       row_cluster=False,
                    #    row_colors=self.data.cluster,
                       col_cluster=False,
                       cbar_pos=None)
        
        # handles = [plt.Rectangle((0, 0), 1, 1, color=self.colors[i], label=self.state_label[i]) for i in range(len(self.state_label))]
        # plt.legend(handles=handles, labels=self.state_label, loc='center', bbox_to_anchor=(0.5, -0.2), ncol=len(self.state_label) // 2)
        
        plt.xlabel("Time")
        plt.ylabel("Patients")
        plt.title("Trajectory of Temporal Vectors")
        plt.show()

    def plot_inertia(self, linkage_matrix):
        """
        Plot the inertia diagram to help determine the optimal number of clusters.

        Parameters:
        linkage_matrix (numpy.ndarray): The linkage matrix containing the hierarchical clustering information.

        Returns:
        None
        """
        last = linkage_matrix[-10:, 2]
        last_rev = last[::-1]
        idxs = np.arange(2, len(last) + 2)

        plt.figure(figsize=(10, 6))
        plt.step(idxs, last_rev, c="black")
        plt.xlabel("Number of clusters")
        plt.ylabel("Inertia")
        plt.title("Inertia Diagram")
        plt.show()

    def assign_clusters(self, linkage_matrix, num_clusters):
        """
        Assign patients to clusters based on the dendrogram.

        Parameters:
        linkage_matrix (numpy.ndarray): The linkage matrix containing the hierarchical clustering information.
        num_clusters (int): The number of clusters to form.

        Returns:
        numpy.ndarray: An array of cluster labels assigned to each patient.
        """
        clusters = cut_tree(linkage_matrix, n_clusters=num_clusters) + 1
        return clusters.flatten()
    
    def plot_cluster_heatmaps(self, clusters, sorted=True):
        """
        Plot heatmaps for each cluster.

        Parameters:
        df (pd.DataFrame): The DataFrame containing the treatment data.
        clusters (numpy.ndarray): The cluster assignments for each patient.
        num_clusters (int): The number of clusters.
        sorted (bool): Whether to sort the data within each cluster. Default is True.

        Returns:
        None
        """
        num_clusters = len(np.unique(clusters))
        cluster_data = {}
        for cluster_label in range(1, num_clusters + 1):
            cluster_indices = np.where(clusters == cluster_label)[0]
            cluster_df = self.data.iloc[cluster_indices]
            if sorted:
                cluster_df = cluster_df.sort_values(by=cluster_df.columns.tolist())
            cluster_data[cluster_label] = cluster_df

        num_rows = (num_clusters + 1) // 2
        num_cols = min(2, num_clusters)
        fig, axs = plt.subplots(num_rows, num_cols, figsize=(15, 10))
        if num_clusters == 2:
            axs = np.array([axs])

        for i, (cluster_label, cluster_df) in enumerate(cluster_data.items()):
            row = i // num_cols
            col = i % num_cols
            sns.heatmap(cluster_df, cmap=self.colors, cbar=False, ax=axs[row, col])
            axs[row, col].set_title(f'Heatmap du cluster {cluster_label}')
            axs[row, col].set_xlabel('Time')
            axs[row, col].set_ylabel('Patients')

        if num_clusters % 2 != 0:
            fig.delaxes(axs[-1, -1])

        handles = [plt.Rectangle((0, 0), 1, 1, color=self.colors[i], label=self.state_label[i]) for i in range(len(self.state_label))]
        plt.legend(handles=handles, labels=self.state_label, loc='center', bbox_to_anchor=(-0.1, -0.6), ncol=len(self.state_label) // 2)

        plt.tight_layout()
        plt.show()

    def plot_cluster_treatment_percentage(self, clusters):
        """
        Plot the percentage of patients under each treatment over time for each cluster.

        Parameters:
        clusters (numpy.ndarray): The cluster assignments for each patient.

        Returns:
        None
        """
        num_clusters = len(np.unique(clusters))
        colors = self.colors
        events_value = self.state_numeric
        events_keys = self.state_label
        num_rows = (num_clusters + 1) // 2
        num_cols = min(2, num_clusters)

        fig, axs = plt.subplots(num_rows, num_cols, figsize=(15, 10))
        if num_clusters == 2:
            axs = np.array([axs])
        if num_clusters % 2 != 0:
            fig.delaxes(axs[-1, -1])

        for cluster_label in range(1, num_clusters + 1):
            cluster_indices = np.where(clusters == cluster_label)[0]
            cluster_data = self.data.iloc[cluster_indices]

            row = (cluster_label - 1) // num_cols
            col = (cluster_label - 1) % num_cols

            ax = axs[row, col]

            for treatment, treatment_label, color in zip(events_value, events_keys, colors):
                treatment_data = cluster_data[cluster_data.eq(treatment).any(axis=1)]
                months = treatment_data.columns
                percentages = (treatment_data.apply(lambda x: x.value_counts().get(treatment, 0)) / len(treatment_data)) * 100
                ax.plot(months, percentages, label=f'{treatment_label}', color=color)
            
            ax.set_title(f'Cluster {cluster_label}')
            ax.set_xlabel('Time')
            ax.set_ylabel('Percentage of Patients')
            ax.legend(title='State')
        
        plt.tight_layout()
        plt.show()
    
    def bar_cluster_treatment_percentage(self, clusters):
        """
        Plot the percentage of patients under each treatment over time for each cluster using bar charts.

        Parameters:
        df (pd.DataFrame): The DataFrame containing the treatment data.
        clusters (numpy.ndarray): The cluster assignments for each patient.
        num_clusters (int): The number of clusters. Default is 4.

        Returns:
        None
        """
        num_clusters = len(np.unique(clusters))
        num_rows = (num_clusters + 1) // 2  
        num_cols = min(2, num_clusters)
        fig, axs = plt.subplots(num_rows, num_cols, figsize=(15, 10))
        if num_clusters == 2:
            axs = np.array([axs])
        if num_clusters % 2 != 0:
            fig.delaxes(axs[-1, -1])

        for cluster_label in range(1, num_clusters + 1):
            cluster_indices = np.where(clusters == cluster_label)[0]
            cluster_data = self.data.iloc[cluster_indices]

            row = (cluster_label - 1) // num_cols
            col = (cluster_label - 1) % num_cols

            ax = axs[row, col]

            for treatment, treatment_label, color in zip(self.state_numeric, self.state_label, self.colors):
                treatment_data = cluster_data[cluster_data.eq(treatment).any(axis=1)]
                months = treatment_data.columns
                percentages = (treatment_data.apply(lambda x: x.value_counts().get(treatment, 0)) / len(treatment_data)) * 100
                ax.bar(months, percentages, label=f'{treatment_label}', color=color)

            ax.set_title(f'Cluster {cluster_label}')
            ax.set_xlabel('Time')
            ax.set_ylabel('Percentage of Patients')
            ax.legend(title='State')

        plt.tight_layout()
        plt.show()

    def plot_stacked_bar(self, clusters):
        """
        Plot stacked bar charts showing the percentage of patients under each treatment over time for each cluster.

        Parameters:
        clusters (numpy.ndarray): The cluster assignments for each patient.

        Returns:
        None
        """
        num_clusters = len(np.unique(clusters))
        num_rows = (num_clusters + 1) // 2  
        num_cols = min(2, num_clusters)
        fig, axs = plt.subplots(num_rows, num_cols, figsize=(15, 10))
        if num_clusters == 2:
            axs = np.array([axs])
        if num_clusters % 2 != 0:
            fig.delaxes(axs[-1, -1])

        for cluster_label in range(1, num_clusters + 1):
            cluster_indices = np.where(clusters == cluster_label)[0]
            cluster_data = self.data.iloc[cluster_indices]
            
            row = (cluster_label - 1) // num_cols
            col = (cluster_label - 1) % num_cols
            
            ax = axs[row, col]
            
            stacked_data = []
            for treatment in self.state_numeric:
                treatment_data = cluster_data[cluster_data.eq(treatment).any(axis=1)]
                months = treatment_data.columns
                percentages = (treatment_data.apply(lambda x: x.value_counts().get(treatment, 0)) / len(treatment_data)) * 100
                stacked_data.append(percentages.values)
            
            months = range(len(months))
            bottom = np.zeros(len(months))
            for i, data in enumerate(stacked_data):
                ax.bar(months, data, bottom=bottom, label=self.state_label[i], color=self.colors[i])
                bottom += data
            
            ax.set_title(f'Cluster {cluster_label}')
            ax.set_xlabel('Time')
            ax.set_ylabel('Percentage of Patients')
            ax.legend(title='Treatment')
        
        plt.tight_layout()
        plt.show()





def main():
    df = pd.read_csv('data/mvad_data.csv')
    # tranformer vos données en format large si c'est n'est pas le cas 
    state_mapping = {"EM": 2, "FE": 4, "HE": 6, "JL": 8, "SC": 10, "TR": 12}
    colors = ['blue', 'orange', 'green', 'red', 'yellow', 'gray']
    df_numeriques = df.replace(state_mapping)

    # print(df_numeriques.head())
    # print(df_numeriques.columns)
    # print(df_numeriques.shape)
    # print(df_numeriques.info())
    # print(df_numeriques.isnull().sum())
    # print(df_numeriques.describe())
    # print(df_numeriques.dtypes)
    
    tca = TCA(df_numeriques,state_mapping,colors)
   
    # tca.plot_treatment_percentages(df_numeriques)

    distance_matrix = tca.calculate_distance_matrix()
    # print(len(distance_matrix))

    linkage_matrix = tca.cluster(distance_matrix)

    # tca.plot_dendrogram(linkage_matrix)
    # tca.plot_clustermap(linkage_matrix)
    # tca.plot_inertia(linkage_matrix)

    clusters = tca.assign_clusters(linkage_matrix, num_clusters=4)
    df_numeriques['cluster'] = pd.Series(clusters).apply(lambda x : 'group_'+str(x))
    print(df_numeriques['cluster'].value_counts())

    df_cluster_1 = df_numeriques[df_numeriques['cluster'] == 'group_1']
    df_cluster_2 = df_numeriques[df_numeriques['cluster'] == 'group_2']
    df_cluster_3 = df_numeriques[df_numeriques['cluster'] == 'group_3']
    df_cluster_4 = df_numeriques[df_numeriques['cluster'] == 'group_4']  

    sns.displot(data=df_cluster_1, y=df_cluster_1.index)
    plt.show()
    
    # for patient in df_cluster_1.index:
    #     patient_data = df_cluster_1.loc[patient].drop('cluster')
    #     print(patient_data)
        # plt.figure(figsize=(8, 6))
        # plt.bar(patient_data.index, patient_data.values, color=colors)
        # plt.xlabel('Time')
        # plt.ylabel('Treatment')
        # plt.title(f'Stacked Bar for Patient {patient} in Cluster 1')
        # plt.show()

        # break
    
    # tca.plot_cluster_heatmaps(clusters)
    # tca.plot_cluster_treatment_percentage(clusters)
    # tca.bar_cluster_treatment_percentage(clusters)
    # tca.plot_stacked_bar(clusters)

if __name__ == "__main__":
    main()