import { createApp } from "vue"
import { createRouter, createWebHistory } from "vue-router"
import "./style.css"
import "./install"
import App from "./App.vue"
import Today from "./views/TodayView.vue"
import NewVisit from "./views/NewVisitView.vue"
import Search from "./views/SearchView.vue"
import Cases from "./views/CasesView.vue"
import NewCase from "./views/NewCaseView.vue"
import CaseDetail from "./views/CaseView.vue"
import Visits from "./views/VisitsView.vue"
import VisitDetail from "./views/VisitView.vue"
import Notifications from "./views/NotificationsView.vue"
import Profile from "./views/ProfileView.vue"
import Account from "./views/AccountView.vue"
import ChangePassword from "./views/ChangePasswordView.vue"
import ResetPassword from "./views/ResetPasswordView.vue"
import Debts from "./views/DebtsView.vue"
import Debt from "./views/DebtView.vue"
import Invoice from "./views/InvoiceView.vue"
import Orders from "./views/OrdersView.vue"
import NewOrder from "./views/NewOrderView.vue"
import Order from "./views/OrderView.vue"

const router = createRouter({
  history: createWebHistory("/KayanickCRM"),
  scrollBehavior(to, from, saved) {
    // lists are kept alive; give them a moment to render before restoring where you were
    if (saved) return new Promise((resolve) => setTimeout(() => resolve(saved), 200))
    return { top: 0 }
  },
  routes: [
    { path: "/", name: "today", component: Today },
    { path: "/visit", name: "visit", component: NewVisit },
    { path: "/search", name: "search", component: Search },
    { path: "/cases", name: "cases", component: Cases },
    { path: "/case/new", name: "case", component: NewCase },
    { path: "/case/:name", name: "case-detail", component: CaseDetail },
    { path: "/visits", name: "visits", component: Visits },
    { path: "/visits/:name", name: "visit-detail", component: VisitDetail },
    { path: "/notifications", name: "notifications", component: Notifications },
    { path: "/hospital/:name", name: "hospital", component: Profile },
    { path: "/doctor/:name", name: "doctor", component: Profile },
    { path: "/debts", name: "debts", component: Debts },
    { path: "/debts/:customer", name: "debt", component: Debt },
    { path: "/invoice/:name", name: "invoice", component: Invoice },
    { path: "/orders", name: "orders", component: Orders },
    { path: "/orders/new", name: "new-order", component: NewOrder },
    { path: "/orders/:name", name: "order", component: Order },
    { path: "/account", name: "account", component: Account },
    { path: "/change-password", name: "change-password", component: ChangePassword },
    { path: "/admin/reset-password", name: "reset-password", component: ResetPassword },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
})
createApp(App).use(router).mount("#app")
