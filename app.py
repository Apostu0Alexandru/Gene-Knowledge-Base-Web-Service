from flask import Flask, render_template, jsonify
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import requests

app = Flask(__name__)

# Load and process data
def load_data():
    # Load the Excel file with both sheets
    excel_file = 'data/NIHMS1635539-supplement-1635539_Sup_tab_4.xlsx'
    
    # Load S4B sheet for volcano plot - skip metadata rows
    volcano_data = pd.read_excel(excel_file, sheet_name='S4B limma results', skiprows=2)
    print(f"Volcano data columns: {volcano_data.columns.tolist()[:10]}")
    
    # Load S4A sheet for boxplots - skip metadata rows
    sample_data = pd.read_excel(excel_file, sheet_name='S4A values', header=2)
    print(f"Sample data columns: {sample_data.columns.tolist()[:15]}")
    
    return volcano_data, sample_data

volcano_data, sample_data = load_data()

@app.route('/')
def index():
    if volcano_data.empty:
        return "Error: Could not load data. Please check the console for details."
    
    # Create a volcano plot
    volcano_df = volcano_data.copy()
    
    # Find the adjusted p-value column
    adj_p_val_column = 'adj.P.Val'
    logfc_column = 'logFC'
    gene_col = 'EntrezGeneSymbol'
    
    # Print data info for debugging
    print(f"Data shape: {volcano_df.shape}")
    print(f"Sample data:\n{volcano_df[[logfc_column, adj_p_val_column, gene_col]].head()}")
    
    # Create the new column with -log10 transform
    volcano_df['-log10(adj.P.Val)'] = -np.log10(pd.to_numeric(volcano_df[adj_p_val_column], errors='coerce').fillna(1))
    
    # Create direct scatter plot instead of using px.scatter
    fig = go.Figure()
    
    # Add scatter trace with explicit data conversion
    fig.add_trace(go.Scatter(
        x=volcano_df[logfc_column].tolist(),
        y=volcano_df['-log10(adj.P.Val)'].tolist(),
        mode='markers',
        text=volcano_df[gene_col].tolist(),
        hoverinfo='text',
        marker=dict(
            size=8,
            opacity=0.8,
            color='blue',
            line=dict(width=1, color='black')
        )
    ))
    
    # Update layout
    fig.update_layout(
        title='Volcano Plot of Protein Activity Levels',
        xaxis_title='Log2 Fold Change',
        yaxis_title='-log10(adj P-Value)',
        hovermode='closest',
        plot_bgcolor='rgba(240,240,240,0.8)'
    )
    
    # Create a simple JavaScript-friendly data structure
    volcano_plot_json = json.dumps({
        'data': [{
            'x': volcano_df[logfc_column].tolist(),
            'y': volcano_df['-log10(adj.P.Val)'].tolist(),
            'text': volcano_df[gene_col].tolist(),
            'type': 'scatter',
            'mode': 'markers',
            'marker': {
                'size': 8,
                'opacity': 0.8,
                'color': 'blue',
                'line': {'width': 1, 'color': 'black'}
            }
        }],
        'layout': {
            'title': {'text': 'Volcano Plot of Protein Activity Levels'},
            'xaxis': {'title': {'text': 'Log2 Fold Change'}},
            'yaxis': {'title': {'text': '-log10(adj P-Value)'}},
            'hovermode': 'closest',
            'plot_bgcolor': 'rgba(240,240,240,0.8)'
        }
    })
    
    return render_template('index.html', 
                          volcano_plot_json=volcano_plot_json, 
                          gene_column_name=gene_col)


