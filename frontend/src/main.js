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

const router = createRouter({
  history: createWebHistory("/KayanickCRM"),
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
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
})
createApp(App).use(router).mount("#app")
