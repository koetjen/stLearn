"""
Title: SpatialBasePlot for all spatial coordinates and image plot
Author: Duy Pham
Date: 20 Feb 2021
"""

from typing import Optional, Union, Mapping  # Special
from typing import Sequence, Iterable  # ABCs
from typing import Tuple  # Classes

import numpy as np
import pandas as pd
from anndata import AnnData

from matplotlib import rcParams, ticker, gridspec, axes
import matplotlib.pyplot as plt
import matplotlib
from scipy.interpolate import griddata
import networkx as nx

from ..classes import Spatial
from ..utils import _AxesSubplot, Axes
from .utils import centroidpython, get_cluster, get_node, check_sublist

################################################################
#                                                              #
#                  Spatial base plot class                     #
#                                                              #
################################################################


class SpatialBasePlot(Spatial):
    def __init__(
        self,
        # plotting param
        adata: AnnData,
        title: Optional["str"] = None,
        figsize: Optional[Tuple[float, float]] = None,
        cmap: Optional[str] = "Spectral_r",
        use_label: Optional[str] = None,
        list_clusters: Optional[list] = None,
        ax: Optional[_AxesSubplot] = None,
        show_plot: Optional[bool] = True,
        show_axis: Optional[bool] = False,
        show_image: Optional[bool] = True,
        show_color_bar: Optional[bool] = True,
        crop: Optional[bool] = True,
        margin: Optional[bool] = 100,
        size: Optional[float] = 7,
        image_alpha: Optional[float] = 1.0,
        cell_alpha: Optional[float] = 0.7,
        use_raw: Optional[bool] = False,
        fname: Optional[str] = None,
        dpi: Optional[int] = 120,
        **kwds
    ):
        super().__init__(
            adata,
        )
        self.title = title
        self.figsize = figsize
        self.image_alpha = image_alpha
        self.cell_alpha = cell_alpha
        self.size = size
        self.query_adata = self.adata[0].copy()
        self.list_clusters = list_clusters
        self.fname = fname
        self.dpi = dpi

        if use_raw:
            self.query_adata = self.adata[0].raw.to_adata().copy()

        if self.list_clusters != None:
            assert use_label != None, "Please specify `use_label` parameter!"

        if use_label != None:

            assert (
                use_label in self.adata[0].obs.columns
            ), "Please choose the right label in `adata.obs.columns`!"
            self.use_label = use_label

            if self.list_clusters is None:

                self.list_clusters = np.array(
                    self.adata[0].obs[use_label].cat.categories
                )
            else:
                if type(self.list_clusters) != list:
                    self.list_clusters = [self.list_clusters]

                self.list_clusters = np.array(self.list_clusters).astype(str)

            self.query_indexes = self._get_query_clusters_index()

            self._select_clusters()

        # Initialize cmap
        scanpy_cmap = ["vega_10_scanpy", "vega_20_scanpy", "default_102", "default_28"]
        stlearn_cmap = ["jana_40", "default"]
        cmap_available = plt.colormaps() + scanpy_cmap + stlearn_cmap
        assert cmap in cmap_available, "cmap should be one of these colors: " + str(
            cmap_available
        )
        self.cmap = cmap

        self.fig, self.ax = self._generate_frame()

        if show_axis == False:
            self._remove_axis(self.ax)

        if show_image:
            self._add_image(self.ax)

        if show_plot == False:
            plt.close(self.fig)

    def _select_clusters(self):
        def create_query(list_cl, use_label):
            ini = ""
            for sub in list_cl:
                ini = ini + self.use_label + ' == "' + str(sub) + '" | '
            return ini[:-2]

        if self.list_clusters is not None:
            self.query_adata = self.query_adata[
                self.query_adata.obs.query(
                    create_query(self.list_clusters, self.use_label)
                ).index
            ].copy()
        else:
            self.query_adata = self.query_adata.copy()

    def _generate_frame(self):
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=self.figsize)
        return [fig, ax]

    def _add_image(self, main_ax: Axes):
        image = self.query_adata.uns["spatial"][self.library_id]["images"][self.img_key]
        main_ax.imshow(
            image,
            alpha=self.image_alpha,
            zorder=-1,
        )

    def _plot_colorbar(self, plot_ax: Axes):

        cb = plt.colorbar(plot_ax, aspect=10, shrink=0.5, cmap=self.cmap)
        cb.outline.set_visible(False)

    def _remove_axis(self, main_ax: Axes):
        main_ax.axis("off")

    def _crop_image(self, main_ax: _AxesSubplot, margin: float):

        main_ax.set_xlim(self.imagecol.min() - margin, self.imagecol.max() + margin)

        main_ax.set_ylim(self.imagerow.min() - margin, self.imagerow.max() + margin)

        main_ax.set_ylim(main_ax.get_ylim()[::-1])

    def _add_color_bar(self, plot):
        cb = plt.colorbar(plot, aspect=10, shrink=0.5, cmap=self.cmap)
        cb.outline.set_visible(False)

    def _add_title(self):
        plt.title(self.title)

    def _get_query_clusters_index(self):
        index_query = []
        full_labels = self.adata[0].obs[self.use_label].cat.categories

        for query in self.list_clusters:
            index_query.append(np.where(np.array(full_labels) == query)[0][0])

        return index_query

    def _save_output(self):

        self.fig.savefig(
            fname=self.fname, bbox_inches="tight", pad_inches=0, dpi=self.dpi
        )


