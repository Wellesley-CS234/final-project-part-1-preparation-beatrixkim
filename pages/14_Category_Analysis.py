# This app was written with the help of Claude AI, but ideas for data interactions were mine.

"""
Streamlit app for analyzing distribution of article types across Wikipedia language editions
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuration and Data Loading
st.set_page_config(layout="wide", page_title="Climate Change Article Types Analysis")

@st.cache_data
def load_data():
    # Load the CSV
    df = pd.read_csv('../data/st14_data.csv')

    # Get all article columns
    article_columns = [col for col in df.columns if col.startswith('article_')]

    # Reshape from wide to long format
    data_long = []
    for _, row in df.iterrows():
        qid = row['qid']
        category = row['category']
        
        for col in article_columns:
            lang_code = col.replace('article_', '')
            if pd.notna(row[col]) and row[col] != '':
                data_long.append({
                    'qid': qid,
                    'language_code': lang_code,
                    'article_url': row[col],
                    'category': category
                })
    
    df_long = pd.DataFrame(data_long)

    return df_long

df_long = load_data()

# Language code to full name mapping
lang_map = {
    'en': 'English',
    'ar': 'Arabic',
    'fr': 'French',
    'es': 'Spanish',
    'de': 'German',
    'pt': 'Portuguese',
    'zh': 'Chinese',
    'ru': 'Russian',
    'uk': 'Ukrainian',
    'it': 'Italian',
    'ja': 'Japanese',
    'nl': 'Dutch',
    'id': 'Indonesian',
    'pl': 'Polish',
    'sv': 'Swedish',
    'fi': 'Finnish',
    'cs': 'Czech',
    'ko': 'Korean',
    'he': 'Hebrew',
    'el': 'Greek',
    'da': 'Danish',
    'hu': 'Hungarian',
    'hi': 'Hindi',
    'ro': 'Romanian',
    'bg': 'Bulgarian'
}

# 2. Main Page stuff
st.title("Climate Change Article Types Across Wikipedia Languages")
st.subheader("Exploring How Article Categories Vary Across the Top 25 Language Editions")

st.markdown("""
**Research Question:** How does the distribution of article types (humans, events, 
organizations, concepts) vary across the top 25 Wikipedia language editions?

**Data Description:** This dataset contains climate change-related articles from the 
WikiProject Climate Change. Each article was classified using Wikidata's "instance of" 
(P31) property, as well as a broader subclass hierarchy to categorize articles into:
- **Concept**: concepts, ideas
- **Event**: Conferences, disasters, etc.
- **Human**: Scientists, politicians, etc.
- **Organization**: Companies, NGOs, etc.
- **Other**: Articles that don't fit the above categories

