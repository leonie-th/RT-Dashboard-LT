# Streamlit App - Dashboard

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

st.set_page_config(layout="wide")

st.title("Eine Analyse von Artikeln von RT")

# Datensatz laden
dataset_url = "https://github.com/polcomm-passau/computational_methods_python/raw/refs/heads/main/RT_D_Small.xlsx"
df = pd.read_excel(dataset_url)

# 'date' Spalte in Datumsformat umwandeln
df['date'] = pd.to_datetime(df['date'])

# Spalten für Reaktionen, Shares und Kommentare definieren
reaction_columns = ['haha', 'like', 'wow', 'angry', 'sad', 'love', 'hug']
engagement_columns = ['shares', 'comments_num']
all_metrics_columns = reaction_columns + engagement_columns

# --- MEHRERE SUCHBEGRIFFE EINGEBEN ---
st.subheader("Suchbegriffe eingeben")
search_input = st.text_input(
    "Gib mehrere Suchbegriffe ein (getrennt durch Komma):", 
    "grün, Klima, Energie"
)

# Suchbegriffe in Liste umwandeln und bereinigen
search_terms = [term.strip() for term in search_input.split(',') if term.strip()]

if not search_terms:
    st.warning("Bitte gib mindestens einen Suchbegriff ein.")
    st.stop()

# Farbpalette für die Suchbegriffe
colors = px.colors.qualitative.Set2[:len(search_terms)]

# --- LINIENDIAGRAMM: PROZENTUALER ANTEIL ÜBER ZEIT (MEHRERE BEGRIFFE) ---
st.subheader("Prozentualer Anteil der Artikel im Zeitverlauf")

total_posts_per_day = df['date'].value_counts().sort_index()

# DataFrame für Plotly erstellen
time_series_data = []

for i, term in enumerate(search_terms):
    search_condition = df['text'].fillna('').str.contains(term, case=False, na=False) | \
                      df['fulltext'].fillna('').str.contains(term, case=False, na=False)
    
    filtered_df = df[search_condition]
    
    if not filtered_df.empty:
        filtered_posts_per_day = filtered_df['date'].value_counts().sort_index()
        percentage_per_day = (filtered_posts_per_day / total_posts_per_day) * 100
        percentage_per_day = percentage_per_day.fillna(0)
        
        for date, percentage in percentage_per_day.items():
            time_series_data.append({
                'Datum': date,
                'Anteil (%)': percentage,
                'Suchbegriff': term,
                'Anzahl Artikel': filtered_posts_per_day.get(date, 0),
                'Gesamt Artikel': total_posts_per_day.get(date, 0)
            })