################################################################
#                                                              #
#                      Gene plot class                         #
#                                                              #
################################################################

import warnings


class GenePlot(SpatialBasePlot):
    def __init__(
        self,
        adata: AnnData,
        # plotting param
        title: Optional["str"] = None,
        figsize: Optional[Tuple[float, float]] = None,
        cmap: Optional[str] = "Spectral_r",
        use_label: Optional[str] = None,
        list_clusters: Optional[list] = None,
        ax: Optional[_AxesSubplot] = None,
        show_plot: Optional[bool] = True,
        show_axis: Optional[bool] = False,
        show_image: Optional[bool] = True,
        show_color_bar: Optional[bool] = True,
        crop: Optional[bool] = True,
        margin: Optional[bool] = 100,
        size: Optional[float] = 7,
        image_alpha: Optional[float] = 1.0,
        cell_alpha: Optional[float] = 1.0,
        use_raw: Optional[bool] = False,
        fname: Optional[str] = None,
        dpi: Optional[int] = 120,
        # gene plot param
        gene_symbols: Union[str, list] = None,
        threshold: Optional[float] = None,
        method: str = "CumSum",
        contour: bool = False,
        step_size: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            adata=adata,
            title=title,
            figsize=figsize,
            cmap=cmap,
            use_label=use_label,
            list_clusters=list_clusters,
            ax=ax,
            show_plot=show_plot,
            show_axis=show_axis,
            show_image=show_image,
            show_color_bar=show_color_bar,
            crop=crop,
            margin=margin,
            size=size,
            image_alpha=image_alpha,
            cell_alpha=cell_alpha,
            use_raw=use_raw,
            fname=fname,
            dpi=dpi,
        )

        method_available = ["CumSum", "NaiveMean"]
        assert method in method_available, "Please choose available method in: " + str(
            method_available
        )
        self.method = method

        self.step_size = step_size

        if self.title == None:
            if type(gene_symbols) == str:

                self.title = str(gene_symbols)
                gene_symbols = [gene_symbols]
            else:
                self.title = ", ".join(gene_symbols)

        self._add_title()

        self.gene_symbols = gene_symbols

        gene_values = self._get_gene_expression()

        self.available_ids = self._add_threshold(gene_values, threshold)

        if contour:
            plot = self._plot_contour(gene_values[self.available_ids])
        else:
            plot = self._plot_genes(gene_values[self.available_ids])

        if show_color_bar:
            self._add_color_bar(plot)

        if crop:
            self._crop_image(self.ax, margin)

        if fname != None:
            self._save_output()

    def _get_gene_expression(self):

        # Gene plot option
        if len(self.gene_symbols) == 0:
            raise ValueError("Genes should be provided, please input genes")

        elif len(self.gene_symbols) == 1:

            if self.gene_symbols[0] not in self.query_adata.var_names:
                raise ValueError(
                    self.gene_symbols[0]
                    + " is not exist in the data, please try another gene"
                )

            colors = self.query_adata[:, self.gene_symbols].to_df().iloc[:, -1]

            return colors
        else:

            for gene in self.gene_symbols:
                if gene not in self.query_adata.var.index:
                    self.gene_symbols.remove(gene)
                    warnings.warn(
                        "We removed " + gene + " because they not exist in the data"
                    )
                if len(self.gene_symbols) == 0:
                    raise ValueError("All provided genes are not exist in the data")

            count_gene = self.query_adata[:, self.gene_symbols].to_df()

            if self.method is None:
                raise ValueError(
                    "Please provide method to combine genes by NaiveMean/CumSum"
                )

            if self.method == "NaiveMean":
                present_genes = (count_gene > 0).sum(axis=1) / len(self.gene_symbols)

                count_gene = (count_gene.mean(axis=1)) * present_genes

            elif self.method == "CumSum":
                count_gene = count_gene.cumsum(axis=1).iloc[:, -1]

            colors = count_gene

            return colors

    def _plot_genes(self, gene_values: pd.Series):

        vmin = min(gene_values)
        vmax = max(gene_values)
        # Plot scatter plot based on pixel of spots
        imgcol_new = self.query_adata.obsm["spatial"][:, 0] * self.scale_factor
        imgrow_new = self.query_adata.obsm["spatial"][:, 1] * self.scale_factor
        plot = self.ax.scatter(
            imgcol_new,
            imgrow_new,
            edgecolor="none",
            alpha=self.cell_alpha,
            s=self.size,
            marker="o",
            vmin=vmin,
            vmax=vmax,
            cmap=plt.get_cmap(self.cmap),
            c=gene_values,
        )
        return plot

    def _plot_contour(self, gene_values: pd.Series):

        imgcol_new = self.query_adata.obsm["spatial"][:, 0] * self.scale_factor
        imgrow_new = self.query_adata.obsm["spatial"][:, 1] * self.scale_factor
        # Extracting x,y and values (z)
        z = gene_values
        y = imgrow_new
        x = imgcol_new

        # Interpolating values to get better coverage
        xi = np.linspace(x.min(), x.max(), 100)
        yi = np.linspace(y.min(), y.max(), 100)
        zi = griddata((x, y), z, (xi[None, :], yi[:, None]), method="linear")

        if self.step_size == None:
            self.step_size = int(np.max(z) / 50)
            if self.step_size < 1:
                self.step_size = 1
        # Creating contour plot with a step size of 10

        cs = plt.contourf(
            xi,
            yi,
            zi,
            range(0, int(np.nanmax(zi)) + self.step_size, self.step_size),
            cmap=plt.get_cmap(self.cmap),
            alpha=self.cell_alpha,
        )
        return cs

    def _add_threshold(self, gene_values, threshold):
        if threshold == None:
            return np.repeat(True, len(gene_values))
        else:
            return gene_values > threshold


