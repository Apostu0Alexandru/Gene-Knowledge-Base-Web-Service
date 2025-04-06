# app.py
from flask import Flask, render_template, jsonify
import pandas as pd
import numpy as np
import os
import requests

app = Flask(__name__)

# Load data
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'NIHMS1635539-supplement-1635539_Sup_tab_4.xlsx')
limma_df = pd.read_excel(DATA_FILE, sheet_name='S4B limma results')
values_df = pd.read_excel(DATA_FILE, sheet_name='S4A values')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/volcano-data')
def volcano_data():
    data = {
        'x': limma_df['logFC'].tolist(),
        'y': (-np.log10(limma_df['adj.P.Val'])).tolist(),
        'genes': limma_df['EntrezGeneSymbol'].tolist(),
        'pvals': limma_df['adj.P.Val'].tolist()
    }
    return jsonify(data)

@app.route('/api/boxplot/<gene>')
def boxplot_data(gene):
    gene_data = values_df[values_df['EntrezGeneSymbol'] == gene]
    if gene_data.empty:
        return jsonify({'error': 'Gene not found'}), 404
    
    donors = [col for col in values_df.columns if 'Set002' in col]
    young = [col for col in donors if 'YD' in col]
    old = [col for col in donors if 'OD' in col]
    
    return jsonify({
        'young': gene_data[young].values.flatten().tolist(),
        'old': gene_data[old].values.flatten().tolist()
    })

@app.route('/api/papers/<gene>')
def get_papers(gene):
    # MyGene.info API integration
    query = requests.get(f"https://mygene.info/v3/query?q=symbol:{gene}")
    if not query.ok or not query.json().get('hits'):
        return jsonify([])
    
    gene_id = query.json()['hits'][0]['_id']
    gene_info = requests.get(f"https://mygene.info/v3/gene/{gene_id}")
    
    papers = []
    if gene_info.ok and 'generif' in gene_info.json():
        for rif in gene_info.json()['generif']:
            if 'pubmed' in rif:
                papers.append({
                    'title': rif.get('text', 'No title available'),
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{rif['pubmed']}/"
                })
    
    return jsonify(papers[:5])  # Return top 5 papers

if __name__ == '__main__':
    app.run(debug=True)
