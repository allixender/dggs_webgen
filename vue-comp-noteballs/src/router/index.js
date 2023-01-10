import { createRouter, createWebHashHistory } from "vue-router";

import ViewNotes from "@/views/ViewNotes.vue";
import ViewStats from "@/views/ViewStats.vue";

const GlobeDemo = () => import("@/views/GlobeDemo.vue");
const CesiumDemo = () => import("@/views/CesiumDemo.vue");
const DeckglDemo = () => import("@/views/DeckglDemo.vue");

const routes = [
  {
    path: "/",
    name: "notes",
    component: ViewNotes,
  },
  {
    path: "/stats",
    name: "stats",
    component: ViewStats,
  },
  {
    path: "/globe",
    name: "globe",
    component: GlobeDemo,
  },
  {
    path: "/cesium",
    name: "cesium",
    component: CesiumDemo,
  },
  {
    path: "/deckgl",
    name: "deckgl",
    component: DeckglDemo,
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes: routes,
});

export default router;