################################################################
#                                                              #
#                      Cluster plot class                      #
#                                                              #
################################################################


class ClusterPlot(SpatialBasePlot):
    def __init__(
        self,
        adata: AnnData,
        # plotting param
        title: Optional["str"] = None,
        figsize: Optional[Tuple[float, float]] = None,
        cmap: Optional[str] = "default",
        use_label: Optional[str] = None,
        list_clusters: Optional[list] = None,
        ax: Optional[_AxesSubplot] = None,
        show_plot: Optional[bool] = True,
        show_axis: Optional[bool] = False,
        show_image: Optional[bool] = True,
        show_color_bar: Optional[bool] = True,
        crop: Optional[bool] = True,
        margin: Optional[bool] = 100,
        size: Optional[float] = 5,
        image_alpha: Optional[float] = 1.0,
        cell_alpha: Optional[float] = 1.0,
        fname: Optional[str] = None,
        dpi: Optional[int] = 120,
        # cluster plot param
        show_subcluster: Optional[bool] = False,
        show_cluster_labels: Optional[bool] = False,
        show_trajectories: Optional[bool] = False,
        reverse: Optional[bool] = False,
        show_node: Optional[bool] = False,
        threshold_spots: Optional[int] = 5,
        text_box_size: Optional[float] = 5,
        color_bar_size: Optional[float] = 10,
        bbox_to_anchor: Optional[Tuple[float, float]] = (1, 1),
    ):
        super().__init__(
            adata=adata,
            title=title,
            figsize=figsize,
            cmap=cmap,
            use_label=use_label,
            list_clusters=list_clusters,
            ax=ax,
            show_plot=show_plot,
            show_axis=show_axis,
            show_image=show_image,
            show_color_bar=show_color_bar,
            crop=crop,
            margin=margin,
            size=size,
            image_alpha=image_alpha,
            cell_alpha=cell_alpha,
            fname=fname,
            dpi=dpi,
        )

        self.cmap_ = self._get_cmap(self.cmap)

        self._add_cluster_colors()

        self._plot_clusters()
        self.threshold_spots = threshold_spots
        self.text_box_size = text_box_size
        self.color_bar_size = color_bar_size
        self.reverse = reverse
        self.show_node = show_node

        if show_color_bar:
            self._add_cluster_bar(bbox_to_anchor)

        if show_cluster_labels:
            self._add_cluster_labels()

        if show_subcluster:
            self._add_sub_clusters()
        if show_trajectories:
            self._add_trajectories()

        if crop:
            self._crop_image(self.ax, margin)

        if fname != None:
            self._save_output()

    def _add_cluster_colors(self):
        self.adata[0].uns[self.use_label + "_colors"] = []

        for i, cluster in enumerate(self.adata[0].obs.groupby(self.use_label)):
            self.adata[0].uns[self.use_label + "_colors"].append(
                matplotlib.colors.to_hex(self.cmap_(i / (self.cmap_n - 1)))
            )

    def _plot_clusters(self):
        # Plot scatter plot based on pixel of spots

        for i, cluster in enumerate(self.query_adata.obs.groupby(self.use_label)):
            # Plot scatter plot based on pixel of spots
            subset_spatial = self.query_adata.obsm["spatial"][
                check_sublist(list(self.query_adata.obs.index), list(cluster[1].index))
            ]

            imgcol_new = subset_spatial[:, 0] * self.scale_factor
            imgrow_new = subset_spatial[:, 1] * self.scale_factor
            _ = self.ax.scatter(
                imgcol_new,
                imgrow_new,
                c=[self.cmap_(self.query_indexes[i] / (self.cmap_n - 1))],
                label=cluster[0],
                edgecolor="none",
                alpha=self.cell_alpha,
                s=self.size,
                marker="o",
            )

    def _get_cmap(self, cmap):
        from scanpy.plotting import palettes
        from stlearn.plotting import palettes_st

        if cmap == "vega_10_scanpy":
            cmap = palettes.vega_10_scanpy
        elif cmap == "vega_20_scanpy":
            cmap = palettes.vega_20_scanpy
        elif cmap == "default_102":
            cmap = palettes.default_102
        elif cmap == "default_28":
            cmap = palettes.default_28
        elif cmap == "jana_40":
            cmap = palettes_st.jana_40
        elif cmap == "default":
            cmap = palettes_st.default
        else:
            self.cmap_n = plt.get_cmap(cmap).N
            return plt.get_cmap(cmap)

        self.cmap_n = len(cmap)
        cmaps = matplotlib.colors.LinearSegmentedColormap.from_list("", cmap)

        cmap_ = plt.cm.get_cmap(cmaps)
        return cmap_

    def _add_cluster_bar(self, bbox_to_anchor):
        lgnd = self.ax.legend(
            bbox_to_anchor=bbox_to_anchor,
            labelspacing=0.05,
            fontsize=self.color_bar_size,
            handleheight=1.0,
            edgecolor="white",
        )
        for handle in lgnd.legendHandles:
            handle.set_sizes([20.0])

    def _add_cluster_labels(self):

        for i, label in enumerate(self.list_clusters):

            label_index = list(
                self.query_adata.obs[
                    self.query_adata.obs[self.use_label] == str(label)
                ].index
            )
            subset_spatial = self.query_adata.obsm["spatial"][
                check_sublist(list(self.query_adata.obs.index), label_index)
            ]

            imgcol_new = subset_spatial[:, 0] * self.scale_factor
            imgrow_new = subset_spatial[:, 1] * self.scale_factor

            if (
                len(
                    self.query_adata.obs[
                        self.query_adata.obs[self.use_label] == str(label)
                    ][self.use_label].cat.categories
                )
                < 2
            ):
                centroids = [centroidpython(imgcol_new, imgrow_new)]

            else:
                from sklearn.neighbors import NearestCentroid

                clf = NearestCentroid()
                clf.fit(
                    np.column_stack((spatial.imagecol, spatial.imagerow)),
                    np.repeat(label, len(imgcol_new)),
                )

                centroids = clf.centroids_

            if centroids[0][0] < 1500:
                x = -100
                y = 50
            else:
                x = 100
                y = -50

            colors = self.adata[0].uns[self.use_label + "_colors"]
            index = self.query_indexes[i]
            self.ax.text(
                centroids[0][0] + x,
                centroids[0][1] + y,
                label,
                color="black",
                fontsize=self.text_box_size,
                zorder=3,
                bbox=dict(
                    facecolor=colors[index],
                    boxstyle="round",
                    alpha=1.0,
                ),
            )

    def _add_sub_clusters(self):

        if "sub_cluster_labels" not in self.query_adata.obs.columns:
            raise ValueError("Please run stlearn.spatial.cluster.localization")

        for i, label in enumerate(self.list_clusters):
            label_index = list(
                self.query_adata.obs[
                    self.query_adata.obs[self.use_label] == str(label)
                ].index
            )
            subset_spatial = self.query_adata.obsm["spatial"][
                check_sublist(list(self.query_adata.obs.index), label_index)
            ]

            imgcol_new = subset_spatial[:, 0] * self.scale_factor
            imgrow_new = subset_spatial[:, 1] * self.scale_factor

            if (
                len(
                    self.query_adata.obs[
                        self.query_adata.obs[self.use_label] == str(label)
                    ]["sub_cluster_labels"].unique()
                )
                < 2
            ):
                centroids = [centroidpython(imgcol_new, imgrow_new)]
                # classes = np.array(self.query_adata.obs[self.query_adata.obs[self.use_label] == str(label)]["sub_cluster_labels"])

            else:
                from sklearn.neighbors import NearestCentroid

                clf = NearestCentroid()
                clf.fit(
                    np.column_stack((imgcol_new, imgrow_new)),
                    self.query_adata.obs[
                        self.query_adata.obs[self.use_label] == str(label)
                    ]["sub_cluster_labels"],
                )

                centroids = clf.centroids_
                classes = clf.classes_

            for j, label in enumerate(classes):
                if (
                    len(
                        self.query_adata.obs[
                            self.query_adata.obs["sub_cluster_labels"] == label
                        ]
                    )
                    > self.threshold_spots
                ):
                    if centroids[i][0] < 1500:
                        x = -100
                        y = 50
                    else:
                        x = 100
                        y = -50
                    colors = self.adata[0].uns[self.use_label + "_colors"]
                    index = self.query_indexes[i]
                    self.ax.text(
                        centroids[j][0] + x,
                        centroids[j][1] + y,
                        label,
                        color="black",
                        fontsize=5,
                        zorder=3,
                        bbox=dict(
                            facecolor=colors[index],
                            boxstyle="round",
                            alpha=1.0,
                        ),
                    )

    def _add_trajectories(self):
        used_colors = self.adata[0].uns[self.use_label + "_colors"]
        cmaps = matplotlib.colors.LinearSegmentedColormap.from_list("", used_colors)

        cmap = plt.get_cmap(cmaps)

        if not self.adata[0].uns["PTS_graph"]:
            raise ValueError("Please run stlearn.spatial.trajectory.pseudotimespace!")

        tmp = self.adata[0].uns["PTS_graph"]

        G = tmp.copy()

        remove = [edge for edge in G.edges if 9999 in edge]
        G.remove_edges_from(remove)
        G.remove_node(9999)
        centroid_dict = self.adata[0].uns["centroid_dict"]
        if self.reverse:
            nx.draw_networkx_edges(
                G,
                pos=centroid_dict,
                node_size=10,
                alpha=1.0,
                width=2.5,
                edge_color="#f4efd3",
                arrowsize=17,
                arrowstyle="<|-",
                connectionstyle="arc3,rad=0.2",
            )
        else:
            nx.draw_networkx_edges(
                G,
                pos=centroid_dict,
                node_size=10,
                alpha=1.0,
                width=2.5,
                edge_color="#f4efd3",
                arrowsize=17,
                arrowstyle="-|>",
                connectionstyle="arc3,rad=0.2",
            )

        if self.show_node:
            for x, y in centroid_dict.items():

                if x in get_node(list_cluster, self.adata[0].uns["split_node"]):
                    a.text(
                        y[0],
                        y[1],
                        get_cluster(str(x), self.adata[0].uns["split_node"]),
                        color="black",
                        fontsize=8,
                        zorder=100,
                        bbox=dict(
                            facecolor=cmap(
                                int(
                                    get_cluster(str(x), self.adata[0].uns["split_node"])
                                )
                                / (len(used_colors) - 1)
                            ),
                            boxstyle="circle",
                            alpha=1,
                        ),
                    )


