const timestamps = chartData.timestamps;
const hydroData = chartData.hydro;
const thermalData = chartData.thermal;
const ctx = document.getElementById('chart').getContext('2d');

new Chart(ctx, {
    type: 'line',
    data: {
        labels: timestamps,
        datasets: [
            {
                label: 'Hydro',
                data: hydroData,
                borderColor: '#4faaf9',
                backgroundColor: 'rgba(79,170,249,0.1)',
                fill: true
            },
            {
                label: 'Thermal',
                data: thermalData,
                borderColor: '#f7744c',
                backgroundColor: 'rgba(247, 116, 76, 0.1)',
                fill: true
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Timestamp'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Values'
                },
                beginAtZero: true
            }
        }
    }
});
