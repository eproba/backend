let user
let users

// Function to fetch the current user
async function getUser() {
    const response = await fetch('/api/user/');
    user = await response.json();
}

// Function to fetch the users of the team
async function getUsers(teamId) {
    const response = await fetch(`/api/users/?team=${teamId}`);
    users = await response.json();
}


async function prepareData() {
    const ranks = users.map(user => user.rank);
    const uniqueRanks = [...new Set(ranks)];
    const data = Array(uniqueRanks.length).fill(0);
    ranks.forEach(rank => data[uniqueRanks.indexOf(rank)]++);
    return {
        series: data,
        labels: uniqueRanks,
    };
}


async function renderPieChart(data) {

    console.log(data);

    var options = {
        series: data.series,
        chart: {
            width: 380,
            type: 'pie',
        },
        labels: data.labels,
        stroke: {
            width: 1,
            colors: 'var(--bulma-box-background-color)',
        },
        legend: {
            show: true,
            labels: {
                colors: "var(--bulma-text)",
            },
        },
        responsive: [{
            breakpoint: 480,
            options: {
                chart: {
                    width: 300
                },
                legend: {
                    position: 'bottom'
                }
            }
        }]
    };

    var chart = new ApexCharts(document.querySelector("#chart"), options);
    chart.render();


}


document.addEventListener('DOMContentLoaded', async () => {

        await getUser();

        const teamId = user.team;

        await getUsers(teamId);

        const data = await prepareData();

        await renderPieChart(data);

    }
);
