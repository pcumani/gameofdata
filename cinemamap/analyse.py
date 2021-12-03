import re

import seaborn as sns
import matplotlib.pyplot as plt


def pie_chart_pdm(data, title):
    """Moyenne des parts de marché."""
    labels = [x for x in data.columns if x.startswith('PdM') and "Art et Essai" not in x]
    df_pdm = data[labels]

    labels = [re.sub('PdM en entrées des ', '', x)
              for x in data.columns if x.startswith('PdM') and "Art et Essai" not in x]
    # stats pdm
    summary_pdm = df_pdm.mean().rename("value")

    # define Seaborn color palette to use
    colors = sns.color_palette('pastel')[0:4]

    # create pie chart
    fig1, ax1 = plt.subplots()
    plt.subplots_adjust(bottom=0.5)
    # draw circle
    ax1.pie(summary_pdm, colors=colors, labels=labels, autopct='%1.1f%%', startangle=90)
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig = plt.gcf()
    # Equal aspect ratio ensures that pie is drawn as a circle
    fig.gca().add_artist(centre_circle, )
    ax1.axis('equal')
    ax1.set_title(title, weight='bold')
    plt.tight_layout()

    return fig


def do_barplot_count_cinema(data, var_group_name, y_label, x_label, title):
    """Display barplot of number count group by var."""
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.set_theme(style="whitegrid")

    nb_cine_size_dep = data.groupby([var_group_name]).size()

    df_nb_cine = nb_cine_size_dep.rename('Count').to_frame()

    ax = sns.barplot(x=nb_cine_size_dep.index, y="Count", data=df_nb_cine)
    x_ticks_len = len(nb_cine_size_dep.index) + 1
    ax.set_xticks(range(0, x_ticks_len, 5), labels=nb_cine_size_dep.index[::5])
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    return fig


def do_bar_plot_var(data, varname, x_label, y_label, title):
    """Display barplot for specific variable."""
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.set_theme(style="whitegrid")

    sns.barplot(x="nom", y=varname, data=data, ax=ax)

    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    plt.xticks(rotation=70)
    return fig


def do_bar_plot_ratio(data, varname, varname2, x_label, y_label, title):
    """Display barplot for specific variable."""
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.set_theme(style="whitegrid")

    df = data[['nom', varname, varname2]].copy(deep=True)
    df.loc[:, 'Ratio'] = df[varname] / df[varname2]
    sns.barplot(x="nom", y='Ratio', data=df, ax=ax)

    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    plt.xticks(rotation=70)
    return fig


def do_plot_ratio_seances_entree(data, y_label, title):
    """Ratio fait sur annee entree 2019."""
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.set_style("darkgrid")
    ax = sns.lineplot(data=data, x="nom", y="Taux occupation par seance", ax=ax)
    plt.xticks(rotation=70)
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel(y_label)

    return fig
