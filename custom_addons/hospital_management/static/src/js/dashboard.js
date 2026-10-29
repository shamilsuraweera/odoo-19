/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class HospitalDashboard extends Component {
    static template = "hospital_management.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: {} });
        onWillStart(async () => {
            this.state.data = await this.orm.call("hospital.appointment", "get_dashboard_data", []);
        });
    }

    openAppointments(name, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "hospital.appointment",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }

    openModel(name, resModel, domain = []) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: resModel,
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }
}

registry.category("actions").add("hospital_dashboard", HospitalDashboard);
