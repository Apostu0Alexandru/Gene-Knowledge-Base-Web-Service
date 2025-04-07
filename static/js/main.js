// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Parse the volcano plot data from the server
    const volcanoDataElement = document.getElementById('volcano-data');
    if (!volcanoDataElement) {
        console.error("Could not find volcano-data element");
        return;
    }
    
    try {
        const volcanoData = JSON.parse(volcanoDataElement.textContent);
        
        // Debug output to see the data structure
        console.log("Volcano data loaded:", volcanoData);
        
        // Verify that data points exist
        if (volcanoData.data && volcanoData.data.length > 0 && volcanoData.data[0].x) {
            console.log(`Found ${volcanoData.data[0].x.length} data points`);
        } else {
            console.error("No data points found in the volcano data");
        }
        
        // Render the volcano plot
        Plotly.newPlot('volcano', volcanoData.data, volcanoData.layout, {
            responsive: true,
            displayModeBar: true
        }).then(() => {
            console.log("Volcano plot rendered successfully");
        }).catch(err => {
            console.error("Error rendering volcano plot:", err);
        });
        
        // Add click event to the volcano plot
        document.getElementById('volcano').on('plotly_click', function(data) {
            if (!data || !data.points || data.points.length === 0) {
                console.error('No point data available in click event');
                return;
            }
            
            const point = data.points[0];
            const gene = point.text;
            
            console.log(`Selected gene: ${gene}`);
            
            // Display loading indicators
            document.getElementById('boxplot').innerHTML = '<p>Loading boxplot data...</p>';
            document.getElementById('publications-content').innerHTML = '<p>Loading publication data...</p>';
            
            // Load the boxplot for the selected gene
            fetch(`/boxplot/${gene}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(boxplotData => {
                    if (boxplotData.error) {
                        document.getElementById('boxplot').innerHTML = `<p class="error">${boxplotData.error}</p>`;
                        return;
                    }
                    
                    console.log("Boxplot data received:", boxplotData);
                    
                    Plotly.newPlot('boxplot', boxplotData.data, boxplotData.layout, {
                        responsive: true
                    }).catch(err => {
                        console.error("Error rendering boxplot:", err);
                        document.getElementById('boxplot').innerHTML = '<p class="error">Error rendering boxplot.</p>';
                    });
                })
                .catch(error => {
                    console.error('Error loading boxplot:', error);
                    document.getElementById('boxplot').innerHTML = '<p class="error">Error loading boxplot data. Please try again.</p>';
                });
            
            // Load the gene information for the selected gene
            fetch(`/gene_info/${gene}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(geneInfo => {
                    const publicationsDiv = document.getElementById('publications-content');
                    
                    if (geneInfo.error) {
                        publicationsDiv.innerHTML = `<p class="error">${geneInfo.error}</p>`;
                        return;
                    }
                    
                    console.log("Publication data received:", geneInfo);
                    
                    if (geneInfo.publications && geneInfo.publications.length > 0) {
                        let publicationsHtml = `<h3>Publications for ${gene}</h3><ul class="publication-list">`;
                        geneInfo.publications.forEach(pub => {
                            publicationsHtml += `
                                <li class="publication-item">
                                    <a href="${pub.url}" target="_blank" rel="noopener noreferrer">
                                        PubMed ID: ${pub.pubmed_id}
                                    </a>
                                </li>`;
                        });
                        publicationsHtml += '</ul>';
                        publicationsDiv.innerHTML = publicationsHtml;
                    } else {
                        publicationsDiv.innerHTML = `<p>No publications found for ${gene}.</p>`;
                    }
                })
                .catch(error => {
                    console.error('Error loading gene information:', error);
                    document.getElementById('publications-content').innerHTML = 
                        '<p class="error">Error loading publication data. Please try again.</p>';
                });
        });
    } catch (error) {
        console.error("Error parsing volcano data:", error);
        document.getElementById('volcano').innerHTML = 
            '<p class="error">Error loading volcano plot data. Please check the console for details.</p>';
    }
});