################################################################
#                                                              #
#                      SubCluster plot class                   #
#                                                              #
################################################################


class SubClusterPlot(SpatialBasePlot):
    def __init__(
        self,
        adata: AnnData,
        # plotting param
        title: Optional["str"] = None,
        figsize: Optional[Tuple[float, float]] = None,
        cmap: Optional[str] = "jet",
        use_label: Optional[str] = None,
        list_clusters: Optional[list] = None,
        ax: Optional[_AxesSubplot] = None,
        show_plot: Optional[bool] = True,
        show_axis: Optional[bool] = False,
        show_image: Optional[bool] = True,
        show_color_bar: Optional[bool] = True,
        crop: Optional[bool] = True,
        margin: Optional[bool] = 100,
        size: Optional[float] = 5,
        image_alpha: Optional[float] = 1.0,
        cell_alpha: Optional[float] = 1.0,
        fname: Optional[str] = None,
        dpi: Optional[int] = 120,
        # subcluster plot param
        cluster: Optional[int] = 0,
        text_box_size: Optional[float] = 5,
        bbox_to_anchor: Optional[Tuple[float, float]] = (1, 1),
        **kwargs
    ):
        super().__init__(
            adata=adata,
            title=title,
            figsize=figsize,
            cmap=cmap,
            use_label=use_label,
            list_clusters=list_clusters,
            ax=ax,
            show_plot=show_plot,
            show_axis=show_axis,
            show_image=show_image,
            show_color_bar=show_color_bar,
            crop=crop,
            margin=margin,
            size=size,
            image_alpha=image_alpha,
            cell_alpha=cell_alpha,
            fname=fname,
            dpi=dpi,
        )

        self.text_box_size = text_box_size
        self.cluster = cluster

        self._plot_subclusters()

        self._add_subclusters_label()

        if crop:
            self._crop_image(self.ax, margin)

        if fname != None:
            self._save_output()

    def _plot_subclusters(self):
        subset = self.adata[0].obs[
            self.adata[0].obs[self.use_label] == str(self.cluster)
        ]
        colors = subset["sub_cluster_labels"]
        sub_anndata = self.adata[0][subset.index, :]
        self.imgcol_new = sub_anndata.obsm["spatial"][:, 0] * self.scale_factor
        self.imgrow_new = sub_anndata.obsm["spatial"][:, 1] * self.scale_factor

        keys = list(np.sort(colors.unique()))
        self.vals = np.arange(len(keys))
        self.mapping = dict(zip(keys, self.vals))

        colors = colors.replace(self.mapping)

        plot = self.ax.scatter(
            self.imgcol_new,
            self.imgrow_new,
            edgecolor="none",
            s=self.size,
            marker="o",
            cmap=plt.get_cmap(self.cmap),
            c=colors,
            alpha=self.cell_alpha,
        )

    def _add_subclusters_label(self):
        if (
            len(
                self.adata[0]
                .obs[self.adata[0].obs[self.use_label] == str(self.cluster)][
                    "sub_cluster_labels"
                ]
                .unique()
            )
            < 2
        ):
            centroids = [
                centroidpython(
                    self.adata[0]
                    .obs[self.adata[0].obs[self.use_label] == str(self.cluster)][
                        ["imagecol", "imagerow"]
                    ]
                    .values
                )
            ]
            classes = np.array(
                [
                    self.adata[0].obs[
                        self.adata[0].obs[self.use_label] == str(self.cluster)
                    ]["sub_cluster_labels"][0]
                ]
            )

        else:
            from sklearn.neighbors import NearestCentroid

            clf = NearestCentroid()
            clf.fit(
                np.column_stack((self.imgcol_new, self.imgrow_new)),
                self.adata[0].obs[
                    self.adata[0].obs[self.use_label] == str(self.cluster)
                ]["sub_cluster_labels"],
            )

            centroids = clf.centroids_
            classes = clf.classes_

        norm = matplotlib.colors.Normalize(vmin=min(self.vals), vmax=max(self.vals))

        m = matplotlib.cm.ScalarMappable(norm=norm, cmap=self.cmap)

        for i, label in enumerate(classes):
            if centroids[i][0] < 1000:
                x = -100
                y = 100
            else:
                x = 100
                y = -100

            self.ax.text(
                centroids[i][0] + x,
                centroids[i][1] + y,
                label,
                color="white",
                fontsize=self.text_box_size,
                zorder=3,
                bbox=dict(
                    facecolor=matplotlib.colors.to_hex(m.to_rgba(self.mapping[label])),
                    boxstyle="round",
                    alpha=0.5,
                ),
            )