@app.route('/boxplot/<gene>')
def boxplot(gene):
    try:
        # Ensure EntrezGeneSymbol column exists
        if 'EntrezGeneSymbol' not in sample_data.columns:
            return jsonify({'error': 'EntrezGeneSymbol column not found in sample data'})
        
        # Find the row for the selected gene
        gene_row = sample_data[sample_data['EntrezGeneSymbol'] == gene]
        if gene_row.empty:
            return jsonify({'error': f'Gene {gene} not found in sample data'})
        
        # Extract donor-related columns
        young_values = []
        old_values = []
        
        for col in sample_data.columns:
            if 'YD' in col:  # Young donors
                try:
                    value = float(gene_row[col].values[0])
                    young_values.append(value)
                except (ValueError, TypeError):
                    pass
            elif 'OD' in col:  # Old donors
                try:
                    value = float(gene_row[col].values[0])
                    old_values.append(value)
                except (ValueError, TypeError):
                    pass
        
        print(f"Found {len(young_values)} young samples and {len(old_values)} old samples")
        
        # Create boxplot data structure with enhanced styling
        data = [
            {
                'y': young_values,
                'name': 'Young',
                'type': 'box',
                'boxpoints': 'all',
                'jitter': 0.5,         # Increased jitter for better point separation
                'pointpos': 0,         # Center points in the box
                'marker': {
                    'color': '#3366CC',  # Distinct blue color for young group
                    'size': 8,           # Larger point size
                    'opacity': 0.8,      # Semi-transparent points
                    'line': {            # Add border to points
                        'width': 1,
                        'color': '#000000'
                    }
                },
                'line': {
                    'width': 2           # Thicker box outline
                },
                'fillcolor': 'rgba(51, 102, 204, 0.1)'  # Light fill color
            },
            {
                'y': old_values,
                'name': 'Old',
                'type': 'box',
                'boxpoints': 'all',
                'jitter': 0.5,
                'pointpos': 0,
                'marker': {
                    'color': '#FF6600',  # Distinct orange color for old group
                    'size': 8,
                    'opacity': 0.8,
                    'line': {
                        'width': 1,
                        'color': '#000000'
                    }
                },
                'line': {
                    'width': 2
                },
                'fillcolor': 'rgba(255, 102, 0, 0.1)'
            }
        ]
        
        layout = {
            'title': {
                'text': f'Protein Level for {gene}: Young vs Old',
                'font': {
                    'size': 18,
                    'color': '#333333'
                }
            },
            'yaxis': {
                'title': 'Protein Concentration',
                'gridcolor': '#E2E2E2',
                'zeroline': True,
                'zerolinecolor': '#969696',
                'zerolinewidth': 1
            },
            'xaxis': {
                'title': 'Age Group'
            },
            'plot_bgcolor': 'white',
            'boxmode': 'group',
            'boxgap': 0.4,
            'margin': {'l': 60, 'r': 40, 't': 80, 'b': 60},
            'height': 600,
            'width': 550
        }
        
        return jsonify({'data': data, 'layout': layout})
    
    except Exception as e:
        return jsonify({'error': f'Error processing request: {str(e)}'})

@app.route('/gene_info/<gene>')
def gene_info(gene):
    # Query MyGene.info for gene information
    try:
        # First find the gene ID
        query_response = requests.get(f'https://mygene.info/v3/query?q=symbol:{gene}&fields=generif')
        query_data = query_response.json()
        
        if 'hits' in query_data and len(query_data['hits']) > 0:
            gene_id = query_data['hits'][0]['_id']
            
            # Get detailed information for the gene
            gene_response = requests.get(
                f'https://mygene.info/v3/gene/{gene_id}?fields=generif,name,summary,publications'
            )
            gene_data = gene_response.json()
            
            # Extract publications with better error handling
            publications = []
            
            # Try different publication paths in the API response
            if 'generif' in gene_data and 'pubmed' in gene_data['generif']:
                for pubmed_id in gene_data['generif']['pubmed'][:10]:  # Limit to 10 papers
                    publications.append({
                        'pubmed_id': pubmed_id,
                        'url': f'https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/'
                    })
            elif 'publications' in gene_data:
                for pub in gene_data['publications'][:10]:
                    if isinstance(pub, dict) and 'pubmed' in pub:
                        publications.append({
                            'pubmed_id': pub['pubmed'],
                            'url': f'https://pubmed.ncbi.nlm.nih.gov/{pub["pubmed"]}/'
                        })
                    elif isinstance(pub, str) or isinstance(pub, int):
                        publications.append({
                            'pubmed_id': str(pub),
                            'url': f'https://pubmed.ncbi.nlm.nih.gov/{pub}/'
                        })
            
            # Fallback: Use PubMed search if no publications found
            if not publications:
                publications.append({
                    'pubmed_id': 'Search',
                    'url': f'https://pubmed.ncbi.nlm.nih.gov/?term={gene}'
                })
            
            return jsonify({
                'gene_id': gene_id,
                'symbol': gene,
                'publications': publications
            })
        else:
            return jsonify({'error': 'Gene not found in MyGene.info', 'symbol': gene})
    
    except Exception as e:
        return jsonify({'error': str(e), 'symbol': gene})

if __name__ == '__main__':
    app.run(debug=True)
