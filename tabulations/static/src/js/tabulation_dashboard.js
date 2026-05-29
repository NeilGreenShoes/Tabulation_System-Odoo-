/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, useRef } from "@odoo/owl";

class TabulationDashboardController extends FormController {

    setup() {
        super.setup();

        this.busService = useService("bus_service");
        this.orm = useService("orm");
        this.actionService = useService("action");

        this.events = [];
        this.teams = [];
        this.team_banner = [];
        this.standings = [];
        this.stages = [];
        this.sessions = [];
        this.judges = [];

        this.standingsRef = useRef("standingsContainer");

        onWillStart(async () => {
            await this.loadDashboard();
        });

        onMounted(() => {
            this.busService.subscribe("dashboard_refresh", (payload) => {
                this.loadDashboard().then(() => {
                    this.renderDashboard();
                });
            });

            this.busService.start();
            
            setTimeout(() => {
                this.renderDashboard();
            }, 100);
        });
    }

    async loadDashboard() {
        try {
            const data = await this.orm.call(
                "report.tabulation.dashboard",
                "get_dashboard_data",
                []
            );

            this.events = data.events || [];
            this.teams = data.teams || [];
            this.team_banner = data.teams || [];
            this.standings = data.standings || [];
            this.sessions = data.sessions || [];

            console.log(this.events)
            console.log("THIS IS TEAMS: ", this.teams)
            console.log(this.standings)
            console.log(this.sessions)


        } catch (error) {
            console.error("Dashboard load failed:", error);
        }
    }

