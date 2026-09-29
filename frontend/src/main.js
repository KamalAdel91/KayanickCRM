import { createApp } from "vue"
import { createRouter, createWebHistory } from "vue-router"
import "./style.css"
import App from "./App.vue"
import Today from "./views/TodayView.vue"
import NewVisit from "./views/NewVisitView.vue"
import Search from "./views/SearchView.vue"
import Cases from "./views/CasesView.vue"
import NewCase from "./views/NewCaseView.vue"

const router = createRouter({
  history: createWebHistory("/kayanick"),
  routes: [
    { path: "/", name: "today", component: Today },
    { path: "/visit", name: "visit", component: NewVisit },
    { path: "/search", name: "search", component: Search },
    { path: "/cases", name: "cases", component: Cases },
    { path: "/case/new", name: "case", component: NewCase },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
})
createApp(App).use(router).mount("#app")
