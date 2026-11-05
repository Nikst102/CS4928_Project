from tslearn.clustering import silhouette_score
from tslearn.clustering import TimeSeriesKMeans
from clusteringInterface import ClusteringInterface
import seaborn as sns
import dataHelper
import cluster_naming
import json
global smell_sign
from scipy import stats
from collections import Counter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statics
from scipy.stats import kruskal
import statistics

class DtwWrapper(ClusteringInterface):

    softdtw = "softdtw"

    def __init__(self, timeseries=None, history_timeseries=False, metric=None, k=None, random_state=0,
                 operations_timeseries=None, timeseries_details=None):
        self.timeseries = timeseries
        self.history_timeseries = history_timeseries
        self.metric = metric
        self.random_state = random_state
        self.k = k
        self.operations_timeseries = operations_timeseries
        self.timeseries_details = timeseries_details

        self.without_history = self.timeseries

    def cluster(self, history=True):
        """
            Performs time series clustering using TimeSeriesKMeans and saves the results, including cluster centers,
            cluster labels, and associated time series data, to JSON files.

            After clustering, cluster centers, labels, and time series data for each cluster are saved to separate JSON files.

            Parameters:
            -----------
            history : bool, optional (default=True)
                If True, saves historical time series data with the release time series after clustering.
                If False, only the considers release time series is used for clustering.

            Files Generated:
            ----------------
            - `cluster_center.json`: Contains the cluster centers for the clustered time series.
            - `cluster_labels.json`: Contains the cluster labels assigned to each original time series.
            - `label_timeseries.json`: Stores the time series data assigned to each cluster label.
            - `label_operations.json`: Stores the operations data associated with each cluster label.
        """
        # Perform clustering
        km_dba = TimeSeriesKMeans(n_clusters=self.k, metric=self.metric, n_jobs=-1, random_state=self.random_state).fit(
            self.timeseries)

        # M4: name clusters by nearest reference centroid, not by cluster number
        cluster_naming.save_cluster_names(cluster_naming.name_clusters(km_dba.cluster_centers_))

        # Calculate silhouette score
        silhouette_score_value = silhouette_score(self.timeseries, km_dba.labels_.tolist(), self.metric, n_jobs=-1,
                                          random_state=self.random_state)
        print(silhouette_score_value)

        # Save cluster centers to a JSON file
        cluster_id = 0
        cluster_centers = {}
        for cluster_center in km_dba.cluster_centers_:
            cluster_centers[str(cluster_id)] = cluster_center.tolist()
            cluster_id = cluster_id + 1

        with open('data/' + self.metric + '/cluster_center.json', 'w') as cluster_centers_file:
            json.dump(cluster_centers, cluster_centers_file)

        # Save labels of original time series to a JSON file
        labels_dict = {"time_series_index": list(range(len(self.timeseries))),
                       "timeseries_details": self.timeseries_details,
                       "cluster_label": km_dba.labels_.tolist()
                       }

        out_file = open('data/' + self.metric + '/cluster_labels.json', 'w')
        json.dump(labels_dict, out_file, indent=4)
        out_file.close()

        if history and isinstance(self.history_timeseries, np.ndarray):

            release_and_history = np.concatenate((self.history_timeseries, self.timeseries), axis=1)
            # release_and_history = release_and_history[:10]
            self.timeseries = release_and_history

        # Create a dictionary to store time series for each cluster label
        label_timeseries_dict = {}
        for label, series in zip(km_dba.labels_, self.timeseries):
            label = str(label)
            if label not in label_timeseries_dict:
                label_timeseries_dict[label] = [series.tolist()]
            else:
                label_timeseries_dict[label].append(series.tolist())

        # Save the label-timeseries dictionary to a JSON file
        with open('data/' + self.metric + '/label_timeseries.json', 'w') as label_timeseries_file:
            json.dump(label_timeseries_dict, label_timeseries_file)

        # Create a dictionary to store time series for each cluster label
        label_operations_dict = {}
        for label, operations in zip(km_dba.labels_, self.operations_timeseries):
            label = str(label)
            if label not in label_operations_dict:
                label_operations_dict[label] = [operations]
            else:
                label_operations_dict[label].append(operations)

        # Save the label-timeseries dictionary to a JSON file
        with open('data/' + self.metric + '/label_operations.json', 'w') as label_timeseries_file:
            json.dump(label_operations_dict, label_timeseries_file)

    def box_plot(self):
        """
            Generates and saves box plots of clustered time series data with average values for each cluster.
        """

        print('performing: ', self.random_state)
        cluster_names = cluster_naming.load_cluster_names()  # M4; None -> authors' mapping
        with open('data/softdtw/label_timeseries.json') as label_timeseries_file:
            time_series = json.load(label_timeseries_file)
        with open('data/softdtw/cluster_labels.json') as label_timeseries_file:
            cluster_labels = json.load(label_timeseries_file)

        from collections import Counter
        label_count_dict = dict(Counter(cluster_labels['cluster_label']))
        scaled_series = {}
        for clusted_id, series_list in time_series.items():
            scaled_series[clusted_id] = []
            for series in series_list:
                scaled_series[clusted_id].append(DtwWrapper.divide_and_average(series, 11))
        colors = plt.cm.rainbow(np.linspace(0, 1, self.k))
        scaled_series = {k: scaled_series[k] for k in sorted(scaled_series)}
        # Plot the data
        sns.set(style="whitegrid")

        # Number of clusters
        num_clusters = len(scaled_series)

        # Create a figure with subplots
        fig, axes = plt.subplots(1, num_clusters, figsize=(25, 6), sharey=True)

        # Loop through each cluster and plot on a subplot
        for idx, (key, value) in enumerate(scaled_series.items()):
            transposed_data = np.array(value).T.tolist()
            averages = [np.mean(cluster) for cluster in transposed_data]

            # Define box colors
            box_colors = ['pink'] + ['lightblue'] * (len(averages) - 1)

            # Plot on the corresponding subplot
            ax = axes[idx]
            sns.boxplot(data=transposed_data, showfliers=False, palette=box_colors, ax=ax)

            color_key = 'red'
            if key == '0':
                color_key = colors[0]
            elif key == '1':
                color_key = colors[1]
            elif key == '2':
                color_key = colors[2]
            elif key == '3':
                color_key = colors[3]

            # Connect averages with red lines and add average markers
            for i in range(len(averages)):
                ax.scatter(i, averages[i], marker='o', color=color_key, s=100, zorder=3)

            for i in range(len(averages) - 1):
                ax.plot([i, i + 1], [averages[i], averages[i + 1]], color=color_key, linewidth=2)

            # Customize x-axis ticks
            x_ticks = ['History'] + [f'{(i + 1) * 10}%' for i in range(len(averages) - 1)]
            ax.set_xticks(range(len(averages)))
            ax.set_xticklabels(x_ticks, fontsize=12)

            ax.set_title(dataHelper.rename_cluster(key, cluster_names), fontsize=16, fontweight="bold")
            # ax.set_title(key, fontsize=16, fontweight="bold")
            ax.set_xlabel('Time Percentiles', fontsize=16, fontweight="bold")
            if idx == 0:
                ax.set_ylabel('Refactoring Density', fontsize=16, fontweight="bold")

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout to make room for the suptitle
        plt.savefig('images/release-patterns.pdf', format="pdf", bbox_inches="tight")
        plt.savefig('images/release-patterns.png', format="png", bbox_inches="tight")
        plt.show()


    def radar_plots(self):
        """
            This script visualizes feature distributions across different clusters using radar plots and performs
            a Chi-Square test for each feature category. The features being analyzed include size, developers, and
            stars.
        """

        with open('data/feature_categories.json') as json_file:
            categories = json.load(json_file)
        labels = categories['labels']
        features = ['size', 'developers', 'stars']
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(24, 8),
                                 subplot_kw=dict(polar=True))  # Ensure polar=True here

        for idx, feature in enumerate(features):
            label_distributions = {
                feature: {}
            }
            import dataHelper  # You may need to adjust this import

            for i in range(0, len(labels)):
                # These are the authors' shipped labels, so the authors' mapping is the right one.
                cluster_label = dataHelper.rename_cluster(labels[i], dataHelper.AUTHORS_CLUSTER_NAMES)
                if cluster_label not in label_distributions[feature]:
                    label_distributions[feature][cluster_label] = []
                label_distributions[feature][cluster_label].append(categories[feature][i])

            results = {}

            for cluster_label, items in label_distributions[feature].items():
                data = items
                counter = Counter(data)
                total_count = len(data)

                for item, count in counter.items():
                    percentage = (count / total_count) * 100
                    if cluster_label not in results:
                        results[cluster_label] = {}
                    results[cluster_label][item] = percentage

            df = pd.DataFrame(results).fillna(0)
            desired_order = ['least', 'less', 'more', 'most']
            df = df.reindex(desired_order)

            num_vars = len(df.columns)
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            angles += angles[:1]

            ax = axes[idx]  # Select the correct axis for this subplot

            for index, row in df.iterrows():
                values = row.values.flatten().tolist()
                values += values[:1]
                ax.plot(angles, values, label=index, linewidth=2, linestyle='solid')
                ax.fill(angles, values, alpha=0.25)

            ax.set_title(f'{feature.capitalize()}', size=16, color='black', weight='bold', pad=20)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(df.columns, color='black', size=14, weight='bold')
            ax.legend(loc='upper right', prop={'size': 12, 'weight': 'bold'})

            # Print the DataFrame as a table
            print(f"DataFrame for {feature}:")
            print(df)

            # Create contingency table
            data = label_distributions[feature].values()
            flattened_data = [(i, letter) for i, sublist in enumerate(data) for letter in sublist]
            df_contingency = pd.DataFrame(flattened_data, columns=['group', 'letter'])
            contingency_table = pd.crosstab(df_contingency['group'], df_contingency['letter'])

            # Perform the Chi-Square test
            chi2, p, dof, expected = stats.chi2_contingency(contingency_table)
            print(f"Chi-Square Statistic for {feature}: {chi2}")
            print(f"P-Value for {feature}: {p}")

        plt.tight_layout()
        plt.savefig('images/radar_plots.png')
        plt.savefig('images/radar_plots.pdf', format='pdf')
        plt.show()

        out_file = open("data/softdtw/feature_distributions.json", "w")
        json.dump(label_distributions, out_file, indent=4)
        out_file.close()

    def operations_distributions(self):
        """
            Analyzes the distribution of refactoring operations across clusters, calculates refactoring distributions,
            performs using the Kruskal-Wallis test, and exports the results to a CSV file.

            Workflow:
            1. Loads refactoring timeseries data from a JSON file ('data/softdtw/label_operations.json').
            2. Iterates through each cluster's timeseries data and groups refactoring operations based on different categories.
            3. Divides the timeseries into three parts (early, middle, late) and calculates the median values of refactoring
               frequencies for each part.
            4. Performs the Kruskal-Wallis test to compare the frequency distributions across the parts of the timeseries.
            5. Stores the results as a CSV file ('data/softdtw/operations-patterns.csv').
        """

        cluster_names = cluster_naming.load_cluster_names()  # M4; None -> authors' mapping
        with open('data/softdtw/label_operations.json') as label_timeseries_file:
            operations = json.load(label_timeseries_file)

        refactoring_categories = list(statics.Rminer.keys())

        results = {}
        for cluster_id, operations_timeseries_list in operations.items():
            results[cluster_id] = []
            converted_timeseries = []
            for operations_timeseries in operations_timeseries_list:
                converted_operations_timeseries = []
                for operations_timeserie in operations_timeseries:
                    temp = {}
                    for refactoring_level in list(statics.Rminer.keys()):
                        if refactoring_level not in temp:
                            temp[refactoring_level] = 0

                    for refactoring, frequency in operations_timeserie.items():
                        for refactoring_level in refactoring_categories:
                            flag = True
                            if refactoring in statics.Rminer[refactoring_level]:
                                temp[refactoring_level] += frequency
                            if not flag:
                                raise ValueError

                    converted_operations_timeseries.append(temp)
                converted_timeseries.append(converted_operations_timeseries)
            results[cluster_id] = converted_timeseries

        parts = 3
        scaled_operations_timeseries = {}
        not_scaled_operations_timeseries = {}
        for cluster_id, operations_timeseries_list in results.items():
            scaled_operations_timeseries[cluster_id] = []
            not_scaled_operations_timeseries[cluster_id] = []
            for operations_timeseries in operations_timeseries_list:
                scaled_operations_timeseries[cluster_id].append(
                    DtwWrapper.divide_operations(operations_timeseries, parts)[0])
                not_scaled_operations_timeseries[cluster_id].append(
                    DtwWrapper.divide_operations(operations_timeseries, parts)[1])

        overall = {}
        for cluster_id, timeseries_list in not_scaled_operations_timeseries.items():
            overall[cluster_id] = {}
            for timeseries in timeseries_list:
                for refactoring, value in timeseries.items():
                    if refactoring not in overall[cluster_id]:
                        overall[cluster_id][refactoring] = []
                    overall[cluster_id][refactoring].append(value)

        summary = {}
        for cluster_id, details in overall.items():
            # cluster_id = dataHelper.rename_cluster(cluster_id)
            summary[dataHelper.rename_cluster(cluster_id, cluster_names)] = {}
            for refactoring, numbers in details.items():
                summary[dataHelper.rename_cluster(cluster_id, cluster_names)][refactoring] = statistics.median(numbers)

        data = summary

        to_dt_list = []
        for cluster_id, timeseries_list in scaled_operations_timeseries.items():
            for timeseries in timeseries_list:
                for part in range(0, parts):
                    for refactoring, value in timeseries[part].items():
                        to_dt_list.append([cluster_id, part, refactoring, value])
        df = pd.DataFrame(to_dt_list, columns=['cluster_id', 'part', 'refactoring_type', 'frequency'])

        # Initialize a list to store the results for the DataFrame
        results = []

        # Sort the 'part' column
        df.sort_values('part', inplace=True)

        # Perform Kruskall-Wallis
        for cluster_id in df['cluster_id'].unique():
            cluster_data = df[df['cluster_id'] == cluster_id]

            for i, refactoring_type in enumerate(cluster_data['refactoring_type'].unique()):
                subset_data = cluster_data[cluster_data['refactoring_type'] == refactoring_type]

                # Calculate medians
                early_median = subset_data[subset_data['part'] == 0]['frequency'].median()
                middle_median = subset_data[subset_data['part'] == 1]['frequency'].median()
                late_median = subset_data[subset_data['part'] == 2]['frequency'].median()

                # Perform Kruskal-Wallis test
                parts = [subset_data[subset_data['part'] == part]['frequency'] for part in subset_data['part'].unique()]
                kruskal_result = kruskal(*parts)

                if kruskal_result.pvalue <= 0.05:
                    results.append({
                        'cluster_id': dataHelper.rename_cluster(cluster_id, cluster_names),
                        'refactoring_type': refactoring_type,
                        'early_median': round(early_median, 5) * 1000,
                        'middle_median': round(middle_median, 5) * 1000,
                        'late_median': round(late_median, 5) * 1000,
                        'p_value': round(kruskal_result.pvalue, 5)
                    })

        # Adjust the display settings to show all rows and columns
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)

        results_df = pd.DataFrame(results)

        # Define the desired order for refactoring_type
        refactoring_order = ['Variable', 'Method', 'Class', 'Package', 'Organization', 'Test', 'All']

        # Convert the refactoring_type column to a categorical type with the specified order
        results_df['refactoring_type'] = pd.Categorical(results_df['refactoring_type'], categories=refactoring_order,
                                                        ordered=True)

        # Sort the DataFrame by cluster_id and the ordered refactoring_type
        results_df = results_df.sort_values(by=['cluster_id', 'refactoring_type']).reset_index(drop=True)

        results_df.to_csv('data/softdtw/operations-patterns.csv')

        print(results_df)