    renderDashboard() {
        const root = document.querySelector(".o_tabulation_dashboard");
        if (!root) return;

        // EVENTS
        const eventsDiv = root.querySelector(".events");
        if (eventsDiv) {
            let html = `
                <div class="card">
                    <div class="event-container">
            `;

            this.events.forEach(event => {
                html += `
                    <div class="event-card border rounded p-2 mb-2">
                        <strong>${event.name}</strong>
                        <div>Start: ${event.start_date || ""} End: ${event.end_date || ""}</div><hr/>
                        <div>Points: <span class="event-score">${event.max_points}</span></div>
                `;

                if (event.is_weighted){
                    html += `
                        <div>is weighted?: ${event.is_weighted}</div>
                        <div>weight: ${event.weight}</div>
                    `;
                }

                html += `</div>`;
            });

            html += `
                    </div>
                </div>
            `;
            eventsDiv.innerHTML = html;
        }

        // TEAMS
        const teamsDiv = root.querySelector(".teams");
        if (teamsDiv) { 
            let html = `
                <div class="card">
                    <div class="team-container">
            `;

            this.teams.forEach(team => {
                const imageSrc = team.team_banner || '';
                const bannerStyle = imageSrc 
                    ? `background: linear-gradient(to left, rgba(255,255,255,0) 30%, rgba(255,255,255,1) 100%), url('${imageSrc}') center/cover no-repeat; height: 80px;`
                    : `linear-gradient(to left, rgba(255,255,255,1) 30%, rgb(0, 0, 0) 100%)) center/cover no-repeat; height: 80px;`;

                html += `
                    <div class="team-card border rounded mb-2 overflow-hidden" style="${bannerStyle} width: 250px; display: inline-block; margin: 5px;">
                        <div class="p-2">
                            <strong>${team.team_name}</strong>
                            <div>Score: ${team.score || 0}</div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
            teamsDiv.innerHTML = html;
        }

        // SESSIONS
        const sessionsDiv = root.querySelector(".sessions");
        if (sessionsDiv) {
            let html = "";

            this.sessions.forEach(session => {
                const isActive = session.stage === 'Active';
                const isEnded = session.stage === 'End' || session.stage === 'Finished';
                const isInnactive = session.stage === 'Innactive';

                let stageColorClass = 'text-muted'; 
                let classToApply = '';

                if (isActive) {
                    stageColorClass = 'text-success'; 
                    classToApply = 'isActive';
                } else if (isEnded) {
                    stageColorClass = 'text-danger'; 
                    classToApply = 'isEnded';
                } else if (isInnactive) { 
                    stageColorClass = 'text-warning'; 
                    classToApply = 'isInnactive';
                }

                html += `
                    <div class="session-card " data-id="${session.id}">  
                        <div class="session-card-bg ${classToApply}">
                            <div class="session-name oe_title"><h2><strong>Session:</strong> ${session.name}</h2></div>
                            <div class="session-event"><h3><strong>Event:</strong> ${session.event ? session.event.name : 'No Event'}</h3></div>
                            <div class="session-stage">
                                <h4><strong>Status:</strong> 
                                <span class="session-status ${stageColorClass}"> ${session.stage}</span></h4>
                            </div>
                        </div>
                    </div>
                    <hr/>
                `;
            });

            sessionsDiv.innerHTML = html;

            sessionsDiv.addEventListener("click", (event) => {
                const card = event.target.closest(".session-card");
                if (card) {
                    const sessionId = parseInt(card.dataset.id);
                    this.actionService.doAction({
                        name: "Session Details Overview",
                        type: "ir.actions.act_window",
                        res_model: "tabulation.session.wizard",
                        views: [[false, "form"]],
                        target: "new", 
                        view_id: "tabulations.view_tabulation_session_wizard_form",
                        context: {
                            "default_session_id": sessionId,
                        }
                    });
                }
            });
        }

        // STANDINGS
        this.renderStandings();
    }

    renderStandings() {
        const standingsDiv = this.standingsRef.el || document.querySelector(".o_tabulation_dashboard .standings");
        if (!standingsDiv) return;

        let html = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h3 class="mb-0">Standings View</h3>
                    <ul class="nav nav-pills card-header-pills" id="standingsTab" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active" id="list-tab" data-bs-toggle="tab" data-bs-target="#listView" type="button" role="tab" aria-controls="listView" aria-selected="true">
                                List View
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="graph-tab" data-bs-toggle="tab" data-bs-target="#graphView" type="button" role="tab" aria-controls="graphView" aria-selected="false">
                                Graph View
                            </button>
                        </li>
                    </ul>
                </div>

                <div class="card-body tab-content">
                    <div class="tab-pane fade show active" id="listView" role="tabpanel" aria-labelledby="list-tab">
                        <table class="table table-striped mb-0">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Team</th>
                                    <th>Score</th>
                                </tr>
                            </thead>
                            <tbody>
        `;

        this.standings.forEach((team, index) => {
            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${team.team_name}</td>
                    <td>${team.score || 0}</td>
                </tr>
            `;
        });

        html += `
                            </tbody>
                        </table>
                    </div>

                    <div class="tab-pane fade" id="graphView" role="tabpanel" aria-labelledby="graph-tab">
                        <div style="position: relative; height: 350px; width: 100%; display: block;">
                            <canvas id="standingsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;

        standingsDiv.innerHTML = html;

        const tabTriggerList = [].slice.call(standingsDiv.querySelectorAll('[data-bs-toggle="tab"]'));
        tabTriggerList.forEach((tabTriggerEl) => {
            if (window.bootstrap && window.bootstrap.Tab) {
                new window.bootstrap.Tab(tabTriggerEl);
            }
        });

        requestAnimationFrame(() => {
            if (typeof Chart !== 'undefined') {
                const ctx = standingsDiv.querySelector('#standingsChart');
                if (ctx) {
                    const existingChart = Chart.getChart(ctx);
                    if (existingChart) existingChart.destroy();

                    const chart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: this.standings.map(team => team.team_name),
                            datasets: [{
                                label: 'Scores',
                                data: this.standings.map(team => team.score || 0),
                                backgroundColor: 'rgba(13, 110, 253, 0.2)',
                                borderColor: 'rgba(13, 110, 253, 1)',
                                borderWidth: 2,
                                borderRadius: 4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: { beginAtZero: true }
                            },
                            plugins: {
                                legend: { display: false }
                            }
                        }
                    });

                    const graphTabBtn = standingsDiv.querySelector('#graph-tab');
                    if (graphTabBtn) {
                        graphTabBtn.addEventListener('shown.bs.tab', () => {
                            chart.resize();
                            chart.update();
                        });
                    }
                }
            } else {
                console.error("Chart.js missing globally. Verify 'web.assets_backend' includes Chart.js references.");
            }
        });
    }
}

registry.category("views").add("tabulation_dashboard_js", {
    ...formView,
    Controller: TabulationDashboardController,
});