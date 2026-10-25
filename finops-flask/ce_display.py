import datetime
import json
import decimal
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

# Function to fetch data from the database based on the cost center and date range
def fetch_data_by_cost_center_and_date_range(cost_center, start_date, end_date):
    conn = psycopg2.connect(
        dbname='finops',
        user='odoo',
        password='kepoajalu',
        host='localhost',
        port='5432'
    )
    cursor = conn.cursor()

    cursor.execute(f"SELECT service, cost, date FROM cost WHERE cost_center = '{cost_center}' AND date BETWEEN '{start_date}' AND '{end_date}'")
    rows = cursor.fetchall()

    data = []
    for row in rows:
        service = row[0]
        cost = float(row[1]) if isinstance(row[1], decimal.Decimal) else row[1]
        date = row[2].strftime('%b-%d*')
        data.append({'service': service, 'cost': cost, 'date': date})

    cursor.close()
    conn.close()

    return data

# Function to calculate the total cost for each service on a specific date
def calculate_service_total(data):
    service_totals = {}
    for entry in data:
        key = (entry['service'], entry['date'])
        if key not in service_totals:
            service_totals[key] = 0
        service_totals[key] += entry['cost']
    return [{'service': key[0], 'total_cost': value, 'date': key[1]} for key, value in service_totals.items()]

# Function to get the available dates for the specified cost center
def get_available_dates(cost_center):
    conn = psycopg2.connect(
        dbname='finops',
        user='odoo',
        password='kepoajalu',
        host='localhost',
        port='5432'
    )
    cursor = conn.cursor()

    cursor.execute(f"SELECT DISTINCT date FROM cost WHERE cost_center = '{cost_center}'")
    rows = cursor.fetchall()

    dates = [row[0].strftime('%b-%d*') for row in rows]

    cursor.close()
    conn.close()

    return dates

@app.route('/data')
def get_filtered_data():
    cost_center = request.args.get('cost_center')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    filtered_data = fetch_data_by_cost_center_and_date_range(cost_center, start_date, end_date)
    service_totals = calculate_service_total(filtered_data)
    
    # Get available dates for the specified cost center
    dates = get_available_dates(cost_center)
    
    # Add the available dates to the response
    response = {'service_totals': service_totals, 'dates': dates}
    
    return jsonify(response)

@app.route('/')
def index():
    # Fetch available cost centers from the database
    conn = psycopg2.connect(
        dbname='finops',
        user='odoo',
        password='kepoajalu',
        host='localhost',
        port='5432'
    )
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT cost_center FROM cost")
    rows = cursor.fetchall()

    cost_centers = [row[0] for row in rows]

    cursor.close()
    conn.close()

    # Generate HTML template with cost centers as options in the dropdown menu
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cost and Usage Breakdown</title>
        <!-- Bootstrap CSS -->
        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <div class="container mt-3">
            <div class="row">
                <div class="col-md-4">
                    <label for="cost-center-select">Select Cost Center:</label>
                    <select class="form-control" id="cost-center-select">
    """

    for cost_center in cost_centers:
        html_template += f"<option value='{cost_center}'>{cost_center}</option>"

    html_template += """
                    </select>
                </div>
                <div class="col-md-4">
                    <label for="start-date">Start Date:</label>
                    <input type="date" class="form-control" id="start-date">
                </div>
                <div class="col-md-4">
                    <label for="end-date">End Date:</label>
                    <input type="date" class="form-control" id="end-date">
                </div>
            </div>
            <div class="row mt-3">
                <div class="col">
                    <button class="btn btn-primary" onclick="applyFilter()">Apply Filter</button>
                </div>
            </div>
            <div class="row mt-3">
                <canvas id="myChart"></canvas>
            </div>
            <div class="row mt-3">
                <table class="table table-bordered" id="cost-usage-table">
                    <thead class="thead-light">
                        <tr>
                            <th>Service</th>
                            <th id="date-columns"></th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
        <script>
            var ctx = document.getElementById('myChart').getContext('2d');
            var myChart;

            function applyFilter() {
                var costCenter = document.getElementById('cost-center-select').value;
                var startDate = document.getElementById('start-date').value;
                var endDate = document.getElementById('end-date').value;
                fetchAndUpdateChart(costCenter, startDate, endDate);
                fetchAndUpdateTable(costCenter, startDate, endDate);
            }

            function fetchAndUpdateChart(costCenter, startDate, endDate) {
                fetch(`/data?cost_center=${costCenter}&start_date=${startDate}&end_date=${endDate}`)
                .then(response => response.json())
                .then(data => {
                    updateChart(data);
                });
            }

            function fetchAndUpdateTable(costCenter, startDate, endDate) {
                fetch(`/data?cost_center=${costCenter}&start_date=${startDate}&end_date=${endDate}`)
                .then(response => response.json())
                .then(data => {
                    updateTable(data);
                });
            }

            function updateChart(data) {
                if (myChart) {
                    myChart.destroy();
                }

                var datasets = [];
                var serviceData = {};

                data.service_totals.forEach(entry => {
                    if (!(entry.service in serviceData)) {
                        serviceData[entry.service] = [];
                    }
                    serviceData[entry.service].push({ x: entry.date, y: entry.total_cost });
                });

                Object.entries(serviceData).forEach(([service, data]) => {
                    datasets.push({
                        label: service,
                        data: data,
                        stack: 'stack1', 
                        borderWidth: 1
                    });
                });

                var chartConfig = {
                    type: 'bar',  // Change to 'bar' for stacked bar chart
                    data: { datasets: datasets },
                    options: {
                        scales: {
                            xAxes: [{ type: 'time', time: { unit: 'day' } }],
                            yAxes: [{ stacked: true, ticks: { beginAtZero: true } }]
                        }
                    }
                };

                myChart = new Chart(ctx, chartConfig);
            }

            function updateTable(data) {
                var tableBody = document.querySelector('#cost-usage-table tbody');
                tableBody.innerHTML = '';

                // Extract the unique months from the data
                var months = data.dates;

                // Prepare a dictionary to hold service costs for each month
                var monthlyCosts = {};

                // Iterate over the data to populate the monthlyCosts dictionary
                data.service_totals.forEach(entry => {
                    var service = entry.service;
                    var date = entry.date;
                    var cost = entry.total_cost;

                    // Initialize an empty dictionary for the service if not already present
                    if (!monthlyCosts[service]) {
                        monthlyCosts[service] = {};
                    }

                    // Store the cost for the corresponding month and year
                    monthlyCosts[service][date] = cost;
                });

                // Filter months based on the range selected by the user
                var startDate = document.getElementById('start-date').value;
                var endDate = document.getElementById('end-date').value;
                var filteredMonths = months.filter(month => (month >= startDate && month <= endDate));

                // Generate the table header with month-year format
                var tableHeader = '<tr><th>Service</th>';
                filteredMonths.forEach(month => {
                    tableHeader += `<th>${month}</th>`;
                });
                tableHeader += '</tr>';
                document.querySelector('#cost-usage-table thead').innerHTML = tableHeader;

                // Iterate over the monthlyCosts dictionary to generate table rows
                for (var service in monthlyCosts) {
                    var row = `<tr><td>${service}</td>`;

                    // Iterate over the filtered months to populate the table cells
                    filteredMonths.forEach(month => {
                        var cost = monthlyCosts[service][month] || '';
                        row += `<td>${cost}</td>`;
                    });

                    row += '</tr>';
                    tableBody.innerHTML += row;
                }
            }
            // Initial chart and table load
            applyFilter();
        </script>
    </body>
    </html>
    """

    return html_template

if __name__ == '__main__':
    app.run(debug=True)