**Data Preparation:** Articles were queried from Wikidata, classified using P31 
instance types expanded with P279 subclass hierarchies and merged with 
Wikipedia article URLs across the top 25 language editions. 
This method was used because initially, upon classifying articles solely
on their PID, I noticed that many articles fell through the cracks—NGOs were
not, for example, included under the organization category, so I revised my 
approach to account for Wikidata's "subclass of" type (not a PID, but a QID).
""")

st.markdown("---")

# 3. Calculate summary statistics for top 25 languages
lang_counts = df_long.groupby('language_code').size().sort_values(ascending=False)
top_25_languages = lang_counts.head(25).index.tolist()
df_top25 = df_long[df_long['language_code'].isin(top_25_languages)].copy()

# Create pivot tables for all data
lang_category_all = df_top25.groupby(['language_code', 'category']).size().reset_index(name='count')
pivot_counts_all = lang_category_all.pivot(
    index='language_code',
    columns='category',
    values='count'
).fillna(0)
pivot_counts_all = pivot_counts_all.loc[top_25_languages]

pivot_pct_all = pivot_counts_all.div(pivot_counts_all.sum(axis=1), axis=0) * 100

# 4. Widgets
st.subheader("Visualization Controls")

col1, col2 = st.columns(2)

with col1:
    # Widget 1: Select categories to display
    category_order = ['event', 'concept', 'organization', 'human', 'none', 'other']
    available_categories = [cat for cat in category_order if cat in pivot_pct_all.columns]
    
    category_options = st.multiselect(
        "Select Article Types to Display:",
        options=available_categories,
        default=available_categories
    )

with col2:
    # Widget 2: Sort options
    sort_option = st.selectbox(
        "Sort Languages By:",
        options=[
            "Article Count (Descending)",
            "Article Count (Ascending)",
            "Highest % Event",
            "Highest % Concept",
            "Highest % Organization", 
            "Highest % Human",
            "Highest % Other"
        ],
        index=0
    )

col3, col4 = st.columns(2)

with col3:
    # Widget 3: Chart type
    chart_type = st.radio(
        "Display Type:",
        options=["Percentage (Stacked)", "Raw Counts (Stacked)", "Grouped Bars"],
        index=0,
        horizontal=True
    )

with col4:
    # Widget 4: Number of languages to show
    num_languages = st.slider(
        "Number of Languages to Display:",
        min_value=5,
        max_value=25,
        value=25,
        step=5
    )

# 5. Apply filters and sorting
# Filter categories
if len(category_options) == 0:
    st.warning("Please select at least one article type to display.")
    st.stop()

pivot_counts_filtered = pivot_counts_all[category_options]
pivot_pct_filtered = pivot_pct_all[category_options]

# Apply sorting
if sort_option == "Article Count (Descending)":
    lang_order = lang_counts[top_25_languages].sort_values(ascending=False).index.tolist()
elif sort_option == "Article Count (Ascending)":
    lang_order = lang_counts[top_25_languages].sort_values(ascending=True).index.tolist()
elif sort_option.startswith("Highest %"):
    category = sort_option.split("% ")[1].lower()
    if category in pivot_pct_all.columns:
        lang_order = pivot_pct_all[category].sort_values(ascending=False).index.tolist()
    else:
        lang_order = top_25_languages
else:
    lang_order = top_25_languages

# Limit to selected number of languages
lang_order = lang_order[:num_languages]

pivot_counts_display = pivot_counts_filtered.loc[lang_order]
pivot_pct_display = pivot_pct_filtered.loc[lang_order]

# 6. Create visualization
st.markdown("---")
st.subheader("Article Type Distribution")

# Prepare data for plotting
if chart_type == "Percentage (Stacked)":
    df_plot = pivot_pct_display.reset_index().melt(
        id_vars='language_code',
        var_name='category',
        value_name='percentage'
    )
    df_plot['language_name'] = df_plot['language_code'].apply(
        lambda x: f"{lang_map.get(x, x)}\n(n={lang_counts[x]})"
    )
    
    # Reorder categories
    df_plot['category'] = pd.Categorical(
        df_plot['category'],
        categories=category_options,
        ordered=True
    )
    
    color_map = {
        'event': '#66c2a5',
        'concept': '#fc8d62',
        'organization': '#8da0cb',
        'human': '#e78ac3',
        'none': '#a6d854',
        'other': '#ffd92f'
    }
    
    fig = px.bar(
        df_plot,
        x='language_name',
        y='percentage',
        color='category',
        title="Distribution of Article Types Across Wikipedia Language Editions (%)",
        labels={'language_name': 'Language Edition', 'percentage': 'Percentage of Articles'},
        color_discrete_map=color_map,
        height=600
    )
    fig.update_layout(barmode='stack', yaxis_range=[0, 100])
    
elif chart_type == "Raw Counts (Stacked)":
    df_plot = pivot_counts_display.reset_index().melt(
        id_vars='language_code',
        var_name='category',
        value_name='count'
    )
    df_plot['language_name'] = df_plot['language_code'].apply(
        lambda x: f"{lang_map.get(x, x)}\n(n={lang_counts[x]})"
    )
    
    df_plot['category'] = pd.Categorical(
        df_plot['category'],
        categories=category_options,
        ordered=True
    )
    
    color_map = {
        'event': '#66c2a5',
        'concept': '#fc8d62',
        'organization': '#8da0cb',
        'human': '#e78ac3',
        'none': '#a6d854',
        'other': '#ffd92f'
    }
    
    fig = px.bar(
        df_plot,
        x='language_name',
        y='count',
        color='category',
        title="Distribution of Article Types Across Wikipedia Language Editions (Counts)",
        labels={'language_name': 'Language Edition', 'count': 'Number of Articles'},
        color_discrete_map=color_map,
        height=600
    )
    fig.update_layout(barmode='stack')
    
else:  # Grouped Bars
    df_plot = pivot_pct_display.reset_index().melt(
        id_vars='language_code',
        var_name='category',
        value_name='percentage'
    )
    df_plot['language_name'] = df_plot['language_code'].apply(
        lambda x: f"{lang_map.get(x, x)}\n(n={lang_counts[x]})"
    )
    
    df_plot['category'] = pd.Categorical(
        df_plot['category'],
        categories=category_options,
        ordered=True
    )
    
    color_map = {
        'event': '#66c2a5',
        'concept': '#fc8d62',
        'organization': '#8da0cb',
        'human': '#e78ac3',
        'none': '#a6d854',
        'other': '#ffd92f'
    }
    
    fig = px.bar(
        df_plot,
        x='language_name',
        y='percentage',
        color='category',
        title="Distribution of Article Types Across Wikipedia Language Editions (Grouped)",
        labels={'language_name': 'Language Edition', 'percentage': 'Percentage of Articles'},
        color_discrete_map=color_map,
        barmode='group',
        height=600
    )

fig.update_layout(
    xaxis_title="",
    font=dict(size=11),
    legend=dict(
        title="Article Type",
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.02
    )
)

st.plotly_chart(fig, use_container_width=True)

# 7. Summary Statistics
st.markdown("---")
st.subheader("Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_articles = len(df_top25)
    st.metric("Total Articles", f"{total_articles:,}")

with col2:
    st.metric("Languages Analyzed", num_languages)

with col3:
    st.metric("Article Types", len(category_options))

with col4:
    most_common = df_top25['category'].value_counts().index[0]
    st.metric("Most Common Type", most_common.capitalize())

# 8. Key Findings
st.markdown("---")
st.subheader("Key Findings")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Consistency Across Languages")
    st.markdown("""
    Despite vast differences in article counts (English: 2,991 vs Bulgarian: 216), 
    the **proportional distribution remains remarkably similar** across all languages.
    
    This suggests Wikipedia's structural approach to climate change content is 
    **globally standardized**, regardless of language or cultural context.
    """)

with col2:
    st.markdown("### Category Breakdown")
    overall_pct = (df_top25['category'].value_counts() / len(df_top25) * 100).round(1)
    for cat in category_options:
        if cat in overall_pct.index:
            st.markdown(f"- **{cat.capitalize()}**: {overall_pct[cat]}%")

# 9. Detailed Breakdown
with st.expander("Show Detailed Breakdown by Language"):
    st.markdown("### Articles by Language and Type")
    
    summary_df = pivot_counts_display.copy()
    summary_df['Total'] = summary_df.sum(axis=1)
    summary_df.index = summary_df.index.map(lambda x: f"{lang_map.get(x, x)} ({x})")
    
    st.dataframe(summary_df.style.format("{:.0f}"), use_container_width=True)
    
    st.markdown("### Percentage Distribution")
    summary_pct = pivot_pct_display.copy()
    summary_pct.index = summary_pct.index.map(lambda x: f"{lang_map.get(x, x)} ({x})")
    
    st.dataframe(summary_pct.style.format("{:.1f}%"), use_container_width=True)

# 10. Category Definitions
with st.expander("Show Article Type Definitions"):
    st.markdown("### How Articles Were Classified")
    st.markdown("""
    Articles were classified using Wikidata's **P31 (instance of)** property combined 
    with **P279 (subclass of)** hierarchies to capture both direct instances and subclasses:
    """)
    
    definitions = {
        'concept': 'Scientific concepts, theories, properties, phenomena (e.g., greenhouse effect, carbon cycle)',
        'event': 'Conferences, protests, disasters, climate summits (e.g., COP meetings, climate strikes)',
        'human': 'Biographies of climate activists, scientists, politicians (e.g., Greta Thunberg, Al Gore)',
        'organization': 'Companies, NGOs, government agencies, research institutions (e.g., IPCC, Greenpeace)',
        'none': 'Articles with no instance type information in Wikidata',
        'other': 'Articles that don\'t fit the above categories (technologies, geographic features, policies, etc.)'
    }
    
    for cat in category_options:
        if cat in definitions:
            st.markdown(f"**{cat.capitalize()}:** {definitions[cat]}")

# 11. Raw Data Sample
with st.expander("Show Raw Data Sample"):
    st.markdown("### Sample of Classified Articles")
    
    display_df = df_top25.copy()
    display_df['language_name'] = display_df['language_code'].map(lang_map)
    display_df = display_df[display_df['category'].isin(category_options)]
    
    sample_df = display_df[['language_name', 'language_code', 'category', 'qid', 'article_url']].sample(
        min(100, len(display_df))
    ).sort_values(['language_code', 'category'])
    
    st.dataframe(sample_df, use_container_width=True)

st.markdown("---")
st.markdown("""
**Conclusion:** Despite using an extended subclass hierarchy that significantly reduced 
the "other" category, the distribution of article types remains remarkably consistent 
across all 25 Wikipedia language editions, suggesting a globally standardized approach 
to climate change coverage.

*Created by [Your Name] for CS 248 Final Project*
""")