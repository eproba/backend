let user
let team
let users

const functionMap = {
    0: 'Druh',
    1: 'Podzastępowy(-a)',
    2: 'Zastępowy(-a)',
    3: 'Przyboczny(-a)',
    4: 'Drużynowy(-a)',
    5: 'Wyższa funkcja',
}

// Function to fetch the current user
async function getUser() {
    const response = await fetch('/api/user/');
    user = await response.json();
}

// Function to fetch the team data
async function getTeam(teamId) {
    const response = await fetch(`/api/teams/${teamId}/`);
    team = await response.json();
}

// Function to fetch the users of the team
async function getUsers(teamId) {
    const response = await fetch(`/api/users/?team=${teamId}`);
    users = await response.json();
}


// Utility function to generate a random muted color
function getRandomMutedColor() {
    const hue = Math.floor(Math.random() * 360); // Random hue
    const saturation = 30; // Low saturation for muted colors
    const lightness = 50; // Mid-range lightness
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

// Utility function to adjust the brightness of a color
function adjustColorBrightness(color, amount) {
    const hsl = color.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
    const hue = parseInt(hsl[1]);
    const saturation = parseInt(hsl[2]);
    const lightness = parseInt(hsl[3]) + amount;
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

async function prepareData() {
    // Step 1: Create a base structure for the team
    let teamData = {
        id: team.id,
        data: {
            id: team.id,
            name: team.short_name,
        },
        options: {
            nodeBGColor: 'var(--bulma-primary)', // Team node color
            nodeBGColorHover: 'var(--bulma-primary)', // Team node color on hover
        },
        children: [], // This will hold patrols
    };

    // Step 2: Create a map of patrols to users with colors
    const patrolsMap = {};

    // Initialize patrolsMap with patrols from the team
    team.patrols.forEach((patrol) => {
        const baseColor = getRandomMutedColor(); // Generate a muted color for the patrol
        const patrolColor = adjustColorBrightness(baseColor, 10); // Slightly lighten the base color for the patrol node

        patrolsMap[patrol.id] = {
            id: patrol.id,
            data: {
                id: patrol.id,
                name: patrol.name,
            },
            options: {
                nodeBGColor: patrolColor, // Patrol node color
                nodeBGColorHover: adjustColorBrightness(patrolColor, 10), // Lighten the color on hover
            },
            children: [], // This will hold users
        };

        // Step 3: Set the base color to be used for users in this patrol
        patrolsMap[patrol.id].baseColor = baseColor; // Base color for users
    });

    // Step 4: Add users to their respective patrols with new data structure
    users.forEach((user) => {
        const patrolId = user.patrol;

        if (patrolsMap[patrolId]) {
            patrolsMap[patrolId].children.push({
                id: user.id,
                data: {
                    id: user.id,
                    is_user: true,
                    name: user.nickname || `${user.first_name} ${user.last_name}` || 'Unknown',
                    rank: user.rank,
                    is_active: user.is_active,
                    function: user.function,
                },
                options: {
                    nodeBGColor: patrolsMap[patrolId].baseColor, // User node color
                    nodeBGColorHover: adjustColorBrightness(patrolsMap[patrolId].baseColor, 10), // Lighten the color on hover
                },
            });
        }
    });

    // Step 5: Sort users within each patrol by function and name
    Object.values(patrolsMap).forEach((patrol) => {
        patrol.children.sort((a, b) => {
            if (a.data.function !== b.data.function) {
                return a.data.function - b.data.function; // Sort by function (ascending)
            }
            // If functions are the same, sort by name (ascending)
            const nameA = a.data.name.toLowerCase();
            const nameB = b.data.name.toLowerCase();
            if (nameA < nameB) return -1;
            if (nameA > nameB) return 1;
            return 0;
        });
    });

    // Step 6: Add all patrols (including empty ones) to the teamData
    Object.values(patrolsMap).forEach((patrol) => {
        teamData.children.push(patrol);
    });

    // Return the prepared data
    return teamData;
}


async function renderTeamGraph(data) {
    const box = document.getElementById('team-graph');
    const computedStyle = getComputedStyle(box);
    const paddingLeft = parseFloat(computedStyle.paddingLeft);
    const paddingRight = parseFloat(computedStyle.paddingRight);
    const width = box.offsetWidth - paddingLeft - paddingRight;

    // calculate remaining height for the tree from 100vh - distance from top of the page to the top of the box
    const boxRect = box.getBoundingClientRect();
    const top = boxRect.top;
    const height = Math.min(window.innerHeight - top - parseFloat(computedStyle.paddingTop) - parseFloat(computedStyle.paddingBottom) - 20, window.innerHeight * 0.8);

    const options = {
        contentKey: 'data',
        width: width,
        height: height,
        nodeWidth: 120,
        nodeHeight: 80,
        childrenSpacing: 100,
        siblingSpacing: 30,
        direction: 'top',
        canvasStyle: 'border: 1px solid var(--bulma-border-weak); border-radius: 5px;',
        nodeTemplate: (content) =>
            `<div style='display: flex;flex-direction: column;justify-content: center;align-items: center;height: 100%; ${content.is_user ? 'cursor:pointer' : ''}' id='node-${content.id}' class='node' data-node='${JSON.stringify(content)}'>
            <div style="font-weight: bold; font-size: 14px">${content.name}</div>
            ${content.is_user ? `
            <div style="font-size: 12px">${content.rank}</div>
            ${!content.is_active ? '<div style="font-size: 12px; color: red;">Nieaktywny</div>' : ''}
            ${content.function !== 0 ? `<div style="font-size: 12px">${functionMap[content.function]}</div>` : ''}
            ` : ''}
          </div>`,
    };

    const tree = new ApexTree(document.getElementById('svg-tree'), options);
    const graph = tree.render(data);
}

async function nodeClickHandler(nodeId) {
    const node = document.getElementById(nodeId);
    const nodeData = node.dataset.node;

    if (nodeData) {
        const data = JSON.parse(nodeData);

        if (data.is_user) {
            location.href = `/team/user/${data.id}`;
        }
    }
}


document.addEventListener('DOMContentLoaded', async () => {
        // Add a click event to switch to graph view
        document.getElementById('list-view-button').addEventListener('click', () => {
            const url = new URL(window.location.href);
            url.searchParams.delete('graph');
            location.href = url;
        });

        await getUser();

        const teamId = user.team;

        await Promise.all([
            getTeam(teamId),
            getUsers(teamId),
        ]);

        const data = await prepareData();

        await renderTeamGraph(data);

        document.querySelectorAll('.node').forEach((node) => {
            node.addEventListener('click', (event) => nodeClickHandler(event.currentTarget.id));
        });

        window.addEventListener('resize', async () => {
            const canvas = document.getElementById('svg-tree');
            canvas.remove();
            const newCanvas = document.createElement('div');
            newCanvas.id = 'svg-tree';
            document.getElementById('team-graph').appendChild(newCanvas);
            await renderTeamGraph(data);

            document.querySelectorAll('.node').forEach((node) => {
                node.addEventListener('click', (event) => nodeClickHandler(event.currentTarget.id));
            });
        });
    }
);