if time_series_data:
    time_df = pd.DataFrame(time_series_data)
    
    # Interaktives Liniendiagramm mit Hover-Informationen
    fig_line = px.line(
        time_df, 
        x='Datum', 
        y='Anteil (%)', 
        color='Suchbegriff',
        markers=True,
        color_discrete_sequence=colors,
        hover_data={
            'Anzahl Artikel': True,
            'Gesamt Artikel': True,
            'Anteil (%)': ':.2f'
        }
    )
    
    fig_line.update_traces(
        mode='markers+lines',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'Datum: %{x|%Y-%m-%d}<br>' +
                      'Anteil: %{y:.2f}%<br>' +
                      'Artikel mit Begriff: %{customdata[0]}<br>' +
                      'Gesamt Artikel: %{customdata[1]}<extra></extra>'
    )
    
    fig_line.update_layout(
        xaxis_title='Datum',
        yaxis_title='Prozentualer Anteil (%)',
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.warning("Keine Daten für die angegebenen Suchbegriffe gefunden.")

# --- VERGLEICH DER DURCHSCHNITTLICHEN METRIKEN ---
st.subheader("Vergleich der durchschnittlichen Metriken")

# Erstelle Spalten dynamisch basierend auf Anzahl der Suchbegriffe
cols = st.columns(len(search_terms) + 1)

# Sammle Daten für alle Suchbegriffe
metrics_data = {}

for i, term in enumerate(search_terms):
    search_condition = df['text'].fillna('').str.contains(term, case=False, na=False) | \
                      df['fulltext'].fillna('').str.contains(term, case=False, na=False)
    
    filtered_df = df[search_condition]
    
    with cols[i]:
        st.markdown(f"### {term}")
        if not filtered_df.empty:
            st.metric(label="Anzahl Artikel", value=len(filtered_df))
            mean_metrics = filtered_df[all_metrics_columns].mean().round(2)
            metrics_data[term] = mean_metrics
            st.dataframe(mean_metrics, height=350)
        else:
            st.info("Keine Artikel gefunden")

# Referenz: Artikel ohne alle Suchbegriffe
all_search_conditions = pd.Series([False] * len(df))
for term in search_terms:
    all_search_conditions |= (df['text'].fillna('').str.contains(term, case=False, na=False) | 
                              df['fulltext'].fillna('').str.contains(term, case=False, na=False))

filtered_df_without = df[~all_search_conditions]

with cols[-1]:
    st.markdown("### Ohne Suchbegriffe")
    if not filtered_df_without.empty:
        st.metric(label="Anzahl Artikel", value=len(filtered_df_without))
        mean_metrics_without = filtered_df_without[all_metrics_columns].mean().round(2)
        metrics_data['Ohne Begriffe'] = mean_metrics_without
        st.dataframe(mean_metrics_without, height=350)

# --- INTERAKTIVES BALKENDIAGRAMM: VERGLEICH ALLER METRIKEN ---
if metrics_data:
    st.subheader("Interaktiver Vergleich aller Metriken")
    
    # Daten für Plotly vorbereiten
    comparison_data = []
    for term, metrics in metrics_data.items():
        for metric, value in metrics.items():
            comparison_data.append({
                'Suchbegriff': term,
                'Metrik': metric,
                'Wert': value
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Interaktives gruppiertes Balkendiagramm
    fig_bar = px.bar(
        comparison_df,
        x='Metrik',
        y='Wert',
        color='Suchbegriff',
        barmode='group',
        color_discrete_sequence=colors + ['#95A5A6'],
        hover_data={'Wert': ':.2f'}
    )
    
    fig_bar.update_traces(
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'Metrik: %{x}<br>' +
                      'Durchschnitt: %{y:.2f}<extra></extra>'
    )
    
    fig_bar.update_layout(
        xaxis_title='Metrik',
        yaxis_title='Durchschnittlicher Wert',
        hovermode='x',
        height=500
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

# --- DIFFERENZ-HEATMAP ---
if len(search_terms) > 1 and all(term in metrics_data for term in search_terms):
    st.subheader("Heatmap: Unterschiede zwischen Suchbegriffen")
    
    # Matrix für Differenzen erstellen
    diff_matrix = []
    for metric in all_metrics_columns:
        row = []
        for term in search_terms:
            if term in metrics_data:
                row.append(metrics_data[term][metric])
            else:
                row.append(0)
        diff_matrix.append(row)
    
    diff_df = pd.DataFrame(diff_matrix, index=all_metrics_columns, columns=search_terms)
    
    # Interaktive Heatmap
    fig_heatmap = px.imshow(
        diff_df,
        labels=dict(x="Suchbegriff", y="Metrik", color="Durchschnitt"),
        x=search_terms,
        y=all_metrics_columns,
        color_continuous_scale='RdYlGn',
        aspect='auto'
    )
    
    fig_heatmap.update_traces(
        hovertemplate='Suchbegriff: %{x}<br>' +
                      'Metrik: %{y}<br>' +
                      'Wert: %{z:.2f}<extra></extra>'
    )
    
    fig_heatmap.update_layout(height=400)
    
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.subheader("Originale Daten (Auszug)")
st.dataframe(df.head())