################################################################
#                                                              #
#                      Cci Plot class                          #
#                                                              #
################################################################


class CciPlot(GenePlot):
    def __init__(
        self,
        adata: AnnData,
        # plotting param
        title: Optional["str"] = None,
        figsize: Optional[Tuple[float, float]] = None,
        cmap: Optional[str] = "Spectral_r",
        use_label: Optional[str] = None,
        list_clusters: Optional[list] = None,
        ax: Optional[_AxesSubplot] = None,
        show_plot: Optional[bool] = True,
        show_axis: Optional[bool] = False,
        show_image: Optional[bool] = True,
        show_color_bar: Optional[bool] = True,
        crop: Optional[bool] = True,
        margin: Optional[bool] = 100,
        size: Optional[float] = 7,
        image_alpha: Optional[float] = 1.0,
        cell_alpha: Optional[float] = 1.0,
        use_raw: Optional[bool] = False,
        fname: Optional[str] = None,
        dpi: Optional[int] = 120,
        # cci param
        use_het: Optional[str] = "het",
        contour: bool = False,
        step_size: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            adata=adata,
            title=title,
            figsize=figsize,
            cmap=cmap,
            use_label=use_label,
            list_clusters=list_clusters,
            ax=ax,
            show_plot=show_plot,
            show_axis=show_axis,
            show_image=show_image,
            show_color_bar=show_color_bar,
            crop=crop,
            margin=margin,
            size=size,
            image_alpha=image_alpha,
            cell_alpha=cell_alpha,
            use_raw=use_raw,
            fname=fname,
            dpi=dpi,
            gene_symbols=use_het,
            contour=contour,
            step_size=step_size,
        )

    def _get_gene_expression(self):
        return self.query_adata.obsm[self.gene_symbols[0]]
